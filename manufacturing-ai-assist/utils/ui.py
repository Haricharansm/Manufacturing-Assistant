# -*- coding: utf-8 -*-
import streamlit as st
from pathlib import Path
from typing import Optional, List, Tuple

# Resolve assets relative to your repo layout
_ASSETS = Path("manufacturing-ai-assist") / "assets"

def _inject_css_once() -> None:
    if "_saxon_css" not in st.session_state:
        css_path = _ASSETS / "styles.css"
        css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.session_state["_saxon_css"] = True

def show_logo(width: int = 170) -> None:
    _inject_css_once()
    logo = str(_ASSETS / "saxon_logo.png")
    st.markdown(
        (
            '<div class="saxon-topbar">'
            f'<img src="{logo}" width="{width}" alt="Saxon"/>'
            '<div class="saxon-subtle">Manufacturing AI Assist</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )

def header(title: str, subtitle: Optional[str] = None) -> None:
    _inject_css_once()
    st.markdown(
        (
            '<div class="saxon-topbar" style="margin-top:4px;">'
            f'<h1 class="saxon-title">{title}</h1>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f"<div class='caption'>{subtitle}</div>", unsafe_allow_html=True)

def chip(text: str, tone: str = "neutral") -> None:
    st.markdown(
        f'<span class="chip {tone}"><span class="dot"></span>{text}</span>',
        unsafe_allow_html=True,
    )

def chips_row(items: List[Tuple[str, str]]) -> None:
    st.markdown("<div class='chips'>", unsafe_allow_html=True)
    for text, tone in items:
        chip(text, tone)
    st.markdown("</div>", unsafe_allow_html=True)
