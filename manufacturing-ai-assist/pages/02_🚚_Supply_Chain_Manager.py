# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime
from utils.ui import show_logo, greeting, header, chips_row
from utils.ops_offline import sc_expedite_po, sc_alternate_supplier, sc_upgrade_carrier
from utils import api as simapi
import os, requests

st.set_page_config(page_title="Supply Chain", page_icon="🚚", layout="wide")
show_logo(width=170)
greeting(name=st.session_state.get("user_name", "there"), right_badge="Manufacturing AI Assist")
header("Supply Chain Manager", "Inbound, suppliers & logistics")

chips_row([
    ("Open POs: 18", "neutral"),
    ("Late lines: 3", "warn"),
    ("Inventory risks: 3", "warn"),
])

if "tasks" not in st.session_state:
    st.session_state.tasks = []

def add_task(kind, title, details=""):
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": "Supply Chain Manager",
        "kind": kind, "title": title, "details": details
    })

# ---------- Intelligent nudges ----------
with st.expander("🔔 Intelligent nudges", expanded=True):
    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Expedite SKU-19**  \nPull in **2 days** to avoid line-down on L2 tomorrow.")
    with c2:
        if st.button("Accept", key="sc_nudge_expedite"):
            st.success(sc_expedite_po(sku="SKU-19", days_pull=2))
            add_task("PO", "Expedited PO", "SKU-19, ETA −2d")

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Alternate supplier**  \nSource **500** pcs of **SKU-19** from vetted Supplier-B.")
    with c2:
        if st.button("Accept", key="sc_nudge_alt"):
            st.success(sc_alternate_supplier(sku="SKU-19", qty=500))
            add_task("Supplier", "Alternate supplier", "SKU-19, 500 pcs")

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Upgrade carrier**  \nSwitch next outbound to **air** to hit customer promise.")
    with c2:
        if st.button("Accept", key="sc_nudge_carrier"):
            st.success(sc_upgrade_carrier())
            add_task("Logistics", "Upgrade carrier to air")

st.divider()

# ---------- Quick Actions ----------
st.subheader("Quick Actions")
a,b,c = st.columns(3)
if a.button("Create expedited PO", use_container_width=True):
    st.success(sc_expedite_po()); add_task("PO", "Expedited PO")
if b.button("Alternate supplier", use_container_width=True):
    st.success(sc_alternate_supplier()); add_task("Supplier", "Alternate supplier")
if c.button("Upgrade carrier to air", use_container_width=True):
    st.success(sc_upgrade_carrier()); add_task("Logistics", "Upgrade carrier to air")

# Optional ERP snapshot (only if your API is up)
API_URL = os.environ.get("MFG_API_URL","http://localhost:8000")
with st.expander("ERP snapshot (SKU-19)", expanded=False):
    if simapi.api_up():
        try:
            inv = requests.get(f"{API_URL}/inventory/SKU-19", timeout=4).json()
            st.json(inv)
        except Exception as e:
            st.warning(f"ERP snapshot unavailable: {e}")
    else:
        st.caption("Offline demo mode — snapshot hidden.")
