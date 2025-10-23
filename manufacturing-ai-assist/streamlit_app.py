import streamlit as st
from pathlib import Path

from utils.data import load_all_data
from utils.kpis import compute_kpis
from utils.charts import kpi_row
from utils.ai import draft_brief
from utils import api as simapi
from utils.ui import show_logo

# Page config MUST be first before any output
st.set_page_config(page_title="Manufacturing AI Assist", page_icon="🏭", layout="wide")

# Sidebar navigation
st.sidebar.title("streamlit app")
st.sidebar.page_link("pages/00_💬_Chat_Assistant.py", label="Chat Assistant")
st.sidebar.page_link("pages/01_🌿_Plant_Manager.py", label="Plant Manager")
st.sidebar.page_link("pages/02_🚚_Supply_Chain_Manager.py", label="Supply Chain Manager")
st.sidebar.page_link("pages/03_💼_Sales_AE.py", label="Sales AE")

# Header
col_logo, col_title = st.columns([1, 5])
with col_logo:
    show_logo(width=180)
with col_title:
    st.markdown("## Manufacturing AI Assist")

# Data + KPIs
df_orders, df_quality, df_down, df_inv, df_wos = load_all_data()

if simapi.api_up():
    m = simapi.get_metrics() or {}
    if m:
        k = {
            "throughput_per_day": m.get("throughput_per_day", 0),
            "on_time_pct": m.get("on_time_pct", 0),
            "defect_rate_pct": m.get("defect_rate_pct", 0),
            "downtime_hours": m.get("downtime_hours", 0),
            "inventory_risk_count": m.get("inventory_risk_count", 0),
            "throughput_trend": m.get("throughput_trend", "flat"),
            "top_downtime_cause": m.get("top_downtime_cause", "n/a"),
            "top_defect_family": m.get("top_defect_family", "n/a"),
            "lowest_stock_sku": m.get("lowest_stock_sku", "n/a"),
        }
    else:
        k = compute_kpis(df_orders, df_quality, df_down, df_inv)
else:
    k = compute_kpis(df_orders, df_quality, df_down, df_inv)

kpi_row(k)
st.divider()
st.subheader("Daily Brief")
note = st.text_input("Notes (optional)", placeholder="Add any context...")
st.markdown(draft_brief(persona="Overview", k=k, note=note))
