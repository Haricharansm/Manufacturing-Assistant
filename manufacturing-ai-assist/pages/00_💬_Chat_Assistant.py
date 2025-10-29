# -*- coding: utf-8 -*-
import streamlit as st
import json, os, pandas as pd, requests, re
from pathlib import Path
from datetime import datetime

from utils import api as simapi
from utils.data import load_all_data
from utils.kpis import compute_kpis
from utils.ui import show_logo, header, chips_row
from utils.sales_offline import generate_quote, follow_up_email, propose_new_product
from utils.ops_offline import (
    sc_expedite_po, sc_alternate_supplier, sc_upgrade_carrier,
    plant_resequence, plant_batch_changeovers, plant_qa_fast_track
)

# Optional modules (nudges/search); fall back to simple stubs if missing
try:
    from utils.nudges import sales_nudges, sc_nudges, plant_nudges
except Exception:
    def sales_nudges(df_orders, df_inv):
        return [
            {"title":"Cross-sell opportunity",
             "body":"Customers who buy **ASSY-100** also add **KIT-19**. Offer a 5% bundle.",
             "action":{"type":"propose_xsell","assembly":"ASSY-100"}}
        ]
    def sc_nudges(df_inv):
        return [
            {"title":"Late ASNs detected","body":"Suggest **upgrade to air** for critical parts.",
             "action":{"type":"sc_upgrade_carrier"}}
        ]
    def plant_nudges(df_down, df_quality):
        return [
            {"title":"Changeovers driving downtime",
             "body":"Recommend **batch changeovers** and **re-sequence L2**.",
             "action":{"type":"plant_batch_changeovers","line":"L2"}}
        ]

try:
    from utils.search import search_sales, search_sc, search_plant
except Exception:
    def search_sales(q, dfs):  return ("Sales search", dfs["orders"].head(50))
    def search_sc(q, dfs):     return ("Supply chain search", dfs["inv"].head(50))
    def search_plant(q, dfs):  return ("Plant search", dfs["down"].head(50))

# ---------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------
st.set_page_config(page_title="Chat Assistant", page_icon="💬", layout="wide")

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
show_logo(width=170)
header("Conversation", "Chat-first copilot for Sales • Supply Chain • Plant")

PERSONAS = ["Sales AE", "Supply Chain Manager", "Plant Manager"]
persona = st.sidebar.radio("Persona", PERSONAS, index=0)

# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {p: [] for p in PERSONAS}
if "script_idx" not in st.session_state:
    st.session_state.script_idx = 0
if "scenario" not in st.session_state:
    fp = Path("data/scenario.json")
    st.session_state.scenario = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "last_quote" not in st.session_state:
    st.session_state.last_quote = None  # {"id": "...", "md": "..."}

def say(role, content):
    st.session_state.chats[persona].append({"role": role, "content": content})

def assistant(msg):
    say("assistant", msg)

def user(msg):
    say("user", msg)

def add_task(persona_label, kind, title, details=""):
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": persona_label,
        "kind": kind, "title": title, "details": details
    })

# ---------------------------------------------------------------------
# Data helpers (for nudges/search) + Persona KPI strip
# ---------------------------------------------------------------------
def _load_demo_dfs():
    df_orders, df_quality, df_down, df_inv, df_wos = load_all_data()
    return {"orders": df_orders, "quality": df_quality, "down": df_down, "inv": df_inv, "wos": df_wos}

def _metrics_or_defaults():
    if simapi.api_up():
        m = simapi.get_metrics() or {}
        return {
            "open_quotes": m.get("open_quotes", 12),
            "win_rate": m.get("win_rate_30d", 38),
            "avg_cycle": m.get("avg_cycle_days", 3.8),
            "inv_risks": m.get("inventory_risk_count", 3),
            "late_asn": m.get("late_asn_count", 2),
            "lead_time": m.get("avg_inbound_lead_days", 5.4),
            "throughput": m.get("throughput_per_day", 240),
            "downtime": m.get("downtime_hours", 1.2),
            "yield_pct": m.get("first_pass_yield_pct", 98.3),
        }
    return {
        "open_quotes": 12, "win_rate": 38, "avg_cycle": 3.8,
        "inv_risks": 3, "late_asn": 2, "lead_time": 5.4,
        "throughput": 240, "downtime": 1.2, "yield_pct": 98.3,
    }

def render_persona_kpis(selected):
    m = _metrics_or_defaults()
    st.sidebar.markdown("### Overview")
    if selected == "Sales AE":
        c1,c2,c3 = st.sidebar.columns(3)
        c1.metric("Open", m["open_quotes"])
        c2.metric("Win", f"{m['win_rate']}%")
        c3.metric("Cycle", f"{float(m['avg_cycle']):.1f}d")
    elif selected == "Supply Chain Manager":
        c1,c2,c3 = st.sidebar.columns(3)
        c1.metric("Risks", m["inv_risks"])
        c2.metric("Late ASN", m["late_asn"])
        c3.metric("Lead", f"{float(m['lead_time']):.1f}d")
    else:
        c1,c2,c3 = st.sidebar.columns(3)
        c1.metric("TPD", int(m["throughput"]))
        c2.metric("Down", f"{float(m['downtime']):.1f}h")
        c3.metric("FPY", f"{float(m['yield_pct']):.1f}%")

render_persona_kpis(persona)

# ---------------------------------------------------------------------
# Helpers: Scenario banner + Quote artifact markdown
# ---------------------------------------------------------------------
def scenario_banner():
    sc = st.session_state.get("scenario")
    i = st.session_state.get("script_idx", 0)
    if not sc or not sc.get("events"):
        return
    idx = max(0, min(i - 1, len(sc["events"]) - 1))
    ev = sc["events"][idx]
    phase = ev.get("t", "T-0")
    dept = ev.get("dept", "")
    msg = ev.get("msg", "")

    st.markdown(
        f"""
        <div class="card" style="display:flex;gap:10px;align-items:center;margin:8px 0 0 0;">
          <div class="chip warn"><span class="dot"></span>{phase}</div>
          <div class="chip"><span class="dot"></span>{dept}</div>
          <div style="font-weight:600;color:#17223B">Storyline</div>
          <div style="color:#5B677D">— {msg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def _quote_markdown(body_text: str, quote_id: str) -> str:
    return f"""# Quote {quote_id}

{body_text}

---

*Generated by Manufacturing AI Assist (offline demo mode).*
"""

# ---------------------------------------------------------------------
# Top controls (Nudge / Reset / Step)
# ---------------------------------------------------------------------
colA, colB, colC = st.columns([1, 1, 1])
if colA.button("Nudge"):
    if simapi.api_up():
        m = simapi.get_metrics() or {}
        if persona == "Supply Chain Manager":
            assistant(f"Inventory risk: {m.get('inventory_risk_count','?')}. Consider expedited PO or alternate supplier for SKU-19.")
        elif persona == "Plant Manager":
            assistant(f"Throughput trend is {m.get('throughput_trend','flat')}. Consider re-sequence or batching.")
        else:
            assistant("You can request a Daily Brief or use Sales actions.")
    else:
        assistant("Daily Brief and quick actions are available.")

if colB.button("Reset"):
    st.session_state.script_idx = 0
    st.session_state.chats[persona] = []
    st.session_state.tasks = []
    st.session_state.last_quote = None
    if simapi.api_up():
        simapi.reset()
    assistant("Reset complete.")

def _run_story_action(action, params):
    if action == "sales_quote":
        with st.status("Generating quote…", expanded=False) as s:
            res = generate_quote(params.get("assembly", "ASSY-100"), int(params.get("qty", 25)),
                                 prospect=params.get("prospect", "ACME Mfg"))
            assistant(res["body"])
            add_task("Sales AE", "Quote",
                     f"{params.get('assembly','ASSY-100')} x{int(params.get('qty',25))}", res["quote_id"])
            st.session_state.last_quote = {"id": res["quote_id"], "md": _quote_markdown(res["body"], res["quote_id"])}
            s.update(label="Quote ready", state="complete")
    elif action == "sc_expedite_po":
        msg = sc_expedite_po()
        assistant(msg); add_task("Supply Chain Manager", "PO", "Expedited PO", "SKU-19, ETA -2d")
    elif action == "sc_alternate_supplier":
        msg = sc_alternate_supplier(qty=int(params.get("qty", 500)))
        assistant(msg); add_task("Supply Chain Manager", "Supplier", "Alternate supplier", f"{params.get('qty',500)} pcs")
    elif action == "plant_resequence":
        msg = plant_resequence(params.get("line", "L2"))
        assistant(msg); add_task("Plant Manager", "Scheduling", "Re-sequenced L2")
    elif action == "plant_qa_fast_track":
        msg = plant_qa_fast_track(params.get("sku", "SKU-19"))
        assistant(msg); add_task("Plant Manager", "Quality", "QA fast-track", params.get("sku", "SKU-19"))
    else:
        assistant("_No executable action for this step._")

if colC.button("Step"):
    sc = st.session_state.scenario
    i = st.session_state.script_idx
    if sc and i < len(sc["events"]):
        e = sc["events"][i]; st.session_state.script_idx += 1
        assistant(f"**{e['dept']} ({e['t']}):** {e['msg']}")
        _run_story_action(e.get("action", ""), e.get("params", {}))
    else:
        assistant("End of storyline.")

# Show compact storyline banner
scenario_banner()

# Cosmetic chips
chips_row([
    ("On-time ↑", "success"),
    ("Inventory risks: 3", "warn"),
    ("Downtime 1.2h", "neutral"),
])

# If we have a fresh quote artifact, expose a download button
if st.session_state.last_quote:
    q = st.session_state.last_quote
    st.download_button(
        label=f"⬇️ Download {q['id']}.md",
        data=q["md"],
        file_name=f"{q['id']}.md",
        mime="text/markdown",
        use_container_width=False,
    )

st.divider()

# ---------------------------------------------------------------------
# Intelligent Nudges (role-aware)
# ---------------------------------------------------------------------
dfs = _load_demo_dfs()
with st.expander("🔔 Intelligent nudges", expanded=True):
    if persona == "Sales AE":
        cards = sales_nudges(dfs["orders"], dfs["inv"])
    elif persona == "Supply Chain Manager":
        cards = sc_nudges(dfs["inv"])
    else:
        cards = plant_nudges(dfs["down"], dfs["quality"])

    for i, c in enumerate(cards, start=1):
        cols = st.columns([6, 2])
        cols[0].markdown(f"**{c['title']}**  \n{c['body']}")
        if cols[1].button("Accept", key=f"nudge_{i}"):
            a = c.get("action", {}); t = a.get("type")
            if t == "follow_up":
                msg = follow_up_email(a.get("account", "ACME Mfg"), "Q-XXXX", tone="warm")
                assistant(f"**Draft email:**\n\n{msg}")
                add_task("Sales AE", "Follow-up", a.get("account","ACME Mfg"), "Q-XXXX")
            elif t == "propose_xsell":
                assistant(propose_new_product(a.get("assembly","ASSY-100")))
                add_task("Sales AE", "Propose", f"Cross-sell for {a.get('assembly','ASSY-100')}")
            elif t == "open_quote_wizard":
                assistant("Opening quote wizard with prefilled values…")
            elif t == "sc_expedite_po":
                msg = sc_expedite_po(a.get("sku","SKU-19"), a.get("days_pull",2))
                assistant(msg); add_task("Supply Chain Manager","PO","Expedited PO", f"{a.get('sku','SKU-19')}, ETA -{a.get('days_pull',2)}d")
            elif t == "sc_upgrade_carrier":
                msg = sc_upgrade_carrier(); assistant(msg); add_task("Supply Chain Manager","Logistics","Upgrade carrier to air")
            elif t == "plant_batch_changeovers":
                msg = plant_batch_changeovers(a.get("line","L2")); assistant(msg); add_task("Plant Manager","Ops","Batched changeovers")
            elif t == "plant_qa_fast_track":
                msg = plant_qa_fast_track(a.get("sku","SKU-19")); assistant(msg); add_task("Plant Manager","Quality","QA fast-track", a.get("sku","SKU-19"))
            else:
                assistant("Action recorded.")

# ---------------------------------------------------------------------
# Chat transcript (bubbles)
# ---------------------------------------------------------------------
for m in st.session_state.chats[persona]:
    css_class = "chat-user" if m["role"] == "user" else "chat-assist"
    with st.chat_message(m["role"]):
        st.markdown(f"<div class='chat-bubble {css_class}'>{m['content']}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar — Recent tasks + persona actions + search
# ---------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")

with st.sidebar.expander("Recent tasks", expanded=True):
    rows = st.session_state.tasks[-50:][::-1]
    for t in rows:
        tail = f" — {t['details']}" if t.get('details') else ""
        st.write(f"✅ {t['ts']} • {t['persona']} • {t['kind']} • {t['title']}{tail}")
    if rows:
        df_tasks = pd.DataFrame(rows)
        st.download_button(
            "⬇️ Export tasks (CSV)",
            data=df_tasks.to_csv(index=False).encode("utf-8"),
            file_name="recent_tasks.csv",
            mime="text/csv",
            use_container_width=True,
        )

API_URL = os.environ.get("MFG_API_URL", "http://localhost:8000")

# Persona quick actions (Sales offline, SC/Plant offline-first)
if persona == "Sales AE":
    st.sidebar.caption("Sales workspace (offline)")
    with st.sidebar.expander("Quote from BOM", expanded=True):
        a = st.text_input("Assembly", value="ASSY-100")
        qn = st.number_input("Qty", min_value=1, step=5, value=25)
        margin = st.slider("Margin %", 5, 40, 22)
        prospect = st.text_input("Prospect", value="ACME Mfg")
        if st.button("Create Quote", use_container_width=True):
            try:
                with st.status("Generating quote…", expanded=False) as s:
                    res = generate_quote(a.upper(), int(qn), prospect=prospect)
                    if margin != 22:
                        roll = res["rollup"]
                        price = roll["base_cost"] * (1 + margin / 100.0)
                        res["body"] = res["body"].replace("Price:", f"Price: **${price:,.2f}**  (margin {margin}%)\n- ")
                    assistant(res["body"])
                    add_task("Sales AE", "Quote", f"{a.upper()} x{int(qn)}", res["quote_id"])
                    st.session_state.last_quote = {"id": res["quote_id"], "md": _quote_markdown(res["body"], res["quote_id"])}
                    s.update(label="Quote ready", state="complete")
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

# Sidebar search (by function)
st.sidebar.markdown("---")
st.sidebar.subheader("Search")
_query = st.sidebar.text_input("Ask by function", placeholder="e.g., quotes for ACME / inventory SKU-19 / downtime by line")
if _query:
    title, table = ("", None)
    if persona == "Sales AE":
        title, table = search_sales(_query, dfs)
    elif persona == "Supply Chain Manager":
        title, table = search_sc(_query, dfs)
    else:
        title, table = search_plant(_query, dfs)
    st.sidebar.caption(title)
    st.sidebar.dataframe(table, height=220, use_container_width=True)

# ---------------------------------------------------------------------
# Natural-language triggers
# ---------------------------------------------------------------------
def _int_in(text, default=None):
    m = re.search(r"\b(\d{1,5})\b", text)
    return int(m.group(1)) if m else default

prompt = st.chat_input("Type a message")
if prompt:
    user(prompt)
    low = prompt.lower()

    # KPIs
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
                with st.status("Generating quote…", expanded=False) as s:
                    res = generate_quote(assy, qty)
                    assistant(res["body"])
                    add_task("Sales AE", "Quote", f"{assy} x{qty}", res["quote_id"])
                    st.session_state.last_quote = {"id": res["quote_id"], "md": _quote_markdown(res["body"], res["quote_id"])}
                    s.update(label="Quote ready", state="complete")
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
