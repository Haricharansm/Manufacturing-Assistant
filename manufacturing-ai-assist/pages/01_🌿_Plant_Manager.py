
import streamlit as st

from utils.data import load_all_data
from utils.kpis import compute_kpis
from utils import api as simapi
from utils.ui import show_logo

# Page config first
st.set_page_config(page_title="Plant Manager — Production", page_icon="🌿", layout="wide")

# Header
show_logo(width=180)
st.title("Plant Manager — Production")

# Data (used if API isn't running)
df_orders, df_quality, df_down, df_inv, df_wos = load_all_data()
_ = compute_kpis(df_orders, df_quality, df_down, df_inv)

# Actions
st.subheader("Actions")
colA, colB, colC = st.columns(3)
if colA.button("Re-sequence L2", use_container_width=True):
    st.success(simapi.post_action("Re-sequence L2"))
if colB.button("Batch changeovers", use_container_width=True):
    st.success(simapi.post_action("Batch changeovers"))
if colC.button("QA fast-track", use_container_width=True):
    st.success(simapi.post_action("QA fast-track"))

