import streamlit as st
import os, requests, pandas as pd

from utils import api as simapi
from utils.ui import show_logo

# Page config first
st.set_page_config(page_title="Supply Chain — Inbound", page_icon="🚚", layout="wide")

# Header
show_logo(width=180)
st.title("Supply Chain — Inbound")

# Actions
st.subheader("Actions")
c1, c2, c3 = st.columns(3)
if c1.button("Create expedited PO", use_container_width=True):
    st.success(simapi.post_action("Create expedited PO"))
if c2.button("Alternate supplier", use_container_width=True):
    st.success(simapi.post_action("Trigger alternate supplier"))
if c3.button("Upgrade carrier to air", use_container_width=True):
    st.success(simapi.post_action("Upgrade carrier to air"))

st.divider()
st.subheader("ERP Snapshot (SKU-19)")

if simapi.api_up():
    API_URL = os.environ.get("MFG_API_URL", "http://localhost:8000")
    try:
        inv = requests.get(f"{API_URL}/inventory/SKU-19", timeout=4).json()
        st.json(inv)
    except Exception as e:
        st.warning(f"ERP snapshot unavailable: {e}")
else:
    st.caption("Start the API to view the ERP snapshot.")
