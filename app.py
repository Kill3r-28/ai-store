import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.auth import current_user
from lib.db import init_db
from lib.routes import GALLERY_SCRIPT, LOGIN_SCRIPT, REGISTER_SCRIPT
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
nav_pages = [gallery, register]

if current_user() is None:
    nav_pages.append(st.Page(LOGIN_SCRIPT, title="Login", icon="🔑"))

pg = st.navigation(nav_pages, position="sidebar")
pg.run()
