# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime
from utils.ui import show_logo, greeting, header, chips_row
from utils.sales_offline import generate_quote, follow_up_email, propose_new_product

st.set_page_config(page_title="Sales AE", page_icon="💼", layout="wide")
show_logo(width=170)
greeting(name=st.session_state.get("user_name", "there"), right_badge="Manufacturing AI Assist")
header("Sales AE", "Quote, promise date & customer follow-ups")

chips_row([
    ("Open quotes: 12", "neutral"),
    ("Win rate (30d): 38%", "success"),
    ("Avg cycle: 3.8d", "neutral"),
])

if "tasks" not in st.session_state:
    st.session_state.tasks = []

def add_task(kind, title, details=""):
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": "Sales AE",
        "kind": kind, "title": title, "details": details
    })

# ---------- Intelligent nudges ----------
with st.expander("🔔 Intelligent nudges", expanded=True):
    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Follow-up reminder**  \nQuote **Q-176123** sent 3 days ago to **ACME Mfg**. Schedule a friendly check-in.")
    with c2:
        if st.button("Accept", key="ae_nudge_follow"):
            msg = follow_up_email("ACME Mfg", "Q-176123", tone="warm")
            st.success("Draft follow-up created in the Chat Assistant.")
            add_task("Follow-up", "ACME Mfg", "Q-176123")
            # surface draft text in chat assistant page during demo

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Margin guard**  \nPrice floor for **ASSY-100** set to cost × **1.22**.")
    with c2:
        if st.button("Accept", key="ae_nudge_guard"):
            st.success("Margin guard saved for ASSY-100.")
            add_task("Guardrail", "Margin floor", "cost × 1.22")

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Cross-sell**  \nPropose **KIT-19** with ASSY-100 (5% bundle).")
    with c2:
        if st.button("Accept", key="ae_nudge_xsell"):
            st.success("Cross-sell note added to opportunity.")
            add_task("Propose", "KIT-19 with ASSY-100", "5% bundle")

st.divider()

# ---------- Quick Actions ----------
st.subheader("Quick Actions")
with st.form("quote_form", clear_on_submit=False):
    a = st.text_input("Assembly", value="ASSY-100")
    q = st.number_input("Qty", min_value=1, step=5, value=25)
    margin = st.slider("Margin %", 5, 40, 22)
    prospect = st.text_input("Prospect", value="ACME Mfg")
    submitted = st.form_submit_button("Generate Quote")
    if submitted:
        res = generate_quote(a.upper(), int(q), prospect=prospect)
        if margin != 22:
            roll = res["rollup"]; price = roll["base_cost"] * (1 + margin/100.0)
            res["body"] = res["body"].replace("Price:", f"Price: **${price:,.2f}**  (margin {margin}%)\n- ")
        st.success("Quote drafted below:")
        st.markdown(res["body"])
        add_task("Quote", f"{a.upper()} x{int(q)}", res["quote_id"])

col1, col2 = st.columns(2)
with col1:
    if st.button("Draft follow-up email"):
        msg = follow_up_email("ACME Mfg", "Q-XXXX", tone="crisp")
        st.info(f"**Draft email:**\n\n{msg}")
        add_task("Follow-up", "ACME Mfg", "Q-XXXX")
with col2:
    if st.button("Suggest cross-sell"):
        st.info(propose_new_product("ASSY-100"))
        add_task("Propose", "Cross-sell for ASSY-100")
