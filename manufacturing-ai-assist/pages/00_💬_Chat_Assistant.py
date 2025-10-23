
import streamlit as st, json, os, pandas as pd, requests
from pathlib import Path
from utils import api as simapi
from utils.data import load_all_data
from utils.kpis import compute_kpis

st.set_page_config(page_title="Chat Assistant", page_icon="💬", layout="wide")
st.image("assets/saxon_logo.png", width=170)
st.title("Conversation")

PERSONAS = ["Sales AE","Supply Chain Manager","Plant Manager"]
persona = st.sidebar.radio("Persona", PERSONAS, index=0)

if "chats" not in st.session_state:
    st.session_state.chats = {p: [] for p in PERSONAS}
if "script_idx" not in st.session_state:
    st.session_state.script_idx = 0
if "scenario" not in st.session_state:
    fp = Path("data/scenario.json")
    st.session_state.scenario = json.loads(fp.read_text()) if fp.exists() else None

def say(role, content): st.session_state.chats[persona].append({"role":role,"content":content})
def assistant(msg): say("assistant", msg)
def user(msg): say("user", msg)

colA,colB,colC = st.columns([1,1,1])
if colA.button("Nudge"):
    if simapi.api_up():
        m = simapi.get_metrics() or {}
        if persona=="Supply Chain Manager":
            assistant(f"Inventory risk: {m.get('inventory_risk_count','?')}. Consider expedited PO or alternate supplier for SKU-19.")
        elif persona=="Plant Manager":
            assistant(f"Throughput trend is {m.get('throughput_trend','flat')}. Consider re-sequence or batching.")
        else:
            assistant("You can request a Daily Brief or use Sales actions.")
    else:
        assistant("Daily Brief and quick actions are available.")
if colB.button("Reset"):
    st.session_state.script_idx = 0; st.session_state.chats[persona]=[]
    if simapi.api_up(): simapi.reset()
    assistant("Reset complete.")
if colC.button("Step"):
    sc = st.session_state.scenario
    if sc and st.session_state.script_idx < len(sc["events"]):
        e = sc["events"][st.session_state.script_idx]; st.session_state.script_idx += 1
        assistant(f"**{e['dept']} ({e['t']}):** {e['msg']}  \n_Impact:_ {e['impact']}")
    else:
        assistant("End of storyline.")

st.divider()
for m in st.session_state.chats[persona]:
    with st.chat_message(m["role"]): st.markdown(m["content"])

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")

API_URL = os.environ.get("MFG_API_URL","http://localhost:8000")

if persona=="Sales AE":
    if st.sidebar.button("Generate Quote"):
        try:
            r = requests.post(f"{API_URL}/sales/quote", json={"sku":"HX-220","qty":25,"ship_date":str(pd.Timestamp.today()+pd.Timedelta(days=5)),"unit_price":762.0})
            assistant(r.json().get("message","Quote created."))
        except Exception as e:
            assistant(f"Quote error: {e}")
    if st.sidebar.button("Email Customer"):
        try:
            requests.post(f"{API_URL}/sales/email", json={"to":"purchasing@acme.com","subject":"Quote from Saxon.AI","body":"Thank you."})
            assistant("Email queued.")
        except Exception as e:
            assistant(f"Email error: {e}")
    if st.sidebar.button("Set Reminder (3d)"):
        try:
            r = requests.post(f"{API_URL}/sales/reminder", json={"days":3,"note":"Check in"})
            assistant(r.json().get("message","Reminder set."))
        except Exception as e:
            assistant(f"Reminder error: {e}")
elif persona=="Supply Chain Manager":
    if st.sidebar.button("Create expedited PO"): assistant(simapi.post_action("Create expedited PO"))
    if st.sidebar.button("Alternate supplier"): assistant(simapi.post_action("Trigger alternate supplier"))
    if st.sidebar.button("Upgrade carrier to air"): assistant(simapi.post_action("Upgrade carrier to air"))
else:
    if st.sidebar.button("Re-sequence L2"): assistant(simapi.post_action("Re-sequence L2"))
    if st.sidebar.button("Batch changeovers"): assistant(simapi.post_action("Batch changeovers"))
    if st.sidebar.button("QA fast-track"): assistant(simapi.post_action("QA fast-track"))

prompt = st.chat_input("Type a message")
if prompt:
    user(prompt)
    low = prompt.lower()
    if "kpi" in low or "brief" in low or "status" in low:
        if simapi.api_up():
            m = simapi.get_metrics() or {}
            assistant(f"**Brief:** Throughput {m.get('throughput_per_day',0):.0f}/day, OTD risk {m.get('otd_risk_pct',0):.1f}%, On-time {m.get('on_time_pct',0):.1f}%, Defect {m.get('defect_rate_pct',0):.2f}%, Downtime {m.get('downtime_hours',0):.1f}h, Inventory risks {m.get('inventory_risk_count',0)}.")
        else:
            df_orders, df_quality, df_down, df_inv, _ = load_all_data()
            k = compute_kpis(df_orders, df_quality, df_down, df_inv)
            assistant(f"**Brief:** Throughput {k['throughput_per_day']:.0f}/day, On-time {k['on_time_pct']:.1f}%, Defect {k['defect_rate_pct']:.2f}%, Downtime {k['downtime_hours']:.1f}h, Inventory risks {k['inventory_risk_count']}.")
    else:
        assistant("Acknowledged.")
    st.experimental_rerun()
