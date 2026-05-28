"""UI text helpers — bold via HTML (no visible ** in the app)."""

from __future__ import annotations

import html
import re

import streamlit as st


def bold(text: str) -> str:
    return f"<b>{html.escape(text)}</b>"


def bold_line(text: str, *, required: bool = False) -> None:
    suffix = " *" if required else ""
    st.markdown(f"{bold(text)}{suffix}", unsafe_allow_html=True)


def rich(text: str) -> None:
    """Render string that may contain <b>...</b> (other text is escaped if needed)."""
    st.markdown(text, unsafe_allow_html=True)
