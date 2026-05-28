"""
Normalize and patch Streamlit [auth] secrets before OAuth routes run.

Call bootstrap_auth_secrets() at the very start of app.py (before st.set_page_config).
"""

from __future__ import annotations

import os
from typing import Any

GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"
DEFAULT_LOCAL_REDIRECT = "http://localhost:8501/oauth2callback"
OAUTH_CALLBACK_SUFFIX = "/oauth2callback"


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1].strip()
    return v


def _public_base_url(secrets_root: dict[str, Any]) -> str | None:
    """Production app URL without path, e.g. https://nxtwave-ai-store.streamlit.app."""
    for key in ("APP_PUBLIC_URL", "STREAMLIT_APP_URL"):
        raw = secrets_root.get(key) or os.environ.get(key)
        if raw:
            base = _strip_quotes(str(raw)).rstrip("/")
            if base:
                return base
    return None


def resolve_redirect_uri(secrets_root: dict[str, Any], auth: dict[str, Any]) -> str:
    """
    Pick the OAuth redirect URI Streamlit should use.

    On Streamlit Cloud, set APP_PUBLIC_URL so redirect_uri stays correct even if
    [auth].redirect_uri was copied from a local dev template.
    """
    base = _public_base_url(secrets_root)
    if base:
        return f"{base}{OAUTH_CALLBACK_SUFFIX}"

    raw = auth.get("redirect_uri") or os.environ.get("AUTH_REDIRECT_URI") or os.environ.get(
        "OAUTH_REDIRECT_URI"
    )
    if raw:
        uri = _strip_quotes(str(raw)).rstrip("/")
        if not uri.endswith(OAUTH_CALLBACK_SUFFIX):
            uri = f"{uri}{OAUTH_CALLBACK_SUFFIX}"
        return uri

    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    return f"http://localhost:{port}{OAUTH_CALLBACK_SUFFIX}"


def validate_auth_config(
    auth: dict[str, Any], redirect_uri: str, secrets_root: dict[str, Any] | None = None
) -> list[str]:
    """Human-readable validation errors (empty list = OK)."""
    errors: list[str] = []

    client_id = _strip_quotes(str(auth.get("client_id", "")))
    client_secret = _strip_quotes(str(auth.get("client_secret", "")))
    cookie_secret = _strip_quotes(str(auth.get("cookie_secret", "")))

    if not client_id or "YOUR_GOOGLE" in client_id.upper():
        errors.append("Missing or placeholder `client_id` under [auth].")
    elif not client_id.endswith(".apps.googleusercontent.com"):
        errors.append("`client_id` should end with `.apps.googleusercontent.com`.")

    if not client_secret or "YOUR_GOOGLE" in client_secret.upper():
        errors.append("Missing or placeholder `client_secret` under [auth].")
    elif not client_secret.startswith("GOCSPX-"):
        errors.append(
            "`client_secret` should start with `GOCSPX-` (Web application client in Google Cloud)."
        )

    if not cookie_secret or cookie_secret.lower() in ("changeme", "xxx", "somesecret"):
        errors.append("Set a strong random `cookie_secret` under [auth] (32+ characters).")
    elif len(cookie_secret) < 32:
        errors.append("`cookie_secret` should be at least 32 characters.")

    if not redirect_uri.startswith(("http://", "https://")):
        errors.append("`redirect_uri` must be an absolute URL.")
    if redirect_uri.endswith("/"):
        errors.append("`redirect_uri` must not end with `/` (except `/oauth2callback`).")
    if not redirect_uri.endswith(OAUTH_CALLBACK_SUFFIX):
        errors.append(f"`redirect_uri` must end with `{OAUTH_CALLBACK_SUFFIX}`.")

    if secrets_root and "localhost" in redirect_uri and _public_base_url(secrets_root):
        errors.append("redirect_uri points to localhost but APP_PUBLIC_URL is set — check secrets.")

    metadata = _strip_quotes(str(auth.get("server_metadata_url", "")))
    if metadata and metadata != GOOGLE_METADATA_URL:
        if "google" in metadata and "openid-configuration" not in metadata:
            errors.append("`server_metadata_url` looks invalid for Google OIDC.")

    return errors


def bootstrap_auth_secrets() -> list[str]:
    """
    Patch Streamlit's secrets singleton with normalized [auth] values.

    Returns validation errors (empty when configuration looks valid).
    """
    try:
        from streamlit.runtime.secrets import secrets_singleton
    except ImportError:
        return []

    try:
        root: dict[str, Any] = dict(secrets_singleton._secrets or {})
    except Exception:
        return []

    auth: dict[str, Any] = dict(root.get("auth") or {})
    if not auth:
        return []

    for key in ("client_id", "client_secret", "cookie_secret", "server_metadata_url", "redirect_uri"):
        if key in auth and auth[key] is not None:
            auth[key] = _strip_quotes(str(auth[key]))

    if not auth.get("server_metadata_url"):
        auth["server_metadata_url"] = GOOGLE_METADATA_URL

    redirect_uri = resolve_redirect_uri(root, auth)
    auth["redirect_uri"] = redirect_uri

    root["auth"] = auth
    secrets_singleton._secrets = root

    try:
        secrets_singleton._maybe_set_environment_variable("auth", auth)
    except Exception:
        pass

    return validate_auth_config(auth, redirect_uri, root)


def auth_config_summary() -> dict[str, str]:
    """Non-secret summary for debugging on the login page."""
    try:
        import streamlit as st

        auth = dict(st.secrets.get("auth", {}))
    except Exception:
        return {}

    cid = str(auth.get("client_id", ""))
    masked_id = f"{cid[:12]}…" if len(cid) > 12 else "(not set)"
    uri = str(auth.get("redirect_uri", ""))
    return {
        "redirect_uri": uri,
        "client_id": masked_id,
        "cookie_secret_len": str(len(str(auth.get("cookie_secret", "")))),
        "has_metadata_url": "yes" if auth.get("server_metadata_url") else "no",
    }
