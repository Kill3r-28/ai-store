import streamlit as st

from lib.auth import (
    current_user,
    login_as_admin,
    render_sidebar_status,
    sync_google_user,
)
from lib.config import admin_credentials, allowed_email_domains, oauth_is_configured
from lib.routes import GALLERY_SCRIPT
from lib.theme import apply_app_theme

apply_app_theme()

# Pick up a just-completed Google sign-in before deciding what to render.
sync_google_user()

# If the user is already signed in (Google or admin), bounce them to the Gallery.
if current_user() is not None:
    st.switch_page(GALLERY_SCRIPT)

render_sidebar_status()

st.title("Sign in")
st.caption("Pick how you want to continue.")

google_col, admin_col = st.columns(2)

with google_col:
    st.subheader("Continue with Google")
    domains = ", ".join(f"@{d}" for d in allowed_email_domains())
    st.caption(f"Restricted to {domains}.")
    if not oauth_is_configured():
        st.info(
            "Google sign-in isn't configured. Add the `[auth]` block in "
            "`.streamlit/secrets.toml` (or Streamlit Cloud Secrets)."
        )
    elif st.button("Login with Google account", key="google_btn", use_container_width=True):
        try:
            st.login("google")
        except Exception as exc:
            st.error(f"Google sign-in failed: {exc}")

with admin_col:
    st.subheader("Admin login")
    if not admin_credentials():
        st.info(
            "Admin login isn't configured. Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in secrets."
        )
    else:
        show_form = st.session_state.get("show_admin_form", False)
        if not show_form:
            if st.button("Admin login", key="admin_btn", use_container_width=True):
                st.session_state["show_admin_form"] = True
                st.rerun()
        else:
            with st.form("admin_login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="dev@nxtwave")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")
                if submitted:
                    if login_as_admin(username, password):
                        st.session_state.pop("show_admin_form", None)
                        st.switch_page(GALLERY_SCRIPT)
                    else:
                        st.error("Invalid username or password.")
            if st.button("Cancel", key="admin_cancel"):
                st.session_state.pop("show_admin_form", None)
                st.rerun()

st.divider()
if st.button("← Back to Gallery"):
    st.switch_page(GALLERY_SCRIPT)
