import streamlit as st

from lib.auth import require_login, render_user_sidebar
from lib.config import STARTER_USE_CASE_TAGS, is_admin
from lib.db import delete_tool, init_db, list_tools
from lib.formatting import bold
from lib.theme import apply_app_theme

apply_app_theme()
init_db()
user_email, user_name = require_login()
render_user_sidebar()

if not is_admin(user_email):
    st.error("Admin access only. Your email must be listed in ADMIN_EMAILS in secrets.")
    st.stop()

st.title("Admin")
st.caption(f"Starter hashtags: {', '.join('#' + t for t in STARTER_USE_CASE_TAGS)}")

st.subheader("Manage tools")
tools = list_tools()
if not tools:
    st.info("No tools registered yet.")
    st.stop()

for t in tools:
    tags = " ".join(f"#{x}" for x in t.use_case_tags) if t.use_case_tags else "—"
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(
            f"{bold(t.name)} (`{t.id}`) — {t.owner_name} — {tags}",
            unsafe_allow_html=True,
        )
    with col2:
        confirm_key = f"admin_confirm_{t.id}"
        if st.session_state.get(confirm_key):
            if st.button("Confirm", key=f"admin_yes_{t.id}", type="primary"):
                delete_tool(t.id)
                st.session_state.pop(confirm_key, None)
                st.success(f"Deleted {t.name}.")
                st.rerun()
        else:
            if st.button("Delete", key=f"admin_del_{t.id}"):
                st.session_state[confirm_key] = True
                st.rerun()
