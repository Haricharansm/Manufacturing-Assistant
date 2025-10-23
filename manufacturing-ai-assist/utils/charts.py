
import streamlit as st
def kpi(label, value, suffix=""): st.metric(label, f"{value}{suffix}")
def kpi_row(k):
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Throughput/day", f"{k['throughput_per_day']:.0f}")
    with c2: kpi("On-time %", f"{k['on_time_pct']:.1f}", "%")
    with c3: kpi("Defect %", f"{k['defect_rate_pct']:.2f}", "%")
    with c4: kpi("Downtime (h)", f"{k['downtime_hours']:.1f}")
    with c5: kpi("Inventory risks", f"{k['inventory_risk_count']}")
