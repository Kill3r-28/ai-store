from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tool:
    id: str
    name: str
    short_desc: str
    owner_email: str
    owner_name: str
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
    like_count: int = 0
    user_liked: bool = False
    avg_rating: float | None = None
    rating_count: int = 0

    @classmethod
    def from_row(cls, row: dict[str, Any], *, user_liked: bool = False, like_count: int = 0,
                 avg_rating: float | None = None, rating_count: int = 0) -> Tool:
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
            owner_email=row.get("owner_email") or "",
            owner_name=row.get("owner_name") or "",
            tool_type=row.get("tool_type") or "streamlit",
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
            like_count=like_count,
            user_liked=user_liked,
            avg_rating=avg_rating,
            rating_count=rating_count,
        )


@dataclass
class Comment:
    id: int
    tool_id: str
    user_email: str
    user_name: str
    body: str
    status: str
    created_at: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Comment:
        return cls(
            id=row["id"],
            tool_id=row["tool_id"],
            user_email=row["user_email"],
            user_name=row["user_name"],
            body=row["body"],
            status=row.get("status") or "open",
            created_at=row["created_at"],
        )
