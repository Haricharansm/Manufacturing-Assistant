# -*- coding: utf-8 -*-
import streamlit as st
import json, os, pandas as pd, requests, re
from pathlib import Path
from datetime import datetime

from utils import api as simapi
from utils.data import load_all_data
from utils.kpis import compute_kpis
from utils.ui import show_logo, header, chips_row, greeting
from utils.sales_offline import generate_quote, follow_up_email, propose_new_product
from utils.ops_offline import (
    sc_expedite_po, sc_alternate_supplier, sc_upgrade_carrier,
    plant_resequence, plant_batch_changeovers, plant_qa_fast_track
)

# ---------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------
st.set_page_config(page_title="Chat Assistant", page_icon="💬", layout="wide")

# ---------------------------------------------------------------------
# Header (Saxon brand) – logo + greeting + compact subtitle
# ---------------------------------------------------------------------
show_logo(width=170)
greeting(name=os.environ.get("SAXON_USER_NAME", "there"), right_badge="Manufacturing AI Assist")
header("Conversation", "Chat-first copilot for Sales • Supply Chain • Plant")

# KPI chips (static sample; can be computed if API is on)
chips_row([("On-time ↑", "success"), ("Inventory risks: 3", "warn"), ("Downtime 1.2h", "neutral")])

PERSONAS = ["Sales AE", "Supply Chain Manager", "Plant Manager"]
persona = st.sidebar.radio("Persona", PERSONAS, index=0)

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {p: [] for p in PERSONAS}
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "last_quote" not in st.session_state:
    st.session_state.last_quote = None
if "scenario" not in st.session_state:
    fp = Path("data/scenario.json")
    st.session_state.scenario = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None
if "script_idx" not in st.session_state:
    st.session_state.script_idx = 0

def say(role, content): st.session_state.chats[persona].append({"role": role, "content": content})
def assistant(msg):     say("assistant", msg)
def user(msg):          say("user", msg)
def add_task(persona_label, kind, title, details=""):
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": persona_label,
        "kind": kind,
        "title": title,
        "details": details
    })

# ---------------------------------------------------------------------
# Intelligent nudges (brand-forward, no demo-y header buttons)
# ---------------------------------------------------------------------
with st.expander("🔔 Intelligent nudges", expanded=True):
    # Sales nudges example (shown regardless; feel free to branch by persona)
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("**Cross-sell opportunity**  \nCustomers who buy **ASSY-100** often add **KIT-19**. Offer a 5% bundle discount.")
    with col2:
        if st.button("Accept", key="nudge_xsell"):
            msg = "Cross-sell task created for ASSY-100 → propose KIT-19 with 5% bundle discount."
            assistant(f"✅ {msg}")
            add_task("Sales AE", "Propose", "Bundle ASSY-100 + KIT-19", "Offer 5% discount")

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown("**Margin guard**  \nRecent quotes for **ASSY-100** fell below 20% margin. Propose price = cost × **1.22**.")
    with col2:
        if st.button("Accept", key="nudge_margin"):
            msg = "Margin guard applied to ASSY-100: price floor set to cost × 1.22 for next quotes."
            assistant(f"✅ {msg}")
            add_task("Sales AE", "Guardrail", "Margin floor", "cost × 1.22")

# Optional storyline banner (kept minimal; no header buttons)
sc = st.session_state.scenario
if sc and sc.get("events"):
    i = max(0, min(st.session_state.script_idx, len(sc["events"]) - 1))
    ev = sc["events"][i]
    st.caption(f"Storyline • {ev.get('t','T-0')} • {ev.get('dept','')} — {ev.get('msg','')}")

# Expose quote artifact download if present
if st.session_state.last_quote:
    q = st.session_state.last_quote
    st.download_button(
        label=f"⬇️ Download {q['id']}.md",
        data=q["md"],
        file_name=f"{q['id']}.md",
        mime="text/markdown",
    )

st.divider()

# ---------------------------------------------------------------------
# Chat transcript (bubbles)
# ---------------------------------------------------------------------
for m in st.session_state.chats[persona]:
    css_class = "chat-user" if m["role"] == "user" else "chat-assist"
    with st.chat_message(m["role"]):
        st.markdown(f"<div class='chat-bubble {css_class}'>{m['content']}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar — Overview + Recent tasks + persona actions
# ---------------------------------------------------------------------
st.sidebar.markdown("### Overview")
ov1, ov2, ov3 = st.sidebar.columns(3)
ov1.metric("Open", 12); ov2.metric("Win", "38%"); ov3.metric("Cycle", "3.8d")

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")
with st.sidebar.expander("Recent tasks", expanded=True):
    for t in st.session_state.tasks[-10:][::-1]:
        tail = f" — {t['details']}" if t.get('details') else ""
        st.write(f"✅ {t['ts']} • {t['persona']} • {t['kind']} • {t['title']}{tail}")

# small, sensible reset only in sidebar
if st.sidebar.button("Reset conversation"):
    st.session_state.chats[persona] = []
    st.session_state.tasks = []
    st.session_state.last_quote = None
    assistant("Conversation reset.")

API_URL = os.environ.get("MFG_API_URL", "http://localhost:8000")

# Persona quick actions (offline-first)
if persona == "Sales AE":
    st.sidebar.caption("Sales workspace")
    with st.sidebar.expander("Quote from BOM", expanded=True):
        a = st.text_input("Assembly", value="ASSY-100")
        q = st.number_input("Qty", min_value=1, step=5, value=25)
        margin = st.slider("Margin %", 5, 40, 22)
        prospect = st.text_input("Prospect", value="ACME Mfg")
        if st.button("Create Quote", use_container_width=True):
            try:
                res = generate_quote(a.upper(), int(q), prospect=prospect)
                if margin != 22:
                    roll = res["rollup"]; price = roll["base_cost"] * (1 + margin/100.0)
                    res["body"] = res["body"].replace("Price:", f"Price: **${price:,.2f}**  (margin {margin}%)\n- ")
                assistant(res["body"])
                add_task("Sales AE", "Quote", f"{a.upper()} x{int(q)}", res["quote_id"])
                st.session_state.last_quote = {
                    "id": res["quote_id"],
                    "md": f"# Quote {res['quote_id']}\n\n{res['body']}\n\n---\n*Generated by Manufacturing AI Assist.*\n"
                }
            except Exception as e:
                assistant(f"Could not create quote: {e}")

    with st.sidebar.expander("Follow-up", expanded=True):
        acct = st.text_input("Prospect name", value="ACME Mfg", key="fup_acct")
        qid = st.text_input("Quote ID (optional)", value="", key="fup_qid")
        tone = st.selectbox("Tone", ["crisp", "warm", "friendly"], index=0)
        if st.button("Draft Follow-up", use_container_width=True):
            msg = follow_up_email(acct, qid or "Q-XXXX", tone=tone)
            assistant(f"**Draft email to {acct}:**\n\n{msg}")
            add_task("Sales AE", "Follow-up", acct, qid or "Q-XXXX")

    with st.sidebar.expander("Propose related product", expanded=False):
        src = st.text_input("Based on assembly", value="ASSY-100", key="prop_src")
        if st.button("Suggest Cross-sell", use_container_width=True):
            suggestion = propose_new_product(src.upper())
            assistant(suggestion)
            add_task("Sales AE", "Propose", f"Cross-sell for {src.upper()}")

elif persona == "Supply Chain Manager":
    if st.sidebar.button("Create expedited PO"):
        msg = sc_expedite_po() if not simapi.api_up() else simapi.post_action("Create expedited PO")
        assistant(msg); add_task("Supply Chain Manager", "PO", "Expedited PO")
    if st.sidebar.button("Alternate supplier"):
        msg = sc_alternate_supplier() if not simapi.api_up() else simapi.post_action("Trigger alternate supplier")
        assistant(msg); add_task("Supply Chain Manager", "Supplier", "Alternate supplier")
    if st.sidebar.button("Upgrade carrier to air"):
        msg = sc_upgrade_carrier() if not simapi.api_up() else simapi.post_action("Upgrade carrier to air")
        assistant(msg); add_task("Supply Chain Manager", "Logistics", "Upgrade carrier to air")

else:  # Plant Manager
    if st.sidebar.button("Re-sequence L2"):
        msg = plant_resequence("L2") if not simapi.api_up() else simapi.post_action("Re-sequence L2")
        assistant(msg); add_task("Plant Manager", "Scheduling", "Re-sequenced L2")
    if st.sidebar.button("Batch changeovers"):
        msg = plant_batch_changeovers("L2") if not simapi.api_up() else simapi.post_action("Batch changeovers")
        assistant(msg); add_task("Plant Manager", "Ops", "Batched changeovers")
    if st.sidebar.button("QA fast-track"):
        msg = plant_qa_fast_track("SKU-19") if not simapi.api_up() else simapi.post_action("QA fast-track")
        assistant(msg); add_task("Plant Manager", "Quality", "QA fast-track")

# ---------------------------------------------------------------------
# Natural-language triggers (unchanged)
# ---------------------------------------------------------------------
def _int_in(text, default=None):
    m = re.search(r"\b(\d{1,5})\b", text)
    return int(m.group(1)) if m else default

prompt = st.chat_input("Type a message")
if prompt:
    user(prompt)
    low = prompt.lower()

    # KPI brief
    if "kpi" in low or "brief" in low or "status" in low:
        if simapi.api_up():
            m = simapi.get_metrics() or {}
            assistant(
                f"**Brief:** Throughput {m.get('throughput_per_day',0):.0f}/day, "
                f"OTD risk {m.get('otd_risk_pct',0):.1f}%, "
                f"On-time {m.get('on_time_pct',0):.1f}%, "
                f"Defect {m.get('defect_rate_pct',0):.2f}%, "
                f"Downtime {m.get('downtime_hours',0):.1f}h, "
                f"Inventory risks {m.get('inventory_risk_count',0)}."
            )
        else:
            df_orders, df_quality, df_down, df_inv, _ = load_all_data()
            k = compute_kpis(df_orders, df_quality, df_down, df_inv)
            assistant(
                f"**Brief:** Throughput {k['throughput_per_day']:.0f}/day, "
                f"On-time {k['on_time_pct']:.1f}%, "
                f"Defect {k['defect_rate_pct']:.2f}%, "
                f"Downtime {k['downtime_hours']:.1f}h, "
                f"Inventory risks {k['inventory_risk_count']}."
            )

    # Sales NL
    elif low.startswith("quote") or "quote for" in low:
        m = re.search(r"quote.*?([a-z0-9-]{5,})[^0-9]*?(\d+)", low, re.I)
        if m:
            assy, qty = m.group(1).upper(), int(m.group(2))
            try:
                res = generate_quote(assy, qty)
                assistant(res["body"])
                add_task("Sales AE", "Quote", f"{assy} x{qty}", res["quote_id"])
                st.session_state.last_quote = {
                    "id": res["quote_id"],
                    "md": f"# Quote {res['quote_id']}\n\n{res['body']}\n\n---\n*Generated by Manufacturing AI Assist.*\n"
                }
            except Exception as e:
                assistant(f"Could not create quote: {e}")
        else:
            assistant("Try: `quote for ASSY-100 qty 25`")
    elif "follow up" in low or "follow-up" in low:
        assistant(f"**Draft email to ACME Mfg:**\n\n{follow_up_email('ACME Mfg', 'Q-XXXX', tone='crisp')}")
        add_task("Sales AE", "Follow-up", "ACME Mfg", "Q-XXXX")
    elif "propose" in low or "suggest product" in low or "cross sell" in low:
        assistant(propose_new_product("ASSY-100"))
        add_task("Sales AE", "Propose", "Cross-sell for ASSY-100")

    # Supply Chain NL
    elif "expedite po" in low or ("expedite" in low and "po" in low):
        sku = (re.search(r"(sku[- ]?\d+)", low) or re.search(r"(assy[- ]?\d+)", low) or re.search(r"(comp[- ]?\d+)", low))
        sku = sku.group(1).upper() if sku else "SKU-19"
        days = _int_in(low, default=2)
        msg = sc_expedite_po(sku=sku, days_pull=days)
        assistant(msg); add_task("Supply Chain Manager", "PO", "Expedited PO", f"{sku}, ETA -{days}d")
    elif "alternate supplier" in low or "alt supplier" in low:
        sku = (re.search(r"(sku[- ]?\d+)", low) or re.search(r"(assy[- ]?\d+)", low))
        sku = sku.group(1).upper() if sku else "SKU-19"
        qty = _int_in(low, default=500)
        msg = sc_alternate_supplier(sku=sku, qty=qty)
        assistant(msg); add_task("Supply Chain Manager", "Supplier", "Alternate supplier", f"{sku}, {qty} pcs")
    elif "upgrade carrier" in low or ("carrier" in low and "air" in low):
        msg = sc_upgrade_carrier()
        assistant(msg); add_task("Supply Chain Manager", "Logistics", "Upgrade carrier to air")

    # Plant NL
    elif "re-sequence" in low or "resequence" in low:
        line = (re.search(r"(l\d)", low) or re.search(r"line[- ]?(l?\d)", low))
        line = line.group(1).upper() if line else "L2"
        msg = plant_resequence(line)
        assistant(msg); add_task("Plant Manager", "Scheduling", f"Re-sequenced {line}")
    elif "batch changeover" in low or "batch changeovers" in low:
        line = (re.search(r"(l\d)", low) or re.search(r"line[- ]?(l?\d)", low))
        line = line.group(1).upper() if line else "L2"
        msg = plant_batch_changeovers(line)
        assistant(msg); add_task("Plant Manager", "Ops", f"Batched changeovers {line}")
    elif "qa fast" in low or "fast-track" in low or "fast track" in low:
        sku = (re.search(r"(sku[- ]?\d+)", low) or re.search(r"(assy[- ]?\d+)", low))
        sku = sku.group(1).upper() if sku else "SKU-19"
        msg = plant_qa_fast_track(sku)
        assistant(msg); add_task("Plant Manager", "Quality", "QA fast-track", sku)

    else:
        assistant("Acknowledged.")

    st.rerun()
