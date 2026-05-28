import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.db import init_db
from lib.routes import GALLERY_SCRIPT, REGISTER_SCRIPT
from lib.theme import apply_app_theme

st.set_page_config(
    page_title="NxtWave Tool Library",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_app_theme()
init_db()

gallery = st.Page(GALLERY_SCRIPT, title="Gallery", icon="🛍️", default=True)
register = st.Page(REGISTER_SCRIPT, title="Register", icon="➕")

pg = st.navigation([gallery, register], position="sidebar")
pg.run()
