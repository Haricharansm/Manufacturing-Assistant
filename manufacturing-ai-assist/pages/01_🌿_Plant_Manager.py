import streamlit as st

from utils.ui import show_logo
from utils.ops_offline import (
    plant_resequence, plant_batch_changeovers, plant_qa_fast_track
)

st.set_page_config(page_title="Plant Manager — Production", page_icon="🌿", layout="wide")

# Header
show_logo(width=180)
st.title("Plant Manager — Production")

# Ensure task log exists
if "tasks" not in st.session_state:
    st.session_state.tasks = []

def add_task(kind, title, details=""):
    from datetime import datetime
    st.session_state.tasks.append({
        "ts": datetime.utcnow().isoformat(timespec="seconds"),
        "persona": "Plant Manager",
        "kind": kind, "title": title, "details": details
    })

st.subheader("Actions")
colA, colB, colC = st.columns(3)
if colA.button("Re-sequence L2", use_container_width=True):
    msg = plant_resequence("L2")
    st.success(msg); add_task("Scheduling", "Re-sequenced L2")
if colB.button("Batch changeovers", use_container_width=True):
    msg = plant_batch_changeovers("L2")
    st.success(msg); add_task("Ops", "Batched changeovers")
if colC.button("QA fast-track", use_container_width=True):
    msg = plant_qa_fast_track("SKU-19")
    st.success(msg); add_task("Quality", "QA fast-track", "SKU-19")
