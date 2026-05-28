"""Global Streamlit theme — single off-black background (#343231)."""

import streamlit as st

BG = "#343231"
BG_SIDEBAR = "#2e2c2b"
BG_PANEL = "#3d3b39"
BORDER = "#4a4846"


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
        [data-testid="stSidebar"] .user-panel {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
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
        .user-panel {{
            padding: 0.85rem 1rem;
            border-radius: 12px;
            margin-bottom: 0.75rem;
        }}
        .user-panel .user-name {{
            font-weight: 600;
            font-size: 0.95rem;
            margin: 0;
            color: #f5f5f5;
        }}
        .user-panel .user-email {{
            font-size: 0.75rem;
            opacity: 0.75;
            margin: 0.15rem 0 0 0;
            color: #e5e5e5;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
