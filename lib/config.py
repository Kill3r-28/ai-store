import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "registry.db"
LEGACY_TOOLS_JSON = ROOT_DIR / "tools.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DOC_CACHE_TTL_SECONDS = 3600

TOOL_TYPES = ("streamlit", "github_only", "apps_script")
COMMENT_STATUSES = ("open", "accepted", "done")

# Starter hashtags shown on the register page (more can be added by users)
STARTER_USE_CASE_TAGS = [
    "content-gen",
    "ops-automation",
]

INFRA_CHECKLIST_KEYS = [
    "has_ci_cd",
    "has_tests",
    "has_tool_auth",
]

INFRA_RECOMMENDATIONS = {
    "has_ci_cd": "Set up CI/CD (e.g. GitHub Actions) so releases are repeatable and safer.",
    "has_tests": "Add automated tests to catch regressions before users do.",
    "has_tool_auth": "Enable secure login (Google OAuth / SSO) so only NxtWave employees can use the tool.",
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
    raw = get_secret("ALLOWED_EMAIL_DOMAINS", "nxtwave.co.in")
    if not raw:
        return ["nxtwave.co.in"]
    return [d.strip().lstrip("@").lower() for d in raw.split(",") if d.strip()]


def admin_emails() -> set[str]:
    raw = get_secret("ADMIN_EMAILS", "")
    if not raw:
        return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def dev_skip_auth() -> bool:
    return get_secret("DEV_SKIP_AUTH", "false").lower() in ("1", "true", "yes")


def oauth_is_configured() -> bool:
    """True when Streamlit OIDC is available and secrets have real Google credentials."""
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
    def _clean(v: object) -> str:
        s = str(v or "").strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            return s[1:-1].strip()
        return s

    client_id = _clean(auth.get("client_id", ""))
    client_secret = _clean(auth.get("client_secret", ""))
    cookie_secret = _clean(auth.get("cookie_secret", ""))
    if not cookie_secret or len(cookie_secret) < 16:
        return False
    if not client_id or not client_secret:
        return False
    placeholders = ("YOUR_GOOGLE", "your_google", "changeme", "xxxxxxxx")
    if any(p in client_id for p in placeholders):
        return False
    if any(p in client_secret for p in placeholders):
        return False
    return True


def test_personas_enabled() -> bool:
    return dev_skip_auth() or get_secret("ENABLE_TEST_PERSONAS", "false").lower() in (
        "1",
        "true",
        "yes",
    )


def is_admin(email: str) -> bool:
    return email.strip().lower() in admin_emails()
