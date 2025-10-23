
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta

from .models import SimState, KPIResponse, ApplyActionRequest, ApplyActionResponse
from .adapters.config import settings
from .adapters.erp import make_erp
from .adapters.wms import WMS
from .adapters.cmms import CMMS
from .adapters.supplier import SupplierNet

app = FastAPI(title="Manufacturing AI Assist API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATE_FP = DATA / "sim_state.json"
SALES_LOG_FP = DATA / "sales_log.jsonl"

def load_df(name:str)->pd.DataFrame:
    df = pd.read_csv(DATA / f"{name}.csv")
    for c in df.columns:
        if any(k in c.lower() for k in ["date","start","end","planned"]):
            df[c] = pd.to_datetime(df[c])
    return df

def get_state()->SimState:
    if not STATE_FP.exists():
        s = SimState()
        STATE_FP.write_text(s.model_dump_json())
        return s
    return SimState.model_validate_json(STATE_FP.read_text())

def save_state(s:SimState): STATE_FP.write_text(s.model_dump_json())

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/reset")
def reset():
    s = SimState(); save_state(s)
    return {"status":"reset", "state": s.model_dump()}

def compute_kpis(state:SimState)->KPIResponse:
    orders = load_df("orders"); quality = load_df("quality_inspections"); down = load_df("downtime_log"); inv = load_df("inventory")
    eta_days = max(0, 3 - (state.eta_offset_days + state.carrier_upgrade_days))
    otd_risk = 9.5 - (state.eta_offset_days*2.0 + state.carrier_upgrade_days*1.2)
    otd_risk = max(1.0, min(otd_risk, 15.0))
    recent = orders[orders['order_date'] >= (orders['order_date'].max() - pd.Timedelta(days=6))]
    throughput = recent['qty_produced'].sum() / max(1,(recent['order_date'].nunique()))
    if state.resequence: throughput *= 1.03
    if state.batch_changeovers: throughput *= 1.02
    if state.qa_fast_track: throughput *= 1.01
    on_time = (orders['actual_ship_date'] <= orders['promised_ship_date']).mean() * 100
    total_units = quality['units_inspected'].sum(); defects = quality['defects_found'].sum()
    defect_pct = (defects/total_units*100) if total_units else 0.0
    down_recent = down[down['start'] >= (down['start'].max() - pd.Timedelta(days=6))]
    downtime_hours = down_recent['duration_min'].sum()/60.0
    if state.batch_changeovers: downtime_hours = max(0.0, downtime_hours - 0.5)
    inv2 = inv.copy(); idx = inv2['sku']=="SKU-19"
    if idx.any(): inv2.loc[idx,'on_hand'] += state.extra_qty
    inventory_risk = int((inv2['on_hand'] < inv2['safety_stock']).sum())
    last3 = recent[recent['order_date'] >= (orders['order_date'].max() - pd.Timedelta(days=2))]['qty_produced'].mean()
    prev4 = recent[recent['order_date'] < (orders['order_date'].max() - pd.Timedelta(days=2))]['qty_produced'].mean()
    trend = 'up' if last3 > prev4 else 'down' if last3 < prev4 else 'flat'
    top_down = down.groupby('cause')['duration_min'].sum().sort_values(ascending=False).head(1).index.to_list()[0]
    fam = quality.groupby('defect_family')['defects_found'].sum().sort_values(ascending=False).head(1).index.to_list()[0]
    lowest = inv2.sort_values('on_hand').head(1)['sku'].iloc[0]
    return KPIResponse(throughput_per_day=float(throughput), on_time_pct=float(on_time), defect_rate_pct=float(defect_pct),
        downtime_hours=float(downtime_hours), inventory_risk_count=int(inventory_risk), throughput_trend=trend,
        top_downtime_cause=top_down, top_defect_family=fam, lowest_stock_sku=lowest, otd_risk_pct=float(round(otd_risk,1)),
        notes=f"ETA remaining delay ≈ {eta_days} days; extra_qty={state.extra_qty}, carrier_upgrade_days={state.carrier_upgrade_days}, qa_fast_track={state.qa_fast_track}")

@app.get("/metrics", response_model=KPIResponse)
def metrics(): return compute_kpis(get_state())

@app.get("/state")
def state(): return get_state().model_dump()

@app.post("/simulate/action", response_model=ApplyActionResponse)
def simulate_action(req:ApplyActionRequest):
    s = get_state(); label = (req.action or '').lower()
    if not label: raise HTTPException(400, "Missing action")
    if "expedited po" in label or "eta_minus_days" in label: s.eta_offset_days += 2
    elif "alternate supplier" in label or "add_qty" in label: s.extra_qty += 500
    elif "carrier" in label or "air" in label: s.carrier_upgrade_days += 1
    elif "qa fast" in label or "enable_alt_material" in label: s.qa_fast_track = True
    elif "re-sequence" in label or "resequence" in label: s.resequence = True
    elif "batch change" in label: s.batch_changeovers = True
    else: raise HTTPException(400, f"Unknown action: {req.action}")
    save_state(s); return ApplyActionResponse(state=s, message=f"Applied: {req.action}")

# Convenience endpoints
def erp(): return make_erp(settings.ERP_KIND, url=settings.ERP_URL, api_key=settings.ERP_API_KEY)
def wms(): return WMS(url=settings.WMS_URL, api_key=settings.WMS_API_KEY)
def cmms(): return CMMS(url=settings.CMMS_URL, api_key=settings.CMMS_API_KEY)
def supplier_net(): return SupplierNet(url=settings.SUPPLIER_URL, api_key=settings.SUPPLIER_API_KEY)

@app.get("/inventory/{sku}")
def inventory(sku:str): return erp().get_inventory(sku)
@app.post("/po/{sku}")
def create_po(sku:str, qty:int=500, supplier:str="Supplier Z", expedite:bool=True): return erp().create_po(sku=sku, qty=qty, supplier=supplier, expedite=expedite)
@app.get("/asn/{supplier}/{sku}")
def get_asn(supplier:str, sku:str): return wms().get_asn(supplier, sku)
@app.post("/cmms/wo")
def create_work_order(asset:str="Line-L2", desc:str="Batch changeover optimization"): return cmms().create_work_order(asset, desc)
@app.get("/supplier/alternate/{sku}")
def get_alternate_supplier(sku:str): return supplier_net().alternate_supplier(sku)

# Sales flow
def _append_sales_log(obj:dict):
    with open(SALES_LOG_FP, "a") as f:
        f.write(json.dumps(obj) + "\n")

@app.post("/sales/quote")
def sales_generate_quote(sku:str="HX-220", qty:int=25, ship_date:str=None, unit_price:float=762.0):
    sdate = pd.to_datetime(ship_date) if ship_date else pd.Timestamp.today()+pd.Timedelta(days=5)
    kpi = compute_kpis(get_state())
    risk = kpi.inventory_risk_count > 0 and (sdate - pd.Timestamp.today()).days <= 3
    record = {"ts": datetime.utcnow().isoformat(), "type":"quote", "sku":sku, "qty":qty, "ship_date":str(sdate.date()), "unit_price":unit_price, "risk": bool(risk)}
    _append_sales_log(record)
    msg = "Quote generated." + (" Potential stock risk flagged to Supply Chain." if risk else "")
    return {"status":"ok", "message": msg, "quote_id":"Q-"+str(int(datetime.utcnow().timestamp())), "record": record}

@app.post("/sales/email")
def sales_email(to:str="purchasing@acme.com", subject:str="Quote from Saxon.AI", body:str="Thank you.", attach_quote_id:str|None=None):
    record = {"ts": datetime.utcnow().isoformat(), "type":"email", "to":to, "subject":subject, "attach": attach_quote_id}
    _append_sales_log(record)
    return {"status":"ok", "message":"Email queued.", "record": record}

@app.post("/sales/reminder")
def sales_set_reminder(days:int=3, note:str="Follow up"):
    due = datetime.utcnow() + timedelta(days=days)
    record = {"ts": datetime.utcnow().isoformat(), "type":"reminder", "due": due.isoformat(), "note": note}
    _append_sales_log(record)
    return {"status":"ok", "message":f"Reminder set for {due.date()}.", "record": record}
