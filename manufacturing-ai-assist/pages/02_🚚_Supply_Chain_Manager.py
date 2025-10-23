import streamlit as st
import os, requests, pandas as pd

from utils.ui import show_logo
from utils.ops_offline import (
    sc_expedite_po, sc_alternate_supplier, sc_upgrade_carrier, erp_snapshot
)
from utils import api as simapi  # optional live API

st.set_page_config(page_title="Supply Chain — Inbound", page_icon="🚚", layout="wide")

# Header
show_logo(width=180)
st.title("Supply Chain — Inbound")

# Ensure task log exists
if "tasks" not in st.session_state:
    st.session_state.tasks = []

def add_task(kind, title, details=""):
    from datetime import datetime
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": "Supply Chain Manager",
        "kind": kind, "title": title, "details": details
    })

# Actions (offline-first)
st.subheader("Actions")
c1, c2, c3 = st.columns(3)
if c1.button("Create expedited PO", use_container_width=True):
    msg = sc_expedite_po()
    st.success(msg); add_task("PO", "Expedited PO", "SKU-19, ETA -2d")
if c2.button("Alternate supplier", use_container_width=True):
    msg = sc_alternate_supplier()
    st.success(msg); add_task("Supplier", "Alternate supplier", "SKU-19, 500 pcs")
if c3.button("Upgrade carrier to air", use_container_width=True):
    msg = sc_upgrade_carrier()
    st.success(msg); add_task("Logistics", "Upgraded carrier to air")

st.divider()
st.subheader("ERP Snapshot (SKU-19)")

# Offline snapshot by default
st.json(erp_snapshot("SKU-19"))

# Optional live
if simapi.api_up():
    API_URL = os.environ.get("MFG_API_URL", "http://localhost:8000")
    try:
        live = requests.get(f"{API_URL}/inventory/SKU-19", timeout=4).json()
        with st.expander("Live ERP (API)", expanded=False):
            st.json(live)
    except Exception as e:
        st.caption(f"Live ERP unavailable: {e}")

# Recent tasks sidebar (if user opens this page first)
with st.sidebar.expander("Recent tasks", expanded=False):
    for t in st.session_state.tasks[-8:][::-1]:
        st.write(f"✅ {t['ts']} • {t['persona']} • {t['kind']} • {t['title']}")
