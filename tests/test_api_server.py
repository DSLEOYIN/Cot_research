from fastapi.testclient import TestClient

import api_server
from api_server import create_app


def test_session_api_creates_and_lists_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    created = client.post("/api/sessions", json={"title": "测试会话"}).json()
    listed = client.get("/api/sessions").json()

    assert created["title"] == "测试会话"
    assert listed[0]["id"] == created["id"]


def test_platform_prototype_api_exposes_capabilities_permissions_and_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    openapi = client.get("/openapi.json")
    capabilities = client.get("/api/capabilities")
    data_query = client.get("/api/capabilities/data_query")
    my_capabilities = client.get("/api/users/me/capabilities")
    organizations = client.get("/api/organizations")
    org_permissions = client.get("/api/organizations/gac-international/permissions")
    skills = client.get("/api/admin/skills")
    skill = client.get("/api/admin/skills/data_query")
    mcps = client.get("/api/admin/mcps")
    mcp = client.get("/api/admin/mcps/sql_executor")
    assets = client.get("/api/admin/assets")
    governance_tasks = client.get("/api/admin/governance/tasks")
    release_activities = client.get("/api/admin/governance/activities")
    metrics = client.get("/api/admin/metrics/overview")
    skill_metrics = client.get("/api/admin/metrics/skills")
    organization_metrics = client.get("/api/admin/metrics/organizations")
    alerts = client.get("/api/admin/alerts")
    action_governance = client.get("/api/admin/action-governance")

    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "广汽集团 AI 一体化平台 API"
    assert capabilities.status_code == 200
    assert data_query.status_code == 200
    assert my_capabilities.status_code == 200
    assert organizations.status_code == 200
    assert org_permissions.status_code == 200
    assert skills.status_code == 200
    assert skill.status_code == 200
    assert mcps.status_code == 200
    assert mcp.status_code == 200
    assert assets.status_code == 200
    assert governance_tasks.status_code == 200
    assert release_activities.status_code == 200
    assert metrics.status_code == 200
    assert skill_metrics.status_code == 200
    assert organization_metrics.status_code == 200
    assert alerts.status_code == 200
    assert action_governance.status_code == 200
    assert data_query.json()["displayName"] == "数据查询与分析"
    assert org_permissions.json()["organizationName"] == "广汽国际"
    assert assets.json()[0]["asset_id"]
    assert assets.json()[0]["asset_type"] in {"skill", "mcp"}
    assert assets.json()[0]["current_stage"]
    assert assets.json()[0]["risk_level"]
    assert assets.json()[0]["owner"]
    assert assets.json()[0]["dependency_status"]
    assert assets.json()[0]["action_url"]
    assert governance_tasks.json()[0]["title"]
    assert release_activities.json()[0]["action"]
    assert "monthlyActiveUsers" in metrics.json()
    assert "failureReasons" in skill_metrics.json()
    assert "organizationItems" in organization_metrics.json()
    assert alerts.json()[0]["message"]
    assert action_governance.json()[0]["approvalStatus"]


def test_platform_prototype_api_exposes_unified_assets_with_stable_fields_and_persisted_updates(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "registry.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    created_skill = first_client.post(
        "/api/admin/skills",
        json={
            "name": "fleet_alert_watch",
            "displayName": "车队预警追踪",
            "category": "运营分析",
            "description": "监控车队异常预警并输出治理建议。",
            "outputType": "分析报告",
            "applicableOrganizations": ["广汽国际"],
            "status": "draft",
            "businessDomain": "运营分析",
            "riskLevel": "中",
            "requiresApproval": True,
            "writesData": False,
            "mcpTools": ["knowledge_retrieval"],
        },
    )
    submitted = first_client.post("/api/admin/governance/skills/fleet_alert_watch/submit")
    assets = first_client.get("/api/admin/assets")

    assert created_skill.status_code == 200
    assert submitted.status_code == 200
    assert assets.status_code == 200
    created_asset = next(item for item in assets.json() if item["asset_id"] == "skill:fleet_alert_watch")
    assert created_asset["asset_type"] == "skill"
    assert created_asset["current_stage"] == "review"
    assert created_asset["risk_level"] == "中"
    assert created_asset["dependency_status"] == "1 个 MCP 依赖"
    assert created_asset["action_url"] == "/admin/skills/fleet_alert_watch"

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    restarted_assets = restarted_client.get("/api/admin/assets")

    assert restarted_assets.status_code == 200
    restarted_asset = next(item for item in restarted_assets.json() if item["asset_id"] == "skill:fleet_alert_watch")
    assert restarted_asset["current_stage"] == "review"
    assert restarted_asset["owner"]


def test_unified_assets_are_sorted_by_stage_priority_then_type_and_name(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    assets = client.get("/api/admin/assets")

    assert assets.status_code == 200
    payload = assets.json()
    assert [item["asset_id"] for item in payload[:4]] == [
        "mcp:inventory_snapshot_mcp",
        "skill:global_policy_watch",
        "mcp:sql_executor",
        "mcp:knowledge_retrieval",
    ]
    assert payload[0]["current_stage"] == "review"
    assert payload[1]["current_stage"] == "publish"
    assert payload[2]["asset_type"] == "mcp"
    assert payload[2]["current_stage"] == "published"
    assert payload[3]["current_stage"] == "published"


def test_admin_unified_tasks_endpoint_exposes_asset_aligned_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    tasks = client.get("/api/admin/tasks")

    assert tasks.status_code == 200
    payload = tasks.json()
    inventory_task = next(item for item in payload if item["task_id"] == "mcp-task-014")
    assert inventory_task["task_type"] == "mcp"
    assert inventory_task["asset_id"] == "mcp:inventory_snapshot_mcp"
    assert inventory_task["asset_type"] == "mcp"
    assert inventory_task["current_stage"] == "review"
    assert inventory_task["action_url"] == "/admin/mcps/inventory_snapshot_mcp"
    assert inventory_task["parent_task_id"] == "skill-task-001"
    assert inventory_task["owner"] == "运维-王敏"


def test_admin_asset_detail_endpoint_returns_asset_detail_tasks_and_activities(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    skill_detail = client.get("/api/admin/assets/skill:global_policy_watch")
    mcp_detail = client.get("/api/admin/assets/mcp:inventory_snapshot_mcp")
    missing = client.get("/api/admin/assets/skill:not_exists")

    assert skill_detail.status_code == 200
    assert skill_detail.json()["asset"]["asset_id"] == "skill:global_policy_watch"
    assert skill_detail.json()["asset"]["current_stage"] == "publish"
    assert skill_detail.json()["detail"]["displayName"] == "海外政策追踪"
    assert skill_detail.json()["detail"]["asset_type"] == "skill"
    assert skill_detail.json()["tasks"][0]["asset_id"] == "skill:global_policy_watch"
    assert skill_detail.json()["activities"][0]["entityType"] == "skill"

    assert mcp_detail.status_code == 200
    assert mcp_detail.json()["asset"]["asset_id"] == "mcp:inventory_snapshot_mcp"
    assert mcp_detail.json()["detail"]["displayName"] == "库存快照连接器"
    assert mcp_detail.json()["detail"]["asset_type"] == "mcp"
    assert mcp_detail.json()["tasks"][0]["task_id"] == "mcp-task-014"

    assert missing.status_code == 404


def test_admin_asset_action_endpoints_support_test_submit_and_publish(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    skill_test = client.post("/api/admin/assets/skill:data_query/test", json={"query": "本月销量"})
    mcp_test = client.post("/api/admin/assets/mcp:inventory_snapshot_mcp/test")
    submitted = client.post("/api/admin/assets/skill:data_query/submit")
    published = client.post("/api/admin/assets/mcp:inventory_snapshot_mcp/publish")
    missing_action = client.post("/api/admin/assets/skill:not_exists/test")

    assert skill_test.status_code == 200
    assert skill_test.json()["asset_id"] == "skill:data_query"
    assert skill_test.json()["action"] == "test"
    assert skill_test.json()["status"] == "passed"

    assert mcp_test.status_code == 200
    assert mcp_test.json()["asset_id"] == "mcp:inventory_snapshot_mcp"
    assert mcp_test.json()["action"] == "test"
    assert mcp_test.json()["status"] == "passed"

    assert submitted.status_code == 200
    assert submitted.json()["asset"]["asset_id"] == "skill:data_query"
    assert submitted.json()["asset"]["current_stage"] == "review"
    assert submitted.json()["result"]["task"]["entityName"] == "data_query"

    assert published.status_code == 200
    assert published.json()["asset"]["asset_id"] == "mcp:inventory_snapshot_mcp"
    assert published.json()["asset"]["current_stage"] == "published"
    assert published.json()["result"]["task"]["releaseStatus"] == "published"

    assert missing_action.status_code == 404


def test_unified_assets_reflect_governance_publish_and_health_check_mutations(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "chat.db"
    app = create_app(db_path=db_path)
    client = TestClient(app)

    published = client.post("/api/admin/governance/tasks/skill-task-002/publish")
    health_checked = client.post("/api/admin/mcps/inventory_snapshot_mcp/health-check")
    assets = client.get("/api/admin/assets")

    assert published.status_code == 200
    assert health_checked.status_code == 200
    assert assets.status_code == 200

    published_skill = next(item for item in assets.json() if item["asset_id"] == "skill:global_policy_watch")
    checked_mcp = next(item for item in assets.json() if item["asset_id"] == "mcp:inventory_snapshot_mcp")

    assert published_skill["release_status"] == "published"
    assert published_skill["current_stage"] == "published"
    assert published_skill["action_url"] == "/admin/skills/global_policy_watch"
    assert checked_mcp["status"] == "ready_for_review"
    assert checked_mcp["current_stage"] == "review"
    assert checked_mcp["dependency_status"] == "被 1 个 Skill 引用"


def test_platform_prototype_api_supports_governance_mutation_dry_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    permission_update = client.patch(
        "/api/organizations/gac-international/permissions",
        json={"approvalMode": "平台管理员复核"},
    )
    role_update = client.patch(
        "/api/admin/roles/sales-analyst",
        json={"openSkills": ["数据查询与分析", "请假申请"], "actionPermissions": ["查询", "下载", "提交"]},
    )
    skill_test = client.post(
        "/api/admin/skills/data_query/test",
        json={"query": "本月中东公司销量多少？"},
    )
    mcp_update = client.patch(
        "/api/admin/mcps/sql_executor",
        json={"releaseStatus": "testing"},
    )
    mcp_health = client.post("/api/admin/mcps/sql_executor/health-check")

    assert permission_update.status_code == 200
    assert permission_update.json()["approvalMode"] == "平台管理员复核"
    assert role_update.status_code == 200
    assert role_update.json()["openSkills"] == ["数据查询与分析", "请假申请"]
    assert skill_test.status_code == 200
    assert skill_test.json()["status"] == "passed"
    assert mcp_update.status_code == 200
    assert mcp_update.json()["releaseStatus"] == "testing"
    assert mcp_health.status_code == 200
    assert mcp_health.json()["health"] == "healthy"


def test_role_template_updates_persist_and_change_effective_permissions(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "chat.db"
    app = create_app(db_path=db_path)
    client = TestClient(app)

    updated_role = client.patch(
        "/api/admin/roles/sales-analyst",
        json={
            "openSkills": ["数据查询与分析", "请假申请"],
            "dataDomains": ["销售", "库存", "人力"],
            "actionPermissions": ["查询", "下载", "提交"],
        },
    )
    account = client.get("/api/admin/accounts/u-sales-chen/permissions")

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    fetched_role = restarted_client.get("/api/admin/roles")
    restarted_account = restarted_client.get("/api/admin/accounts/u-sales-chen/permissions")

    assert updated_role.status_code == 200
    assert "请假申请" in account.json()["effectiveSkills"]
    assert "提交" in account.json()["effectiveActionPermissions"]
    sales_role = next(role for role in fetched_role.json() if role["id"] == "sales-analyst")
    assert "请假申请" in sales_role["openSkills"]
    assert "人力" in sales_role["dataDomains"]
    assert "请假申请" in restarted_account.json()["effectiveSkills"]


def test_permission_audit_log_records_role_organization_and_account_changes(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    client.patch("/api/admin/roles/sales-analyst", json={"actionPermissions": ["查询", "下载", "提交"]})
    client.patch("/api/organizations/gac-international/permissions", json={"approvalMode": "平台管理员复核"})
    client.patch("/api/admin/accounts/u-sales-chen/permissions", json={"allowedSkills": ["请假申请"]})

    audit_logs = client.get("/api/admin/audit/permissions")
    account = client.get("/api/admin/accounts/u-sales-chen/permissions")

    assert audit_logs.status_code == 200
    assert len(audit_logs.json()) >= 3
    assert audit_logs.json()[0]["entityType"] in {"account", "organization", "role"}
    assert audit_logs.json()[0]["changeSummary"]
    assert account.json()["permissionSources"]["organization"]
    assert account.json()["permissionSources"]["roles"]
    assert account.json()["permissionSources"]["accountOverride"]


def test_platform_prototype_api_supports_creating_skill_and_mcp_drafts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    skill_created = client.post(
        "/api/admin/skills",
        json={
            "name": "global_policy_watch_draft",
            "displayName": "海外政策追踪草案",
            "category": "政策分析",
        },
    )
    mcp_created = client.post(
        "/api/admin/mcps",
        json={
            "name": "policy_feed_connector",
            "displayName": "政策源连接器",
            "category": "Retrieval",
        },
    )

    assert skill_created.status_code == 200
    assert skill_created.json()["status"] == "draft_created"
    assert skill_created.json()["name"] == "global_policy_watch_draft"
    assert mcp_created.status_code == 200
    assert mcp_created.json()["status"] == "draft_created"
    assert mcp_created.json()["name"] == "policy_feed_connector"


def test_admin_skill_create_and_update_persist_across_app_restarts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "registry.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    created = first_client.post(
        "/api/admin/skills",
        json={
            "name": "leave_assistant",
            "displayName": "请假助手",
            "category": "流程助手",
            "description": "提交请假流程前的表单补齐与确认。",
            "outputType": "流程结果",
            "applicableOrganizations": ["广汽乘用车"],
            "status": "draft",
            "businessDomain": "人力流程",
            "riskLevel": "高",
            "requiresApproval": True,
            "writesData": True,
            "mcpTools": ["llm"],
        },
    )
    updated = first_client.patch(
        "/api/admin/skills/leave_assistant",
        json={
            "description": "更新后的描述",
            "mcpTools": ["llm", "knowledge_retrieval"],
        },
    )

    assert created.status_code == 200
    assert updated.status_code == 200

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    fetched = restarted_client.get("/api/admin/skills/leave_assistant")

    assert fetched.status_code == 200
    assert fetched.json()["description"] == "更新后的描述"
    assert fetched.json()["mcpTools"] == ["llm", "knowledge_retrieval"]


def test_admin_mcp_create_and_health_check_persist_across_app_restarts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "registry.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    created = first_client.post(
        "/api/admin/mcps",
        json={
            "name": "oa_gateway",
            "displayName": "OA 网关",
            "category": "Workflow",
            "description": "连接 OA 审批系统。",
            "readWriteRisk": "动作型写入能力，需审批和审计",
            "health": "unknown",
            "releaseStatus": "draft",
            "referencedBy": [],
        },
    )
    checked = first_client.post("/api/admin/mcps/oa_gateway/health-check")

    assert created.status_code == 200
    assert checked.status_code == 200

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    fetched = restarted_client.get("/api/admin/mcps/oa_gateway")

    assert fetched.status_code == 200
    assert fetched.json()["health"] == "healthy"


def test_admin_skill_and_mcp_contracts_share_registry_state(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "registry.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    created_mcp = first_client.post(
        "/api/admin/mcps",
        json={
            "name": "approval_center",
            "displayName": "审批中心",
            "category": "Workflow",
            "description": "审批流中心",
            "readWriteRisk": "动作型写入能力，需审批和审计",
            "health": "healthy",
            "releaseStatus": "published",
            "referencedBy": [],
        },
    )
    created_skill = first_client.post(
        "/api/admin/skills",
        json={
            "name": "expense_assistant",
            "displayName": "报销助手",
            "category": "流程助手",
            "description": "报销填单与提交流程",
            "outputType": "流程结果",
            "applicableOrganizations": ["集团总部"],
            "status": "draft",
            "businessDomain": "财务流程",
            "riskLevel": "高",
            "requiresApproval": True,
            "writesData": True,
            "mcpTools": ["approval_center"],
        },
    )

    assert created_mcp.status_code == 200
    assert created_skill.status_code == 200

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    fetched = restarted_client.get("/api/admin/skills/expense_assistant")

    assert fetched.status_code == 200
    assert fetched.json()["mcpTools"] == ["approval_center"]


def test_governance_submit_and_approve_persist_across_app_restarts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "governance.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    created = first_client.post(
        "/api/admin/skills",
        json={
            "name": "price_policy_watch",
            "displayName": "价格政策追踪",
            "category": "政策分析",
            "description": "跟踪区域价格政策变化。",
            "outputType": "分析报告",
            "applicableOrganizations": ["广汽国际"],
            "status": "draft",
            "businessDomain": "市场分析",
            "riskLevel": "中",
            "requiresApproval": True,
            "writesData": False,
            "mcpTools": ["web_search"],
        },
    )
    submitted = first_client.post("/api/admin/governance/skills/price_policy_watch/submit")

    assert created.status_code == 200
    assert submitted.status_code == 200
    assert submitted.json()["task"]["releaseStatus"] == "ready_for_review"

    approved = first_client.post(f"/api/admin/governance/tasks/{submitted.json()['task']['id']}/approve")

    assert approved.status_code == 200
    assert approved.json()["task"]["releaseStatus"] == "ready_to_publish"
    assert approved.json()["entity"]["releaseStatus"] == "ready_to_publish"

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    tasks = restarted_client.get("/api/admin/governance/tasks").json()
    skill = restarted_client.get("/api/admin/skills/price_policy_watch").json()
    activities = restarted_client.get("/api/admin/governance/activities").json()

    review_task = next(item for item in tasks if item["entityName"] == "price_policy_watch")
    assert review_task["releaseStatus"] == "ready_to_publish"
    assert skill["releaseStatus"] == "ready_to_publish"
    assert any(item["action"] == "submitted_for_review" for item in activities)
    assert any(item["action"] == "review_approved" for item in activities)


def test_governance_publish_unblocks_dependent_tasks_and_persists_history(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "governance.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    tasks = first_client.get("/api/admin/governance/tasks").json()
    mcp_task = next(item for item in tasks if item["id"] == "mcp-task-014")

    approved = first_client.post(f"/api/admin/governance/tasks/{mcp_task['id']}/approve")
    assert approved.status_code == 200

    published = first_client.post(f"/api/admin/governance/tasks/{mcp_task['id']}/publish")
    assert published.status_code == 200
    assert published.json()["task"]["releaseStatus"] == "published"

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    restarted_tasks = restarted_client.get("/api/admin/governance/tasks").json()
    activities = restarted_client.get("/api/admin/governance/activities").json()

    parent_skill_task = next(item for item in restarted_tasks if item["id"] == "skill-task-001")
    published_mcp_task = next(item for item in restarted_tasks if item["id"] == "mcp-task-014")
    assert published_mcp_task["releaseStatus"] == "published"
    assert parent_skill_task["releaseStatus"] == "testing"
    assert any(item["action"] == "published_to_catalog" and item["entityName"] == "库存快照连接器" for item in activities)
    assert any(item["action"] == "dependency_unblocked" and "渠道库存诊断" in item["detail"] for item in activities)


def test_platform_prototype_api_persists_organization_permission_updates(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    update = client.patch(
        "/api/organizations/gac-international/permissions",
        json={
            "openSkills": ["数据查询与分析", "同环比分析", "请假申请"],
            "actionPermissions": ["查询", "下载", "提交"],
            "approvalMode": "动作型能力二次确认",
        },
    )
    fetched = client.get("/api/organizations/gac-international/permissions")
    listed = client.get("/api/organizations")

    assert update.status_code == 200
    assert fetched.json()["openSkills"] == ["数据查询与分析", "同环比分析", "请假申请"]
    assert fetched.json()["actionPermissions"] == ["查询", "下载", "提交"]
    assert fetched.json()["approvalMode"] == "动作型能力二次确认"
    assert listed.json()[0]["approvalMode"] == "动作型能力二次确认"


def test_permission_updates_persist_across_app_restarts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    db_path = tmp_path / "chat.db"
    first_app = create_app(db_path=db_path)
    first_client = TestClient(first_app)

    org_update = first_client.patch(
        "/api/organizations/gac-international/permissions",
        json={
            "openSkills": ["数据查询与分析", "同环比分析", "请假申请"],
            "dataDomains": ["销售", "库存", "人力"],
            "actionPermissions": ["查询", "下载", "提交"],
            "approvalMode": "平台管理员复核",
        },
    )
    account_update = first_client.patch(
        "/api/admin/accounts/u-sales-chen/permissions",
        json={
            "allowedSkills": ["请假申请"],
            "deniedSkills": ["同环比分析"],
        },
    )

    assert org_update.status_code == 200
    assert account_update.status_code == 200

    restarted_app = create_app(db_path=db_path)
    restarted_client = TestClient(restarted_app)
    fetched_org = restarted_client.get("/api/organizations/gac-international/permissions")
    fetched_account = restarted_client.get("/api/admin/accounts/u-sales-chen/permissions")

    assert fetched_org.status_code == 200
    assert fetched_org.json()["approvalMode"] == "平台管理员复核"
    assert fetched_org.json()["actionPermissions"] == ["查询", "下载", "提交"]
    assert fetched_account.status_code == 200
    assert "请假申请" in fetched_account.json()["allowedSkills"]
    assert "同环比分析" in fetched_account.json()["deniedSkills"]


def test_effective_account_permissions_merge_organization_role_and_account_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    client.patch(
        "/api/organizations/gac-international/permissions",
        json={
            "openSkills": ["数据查询与分析"],
            "dataDomains": ["销售", "库存", "财务"],
            "actionPermissions": ["查询"],
            "approvalMode": "部门管理员复核",
        },
    )
    updated_account = client.patch(
        "/api/admin/accounts/u-sales-chen/permissions",
        json={
            "allowedSkills": ["请假申请", "内部数据与联网分析"],
            "deniedSkills": ["同环比分析"],
        },
    )

    assert updated_account.status_code == 200
    payload = updated_account.json()
    assert payload["organizationName"] == "广汽国际"
    assert payload["roleNames"] == ["销售分析岗"]
    assert "数据查询与分析" in payload["effectiveSkills"]
    assert "请假申请" in payload["effectiveSkills"]
    assert "内部数据与联网分析" in payload["effectiveSkills"]
    assert "同环比分析" not in payload["effectiveSkills"]
    assert payload["effectiveDataDomains"] == ["销售", "库存", "财务"]
    assert payload["effectiveActionPermissions"] == ["查询", "下载"]
    assert payload["canAccessAdmin"] is False


def test_mock_auth_login_and_account_skill_permission_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    failed = client.post("/api/auth/login", json={"username": "platform_admin", "password": "wrong"})
    login = client.post("/api/auth/login", json={"username": "platform_admin", "password": "admin123"})
    accounts = client.get("/api/admin/accounts")
    update = client.patch(
        "/api/admin/accounts/u-sales-chen/permissions",
        json={
            "allowedSkills": ["请假申请"],
            "deniedSkills": ["内部数据与联网分析"],
        },
    )
    fetched = client.get("/api/admin/accounts/u-sales-chen/permissions")

    assert failed.status_code == 401
    assert login.status_code == 200
    assert login.json()["account"]["username"] == "platform_admin"
    assert login.json()["account"]["canAccessAdmin"] is True
    assert "数据查询与分析" in login.json()["account"]["effectiveSkills"]
    assert accounts.status_code == 200
    assert accounts.json()[0]["organizationName"]
    assert update.status_code == 200
    assert "请假申请" in fetched.json()["effectiveSkills"]
    assert "内部数据与联网分析" not in fetched.json()["effectiveSkills"]


def test_environment_status_endpoint_reports_mock_mode_and_demo_accounts(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    status = client.get("/api/system/environment")

    assert status.status_code == 200
    assert status.json()["mockApiAvailable"] is True
    assert status.json()["isMockMode"] is True
    assert status.json()["defaultLoginRoute"] == "/login"
    assert status.json()["demoAccounts"][0]["username"] == "platform_admin"


def test_login_returns_invalid_credentials_code_and_permission_denied_code(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    invalid = client.post("/api/auth/login", json={"username": "platform_admin", "password": "wrong"})
    denied = client.post("/api/auth/login", json={"username": "chen_sales", "password": "sales123"})

    assert invalid.status_code == 401
    assert invalid.json()["detail"]["code"] == "invalid_credentials"
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "admin_access_denied"


def test_mock_admin_can_create_account_with_organization_role_and_skill_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    created = client.post(
        "/api/admin/accounts",
        json={
            "username": "wang_ops",
            "password": "ops123",
            "displayName": "王运营",
            "organizationId": "gac-international",
            "roleIds": ["sales-analyst"],
            "allowedSkills": ["内部数据与联网分析"],
            "deniedSkills": ["同环比分析"],
        },
    )
    accounts = client.get("/api/admin/accounts")

    assert created.status_code == 200
    assert created.json()["username"] == "wang_ops"
    assert created.json()["organizationName"] == "广汽国际"
    assert created.json()["roleNames"] == ["销售分析岗"]
    assert "内部数据与联网分析" in created.json()["effectiveSkills"]
    assert "同环比分析" not in created.json()["effectiveSkills"]
    assert any(account["username"] == "wang_ops" for account in accounts.json())


def test_chat_api_saves_messages_and_returns_steps(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "测试会话"}).json()

    response = client.post(
        "/api/chat",
        json={
            "session_id": session["id"],
            "message": "2024年中东公司终端量是多少？",
            "web_search_enabled": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"]["selected_skill"] == "data_web_compare_analysis"
    assert payload["assistant_message"]["content"]
    assert payload["assistant_message"]["steps"]

    detail = client.get(f"/api/sessions/{session['id']}").json()
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]


def test_chat_api_routes_action_requests_to_leave_request_with_confirmation_hint(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "动作型会话"}).json()

    response = client.post(
        "/api/chat",
        json={
            "session_id": session["id"],
            "message": "帮我提交下周三到周五的年假申请",
            "web_search_enabled": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"]["selected_skill"] == "leave_request"
    assert "需确认后提交" in payload["assistant_message"]["content"]
    assert payload["assistant_message"]["steps"]
    session_detail = client.get(f"/api/sessions/{session['id']}").json()
    assert session_detail["pending_action_skill"] == "leave_request"
    assert session_detail["pending_action_status"] == "pending_confirmation"
    assert "年假申请" in session_detail["pending_action_message"]


def test_chat_api_confirms_or_cancels_pending_action_requests(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    confirm_session = client.post("/api/sessions", json={"title": "确认动作型会话"}).json()

    client.post(
        "/api/chat",
        json={
            "session_id": confirm_session["id"],
            "message": "帮我提交下周三到周五的年假申请",
            "web_search_enabled": False,
        },
    )
    confirmed = client.post(
        "/api/chat",
        json={
            "session_id": confirm_session["id"],
            "message": "确认提交",
            "web_search_enabled": False,
        },
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["assistant_message"]["selected_skill"] == "leave_request"
    assert "已提交" in confirmed.json()["assistant_message"]["content"]
    confirm_detail = client.get(f"/api/sessions/{confirm_session['id']}").json()
    assert confirm_detail["pending_action_skill"] is None
    assert confirm_detail["pending_action_status"] is None

    cancel_session = client.post("/api/sessions", json={"title": "取消动作型会话"}).json()
    client.post(
        "/api/chat",
        json={
            "session_id": cancel_session["id"],
            "message": "帮我提交下周三到周五的年假申请",
            "web_search_enabled": False,
        },
    )
    cancelled = client.post(
        "/api/chat",
        json={
            "session_id": cancel_session["id"],
            "message": "取消",
            "web_search_enabled": False,
        },
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["assistant_message"]["selected_skill"] == "leave_request"
    assert "已回退" in cancelled.json()["assistant_message"]["content"]
    cancel_detail = client.get(f"/api/sessions/{cancel_session['id']}").json()
    assert cancel_detail["pending_action_skill"] is None
    assert cancel_detail["pending_action_status"] is None


def test_chat_stream_emits_callback_steps_before_answer(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    def fake_run_agent(question, callback=None, history=None, web_search_enabled=False):
        assert callback is not None
        callback({"step_type": "select_skill", "decision": "选择 chat", "reason": "测试路由"})
        callback({"step_type": "final_answer", "decision": "生成回答", "final_answer": "流式回答"})
        return {
            "selected_skill": "chat",
            "messages": [{"role": "assistant", "content": "流式回答"}],
            "thought_process": [],
        }

    monkeypatch.setattr(api_server, "run_agent", fake_run_agent)
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "流式会话"}).json()

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"session_id": session["id"], "message": "你好", "web_search_enabled": False},
    ) as response:
        body = "\n".join(response.iter_lines())

    assert response.status_code == 200
    assert body.index("event: message_created") < body.index("event: step_started")
    assert body.index("event: step_started") < body.index("event: step_completed")
    assert body.count("event: step_completed") == 2
    assert body.index("event: step_completed") < body.index("event: result_ready")
    assert body.index("event: result_ready") < body.index("event: answer_delta")
    assert body.index("event: answer_delta") < body.index("event: answer_completed")
    assert '"delta": "流式回答"' in body
    assert '"duration_ms":' in body

    detail = client.get(f"/api/sessions/{session['id']}").json()
    assert detail["messages"][-1]["content"] == "流式回答"
    assert len(detail["messages"][-1]["steps"]) == 2
    assert all(step["duration_ms"] is not None for step in detail["messages"][-1]["steps"])


def test_chat_stream_previews_sql_table_before_later_analysis_steps(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    def fake_run_agent(question, callback=None, history=None, web_search_enabled=False):
        assert callback is not None
        callback({
            "step_type": "execute_mcp",
            "decision": "SOP 步骤 1 [sql_execution]：调用原子工具 [sql_executor]",
            "mcp_output": '{"success": true, "data": "| 车型 | 销量 |\\n| --- | --- |\\n| GS8 | 18918 |"}',
        })
        callback({
            "step_type": "execute_mcp",
            "decision": "SOP 步骤 2 [web_search]：调用原子工具 [web_search]",
            "mcp_output": '{"success": true, "data": "公开资料"}',
        })
        return {
            "selected_skill": "data_web_compare_analysis",
            "messages": [{"role": "assistant", "content": "最终分析"}],
            "thought_process": [],
        }

    monkeypatch.setattr(api_server, "run_agent", fake_run_agent)
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "流式预览"}).json()

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"session_id": session["id"], "message": "查询并分析", "web_search_enabled": True},
    ) as response:
        body = "\n".join(response.iter_lines())

    preview_at = body.index("event: preview_ready")
    web_step_at = body.index('"mcp_output": "{\\"success\\": true, \\"data\\": \\"公开资料\\"}"')
    assert preview_at < web_step_at
    assert "### 📊 内部数据查询结果" in body
    assert "| GS8 | 18918 |" in body


def test_streaming_answer_uses_slightly_slower_readable_pacing():
    assert api_server.ANSWER_STREAM_DELAY_SECONDS == 0.024


def test_first_question_auto_names_default_session_and_keeps_title_on_followup(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "新对话"}).json()

    first_question = "请帮我查询2024年中东公司终端销量并分析增长原因"
    client.post(
        "/api/chat",
        json={"session_id": session["id"], "message": first_question, "web_search_enabled": False},
    )
    named = client.get(f"/api/sessions/{session['id']}").json()

    assert named["title"] == "请帮我查询2024年中东公司终端销量并分…"

    client.post(
        "/api/chat",
        json={"session_id": session["id"], "message": "和去年相比呢？", "web_search_enabled": False},
    )
    followup = client.get(f"/api/sessions/{session['id']}").json()

    assert followup["title"] == named["title"]


def test_session_summary_tracks_latest_user_question(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)
    session = client.post("/api/sessions", json={"title": "销量分析"}).json()

    client.post(
        "/api/chat",
        json={"session_id": session["id"], "message": "查询中东公司本月销量", "web_search_enabled": False},
    )
    first = client.get(f"/api/sessions/{session['id']}").json()
    assert first["summary"] == "查询中东公司本月销量"

    client.post(
        "/api/chat",
        json={"session_id": session["id"], "message": "请继续分析增长的主要原因和后续建议", "web_search_enabled": False},
    )
    latest = client.get(f"/api/sessions/{session['id']}").json()
    assert latest["summary"] == "请继续分析增长的主要原因和后续建议"
