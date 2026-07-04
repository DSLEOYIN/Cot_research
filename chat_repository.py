from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(".system_generated/chat_sessions.db")
_UNSET = object()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _bool(value: int | bool | None) -> bool:
    return bool(value)


class ChatRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    is_pinned INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_mode TEXT,
                    last_web_search_enabled INTEGER DEFAULT 0,
                    pending_action_skill TEXT,
                    pending_action_message TEXT,
                    pending_action_status TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    selected_skill TEXT,
                    web_search_enabled INTEGER DEFAULT 0,
                    trace_open INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS message_steps (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    step_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT DEFAULT '',
                    mcp_name TEXT,
                    mcp_input TEXT,
                    mcp_output TEXT,
                    llm_output TEXT,
                    error TEXT,
                    duration_ms INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
                );
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
            if "pending_action_skill" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN pending_action_skill TEXT")
            if "pending_action_message" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN pending_action_message TEXT")
            if "pending_action_status" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN pending_action_status TEXT")

    def create_session(self, title: str | None = None) -> dict[str, Any]:
        created_at = _now()
        session_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, summary, is_pinned, created_at, updated_at)
                VALUES (?, ?, '', 0, ?, ?)
                """,
                (session_id, title or "新对话", created_at, created_at),
            )
        return self.get_session_summary(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*,
                       COALESCE(
                           NULLIF(s.summary, ''),
                           (
                               SELECT m.content FROM messages m
                               WHERE m.session_id = s.id AND m.role = 'user'
                               ORDER BY m.created_at DESC
                               LIMIT 1
                           ),
                           ''
                       ) AS display_summary
                FROM sessions s
                ORDER BY s.is_pinned DESC, s.updated_at DESC
                """
            ).fetchall()
        return [self._session_from_row(row) for row in rows]

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT s.*,
                       COALESCE(
                           NULLIF(s.summary, ''),
                           (
                               SELECT m.content FROM messages m
                               WHERE m.session_id = s.id AND m.role = 'user'
                               ORDER BY m.created_at DESC
                               LIMIT 1
                           ),
                           ''
                       ) AS display_summary
                FROM sessions s
                WHERE s.id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Session not found: {session_id}")
        return self._session_from_row(row)

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session_summary(session_id)
        with self._connect() as conn:
            message_rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            step_rows = conn.execute(
                """
                SELECT s.* FROM message_steps s
                JOIN messages m ON m.id = s.message_id
                WHERE m.session_id = ?
                ORDER BY s.step_index ASC, s.created_at ASC
                """,
                (session_id,),
            ).fetchall()

        steps_by_message: dict[str, list[dict[str, Any]]] = {}
        for row in step_rows:
            step = self._step_from_row(row)
            steps_by_message.setdefault(step["message_id"], []).append(step)

        session["messages"] = []
        for row in message_rows:
            message = self._message_from_row(row)
            message["steps"] = steps_by_message.get(message["id"], [])
            session["messages"].append(message)
        return session

    def update_session(
        self,
        session_id: str,
        *,
        title: str | None = None,
        summary: str | None = None,
        is_pinned: bool | None = None,
        last_mode: str | None = None,
        last_web_search_enabled: bool | None = None,
        pending_action_skill: str | None | object = _UNSET,
        pending_action_message: str | None | object = _UNSET,
        pending_action_status: str | None | object = _UNSET,
    ) -> dict[str, Any]:
        updates: list[str] = ["updated_at = ?"]
        values: list[Any] = [_now()]
        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if summary is not None:
            updates.append("summary = ?")
            values.append(summary)
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            values.append(int(is_pinned))
        if last_mode is not None:
            updates.append("last_mode = ?")
            values.append(last_mode)
        if last_web_search_enabled is not None:
            updates.append("last_web_search_enabled = ?")
            values.append(int(last_web_search_enabled))
        if pending_action_skill is not _UNSET:
            updates.append("pending_action_skill = ?")
            values.append(pending_action_skill)
        if pending_action_message is not _UNSET:
            updates.append("pending_action_message = ?")
            values.append(pending_action_message)
        if pending_action_status is not _UNSET:
            updates.append("pending_action_status = ?")
            values.append(pending_action_status)
        values.append(session_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?", values)
        return self.get_session_summary(session_id)

    def delete_session(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        selected_skill: str | None = None,
        web_search_enabled: bool = False,
        trace_open: bool = False,
    ) -> dict[str, Any]:
        created_at = _now()
        message_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO messages
                (id, session_id, role, content, selected_skill, web_search_enabled, trace_open, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    selected_skill,
                    int(web_search_enabled),
                    int(trace_open),
                    created_at,
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ?, last_mode = COALESCE(?, last_mode), last_web_search_enabled = ? WHERE id = ?",
                (created_at, selected_skill, int(web_search_enabled), session_id),
            )
        return self._message_from_row(
            {
                "id": message_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "selected_skill": selected_skill,
                "web_search_enabled": int(web_search_enabled),
                "trace_open": int(trace_open),
                "created_at": created_at,
            }
        )

    def update_message(self, message_id: str, *, content: str, selected_skill: str | None = None) -> dict[str, Any]:
        updates = ["content = ?"]
        values: list[Any] = [content]
        if selected_skill is not None:
            updates.append("selected_skill = ?")
            values.append(selected_skill)
        values.append(message_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE messages SET {', '.join(updates)} WHERE id = ?", values)
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return self._message_from_row(row)

    def add_step(
        self,
        message_id: str,
        *,
        step_index: int,
        step_type: str,
        title: str,
        status: str,
        summary: str = "",
        mcp_name: str | None = None,
        mcp_input: Any = None,
        mcp_output: Any = None,
        llm_output: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        created_at = _now()
        step_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO message_steps
                (id, message_id, step_index, step_type, title, status, summary, mcp_name,
                 mcp_input, mcp_output, llm_output, error, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    message_id,
                    step_index,
                    step_type,
                    title,
                    status,
                    summary,
                    mcp_name,
                    _json_dump(mcp_input),
                    _json_dump(mcp_output),
                    llm_output,
                    error,
                    duration_ms,
                    created_at,
                ),
            )
        return self._step_from_row(
            {
                "id": step_id,
                "message_id": message_id,
                "step_index": step_index,
                "step_type": step_type,
                "title": title,
                "status": status,
                "summary": summary,
                "mcp_name": mcp_name,
                "mcp_input": _json_dump(mcp_input),
                "mcp_output": _json_dump(mcp_output),
                "llm_output": llm_output,
                "error": error,
                "duration_ms": duration_ms,
                "created_at": created_at,
            }
        )

    def _session_from_row(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        keys = row.keys()
        return {
            "id": row["id"],
            "title": row["title"],
            "summary": row["display_summary"] if "display_summary" in keys else row["summary"] or "",
            "is_pinned": _bool(row["is_pinned"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_mode": row["last_mode"],
            "last_web_search_enabled": _bool(row["last_web_search_enabled"]),
            "pending_action_skill": row["pending_action_skill"] if "pending_action_skill" in keys else None,
            "pending_action_message": row["pending_action_message"] if "pending_action_message" in keys else None,
            "pending_action_status": row["pending_action_status"] if "pending_action_status" in keys else None,
        }

    def _message_from_row(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "selected_skill": row["selected_skill"],
            "web_search_enabled": _bool(row["web_search_enabled"]),
            "trace_open": _bool(row["trace_open"]),
            "created_at": row["created_at"],
        }

    def _step_from_row(self, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "message_id": row["message_id"],
            "step_index": row["step_index"],
            "step_type": row["step_type"],
            "title": row["title"],
            "status": row["status"],
            "summary": row["summary"] or "",
            "mcp_name": row["mcp_name"],
            "mcp_input": row["mcp_input"],
            "mcp_output": row["mcp_output"],
            "llm_output": row["llm_output"] or "",
            "error": row["error"],
            "duration_ms": row["duration_ms"],
            "created_at": row["created_at"],
        }
