from __future__ import annotations

import streamlit as st

from lib.config import (
    allowed_email_domains,
    dev_skip_auth,
    google_oauth_is_configured,
    test_personas_enabled,
)
from lib.google_oauth import (
    build_authorization_url,
    exchange_code_for_user,
    get_app_redirect_uri,
    verify_oauth_state,
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


def get_user() -> tuple[str | None, str | None]:
    if dev_skip_auth() or test_personas_enabled() or not google_oauth_is_configured():
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


def handle_google_oauth_return() -> bool:
    """
    Process ?code= & ?state= after Google redirects to the app root.

    Returns True when the page should stop rendering (error or pending rerun).
    """
    if dev_skip_auth() or test_personas_enabled() or not google_oauth_is_configured():
        return False

    q = st.query_params
    if q.get("error"):
        desc = q.get("error_description") or q.get("error")
        st.error(f"Google sign-in failed: {desc}")
        st.query_params.clear()
        st.stop()

    code = q.get("code")
    state = q.get("state")
    if not code:
        return False

    if not state or not verify_oauth_state(str(state)):
        st.error("Sign-in session expired or invalid. Please try again.")
        st.query_params.clear()
        st.stop()

    try:
        profile = exchange_code_for_user(str(code))
    except Exception as exc:
        st.error(f"Sign-in failed: {exc}")
        with st.expander("Debug"):
            st.write(f"redirect_uri used: `{get_app_redirect_uri()}`")
            st.caption(
                "Add this exact URL under Google Cloud → Authorized redirect URIs. "
                "Remove `/oauth2callback` if you still use Streamlit native auth."
            )
        st.query_params.clear()
        st.stop()

    email = str(profile.get("email") or "").strip()
    name = str(profile.get("name") or email.split("@")[0])
    verified = profile.get("email_verified", True)
    hd = profile.get("hd")

    if not email:
        st.error("Google did not return an email address.")
        st.query_params.clear()
        st.stop()

    if verified is False:
        st.error("Please verify your Google account email before continuing.")
        st.query_params.clear()
        st.stop()

    if not _email_allowed(email, str(hd) if hd else None):
        st.error(
            f"Access restricted to @{', @'.join(allowed_email_domains())}. "
            "Use your company Google account."
        )
        st.query_params.clear()
        st.stop()

    _set_user(email, name)
    st.query_params.clear()
    st.rerun()


def render_oauth_config_errors() -> bool:
    """Show configuration problems on the login screen."""
    if google_oauth_is_configured():
        return False

    creds_missing = not google_oauth_is_configured()
    st.error(
        "Google sign-in is not configured. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, "
        "and `OAUTH_STATE_SECRET` in Streamlit Cloud **Secrets** (see `docs/DEPLOY_OAUTH.md`)."
    )
    if creds_missing:
        st.caption("Remove the `[auth]` block from Cloud secrets — it enables broken `/oauth2callback`.")
    st.stop()
    return True


def require_login() -> tuple[str, str]:
    """Gate pages; returns (email, name). Blocks on home until authenticated."""
    from lib.home import show_google_home, show_persona_home

    handle_google_oauth_return()

    use_personas = dev_skip_auth() or test_personas_enabled() or not google_oauth_is_configured()

    if use_personas:
        email, name = get_user()
        if email and name:
            return email, name
        show_persona_home(oauth_pending=not google_oauth_is_configured() and not dev_skip_auth())

    email, name = get_user()
    if email and name:
        return email, name

    show_google_home()


def render_user_sidebar() -> None:
    email, name = get_user()
    if not email:
        return

    use_personas = dev_skip_auth() or test_personas_enabled() or not google_oauth_is_configured()

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
    st.session_state["dev_logged_out"] = True
    st.rerun()
