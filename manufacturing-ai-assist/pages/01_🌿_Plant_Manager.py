# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime

from utils.ui import show_logo, greeting, header, chips_row
from utils.ops_offline import (
    plant_resequence, plant_batch_changeovers, plant_qa_fast_track
)
from utils import api as simapi

# -------- Page chrome --------
st.set_page_config(page_title="Plant Manager", page_icon="🌿", layout="wide")
show_logo(width=170)
greeting(name=st.session_state.get("user_name", "there"), right_badge="Manufacturing AI Assist")
header("Plant Manager", "Production & operations")

chips_row([
    ("OEE 82%", "success"),
    ("Changeovers today: 4", "neutral"),
    ("Downtime 1.2h", "warn"),
])

# -------- Shared task log --------
if "tasks" not in st.session_state:
    st.session_state.tasks = []

def add_task(kind, title, details=""):
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": "Plant Manager",
        "kind": kind, "title": title, "details": details
    })

# -------- Intelligent nudges --------
with st.expander("🔔 Intelligent nudges", expanded=True):
    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Re-sequence L2**  \nForecast spike on **L2** tomorrow 08:00–12:00. Move high-mix order **O-1842** to afternoon window.")
    with c2:
        if st.button("Accept", key="pm_nudge_resq"):
            msg = plant_resequence("L2")
            st.success(msg)
            add_task("Scheduling", "Re-sequenced L2", "Shifted O-1842")

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**QA fast-track**  \nCritical part **SKU-19** waiting at QA. Prioritize to unblock assembly.")
    with c2:
        if st.button("Accept", key="pm_nudge_fastqa"):
            msg = plant_qa_fast_track("SKU-19")
            st.success(msg)
            add_task("Quality", "QA fast-track", "SKU-19")

    c1, c2 = st.columns([5,1])
    with c1:
        st.markdown("**Batch changeovers**  \nCluster small lots on **L2** to reduce three changeovers to one.")
    with c2:
        if st.button("Accept", key="pm_nudge_batch"):
            msg = plant_batch_changeovers("L2")
            st.success(msg)
            add_task("Ops", "Batched changeovers", "L2")

st.divider()

# -------- Quick Actions --------
st.subheader("Quick Actions")
a,b,c = st.columns(3)
if a.button("Re-sequence L2", use_container_width=True):
    st.success(plant_resequence("L2")); add_task("Scheduling", "Re-sequenced L2")
if b.button("Batch changeovers", use_container_width=True):
    st.success(plant_batch_changeovers("L2")); add_task("Ops", "Batched changeovers")
if c.button("QA fast-track", use_container_width=True):
    sku = "SKU-19"
    st.success(plant_qa_fast_track(sku)); add_task("Quality", "QA fast-track", sku)
