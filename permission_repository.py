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


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


class PermissionRepository:
    def __init__(
        self,
        db_path: str | Path,
        *,
        organizations: list[dict[str, Any]],
        roles: list[dict[str, Any]],
        accounts: list[dict[str, Any]],
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed_if_empty(organizations=organizations, roles=roles, accounts=accounts)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    organization_name TEXT NOT NULL,
                    role_name TEXT NOT NULL,
                    open_skills TEXT NOT NULL,
                    data_domains TEXT NOT NULL,
                    action_permissions TEXT NOT NULL,
                    approval_mode TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    role_name TEXT NOT NULL,
                    open_skills TEXT NOT NULL,
                    data_domains TEXT NOT NULL,
                    action_permissions TEXT NOT NULL,
                    can_access_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    allowed_skills TEXT NOT NULL,
                    denied_skills TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(organization_id) REFERENCES organizations(id)
                );

                CREATE TABLE IF NOT EXISTS account_role_bindings (
                    account_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (account_id, role_id),
                    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                    FOREIGN KEY(role_id) REFERENCES roles(id)
                );

                CREATE TABLE IF NOT EXISTS permission_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    change_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _seed_if_empty(
        self,
        *,
        organizations: list[dict[str, Any]],
        roles: list[dict[str, Any]],
        accounts: list[dict[str, Any]],
    ) -> None:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM organizations").fetchone()
            if row["count"]:
                return
            now = _now()
            conn.executemany(
                """
                INSERT INTO organizations (
                    id, organization_name, role_name, open_skills, data_domains,
                    action_permissions, approval_mode, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["id"],
                        item["organizationName"],
                        item["roleName"],
                        _json_dump(item["openSkills"]),
                        _json_dump(item["dataDomains"]),
                        _json_dump(item["actionPermissions"]),
                        item["approvalMode"],
                        now,
                        now,
                    )
                    for item in organizations
                ],
            )
            conn.executemany(
                """
                INSERT INTO roles (
                    id, role_name, open_skills, data_domains, action_permissions,
                    can_access_admin, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["id"],
                        item["roleName"],
                        _json_dump(item["openSkills"]),
                        _json_dump(item["dataDomains"]),
                        _json_dump(item["actionPermissions"]),
                        int(item["canAccessAdmin"]),
                        now,
                        now,
                    )
                    for item in roles
                ],
            )
            conn.executemany(
                """
                INSERT INTO accounts (
                    id, username, password, display_name, organization_id,
                    allowed_skills, denied_skills, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["id"],
                        item["username"],
                        item["password"],
                        item["displayName"],
                        item["organizationId"],
                        _json_dump(item.get("allowedSkills")),
                        _json_dump(item.get("deniedSkills")),
                        now,
                        now,
                    )
                    for item in accounts
                ],
            )
            conn.executemany(
                """
                INSERT INTO account_role_bindings (account_id, role_id, created_at)
                VALUES (?, ?, ?)
                """,
                [
                    (item["id"], role_id, now)
                    for item in accounts
                    for role_id in item.get("roleIds", [])
                ],
            )

    def _organization_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "organizationName": row["organization_name"],
            "roleName": row["role_name"],
            "openSkills": _json_load(row["open_skills"]),
            "dataDomains": _json_load(row["data_domains"]),
            "actionPermissions": _json_load(row["action_permissions"]),
            "approvalMode": row["approval_mode"],
        }

    def _role_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "roleName": row["role_name"],
            "openSkills": _json_load(row["open_skills"]),
            "dataDomains": _json_load(row["data_domains"]),
            "actionPermissions": _json_load(row["action_permissions"]),
            "canAccessAdmin": bool(row["can_access_admin"]),
        }

    def _account_from_row(self, row: sqlite3.Row, role_ids: list[str]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "username": row["username"],
            "password": row["password"],
            "displayName": row["display_name"],
            "organizationId": row["organization_id"],
            "roleIds": role_ids,
            "allowedSkills": _json_load(row["allowed_skills"]),
            "deniedSkills": _json_load(row["denied_skills"]),
        }

    def _audit(self, entity_type: str, entity_id: str, entity_name: str, change_summary: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO permission_audit_logs (entity_type, entity_id, entity_name, change_summary, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entity_type, entity_id, entity_name, change_summary, _now()),
            )

    def list_permission_audit_logs(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM permission_audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "entityType": row["entity_type"],
                "entityId": row["entity_id"],
                "entityName": row["entity_name"],
                "changeSummary": row["change_summary"],
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    def list_organizations(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM organizations ORDER BY created_at ASC, organization_name ASC").fetchall()
        return [self._organization_from_row(row) for row in rows]

    def get_organization(self, organization_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM organizations WHERE id = ?", (organization_id,)).fetchone()
        return self._organization_from_row(row) if row else None

    def update_organization(self, organization_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_organization(organization_id)
        if current is None:
            return None
        next_value = {
            **current,
            **{key: value for key, value in payload.items() if key in current},
        }
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE organizations
                SET organization_name = ?, role_name = ?, open_skills = ?, data_domains = ?,
                    action_permissions = ?, approval_mode = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_value["organizationName"],
                    next_value["roleName"],
                    _json_dump(next_value["openSkills"]),
                    _json_dump(next_value["dataDomains"]),
                    _json_dump(next_value["actionPermissions"]),
                    next_value["approvalMode"],
                    _now(),
                    organization_id,
                ),
            )
        if payload:
            self._audit("organization", organization_id, next_value["organizationName"], f"更新组织策略：{', '.join(payload.keys())}")
        return self.get_organization(organization_id)

    def list_roles(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM roles ORDER BY created_at ASC, role_name ASC").fetchall()
        return [self._role_from_row(row) for row in rows]

    def get_role(self, role_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
        return self._role_from_row(row) if row else None

    def update_role(self, role_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_role(role_id)
        if current is None:
            return None
        next_value = {
            **current,
            **{key: value for key, value in payload.items() if key in current},
        }
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE roles
                SET role_name = ?, open_skills = ?, data_domains = ?, action_permissions = ?,
                    can_access_admin = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_value["roleName"],
                    _json_dump(next_value["openSkills"]),
                    _json_dump(next_value["dataDomains"]),
                    _json_dump(next_value["actionPermissions"]),
                    int(next_value["canAccessAdmin"]),
                    _now(),
                    role_id,
                ),
            )
        if payload:
            self._audit("role", role_id, next_value["roleName"], f"更新角色模板：{', '.join(payload.keys())}")
        return self.get_role(role_id)

    def _role_ids_for_account(self, conn: sqlite3.Connection, account_id: str) -> list[str]:
        rows = conn.execute(
            "SELECT role_id FROM account_role_bindings WHERE account_id = ? ORDER BY role_id ASC",
            (account_id,),
        ).fetchall()
        return [row["role_id"] for row in rows]

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
            if row is None:
                return None
            role_ids = self._role_ids_for_account(conn, account_id)
        return self._account_from_row(row, role_ids)

    def get_account_by_username(self, username: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM accounts WHERE username = ?", (username,)).fetchone()
            if row is None:
                return None
            role_ids = self._role_ids_for_account(conn, row["id"])
        return self._account_from_row(row, role_ids)

    def list_accounts(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM accounts ORDER BY created_at ASC, username ASC").fetchall()
            role_map = {
                row["id"]: self._role_ids_for_account(conn, row["id"])
                for row in rows
            }
        return [self._account_from_row(row, role_map[row["id"]]) for row in rows]

    def create_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        account = {
            "id": payload.get("id") or f"u-{payload['username']}",
            "username": payload["username"],
            "password": payload.get("password") or "123456",
            "displayName": payload.get("displayName") or payload["username"],
            "organizationId": payload.get("organizationId") or "gac-headquarters",
            "roleIds": payload.get("roleIds") or ["sales-analyst"],
            "allowedSkills": payload.get("allowedSkills") or [],
            "deniedSkills": payload.get("deniedSkills") or [],
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO accounts (
                    id, username, password, display_name, organization_id,
                    allowed_skills, denied_skills, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account["id"],
                    account["username"],
                    account["password"],
                    account["displayName"],
                    account["organizationId"],
                    _json_dump(account["allowedSkills"]),
                    _json_dump(account["deniedSkills"]),
                    now,
                    now,
                ),
            )
            conn.executemany(
                """
                INSERT INTO account_role_bindings (account_id, role_id, created_at)
                VALUES (?, ?, ?)
                """,
                [(account["id"], role_id, now) for role_id in account["roleIds"]],
            )
        created = self.get_account(account["id"])
        if created is None:
            raise RuntimeError(f"Failed to create account: {account['id']}")
        self._audit("account", account["id"], account["displayName"], "创建账号并写入初始权限")
        return created

    def update_account(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        current = self.get_account(account_id)
        if current is None:
            return None
        next_value = {
            **current,
            **{key: value for key, value in payload.items() if key in current},
        }
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE accounts
                SET username = ?, password = ?, display_name = ?, organization_id = ?,
                    allowed_skills = ?, denied_skills = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_value["username"],
                    next_value["password"],
                    next_value["displayName"],
                    next_value["organizationId"],
                    _json_dump(next_value["allowedSkills"]),
                    _json_dump(next_value["deniedSkills"]),
                    _now(),
                    account_id,
                ),
            )
            if "roleIds" in payload:
                conn.execute("DELETE FROM account_role_bindings WHERE account_id = ?", (account_id,))
                conn.executemany(
                    """
                    INSERT INTO account_role_bindings (account_id, role_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    [(account_id, role_id, _now()) for role_id in next_value["roleIds"]],
                )
        if payload:
            self._audit("account", account_id, next_value["displayName"], f"更新账号权限：{', '.join(payload.keys())}")
        return self.get_account(account_id)

    def account_view(self, account_id: str) -> dict[str, Any] | None:
        account = self.get_account(account_id)
        if account is None:
            return None
        organization = self.get_organization(account["organizationId"])
        if organization is None:
            return None
        roles = [role for role_id in account["roleIds"] if (role := self.get_role(role_id))]
        role_skills = _merge_unique(*[role["openSkills"] for role in roles])
        role_domains = _merge_unique(*[role["dataDomains"] for role in roles])
        role_actions = _merge_unique(*[role["actionPermissions"] for role in roles])
        baseline_skills = _merge_unique(organization["openSkills"], role_skills)
        effective_skills = [
            skill
            for skill in _merge_unique(baseline_skills, account["allowedSkills"])
            if skill not in account["deniedSkills"]
        ]
        return {
            "id": account["id"],
            "username": account["username"],
            "displayName": account["displayName"],
            "organizationId": account["organizationId"],
            "organizationName": organization["organizationName"],
            "roleIds": account["roleIds"],
            "roleNames": [role["roleName"] for role in roles],
            "allowedSkills": account["allowedSkills"],
            "deniedSkills": account["deniedSkills"],
            "effectiveSkills": effective_skills,
            "effectiveDataDomains": _merge_unique(organization["dataDomains"], role_domains),
            "effectiveActionPermissions": _merge_unique(organization["actionPermissions"], role_actions),
            "canAccessAdmin": any(role["canAccessAdmin"] for role in roles),
            "permissionSources": {
                "organization": {
                    "organizationName": organization["organizationName"],
                    "openSkills": organization["openSkills"],
                    "dataDomains": organization["dataDomains"],
                    "actionPermissions": organization["actionPermissions"],
                },
                "roles": [
                    {
                        "roleName": role["roleName"],
                        "openSkills": role["openSkills"],
                        "dataDomains": role["dataDomains"],
                        "actionPermissions": role["actionPermissions"],
                    }
                    for role in roles
                ],
                "accountOverride": {
                    "allowedSkills": account["allowedSkills"],
                    "deniedSkills": account["deniedSkills"],
                },
            },
        }

    def list_account_views(self) -> list[dict[str, Any]]:
        return [view for account in self.list_accounts() if (view := self.account_view(account["id"]))]
