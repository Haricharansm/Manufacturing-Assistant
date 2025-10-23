
import streamlit as st
from utils.data import load_all_data
from utils.kpis import compute_kpis
from utils import api as simapi
# pages/01_🌿_Plant_Manager.py
from utils.ui import show_logo
# …
show_logo(width=180)

st.image('assets/saxon_logo.png', width=180)
st.title("Plant Manager — Production")

df_orders, df_quality, df_down, df_inv, df_wos = load_all_data()
_ = compute_kpis(df_orders, df_quality, df_down, df_inv)

st.subheader("Actions")
colA, colB, colC = st.columns(3)
if colA.button("Re-sequence L2", use_container_width=True): st.success(simapi.post_action("Re-sequence L2"))
if colB.button("Batch changeovers", use_container_width=True): st.success(simapi.post_action("Batch changeovers"))
if colC.button("QA fast-track", use_container_width=True): st.success(simapi.post_action("QA fast-track"))
