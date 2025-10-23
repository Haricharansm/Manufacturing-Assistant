# utils/ui.py  (new file)
from pathlib import Path
import streamlit as st

def show_logo(width: int = 170):
    # works from any /pages/*.py location
    repo_root = Path(__file__).resolve().parents[1]
    logo = repo_root / "assets" / "saxon_logo.png"
    if logo.exists():
        st.image(str(logo), width=width)
    else:
        st.markdown(
            '<div style="font-weight:700;font-size:22px;">Manufacturing AI Assist</div>',
            unsafe_allow_html=True,
        )
