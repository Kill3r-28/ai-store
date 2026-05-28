from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from lib.config import DB_PATH, LEGACY_TOOLS_JSON, INFRA_CHECKLIST_KEYS
from lib.models import Comment, Tool


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
                owner_email TEXT NOT NULL,
                owner_name TEXT NOT NULL DEFAULT '',
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

            CREATE TABLE IF NOT EXISTS likes (
                tool_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (tool_id, user_email),
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ratings (
                tool_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
                comment TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (tool_id, user_email),
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                user_name TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS doc_cache (
                tool_id TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                content TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                PRIMARY KEY (tool_id, doc_type),
                FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tools_owner ON tools(owner_email);
            CREATE INDEX IF NOT EXISTS idx_tools_cluster ON tools(cluster_id);
            CREATE INDEX IF NOT EXISTS idx_comments_tool ON comments(tool_id);
            """
        )
    _migrate_legacy_json()


def _migrate_legacy_json() -> None:
    if not LEGACY_TOOLS_JSON.exists():
        return
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
        if count > 0:
            return
        with open(LEGACY_TOOLS_JSON, encoding="utf-8") as f:
            legacy = json.load(f)
        now = _now()
        for item in legacy:
            tool_id = slugify(item.get("name", "tool"))
            base_id = tool_id
            n = 1
            while conn.execute("SELECT 1 FROM tools WHERE id = ?", (tool_id,)).fetchone():
                tool_id = f"{base_id}-{n}"
                n += 1
            conn.execute(
                """
                INSERT INTO tools (
                    id, name, short_desc, owner_email, owner_name, tool_type,
                    app_url, github_repo, launches, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool_id,
                    item.get("name", "Unnamed"),
                    item.get("desc", ""),
                    "legacy@import",
                    "Legacy Import",
                    "streamlit",
                    item.get("url"),
                    None,
                    item.get("launches", 0),
                    now,
                    now,
                ),
            )


def _enrich_tool(row: sqlite3.Row, user_email: str | None) -> Tool:
    tool_id = row["id"]
    with get_conn() as conn:
        like_count = conn.execute(
            "SELECT COUNT(*) FROM likes WHERE tool_id = ?", (tool_id,)
        ).fetchone()[0]
        user_liked = False
        if user_email:
            user_liked = (
                conn.execute(
                    "SELECT 1 FROM likes WHERE tool_id = ? AND user_email = ?",
                    (tool_id, user_email.lower()),
                ).fetchone()
                is not None
            )
        rating_row = conn.execute(
            "SELECT AVG(score) AS avg_score, COUNT(*) AS cnt FROM ratings WHERE tool_id = ?",
            (tool_id,),
        ).fetchone()
    avg = rating_row["avg_score"]
    return Tool.from_row(
        dict(row),
        user_liked=user_liked,
        like_count=like_count,
        avg_rating=float(avg) if avg is not None else None,
        rating_count=rating_row["cnt"] or 0,
    )


def list_tools(
    *,
    user_email: str | None = None,
    search: str | None = None,
    tool_type: str | None = None,
    tag: str | None = None,
    cluster_id: str | None = None,
    owner_only: bool = False,
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
    if owner_only and user_email:
        query += " AND owner_email = ?"
        params.append(user_email.lower())
    query += " ORDER BY name COLLATE NOCASE"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_enrich_tool(r, user_email) for r in rows]


def get_tool(tool_id: str, user_email: str | None = None) -> Tool | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tools WHERE id = ?", (tool_id,)).fetchone()
    if not row:
        return None
    return _enrich_tool(row, user_email)


def get_all_tags() -> list[str]:
    tools = list_tools()
    tags: set[str] = set()
    for t in tools:
        tags.update(t.use_case_tags)
    return sorted(tags)


def get_all_clusters() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT cluster_id FROM tools WHERE cluster_id IS NOT NULL AND cluster_id != ''"
        ).fetchall()
    return sorted(r[0] for r in rows)


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
                id, name, short_desc, owner_email, owner_name, tool_type,
                app_url, github_repo, sheet_url, use_case_tags, cluster_id,
                future_plans_path, infra_checklist, readme_fallback,
                future_plans_fallback, icon_url, launches, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                tool_id,
                data["name"],
                data.get("short_desc", ""),
                data["owner_email"].lower(),
                data.get("owner_name", ""),
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
    return get_tool(tool_id, data["owner_email"])  # type: ignore[return-value]


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
                name = ?, short_desc = ?, tool_type = ?,
                app_url = ?, github_repo = ?, sheet_url = ?,
                use_case_tags = ?, cluster_id = ?, future_plans_path = ?,
                infra_checklist = ?, readme_fallback = ?, future_plans_fallback = ?,
                icon_url = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data.get("name", existing.name),
                data.get("short_desc", existing.short_desc),
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


def toggle_like(tool_id: str, user_email: str) -> bool:
    email = user_email.lower()
    now = _now()
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM likes WHERE tool_id = ? AND user_email = ?",
            (tool_id, email),
        ).fetchone()
        if exists:
            conn.execute(
                "DELETE FROM likes WHERE tool_id = ? AND user_email = ?",
                (tool_id, email),
            )
            return False
        conn.execute(
            "INSERT INTO likes (tool_id, user_email, created_at) VALUES (?, ?, ?)",
            (tool_id, email, now),
        )
        return True


def set_rating(tool_id: str, user_email: str, score: int, comment: str | None = None) -> None:
    email = user_email.lower()
    now = _now()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ratings (tool_id, user_email, score, comment, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tool_id, user_email) DO UPDATE SET
                score = excluded.score,
                comment = excluded.comment,
                updated_at = excluded.updated_at
            """,
            (tool_id, email, score, comment, now, now),
        )


def get_user_rating(tool_id: str, user_email: str) -> int | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT score FROM ratings WHERE tool_id = ? AND user_email = ?",
            (tool_id, user_email.lower()),
        ).fetchone()
    return row["score"] if row else None


def list_comments(tool_id: str) -> list[Comment]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM comments WHERE tool_id = ? ORDER BY created_at DESC",
            (tool_id,),
        ).fetchall()
    return [Comment.from_row(dict(r)) for r in rows]


def add_comment(tool_id: str, user_email: str, user_name: str, body: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO comments (tool_id, user_email, user_name, body, status, created_at)
            VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (tool_id, user_email.lower(), user_name, body, _now()),
        )


def update_comment_status(comment_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE comments SET status = ? WHERE id = ?", (status, comment_id))


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


def assign_cluster(tool_id: str, cluster_id: str | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE tools SET cluster_id = ?, updated_at = ? WHERE id = ?",
            (cluster_id, _now(), tool_id),
        )


def delete_tool(tool_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        return cur.rowcount > 0
