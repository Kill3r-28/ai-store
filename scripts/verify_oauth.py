#!/usr/bin/env python3
"""Validate Google OAuth secrets (in-app flow, app-root redirect)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import httpx
except ImportError:
    print("Install dependencies: pip install -r requirements.txt")
    sys.exit(1)

from lib.config import get_google_credentials, get_oauth_state_secret


def load_secrets() -> dict:
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        print(f"Missing {path}")
        sys.exit(1)
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    with path.open("rb") as f:
        return tomllib.load(f)


def redirect_uri(secrets: dict) -> str:
    base = secrets.get("APP_PUBLIC_URL")
    if base:
        return str(base).strip().rstrip("/") + "/"
    return "http://localhost:8501/"


def main() -> int:
    secrets = load_secrets()
    if secrets.get("auth"):
        print("WARNING: [auth] section found — remove it on Streamlit Cloud to avoid /oauth2callback errors.")

    creds = get_google_credentials()
    if not creds:
        # Load from file without streamlit runtime
        cid = secrets.get("GOOGLE_CLIENT_ID") or (secrets.get("auth") or {}).get("client_id")
        cs = secrets.get("GOOGLE_CLIENT_SECRET") or (secrets.get("auth") or {}).get("client_secret")
        if not cid or not cs:
            print("FAIL: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
            return 1
        creds = (str(cid).strip(), str(cs).strip())

    client_id, client_secret = creds
    uri = redirect_uri(secrets)

    if not get_oauth_state_secret() and not secrets.get("OAUTH_STATE_SECRET"):
        auth = secrets.get("auth") or {}
        if not auth.get("cookie_secret"):
            print("FAIL: Set OAUTH_STATE_SECRET (32+ random chars)")
            return 1

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": "verify-placeholder",
            "grant_type": "authorization_code",
            "redirect_uri": uri,
        },
        timeout=15.0,
    )
    err = resp.json().get("error", "")
    print(f"redirect_uri: {uri}")
    print(f"client_id: {client_id[:24]}…")
    print(f"Google: error={err!r}")

    if err == "invalid_client":
        print("\nFAIL: Invalid client_id or client_secret")
        return 1
    if err in ("invalid_grant", "redirect_uri_mismatch"):
        print("\nOK: Credentials accepted (redirect_uri_mismatch only affects fake code test).")
        return 0
    print(f"\nUnexpected: {resp.json()}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
