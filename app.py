import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.auth import require_login
from lib.config import is_admin
from lib.db import init_db
from lib.routes import ADMIN_SCRIPT, GALLERY_SCRIPT, REGISTER_SCRIPT
from lib.theme import apply_app_theme

st.set_page_config(
    page_title="NxtWave Tool Library",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_app_theme()
init_db()

user_email, user_name = require_login()

gallery = st.Page(GALLERY_SCRIPT, title="Gallery", icon="🛍️", default=True)
register = st.Page(REGISTER_SCRIPT, title="Register", icon="➕")

nav_pages = [gallery, register]
if is_admin(user_email):
    nav_pages.append(st.Page(ADMIN_SCRIPT, title="Admin", icon="🛠️"))

pg = st.navigation(nav_pages, position="sidebar")
pg.run()
