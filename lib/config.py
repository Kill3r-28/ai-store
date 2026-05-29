import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "registry.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DOC_CACHE_TTL_SECONDS = 3600

TOOL_TYPES = ("web_app", "github_only", "apps_script")

STARTER_USE_CASE_TAGS = [
    "content-gen",
    "ops-automation",
]

INFRA_CHECKLIST_KEYS = [
    "has_ci_cd",
    "has_tests",
]

INFRA_RECOMMENDATIONS = {
    "has_ci_cd": "Set up CI/CD (e.g. GitHub Actions) so releases are repeatable and safer.",
    "has_tests": "Add automated tests to catch regressions before users do.",
}


def get_secret(key: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


def allowed_email_domains() -> list[str]:
    raw = get_secret("ALLOWED_EMAIL_DOMAINS", "nxtwave.co.in") or ""
    domains = [d.strip().lstrip("@").lower() for d in raw.split(",") if d.strip()]
    return domains or ["nxtwave.co.in"]


def admin_credentials() -> tuple[str, str] | None:
    username = (get_secret("ADMIN_USERNAME") or "").strip()
    password = get_secret("ADMIN_PASSWORD") or ""
    if not username or not password:
        return None
    return username, password


def oauth_is_configured() -> bool:
    try:
        import streamlit as st
    except ImportError:
        return False
    if not hasattr(st, "login"):
        return False
    try:
        auth = st.secrets.get("auth", {})
    except Exception:
        return False
    if not auth:
        return False
    cookie_secret = str(auth.get("cookie_secret", "")).strip()
    provider = auth.get("google") or {}
    client_id = str(provider.get("client_id", "")).strip()
    client_secret = str(provider.get("client_secret", "")).strip()
    if not client_id or not client_secret or len(cookie_secret) < 16:
        return False
    placeholders = ("YOUR_GOOGLE", "your_google", "changeme", "PASTE_")
    if any(p in client_id for p in placeholders):
        return False
    if any(p in client_secret for p in placeholders):
        return False
    return True
