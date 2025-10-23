
import streamlit as st, os, requests, pandas as pd
st.image('assets/saxon_logo.png', width=180)
st.title("Sales AE — Quote & Promise Date")

API_URL = os.environ.get("MFG_API_URL","http://localhost:8000")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Open Quotes", 12)
with col2: st.metric("Win Rate (30d)", "38%")
with col3: st.metric("Avg Cycle", "3.8d")

st.subheader("Actions")
if st.button("Generate Quote: HX-220×25, ship in 5d, $762"):
    try:
        r = requests.post(f"{API_URL}/sales/quote", json={"sku":"HX-220","qty":25,"ship_date":str(pd.Timestamp.today()+pd.Timedelta(days=5)),"unit_price":762.0})
        st.success(r.json().get("message","Quote created."))
    except Exception as e:
        st.error(f"Quote failed: {e}")
if st.button("Email Customer"):
    try:
        requests.post(f"{API_URL}/sales/email", json={"to":"purchasing@acme.com","subject":"Quote from Saxon.AI","body":"Thank you."})
        st.success("Email queued.")
    except Exception as e:
        st.error(f"Email failed: {e}")
if st.button("Set Reminder (3d)"):
    try:
        r = requests.post(f"{API_URL}/sales/reminder", json={"days":3,"note":"Check in"})
        st.success(r.json().get("message","Reminder set."))
    except Exception as e:
        st.error(f"Reminder failed: {e}")
