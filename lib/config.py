import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "registry.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DOC_CACHE_TTL_SECONDS = 3600

TOOL_TYPES = ("streamlit", "github_only", "apps_script")

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
