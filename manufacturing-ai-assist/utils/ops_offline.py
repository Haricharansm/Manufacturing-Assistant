# utils/ops_offline.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from utils.data import load_all_data
from utils.kpis import compute_kpis

@dataclass
class Snapshot:
    kpis: dict
    note: str = ""

def kpi_snapshot(note: str = "") -> Snapshot:
    df_orders, df_quality, df_down, df_inv, df_wos = load_all_data()
    k = compute_kpis(df_orders, df_quality, df_down, df_inv)
    return Snapshot(kpis=k, note=note)

# ---------- Supply Chain canned actions ----------
def sc_expedite_po(sku: str = "SKU-19", days_pull: int = 2) -> str:
    snap = kpi_snapshot()
    return (
        f"**Expedited PO for {sku}**  \n"
        f"- Carrier upgraded: *priority ground → air*  \n"
        f"- Inbound ETA pulled in **{days_pull}d**  \n"
        f"- Inventory risks remain: **{snap.kpis['inventory_risk_count']}**  \n\n"
        f"**Impact**  \n"
        f"- OTD exposure window reduced.  \n"
        f"- If Plant re-sequences L2, throughput trend likely **{snap.kpis['throughput_trend']}→up**."
    )

def sc_alternate_supplier(sku: str = "SKU-19", qty: int = 500) -> str:
    snap = kpi_snapshot()
    return (
        f"**Triggered alternate supplier for {sku}**  \n"
        f"- Confirmed available qty: **{qty}**  \n"
        f"- ETA: **2d**  \n\n"
        f"**Impact**  \n"
        f"- Covers projected shortfall; inventory risk items ~ **{max(0, snap.kpis['inventory_risk_count']-1)}**.  \n"
        f"- Recommend QA fast-track on receipt."
    )

def sc_upgrade_carrier() -> str:
    return (
        "**Upgraded carrier to air**  \n"
        "- Transit reduced by **~1d**.  \n"
        "- Notify Customer Service to update promise dates if needed."
    )

def erp_snapshot(sku: str = "SKU-19") -> dict:
    return {"sku": sku, "on_hand": 1180, "safety_stock": 900, "open_pos": 2, "lead_time_days": 7, "uom": "EA"}

# ---------- Plant canned actions ----------
def plant_resequence(line: str = "L2") -> str:
    snap = kpi_snapshot()
    return (
        f"**Re-sequenced {line}** to run stocked SKUs while C-19 is inbound.  \n"
        f"- Expected throughput: **+3%** vs current {snap.kpis['throughput_per_day']:.0f}/day.  \n"
        f"- Keep QA on standby for alternate supplier lots."
    )

def plant_batch_changeovers(line: str = "L2") -> str:
    snap = kpi_snapshot()
    return (
        f"**Batched changeovers on {line}**  \n"
        f"- Setup consolidation reduces downtime **≈0.5h/day** (recent: {snap.kpis['downtime_hours']:.1f}h).  \n"
        f"- Pair with re-sequencing for best effect."
    )

def plant_qa_fast_track(sku: str = "SKU-19") -> str:
    return (
        f"**QA fast-track enabled for {sku}**  \n"
        "- Incoming alt-lots prioritized for receiving/inspection.  \n"
        "- Release-to-run target within **2h** of dock time."
    )
