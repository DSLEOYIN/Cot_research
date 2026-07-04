# Skill MCP Registry Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace in-memory Skill / MCP admin prototype data with a SQLite-backed registry while preserving the current frontend REST contracts and governance demo flow.

**Architecture:** Add a dedicated repository for admin Skills and MCPs alongside the existing chat and permission repositories. Persist Skill definitions, MCP definitions, and lightweight test / health-check state in SQLite, then have FastAPI admin endpoints read and mutate this registry while keeping current response shapes stable for the React prototype.

**Tech Stack:** Python, FastAPI, SQLite, pytest, React TypeScript frontend consuming existing REST contracts

---

### Task 1: Lock registry persistence with failing backend tests

**Files:**
- Modify: `tests/test_api_server.py`
- Test: `tests/test_api_server.py`

- [x] **Step 1: Write the failing test for Skill persistence across app restarts**

```python
def test_admin_skill_create_and_update_persist_across_app_restarts(tmp_path, monkeypatch):
    db_path = tmp_path / "registry.db"
    client = _create_test_client(monkeypatch, db_path)

    created = client.post(
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
    assert created.status_code == 200

    updated = client.patch(
        "/api/admin/skills/leave_assistant",
        json={"description": "更新后的描述", "mcpTools": ["llm", "knowledge_retrieval"]},
    )
    assert updated.status_code == 200

    restarted_client = _create_test_client(monkeypatch, db_path)
    fetched = restarted_client.get("/api/admin/skills/leave_assistant")

    assert fetched.status_code == 200
    assert fetched.json()["description"] == "更新后的描述"
    assert fetched.json()["mcpTools"] == ["llm", "knowledge_retrieval"]
```

- [x] **Step 2: Run the Skill persistence test to verify it fails**

Run: `python3 -m pytest tests/test_api_server.py::test_admin_skill_create_and_update_persist_across_app_restarts -q`
Expected: FAIL because the current in-memory Skill prototype does not survive restart.

- [x] **Step 3: Write the failing test for MCP persistence and health-check state**

```python
def test_admin_mcp_create_and_health_check_persist_across_app_restarts(tmp_path, monkeypatch):
    db_path = tmp_path / "registry.db"
    client = _create_test_client(monkeypatch, db_path)

    created = client.post(
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
    assert created.status_code == 200

    checked = client.post("/api/admin/mcps/oa_gateway/health-check")
    assert checked.status_code == 200

    restarted_client = _create_test_client(monkeypatch, db_path)
    fetched = restarted_client.get("/api/admin/mcps/oa_gateway")

    assert fetched.status_code == 200
    assert fetched.json()["health"] == "healthy"
```

- [x] **Step 4: Run the MCP persistence test to verify it fails**

Run: `python3 -m pytest tests/test_api_server.py::test_admin_mcp_create_and_health_check_persist_across_app_restarts -q`
Expected: FAIL because the current in-memory MCP prototype and health state do not survive restart.

- [x] **Step 5: Write the failing test for Skill and MCP relationship consistency**

```python
def test_admin_skill_and_mcp_contracts_share_registry_state(tmp_path, monkeypatch):
    db_path = tmp_path / "registry.db"
    client = _create_test_client(monkeypatch, db_path)

    client.post(
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
    skill = client.post(
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

    assert skill.status_code == 200
    assert client.get("/api/admin/skills/expense_assistant").json()["mcpTools"] == ["approval_center"]
```

- [x] **Step 6: Run the relationship test to verify it fails or exposes missing persistence guarantees**

Run: `python3 -m pytest tests/test_api_server.py::test_admin_skill_and_mcp_contracts_share_registry_state -q`
Expected: FAIL if registry state is not durable or response fields drift from the existing contract.

### Task 2: Introduce a SQLite-backed admin registry repository

**Files:**
- Create: `registry_repository.py`
- Modify: `api_server.py`

- [x] **Step 1: Create the repository schema and seed layer**

```python
class RegistryRepository:
    def __init__(self, db_path: str | Path, *, skills: list[dict[str, Any]], mcps: list[dict[str, Any]]) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._seed_if_empty(skills=skills, mcps=mcps)
```

- [x] **Step 2: Add tables for Skills, MCPs, and operational check state**

```sql
CREATE TABLE IF NOT EXISTS admin_skills (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    output_type TEXT NOT NULL,
    applicable_organizations TEXT NOT NULL,
    status TEXT NOT NULL,
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
```

- [x] **Step 3: Implement list/get/create/update methods for Skills**

```python
def list_skills(self) -> list[dict[str, Any]]:
    ...

def get_skill(self, skill_name: str) -> dict[str, Any] | None:
    ...

def create_skill(self, payload: dict[str, Any]) -> dict[str, Any]:
    ...

def update_skill(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    ...
```

- [x] **Step 4: Implement list/get/create/update methods for MCPs**

```python
def list_mcps(self) -> list[dict[str, Any]]:
    ...

def get_mcp(self, mcp_name: str) -> dict[str, Any] | None:
    ...

def create_mcp(self, payload: dict[str, Any]) -> dict[str, Any]:
    ...

def update_mcp(self, mcp_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    ...
```

- [x] **Step 5: Implement lightweight Skill test and MCP health-check mutation helpers**

```python
def mark_skill_test_result(self, skill_name: str, *, status: str) -> dict[str, Any] | None:
    skill = self.get_skill(skill_name)
    if skill is None:
        return None
    return self.update_skill(skill_name, {"status": status})

def mark_mcp_health_check(self, mcp_name: str, *, health: str) -> dict[str, Any] | None:
    mcp = self.get_mcp(mcp_name)
    if mcp is None:
        return None
    return self.update_mcp(mcp_name, {"health": health})
```

- [x] **Step 6: Wire FastAPI admin endpoints to the repository**

```python
registry_repo = RegistryRepository(
    resolved_db_path,
    skills=deepcopy(PROTOTYPE_ADMIN_SKILLS),
    mcps=deepcopy(PROTOTYPE_ADMIN_MCPS),
)
app.state.registry_repo = registry_repo
```

- [x] **Step 7: Replace in-memory Skill endpoint handlers with repository-backed reads and writes**

```python
@app.get("/api/admin/skills")
def list_admin_skills():
    return registry_repo.list_skills()

@app.patch("/api/admin/skills/{skill_id}")
def update_admin_skill(skill_id: str, payload: dict[str, Any]):
    skill = registry_repo.update_skill(skill_id, payload)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
    return skill
```

- [x] **Step 8: Replace in-memory MCP endpoint handlers with repository-backed reads and writes**

```python
@app.get("/api/admin/mcps")
def list_admin_mcps():
    return registry_repo.list_mcps()

@app.post("/api/admin/mcps/{mcp_id}/health-check")
def run_mcp_health_check(mcp_id: str):
    mcp = registry_repo.mark_mcp_health_check(mcp_id, health="healthy")
    if mcp is None:
        raise HTTPException(status_code=404, detail=f"MCP not found: {mcp_id}")
    return mcp
```

### Task 3: Reconcile frontend contract compatibility and end-to-end verification

**Files:**
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_web_frontend_contract.py` (only if contract assertions need additive coverage)
- Modify: `web_frontend/src/App.tsx` (only if state hydration needs a compatibility fix)
- Modify: `web_frontend/src/api/client.ts` (only if payload typing needs tightening)

- [x] **Step 1: Run the focused backend tests after implementation**

Run: `python3 -m pytest tests/test_api_server.py::test_admin_skill_create_and_update_persist_across_app_restarts tests/test_api_server.py::test_admin_mcp_create_and_health_check_persist_across_app_restarts tests/test_api_server.py::test_admin_skill_and_mcp_contracts_share_registry_state -q`
Expected: PASS.

- [x] **Step 2: Run the full backend and frontend contract suite**

Run: `python3 -m pytest tests/test_api_server.py tests/test_web_frontend_contract.py -q`
Expected: PASS.

- [x] **Step 3: Run the frontend production build**

Run: `cd /Users/leo/work/ai_model/Cot_research/web_frontend && node ./node_modules/typescript/bin/tsc -b && node ./node_modules/vite/bin/vite.js build`
Expected: successful production build with existing chunk warning tolerated unless it becomes a hard failure.

- [x] **Step 4: If the frontend needs a compatibility adjustment, keep it contract-preserving**

```typescript
const normalizedSkill = {
  ...skill,
  applicableOrganizations: Array.isArray(skill.applicableOrganizations) ? skill.applicableOrganizations : [],
  mcpTools: Array.isArray(skill.mcpTools) ? skill.mcpTools : [],
};
```

- [x] **Step 5: Update the plan checklist and stop for branch-finish workflow**

Run: `git diff -- docs/superpowers/plans/2026-06-25-skill-mcp-registry-foundation.md api_server.py registry_repository.py tests/test_api_server.py`
Expected: shows the repository-backed registry implementation plus passing-test coverage.
