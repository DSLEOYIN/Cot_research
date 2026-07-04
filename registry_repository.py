from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dump(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _json_load(value: str | None) -> list[str]:
    if not value:
        return []
    loaded = json.loads(value)
    return loaded if isinstance(loaded, list) else []


def _task_id(task_type: str) -> str:
    return f"{task_type}-task-{int(datetime.now(timezone.utc).timestamp() * 1000000)}"


class RegistryRepository:
    def __init__(
        self,
        db_path: str | Path,
        *,
        skills: list[dict[str, Any]],
        mcps: list[dict[str, Any]],
        governance_tasks: list[dict[str, Any]],
        release_activities: list[dict[str, Any]],
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed_if_empty(
            skills=skills,
            mcps=mcps,
            governance_tasks=governance_tasks,
            release_activities=release_activities,
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _column_names(self, conn: sqlite3.Connection, table_name: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    def _ensure_column(self, conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        if column_name not in self._column_names(conn, table_name):
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_skills (
                    name TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    applicable_organizations TEXT NOT NULL,
                    status TEXT NOT NULL,
                    release_status TEXT NOT NULL DEFAULT 'draft',
                    business_domain TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    requires_approval INTEGER NOT NULL,
                    writes_data INTEGER NOT NULL,
                    mcp_tools TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS admin_mcps (
                    name TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    read_write_risk TEXT NOT NULL,
                    health TEXT NOT NULL,
                    release_status TEXT NOT NULL,
                    referenced_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS governance_tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    blocked_by TEXT,
                    parent_task_id TEXT,
                    release_status TEXT NOT NULL,
                    auto_test_pass_rate TEXT NOT NULL,
                    failure_reason TEXT,
                    review_notes TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS release_activities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(conn, "admin_skills", "release_status", "TEXT NOT NULL DEFAULT 'draft'")

    def _seed_if_empty(
        self,
        *,
        skills: list[dict[str, Any]],
        mcps: list[dict[str, Any]],
        governance_tasks: list[dict[str, Any]],
        release_activities: list[dict[str, Any]],
    ) -> None:
        with self._connect() as conn:
            skill_count = conn.execute("SELECT COUNT(*) AS count FROM admin_skills").fetchone()
            if skill_count and skill_count["count"] == 0:
                now = _now()
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO admin_skills (
                        name, display_name, category, description, output_type,
                        applicable_organizations, status, release_status, business_domain, risk_level,
                        requires_approval, writes_data, mcp_tools, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["name"],
                            item.get("displayName") or item["name"],
                            item.get("category") or "未分类",
                            item.get("description") or "",
                            item.get("outputType") or "文本 / 报告",
                            _json_dump(item.get("applicableOrganizations")),
                            item.get("status") or "draft",
                            item.get("releaseStatus") or "published",
                            item.get("businessDomain") or "待补业务域",
                            item.get("riskLevel") or "中",
                            int(bool(item.get("requiresApproval"))),
                            int(bool(item.get("writesData"))),
                            _json_dump(item.get("mcpTools")),
                            now,
                            now,
                        )
                        for item in skills
                    ],
                )

            mcp_count = conn.execute("SELECT COUNT(*) AS count FROM admin_mcps").fetchone()
            if mcp_count and mcp_count["count"] == 0:
                now = _now()
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO admin_mcps (
                        name, display_name, category, description, read_write_risk,
                        health, release_status, referenced_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["name"],
                            item.get("displayName") or item["name"],
                            item.get("category") or "未分类",
                            item.get("description") or "",
                            item.get("readWriteRisk") or "待补风险说明",
                            item.get("health") or "unchecked",
                            item.get("releaseStatus") or "draft",
                            _json_dump(item.get("referencedBy")),
                            now,
                            now,
                        )
                        for item in mcps
                    ],
                )

            task_count = conn.execute("SELECT COUNT(*) AS count FROM governance_tasks").fetchone()
            if task_count and task_count["count"] == 0:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO governance_tasks (
                        id, title, type, entity_name, priority, stage, owner, updated_at,
                        summary, blocked_by, parent_task_id, release_status, auto_test_pass_rate,
                        failure_reason, review_notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["id"],
                            item["title"],
                            item["type"],
                            item["entityName"],
                            item["priority"],
                            item["stage"],
                            item["owner"],
                            item["updatedAt"],
                            item["summary"],
                            item.get("blockedBy"),
                            item.get("parentTaskId"),
                            item["releaseStatus"],
                            item["autoTestPassRate"],
                            item.get("failureReason"),
                            item.get("reviewNotes"),
                            item.get("createdAt") or _now(),
                        )
                        for item in governance_tasks
                    ],
                )

            activity_count = conn.execute("SELECT COUNT(*) AS count FROM release_activities").fetchone()
            if activity_count and activity_count["count"] == 0:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO release_activities (
                        id, entity_type, entity_name, action, operator, detail, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item["id"],
                            item["entityType"],
                            item["entityName"],
                            item["action"],
                            item["operator"],
                            item["detail"],
                            item["createdAt"],
                        )
                        for item in release_activities
                    ],
                )

    def _skill_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "displayName": row["display_name"],
            "category": row["category"],
            "description": row["description"],
            "outputType": row["output_type"],
            "applicableOrganizations": _json_load(row["applicable_organizations"]),
            "status": row["status"],
            "releaseStatus": row["release_status"],
            "businessDomain": row["business_domain"],
            "riskLevel": row["risk_level"],
            "requiresApproval": bool(row["requires_approval"]),
            "writesData": bool(row["writes_data"]),
            "mcpTools": _json_load(row["mcp_tools"]),
        }

    def _mcp_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "name": row["name"],
            "displayName": row["display_name"],
            "category": row["category"],
            "description": row["description"],
            "readWriteRisk": row["read_write_risk"],
            "health": row["health"],
            "status": row["release_status"],
            "releaseStatus": row["release_status"],
            "referencedBy": _json_load(row["referenced_by"]),
        }

    def _task_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "entityName": row["entity_name"],
            "priority": row["priority"],
            "stage": row["stage"],
            "owner": row["owner"],
            "updatedAt": row["updated_at"],
            "summary": row["summary"],
            "blockedBy": row["blocked_by"],
            "parentTaskId": row["parent_task_id"],
            "releaseStatus": row["release_status"],
            "autoTestPassRate": row["auto_test_pass_rate"],
            "failureReason": row["failure_reason"],
            "reviewNotes": row["review_notes"],
        }

    def _activity_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "entityType": row["entity_type"],
            "entityName": row["entity_name"],
            "action": row["action"],
            "operator": row["operator"],
            "detail": row["detail"],
            "createdAt": row["created_at"],
        }

    def list_skills(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM admin_skills ORDER BY created_at ASC, name ASC").fetchall()
        return [self._skill_from_row(row) for row in rows]

    def get_skill(self, skill_name: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM admin_skills WHERE name = ?", (skill_name,)).fetchone()
        return self._skill_from_row(row) if row else None

    def create_skill(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        skill = {
            "name": payload["name"],
            "displayName": payload.get("displayName") or payload["name"],
            "category": payload.get("category") or "未分类",
            "description": payload.get("description") or "",
            "outputType": payload.get("outputType") or "文本 / 报告",
            "applicableOrganizations": payload.get("applicableOrganizations") or [],
            "status": payload.get("status") or "draft_created",
            "releaseStatus": payload.get("releaseStatus") or "draft",
            "businessDomain": payload.get("businessDomain") or "待补业务域",
            "riskLevel": payload.get("riskLevel") or "中",
            "requiresApproval": bool(payload.get("requiresApproval")),
            "writesData": bool(payload.get("writesData")),
            "mcpTools": payload.get("mcpTools") or [],
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_skills (
                    name, display_name, category, description, output_type,
                    applicable_organizations, status, release_status, business_domain, risk_level,
                    requires_approval, writes_data, mcp_tools, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    skill["name"],
                    skill["displayName"],
                    skill["category"],
                    skill["description"],
                    skill["outputType"],
                    _json_dump(skill["applicableOrganizations"]),
                    skill["status"],
                    skill["releaseStatus"],
                    skill["businessDomain"],
                    skill["riskLevel"],
                    int(skill["requiresApproval"]),
                    int(skill["writesData"]),
                    _json_dump(skill["mcpTools"]),
                    now,
                    now,
                ),
            )
        created = self.get_skill(skill["name"])
        if created is None:
            raise RuntimeError(f"Failed to create skill: {skill['name']}")
        return created

    def update_skill(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_skill(skill_name)
        if current is None:
            return None
        next_value = {**current, **{key: value for key, value in payload.items() if key in current}}
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_skills
                SET display_name = ?, category = ?, description = ?, output_type = ?,
                    applicable_organizations = ?, status = ?, release_status = ?, business_domain = ?,
                    risk_level = ?, requires_approval = ?, writes_data = ?, mcp_tools = ?, updated_at = ?
                WHERE name = ?
                """,
                (
                    next_value["displayName"],
                    next_value["category"],
                    next_value["description"],
                    next_value["outputType"],
                    _json_dump(next_value["applicableOrganizations"]),
                    next_value["status"],
                    next_value["releaseStatus"],
                    next_value["businessDomain"],
                    next_value["riskLevel"],
                    int(next_value["requiresApproval"]),
                    int(next_value["writesData"]),
                    _json_dump(next_value["mcpTools"]),
                    _now(),
                    skill_name,
                ),
            )
        return self.get_skill(skill_name)

    def list_mcps(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM admin_mcps ORDER BY created_at ASC, name ASC").fetchall()
        return [self._mcp_from_row(row) for row in rows]

    def get_mcp(self, mcp_name: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM admin_mcps WHERE name = ?", (mcp_name,)).fetchone()
        return self._mcp_from_row(row) if row else None

    def create_mcp(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        mcp = {
            "name": payload["name"],
            "displayName": payload.get("displayName") or payload["name"],
            "category": payload.get("category") or "未分类",
            "description": payload.get("description") or "",
            "readWriteRisk": payload.get("readWriteRisk") or "待补风险说明",
            "health": payload.get("health") or "unchecked",
            "releaseStatus": payload.get("releaseStatus") or "draft",
            "referencedBy": payload.get("referencedBy") or [],
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admin_mcps (
                    name, display_name, category, description, read_write_risk,
                    health, release_status, referenced_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mcp["name"],
                    mcp["displayName"],
                    mcp["category"],
                    mcp["description"],
                    mcp["readWriteRisk"],
                    mcp["health"],
                    mcp["releaseStatus"],
                    _json_dump(mcp["referencedBy"]),
                    now,
                    now,
                ),
            )
        created = self.get_mcp(mcp["name"])
        if created is None:
            raise RuntimeError(f"Failed to create mcp: {mcp['name']}")
        created["status"] = payload.get("status") or "draft_created"
        return created

    def update_mcp(self, mcp_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_mcp(mcp_name)
        if current is None:
            return None
        next_value = {**current, **{key: value for key, value in payload.items() if key in current}}
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE admin_mcps
                SET display_name = ?, category = ?, description = ?, read_write_risk = ?,
                    health = ?, release_status = ?, referenced_by = ?, updated_at = ?
                WHERE name = ?
                """,
                (
                    next_value["displayName"],
                    next_value["category"],
                    next_value["description"],
                    next_value["readWriteRisk"],
                    next_value["health"],
                    next_value["releaseStatus"],
                    _json_dump(next_value["referencedBy"]),
                    _now(),
                    mcp_name,
                ),
            )
        return self.get_mcp(mcp_name)

    def list_governance_tasks(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM governance_tasks ORDER BY created_at DESC, id DESC").fetchall()
        return [self._task_from_row(row) for row in rows]

    def get_governance_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM governance_tasks WHERE id = ?", (task_id,)).fetchone()
        return self._task_from_row(row) if row else None

    def list_release_activities(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM release_activities ORDER BY created_at DESC, id DESC").fetchall()
        return [self._activity_from_row(row) for row in rows]

    def _create_release_activity(
        self,
        conn: sqlite3.Connection,
        *,
        entity_type: str,
        entity_name: str,
        action: str,
        operator: str,
        detail: str,
    ) -> dict[str, Any]:
        now = _now()
        activity = {
            "id": f"release-{int(datetime.now(timezone.utc).timestamp() * 1000000)}",
            "entityType": entity_type,
            "entityName": entity_name,
            "action": action,
            "operator": operator,
            "detail": detail,
            "createdAt": now,
        }
        conn.execute(
            """
            INSERT INTO release_activities (id, entity_type, entity_name, action, operator, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity["id"],
                activity["entityType"],
                activity["entityName"],
                activity["action"],
                activity["operator"],
                activity["detail"],
                activity["createdAt"],
            ),
        )
        return activity

    def _upsert_governance_task(self, conn: sqlite3.Connection, task: dict[str, Any]) -> dict[str, Any]:
        created_at = task.get("createdAt") or _now()
        conn.execute(
            """
            INSERT INTO governance_tasks (
                id, title, type, entity_name, priority, stage, owner, updated_at,
                summary, blocked_by, parent_task_id, release_status, auto_test_pass_rate,
                failure_reason, review_notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                type = excluded.type,
                entity_name = excluded.entity_name,
                priority = excluded.priority,
                stage = excluded.stage,
                owner = excluded.owner,
                updated_at = excluded.updated_at,
                summary = excluded.summary,
                blocked_by = excluded.blocked_by,
                parent_task_id = excluded.parent_task_id,
                release_status = excluded.release_status,
                auto_test_pass_rate = excluded.auto_test_pass_rate,
                failure_reason = excluded.failure_reason,
                review_notes = excluded.review_notes
            """,
            (
                task["id"],
                task["title"],
                task["type"],
                task["entityName"],
                task["priority"],
                task["stage"],
                task["owner"],
                task["updatedAt"],
                task["summary"],
                task.get("blockedBy"),
                task.get("parentTaskId"),
                task["releaseStatus"],
                task["autoTestPassRate"],
                task.get("failureReason"),
                task.get("reviewNotes"),
                created_at,
            ),
        )
        return {**task, "createdAt": created_at}

    def mark_mcp_health_check(self, mcp_name: str, *, operator: str, health: str = "healthy") -> dict[str, Any] | None:
        with self._connect() as conn:
            updated = self.update_mcp(mcp_name, {"health": health})
            if updated is None:
                return None
            self._create_release_activity(
                conn,
                entity_type="mcp",
                entity_name=updated["displayName"],
                action="health_check_passed",
                operator=operator,
                detail=f"MCP {updated['displayName']} 已完成健康检查，连接与 Schema 校验通过。",
            )
        return self.get_mcp(mcp_name)

    def submit_skill_governance(self, skill_name: str, *, operator: str) -> dict[str, Any] | None:
        skill = self.get_skill(skill_name)
        if skill is None:
            return None
        next_skill = self.update_skill(skill_name, {"releaseStatus": "ready_for_review"})
        if next_skill is None:
            return None
        task = {
            "id": _task_id("skill"),
            "title": f"治理复核 {next_skill['displayName']} Skill",
            "type": "skill",
            "entityName": next_skill["name"],
            "priority": "P1",
            "stage": "ready_for_review",
            "owner": operator,
            "updatedAt": "刚刚",
            "summary": f"Skill {next_skill['displayName']} 已提交治理复核，等待人工确认。",
            "releaseStatus": "ready_for_review",
            "autoTestPassRate": "待补",
            "reviewNotes": "请重点确认组织适用范围、示例输出与风险标签。",
        }
        with self._connect() as conn:
            saved_task = self._upsert_governance_task(conn, task)
            activity = self._create_release_activity(
                conn,
                entity_type="skill",
                entity_name=next_skill["displayName"],
                action="submitted_for_review",
                operator=operator,
                detail=f"Skill {next_skill['displayName']} 已提交治理复核，等待人工确认后进入发布流程。",
            )
        return {"task": saved_task, "entity": next_skill, "activity": activity}

    def approve_governance_task(self, task_id: str, *, operator: str) -> dict[str, Any] | None:
        task = self.get_governance_task(task_id)
        if task is None:
            return None
        if task["type"] == "skill":
            entity = self.update_skill(task["entityName"], {"releaseStatus": "ready_to_publish"})
            if entity is None:
                return None
            next_task = {
                **task,
                "stage": "ready_to_publish",
                "releaseStatus": "ready_to_publish",
                "updatedAt": "刚刚",
                "summary": f"Skill {entity['displayName']} 已完成人工复核，等待发布到集团能力目录。",
                "reviewNotes": "治理审核已通过，请确认最终发布窗口与回滚预案。",
                "owner": operator,
            }
            detail = f"Skill {entity['displayName']} 已完成治理审核，进入待发布队列。"
            entity_name = entity["displayName"]
        else:
            entity = self.update_mcp(task["entityName"], {"releaseStatus": "ready_to_publish"})
            if entity is None:
                return None
            next_task = {
                **task,
                "stage": "ready_to_publish",
                "releaseStatus": "ready_to_publish",
                "updatedAt": "刚刚",
                "summary": f"MCP {entity['displayName']} 已完成人工复核，等待发布到工具目录。",
                "reviewNotes": "治理审核已通过，请确认兼容性说明与发布通知范围。",
                "blockedBy": None,
                "failureReason": None,
                "owner": operator,
            }
            detail = f"MCP {entity['displayName']} 已完成治理审核，进入待发布队列。"
            entity_name = entity["displayName"]
        with self._connect() as conn:
            saved_task = self._upsert_governance_task(conn, next_task)
            activity = self._create_release_activity(
                conn,
                entity_type=task["type"],
                entity_name=entity_name,
                action="review_approved",
                operator=operator,
                detail=detail,
            )
        return {"task": saved_task, "entity": entity, "activity": activity}

    def publish_governance_task(self, task_id: str, *, operator: str) -> dict[str, Any] | None:
        task = self.get_governance_task(task_id)
        if task is None:
            return None
        unlocked_tasks: list[dict[str, Any]] = []
        if task["type"] == "skill":
            entity = self.update_skill(task["entityName"], {"releaseStatus": "published"})
            if entity is None:
                return None
            next_task = {
                **task,
                "stage": "published",
                "releaseStatus": "published",
                "updatedAt": "刚刚",
                "blockedBy": None,
                "failureReason": None,
                "owner": operator,
            }
            detail = f"Skill {entity['displayName']} 已发布到集团能力目录，并保留回滚预案。"
            entity_name = entity["displayName"]
        else:
            entity = self.update_mcp(task["entityName"], {"releaseStatus": "published"})
            if entity is None:
                return None
            next_task = {
                **task,
                "stage": "published",
                "releaseStatus": "published",
                "updatedAt": "刚刚",
                "blockedBy": None,
                "failureReason": None,
                "owner": operator,
            }
            detail = f"MCP {entity['displayName']} 已发布到工具目录，并同步更新引用影响面。"
            entity_name = entity["displayName"]
        with self._connect() as conn:
            saved_task = self._upsert_governance_task(conn, next_task)
            activity = self._create_release_activity(
                conn,
                entity_type=task["type"],
                entity_name=entity_name,
                action="published_to_catalog",
                operator=operator,
                detail=detail,
            )
            if task["type"] == "mcp":
                rows = conn.execute(
                    """
                    SELECT * FROM governance_tasks
                    WHERE release_status = 'blocked_by_dependency'
                    """
                ).fetchall()
                for row in rows:
                    blocked_task = self._task_from_row(row)
                    blocked_reason = blocked_task.get("blockedBy") or ""
                    matches_dependency = any(
                        keyword and keyword in blocked_reason
                        for keyword in [entity["name"], entity["displayName"], task["entityName"], task["title"]]
                    )
                    if not matches_dependency:
                        continue
                    unlocked_task = {
                        **blocked_task,
                        "stage": "testing",
                        "releaseStatus": "testing",
                        "blockedBy": None,
                        "failureReason": None,
                        "updatedAt": "刚刚",
                        "summary": f"{blocked_task['title']} 的依赖已发布，自动恢复联调测试。",
                        "reviewNotes": "依赖发布后已自动解锁，请继续执行联调与回归验证。",
                    }
                    unlocked_tasks.append(self._upsert_governance_task(conn, unlocked_task))
                    self._create_release_activity(
                        conn,
                        entity_type=blocked_task["type"],
                        entity_name=blocked_task["title"],
                        action="dependency_unblocked",
                        operator=operator,
                        detail=f"{blocked_task['title']} 因依赖 {entity['displayName']} 发布成功，已自动从依赖阻塞恢复到联调测试。",
                    )
        return {"task": saved_task, "entity": entity, "activity": activity, "unlockedTasks": unlocked_tasks}
