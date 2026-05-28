#!/usr/bin/env python3
"""Validate Google OAuth secrets before deploying to Streamlit Cloud."""

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

from lib.auth_bootstrap import resolve_redirect_uri, validate_auth_config


def load_secrets() -> dict:
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        print(f"Missing {path} — copy from .streamlit/secrets.toml.example")
        sys.exit(1)

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore

    with path.open("rb") as f:
        return tomllib.load(f)


def main() -> int:
    secrets = load_secrets()
    auth = dict(secrets.get("auth") or {})
    redirect_uri = resolve_redirect_uri(secrets, auth)

    errors = validate_auth_config(auth, redirect_uri, secrets)
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    client_id = str(auth["client_id"]).strip()
    client_secret = str(auth["client_secret"]).strip()

    # invalid_client → bad id/secret; invalid_grant → id/secret OK, code bad (expected here)
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": "verify-oauth-placeholder",
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=15.0,
    )
    body = resp.json()
    err = body.get("error", "")

    print(f"redirect_uri: {redirect_uri}")
    print(f"client_id: {client_id[:20]}…")
    print(f"Google token endpoint: HTTP {resp.status_code} error={err!r}")

    if err == "invalid_client":
        print("\nFAIL: Google rejected client_id/client_secret. Regenerate secret in Google Cloud.")
        return 1
    if err in ("invalid_grant", "redirect_uri_mismatch"):
        print("\nOK: Google accepted your OAuth client credentials.")
        if err == "redirect_uri_mismatch":
            print("Note: redirect_uri mismatch with this test — fix URI in secrets and Google Console.")
        return 0

    print(f"\nUnexpected response: {body}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
