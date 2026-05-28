from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    id: str
    name: str
    short_desc: str
    submitter_name: str
    submitter_email: str
    tool_type: str
    app_url: str | None = None
    github_repo: str | None = None
    sheet_url: str | None = None
    use_case_tags: list[str] = field(default_factory=list)
    cluster_id: str | None = None
    future_plans_path: str = "docs/future_plans.md"
    infra_checklist: dict[str, bool] = field(default_factory=dict)
    readme_fallback: str | None = None
    future_plans_fallback: str | None = None
    icon_url: str | None = None
    launches: int = 0
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Tool:
        tags = row.get("use_case_tags") or "[]"
        if isinstance(tags, str):
            tags = json.loads(tags)
        checklist = row.get("infra_checklist") or "{}"
        if isinstance(checklist, str):
            checklist = json.loads(checklist)
        return cls(
            id=row["id"],
            name=row["name"],
            short_desc=row.get("short_desc") or "",
            submitter_name=row.get("submitter_name") or "",
            submitter_email=row.get("submitter_email") or "",
            tool_type=row.get("tool_type") or "web_app",
            app_url=row.get("app_url"),
            github_repo=row.get("github_repo"),
            sheet_url=row.get("sheet_url"),
            use_case_tags=tags,
            cluster_id=row.get("cluster_id"),
            future_plans_path=row.get("future_plans_path") or "docs/future_plans.md",
            infra_checklist=checklist,
            readme_fallback=row.get("readme_fallback"),
            future_plans_fallback=row.get("future_plans_fallback"),
            icon_url=row.get("icon_url"),
            launches=row.get("launches") or 0,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
