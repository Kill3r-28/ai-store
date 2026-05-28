"""Lightweight auth: Google OIDC for nxtwave users, admin via username/password."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from lib.config import admin_credentials, allowed_email_domains, oauth_is_configured


@dataclass
class User:
    email: str
    name: str
    role: str  # "google" or "admin"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def current_user() -> User | None:
    data = st.session_state.get("auth_user")
    if not data:
        return None
    return User(email=data["email"], name=data["name"], role=data["role"])


def is_admin() -> bool:
    u = current_user()
    return bool(u and u.is_admin)


def _store(email: str, name: str, role: str) -> None:
    st.session_state["auth_user"] = {"email": email, "name": name, "role": role}


def login_as_admin(username: str, password: str) -> bool:
    creds = admin_credentials()
    if not creds:
        return False
    expected_user, expected_pass = creds
    if username.strip() == expected_user and password == expected_pass:
        _store(email=expected_user, name="Admin", role="admin")
        return True
    return False


def email_domain_allowed(email: str) -> bool:
    email_l = email.lower()
    return any(email_l.endswith(f"@{d}") for d in allowed_email_domains())


def sync_google_user() -> bool:
    """Copy st.user into session after a successful Google sign-in. Returns True on first sync."""
    if not oauth_is_configured():
        return False
    if not getattr(st.user, "is_logged_in", False):
        return False
    existing = st.session_state.get("auth_user")
    if existing and existing.get("role") == "google":
        return False

    email = (getattr(st.user, "email", "") or "").strip()
    name = getattr(st.user, "name", None) or (email.split("@")[0] if email else "")
    verified = getattr(st.user, "email_verified", True)

    if not email or not verified:
        st.error("Google account email is missing or unverified.")
        if hasattr(st, "logout"):
            st.logout()
        st.stop()

    if not email_domain_allowed(email):
        domains = ", ".join(f"@{d}" for d in allowed_email_domains())
        st.error(f"Access restricted to {domains}. Sign in with your company Google account.")
        if hasattr(st, "logout"):
            st.logout()
        st.stop()

    _store(email=email, name=name, role="google")
    return True


def logout() -> None:
    st.session_state.pop("auth_user", None)
    if hasattr(st, "logout"):
        try:
            if getattr(st.user, "is_logged_in", False):
                st.logout()
                return
        except Exception:
            pass
    st.rerun()


def render_sidebar_status() -> None:
    """Tiny sign-in / sign-out block for the sidebar."""
    from lib.routes import LOGIN_SCRIPT

    user = current_user()
    with st.sidebar:
        st.divider()
        if user:
            label = f"{user.name}"
            if user.role == "admin":
                label += "  ·  admin"
            st.caption(label)
            st.caption(user.email)
            if st.button("Log out", key="sidebar_logout", use_container_width=True):
                logout()
        else:
            if st.button("Sign in", key="sidebar_signin", type="primary", use_container_width=True):
                st.switch_page(LOGIN_SCRIPT)
