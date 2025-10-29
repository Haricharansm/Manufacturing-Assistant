# utils/ui.py
from __future__ import annotations
import streamlit as st
from datetime import datetime
from pathlib import Path

SAXON_ORANGE = "#FF7A18"
SAXON_NAVY   = "#17223B"
SAXON_GRAY   = "#5B677D"
BG_NEUTRAL   = "#FAF8F5"

_ASSETS_DIR = Path("assets")
_LOGO_PATH  = _ASSETS_DIR / "saxon_logo.png"   # you already have this

def _inject_css():
    st.markdown(
        f"""
        <style>
        /* Page canvas */
        .stApp {{ background: linear-gradient(180deg, {BG_NEUTRAL} 0%, #FFFFFF 65%); }}

        /* Top greeting card */
        .sxn-hero {{
          display:flex; align-items:center; justify-content:space-between;
          gap:16px; padding:18px 22px; margin:0 0 8px 0; border-radius:16px;
          background:#FFFFFF; box-shadow:0 4px 16px rgba(23,34,59,0.06);
          border:1px solid rgba(23,34,59,0.06);
        }}
        .sxn-hello {{
          font-size:22px; font-weight:700; color:{SAXON_NAVY}; letter-spacing:0.2px;
        }}
        .sxn-sub {{
          color:{SAXON_GRAY}; font-size:14px; margin-top:4px;
        }}
        .sxn-pill {{
          background:linear-gradient(90deg, {SAXON_ORANGE}, #FFB347);
          color:#fff; padding:8px 14px; border-radius:999px; font-weight:600;
          box-shadow:0 6px 14px rgba(255,122,24,0.22);
        }}

        /* Chips row used elsewhere */
        .chip {{ display:inline-flex; align-items:center; gap:8px;
          padding:6px 10px; border-radius:12px; font-size:13px; margin-right:8px;
          border:1px solid rgba(23,34,59,0.08); background:#fff; color:{SAXON_NAVY}; }}
        .chip.warn {{ background: #FFF6EE; border-color:#FFE1C9; color:#7A3F0E; }}
        .chip.success {{ background:#ECFDF3; border-color:#C7F0D9; color:#13533A; }}
        .chip .dot {{ width:6px; height:6px; border-radius:50%; background:{SAXON_ORANGE}; display:inline-block; }}

        /* Chat bubbles */
        .chat-bubble {{ padding:12px 14px; border-radius:14px; line-height:1.5;
           border:1px solid rgba(23,34,59,0.08); }}
        .chat-user {{ background:#F4F6FA; }}
        .chat-assist {{ background:#FFFFFF; }}

        /* Hide default Streamlit chrome we don’t need */
        footer {{visibility:hidden}}
        .viewerBadge_container__1QSob {{display:none}}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_logo(width: int = 170):
    """Places the Saxon logo (left-aligned)."""
    if _LOGO_PATH.exists():
        st.image(str(_LOGO_PATH), width=width)
    else:
        st.markdown(f"<div style='font-weight:800;color:{SAXON_NAVY};font-size:22px'>SAXON</div>", unsafe_allow_html=True)

def header(title: str, subtitle: str | None = None):
    _inject_css()
    st.markdown(f"<h1 style='margin:8px 0 2px 0;color:{SAXON_NAVY}'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div style='color:{SAXON_GRAY};margin-bottom:8px'>{subtitle}</div>", unsafe_allow_html=True)

def greeting(name: str | None = None, right_badge: str = "Manufacturing AI Assist"):
    """Hero greeting similar to your reference UI."""
    _inject_css()
    # name can come from env or session
    if name is None:
        name = st.session_state.get("display_name") or os.environ.get("SAXON_USER_NAME") or "there"

    hour = datetime.now().hour
    if   5 <= hour < 12: sal = "Good morning"
    elif 12 <= hour < 17: sal = "Good afternoon"
    elif 17 <= hour < 22: sal = "Good evening"
    else: sal = "Hello"

    st.markdown(
        f"""
        <div class="sxn-hero">
          <div>
            <div class="sxn-hello">{sal}, {name}</div>
            <div class="sxn-sub">Join meetings and discover relevant insights with your Saxon copilot.</div>
          </div>
          <div class="sxn-pill">{right_badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def chips_row(items):
    """items: List[Tuple[label, style_key]] where style_key in {success,warn,neutral}"""
    _inject_css()
    html = []
    for label, style in items:
        cls = "chip"
        if style in ("success","warn"): cls += f" {style}"
        html.append(f"<span class='{cls}'><span class='dot'></span>{label}</span>")
    st.markdown(" ".join(html), unsafe_allow_html=True)
