from __future__ import annotations

import streamlit as st

from lib.auth_bootstrap import auth_config_summary, bootstrap_auth_secrets
from lib.config import (
    allowed_email_domains,
    dev_skip_auth,
    oauth_is_configured,
    test_personas_enabled,
)
from lib.personas import get_login_personas, persona_label


def _email_allowed(email: str, hd: str | None = None) -> bool:
    domains = allowed_email_domains()
    email_lower = email.lower()
    if any(email_lower.endswith(f"@{d}") for d in domains):
        return True
    if hd and hd.lower() in domains:
        return True
    return False


def _set_user(email: str, name: str) -> None:
    st.session_state["user_email"] = email.lower()
    st.session_state["user_name"] = name or email.split("@")[0]
    st.session_state["authenticated"] = True
    st.session_state.pop("dev_logged_out", None)


def is_oauth_callback_request() -> bool:
    """True when Google redirected back with an authorization code."""
    try:
        q = st.query_params
        return bool(q.get("code")) and bool(q.get("state"))
    except Exception:
        return False


def get_user() -> tuple[str | None, str | None]:
    if dev_skip_auth() or test_personas_enabled() or not oauth_is_configured():
        if st.session_state.get("dev_logged_out"):
            return None, None
        email = st.session_state.get("user_email")
        name = st.session_state.get("user_name")
        if email and name:
            return email, name
        return None, None
    if st.session_state.get("authenticated"):
        return st.session_state.get("user_email"), st.session_state.get("user_name")
    return None, None


def sync_user_from_streamlit_oidc() -> bool:
    """Copy st.user into session after a successful Google login."""
    if not oauth_is_configured():
        return False

    if st.session_state.get("authenticated"):
        return True

    if not st.user.is_logged_in:
        return False

    email = getattr(st.user, "email", None) or ""
    name = getattr(st.user, "name", None) or email.split("@")[0]
    verified = getattr(st.user, "email_verified", True)
    hd = getattr(st.user, "hd", None)

    if not email:
        st.error("Could not read email from Google account.")
        if hasattr(st, "logout"):
            st.logout()
        st.stop()

    if not verified:
        st.error("Please verify your Google account email before continuing.")
        st.stop()

    if not _email_allowed(email, hd):
        st.error(
            f"Access restricted to @{', @'.join(allowed_email_domains())}. "
            "Use your company Google account."
        )
        if hasattr(st, "logout"):
            st.logout()
        st.stop()

    _set_user(email, name)
    return True


def handle_oauth_callback() -> bool:
    """
    Lightweight handler while /oauth2callback query params are present.

    Returns True when the caller should stop rendering the rest of the app.
    """
    if not is_oauth_callback_request():
        return False

    if dev_skip_auth() or test_personas_enabled() or not oauth_is_configured():
        return False

    st.markdown("### Completing Google sign-in…")
    if sync_user_from_streamlit_oidc():
        st.query_params.clear()
        st.rerun()
    return True


def render_oauth_config_errors() -> bool:
    """
    Show configuration problems on the login screen.

    Returns True when errors were shown (caller should stop).
    """
    errors = bootstrap_auth_secrets()
    if not errors:
        return False

    st.error("Google sign-in is misconfigured. Fix Streamlit Cloud **Secrets** (or local `secrets.toml`):")
    for err in errors:
        st.markdown(f"- {err}")
    summary = auth_config_summary()
    if summary:
        with st.expander("Auth debug (no secrets shown)"):
            st.json(summary)
    st.stop()
    return True


def require_login() -> tuple[str, str]:
    """Gate pages; returns (email, name). Blocks on home until authenticated."""
    from lib.home import show_google_home, show_persona_home

    if handle_oauth_callback():
        st.stop()

    use_personas = dev_skip_auth() or test_personas_enabled() or not oauth_is_configured()

    if use_personas:
        email, name = get_user()
        if email and name:
            return email, name
        show_persona_home(oauth_pending=not oauth_is_configured() and not dev_skip_auth())

    if sync_user_from_streamlit_oidc():
        email, name = get_user()
        if email and name:
            return email, name

    show_google_home()


def render_user_sidebar() -> None:
    email, name = get_user()
    if not email:
        return

    use_personas = dev_skip_auth() or test_personas_enabled() or not oauth_is_configured()

    with st.sidebar:
        if use_personas:
            st.caption("Test profile")
            personas = get_login_personas()
            labels = [persona_label(p) for p in personas]
            current_id = st.session_state.get("active_persona_id")
            if not current_id:
                for p in personas:
                    if p["email"].lower() == email.lower():
                        current_id = p["id"]
                        break
            try:
                idx = next(i for i, p in enumerate(personas) if p["id"] == current_id)
            except StopIteration:
                idx = 0
            switch_label = st.selectbox(
                "Switch persona",
                labels,
                index=idx,
                label_visibility="collapsed",
                key="persona_sidebar_switch",
            )
            picked = personas[labels.index(switch_label)]
            if picked["email"].lower() != email.lower():
                _set_user(picked["email"], picked["name"])
                st.session_state["active_persona_id"] = picked["id"]
                st.rerun()

        st.markdown(
            f"""
            <div class="user-panel">
                <p class="user-name">{name}</p>
                <p class="user-email">{email}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True, type="primary", key="sidebar_logout"):
            logout_user()


def logout_user() -> None:
    for key in ("authenticated", "user_email", "user_name", "active_persona_id"):
        st.session_state.pop(key, None)
    if dev_skip_auth() or test_personas_enabled() or not oauth_is_configured():
        st.session_state["dev_logged_out"] = True
        st.rerun()
    if hasattr(st, "logout"):
        try:
            if getattr(st.user, "is_logged_in", False):
                st.logout()
                return
        except Exception:
            pass
    st.rerun()
