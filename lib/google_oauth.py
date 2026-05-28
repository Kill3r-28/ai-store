"""Google OAuth handled in-app (avoids Streamlit /oauth2callback 500s on Cloud)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from lib.config import get_google_credentials, get_oauth_state_secret, get_secret

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = "openid email profile"
STATE_MAX_AGE_SECONDS = 600


def get_app_redirect_uri() -> str:
    """OAuth redirect URI — app root (not /oauth2callback)."""
    try:
        import streamlit as st

        url = str(getattr(st.context, "url", "") or "").strip()
        if url.startswith("http"):
            from urllib.parse import urlparse

            parsed = urlparse(url.split("?")[0])
            return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass

    base = get_secret("APP_PUBLIC_URL")
    if base:
        return base.strip().rstrip("/") + "/"

    port = __import__("os").environ.get("STREAMLIT_SERVER_PORT", "8501")
    return f"http://localhost:{port}/"


def _sign_state(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def make_oauth_state() -> str:
    secret = get_oauth_state_secret()
    if not secret:
        raise ValueError("OAUTH_STATE_SECRET or legacy auth.cookie_secret is not configured")
    nonce = secrets.token_urlsafe(16)
    ts = str(int(time.time()))
    payload = f"{nonce}.{ts}"
    return f"{payload}.{_sign_state(payload, secret)}"


def verify_oauth_state(state: str) -> bool:
    secret = get_oauth_state_secret()
    if not secret:
        return False
    try:
        nonce, ts, sig = state.rsplit(".", 2)
        payload = f"{nonce}.{ts}"
        if not hmac.compare_digest(sig, _sign_state(payload, secret)):
            return False
        if int(time.time()) - int(ts) > STATE_MAX_AGE_SECONDS:
            return False
        return True
    except (ValueError, TypeError):
        return False


def build_authorization_url() -> str:
    creds = get_google_credentials()
    if not creds:
        raise ValueError("Google OAuth credentials are not configured")
    client_id, _ = creds
    redirect_uri = get_app_redirect_uri()
    state = make_oauth_state()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _decode_jwt_payload(id_token: str) -> dict[str, Any]:
    part = id_token.split(".")[1]
    padded = part + "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def exchange_code_for_user(code: str) -> dict[str, Any]:
    creds = get_google_credentials()
    if not creds:
        raise ValueError("Google OAuth credentials are not configured")
    client_id, client_secret = creds
    redirect_uri = get_app_redirect_uri()

    resp = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30.0,
    )
    if resp.status_code != 200:
        err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        msg = err.get("error_description") or err.get("error") or resp.text
        raise ValueError(f"Google token exchange failed: {msg}")

    token = resp.json()
    userinfo = token.get("userinfo")
    if isinstance(userinfo, dict) and userinfo:
        return userinfo

    id_token = token.get("id_token")
    if not id_token:
        raise ValueError("Google did not return user information")
    return _decode_jwt_payload(id_token)
