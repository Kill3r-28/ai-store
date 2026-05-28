from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from lib.config import DB_PATH, INFRA_CHECKLIST_KEYS
from lib.models import Tool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_tag(tag: str) -> str:
    t = tag.strip().lower().lstrip("#")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in tags:
        t = normalize_tag(raw)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or str(uuid4())[:8]


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                short_desc TEXT NOT NULL DEFAULT '',
                submitter_name TEXT NOT NULL DEFAULT '',
                submitter_email TEXT NOT NULL DEFAULT '',
                tool_type TEXT NOT NULL DEFAULT 'streamlit',
                app_url TEXT,
                github_repo TEXT,
                sheet_url TEXT,
                use_case_tags TEXT NOT NULL DEFAULT '[]',
                cluster_id TEXT,
                future_plans_path TEXT NOT NULL DEFAULT 'docs/future_plans.md',
                infra_checklist TEXT NOT NULL DEFAULT '{}',
                readme_fallback TEXT,
                future_plans_fallback TEXT,
                icon_url TEXT,
                launches INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS doc_cache (
                tool_id TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                content TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (tool_id, doc_type),
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tools_cluster ON tools(cluster_id);
            """
        )


def list_tools(
    *,
    search: str | None = None,
    tool_type: str | None = None,
    tag: str | None = None,
    cluster_id: str | None = None,
) -> list[Tool]:
    query = "SELECT * FROM tools WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (name LIKE ? OR short_desc LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if tool_type and tool_type != "all":
        query += " AND tool_type = ?"
        params.append(tool_type)
    if tag:
        query += " AND use_case_tags LIKE ?"
        params.append(f'%"{tag}"%')
    if cluster_id:
        query += " AND cluster_id = ?"
        params.append(cluster_id)
    query += " ORDER BY name COLLATE NOCASE"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Tool.from_row(dict(r)) for r in rows]


def get_tool(tool_id: str) -> Tool | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tools WHERE id = ?", (tool_id,)).fetchone()
    if not row:
        return None
    return Tool.from_row(dict(row))


def get_all_tags() -> list[str]:
    tools = list_tools()
    tags: set[str] = set()
    for t in tools:
        tags.update(t.use_case_tags)
    return sorted(tags)


def create_tool(data: dict[str, Any]) -> Tool:
    now = _now()
    tool_id = data.get("id") or slugify(data["name"])
    with get_conn() as conn:
        base_id = tool_id
        n = 1
        while conn.execute("SELECT 1 FROM tools WHERE id = ?", (tool_id,)).fetchone():
            tool_id = f"{base_id}-{n}"
            n += 1
        checklist = data.get("infra_checklist") or {k: False for k in INFRA_CHECKLIST_KEYS}
        conn.execute(
            """
            INSERT INTO tools (
                id, name, short_desc, submitter_name, submitter_email, tool_type,
                app_url, github_repo, sheet_url, use_case_tags, cluster_id,
                future_plans_path, infra_checklist, readme_fallback,
                future_plans_fallback, icon_url, launches, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                tool_id,
                data["name"],
                data.get("short_desc", ""),
                data.get("submitter_name", ""),
                data.get("submitter_email", ""),
                data.get("tool_type", "streamlit"),
                data.get("app_url"),
                data.get("github_repo"),
                data.get("sheet_url"),
                json.dumps(normalize_tags(data.get("use_case_tags") or [])),
                data.get("cluster_id"),
                data.get("future_plans_path") or "docs/future_plans.md",
                json.dumps(checklist),
                data.get("readme_fallback"),
                data.get("future_plans_fallback"),
                data.get("icon_url"),
                now,
                now,
            ),
        )
    return get_tool(tool_id)  # type: ignore[return-value]


def update_tool(tool_id: str, data: dict[str, Any]) -> Tool | None:
    existing = get_tool(tool_id)
    if not existing:
        return None
    now = _now()
    checklist = data.get("infra_checklist", existing.infra_checklist)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tools SET
                name = ?, short_desc = ?, submitter_name = ?, submitter_email = ?,
                tool_type = ?, app_url = ?, github_repo = ?, sheet_url = ?,
                use_case_tags = ?, cluster_id = ?, future_plans_path = ?,
                infra_checklist = ?, readme_fallback = ?, future_plans_fallback = ?,
                icon_url = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data.get("name", existing.name),
                data.get("short_desc", existing.short_desc),
                data.get("submitter_name", existing.submitter_name),
                data.get("submitter_email", existing.submitter_email),
                data.get("tool_type", existing.tool_type),
                data.get("app_url", existing.app_url),
                data.get("github_repo", existing.github_repo),
                data.get("sheet_url", existing.sheet_url),
                json.dumps(normalize_tags(data.get("use_case_tags", existing.use_case_tags))),
                data.get("cluster_id", existing.cluster_id),
                data.get("future_plans_path", existing.future_plans_path),
                json.dumps(checklist),
                data.get("readme_fallback", existing.readme_fallback),
                data.get("future_plans_fallback", existing.future_plans_fallback),
                data.get("icon_url", existing.icon_url),
                now,
                tool_id,
            ),
        )
    return get_tool(tool_id)


def increment_launches(tool_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE tools SET launches = launches + 1, updated_at = ? WHERE id = ?",
            (_now(), tool_id),
        )


def get_doc_cache(tool_id: str, doc_type: str) -> tuple[str, str] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content, fetched_at FROM doc_cache WHERE tool_id = ? AND doc_type = ?",
            (tool_id, doc_type),
        ).fetchone()
    if not row:
        return None
    return row["content"], row["fetched_at"]


def set_doc_cache(tool_id: str, doc_type: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO doc_cache (tool_id, doc_type, content, fetched_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tool_id, doc_type) DO UPDATE SET
                content = excluded.content,
                fetched_at = excluded.fetched_at
            """,
            (tool_id, doc_type, content, _now()),
        )


def clear_doc_cache(tool_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM doc_cache WHERE tool_id = ?", (tool_id,))


def delete_tool(tool_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        return cur.rowcount > 0
