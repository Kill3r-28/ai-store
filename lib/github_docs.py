from __future__ import annotations

import base64
from datetime import datetime, timezone

import httpx

from lib.config import DOC_CACHE_TTL_SECONDS, get_secret
from lib.db import clear_doc_cache, get_doc_cache, set_doc_cache
from lib.models import Tool


def _github_token() -> str | None:
    return get_secret("GITHUB_TOKEN")


def _parse_repo(github_repo: str) -> tuple[str, str] | None:
    repo = github_repo.strip().rstrip("/")
    if repo.startswith("https://github.com/"):
        repo = repo.replace("https://github.com/", "")
    parts = repo.split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None


def _cache_valid(fetched_at: str) -> bool:
    try:
        ts = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age < DOC_CACHE_TTL_SECONDS
    except Exception:
        return False


def fetch_file_from_github(owner: str, repo: str, path: str) -> str | None:
    token = _github_token()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        resp = httpx.get(url, headers=headers, timeout=15.0)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return None
        content = data.get("content")
        if not content:
            return None
        raw = base64.b64decode(content).decode("utf-8", errors="replace")
        return raw
    except Exception:
        return None


def get_tool_readme(tool: Tool, *, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached = get_doc_cache(tool.id, "readme")
        if cached and _cache_valid(cached[1]):
            return cached[0]
    if tool.github_repo:
        parsed = _parse_repo(tool.github_repo)
        if parsed:
            owner, repo = parsed
            content = fetch_file_from_github(owner, repo, "README.md")
            if content:
                set_doc_cache(tool.id, "readme", content)
                return content
    if tool.readme_fallback:
        return tool.readme_fallback
    return "_No README found. Add `README.md` in the GitHub repo or paste content when registering._"


def get_tool_future_plans(tool: Tool, *, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached = get_doc_cache(tool.id, "future_plans")
        if cached and _cache_valid(cached[1]):
            return cached[0]
    if tool.github_repo:
        parsed = _parse_repo(tool.github_repo)
        if parsed:
            owner, repo = parsed
            path = tool.future_plans_path or "docs/future_plans.md"
            content = fetch_file_from_github(owner, repo, path)
            if content:
                set_doc_cache(tool.id, "future_plans", content)
                return content
    if tool.future_plans_fallback:
        return tool.future_plans_fallback
    return "_No roadmap found. Add `docs/future_plans.md` in the repo or paste plans when registering._"


def refresh_tool_docs(tool: Tool) -> None:
    clear_doc_cache(tool.id)
    get_tool_readme(tool, force_refresh=True)
    get_tool_future_plans(tool, force_refresh=True)


def github_infra_hints(github_repo: str) -> dict[str, bool]:
    """Lightweight signals from GitHub API for infra scorecard."""
    parsed = _parse_repo(github_repo)
    if not parsed:
        return {}
    owner, repo = parsed
    token = _github_token()
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    hints: dict[str, bool] = {}
    paths_to_check = {
        "has_ci_cd": ".github/workflows",
        "has_tests": "tests",
        "has_requirements": "requirements.txt",
    }
    for key, path in paths_to_check.items():
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        try:
            resp = httpx.get(url, headers=headers, timeout=10.0)
            hints[key] = resp.status_code == 200
        except Exception:
            hints[key] = False
    readme = fetch_file_from_github(owner, repo, "README.md")
    hints["has_readme_github"] = readme is not None and len(readme) > 0
    return hints


def infra_score_summary(tool: Tool) -> tuple[int, int, dict[str, bool]]:
    """Returns (score, max_score, merged checklist including GitHub hints)."""
    from lib.config import INFRA_CHECKLIST_KEYS

    checklist = dict(tool.infra_checklist or {})
    for k in INFRA_CHECKLIST_KEYS:
        checklist.setdefault(k, False)

    github_hints: dict[str, bool] = {}
    if tool.github_repo:
        github_hints = github_infra_hints(tool.github_repo)
        if github_hints.get("has_ci_cd"):
            checklist["has_ci_cd"] = checklist.get("has_ci_cd") or True
        if github_hints.get("has_tests"):
            checklist["has_tests"] = checklist.get("has_tests") or True

    score = sum(1 for k in INFRA_CHECKLIST_KEYS if checklist.get(k))
    return score, len(INFRA_CHECKLIST_KEYS), {**checklist, **{f"gh_{k}": v for k, v in github_hints.items()}}
