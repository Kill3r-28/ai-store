"""Global Streamlit theme — single off-black background (#343231)."""

import streamlit as st

BG = "#343231"
BG_SIDEBAR = "#2e2c2b"


def apply_app_theme() -> None:
    st.markdown(
        f"""
        <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main > div {{
            background-color: {BG} !important;
            color: #f5f5f5 !important;
        }}
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child {{
            background-color: {BG_SIDEBAR} !important;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(52, 50, 49, 0) !important;
        }}
        [data-testid="stToolbar"] {{
            background-color: rgba(52, 50, 49, 0) !important;
        }}
        .hashtag-compact-wrap {{
            max-width: 420px;
        }}
        .hashtag-compact-wrap [data-testid="stHorizontalBlock"] {{
            gap: 0.35rem;
            align-items: center;
        }}
        .hashtag-compact-wrap [data-testid="stHorizontalBlock"] button {{
            padding: 0.2rem 0.65rem;
            min-height: 2rem;
            font-size: 0.85rem;
            border-radius: 999px;
        }}
        .hashtag-compact-wrap input {{
            font-size: 0.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
