# Admin Usability And Smoke Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the admin prototype self-explanatory and diagnosable during local preview by surfacing environment status, classifying login failures, aligning demo accounts with backend mock data, and adding smoke coverage for the main admin routes.

**Architecture:** Add a small backend environment-status contract and explicit login error payloads, then let the frontend hydrate and render those signals on the login page and during preview bootstrap. Keep the current mock-first fallback model, but stop swallowing backend availability details so users can tell whether they are in mock demo mode, hitting a dead backend, or lacking admin access.

**Tech Stack:** Python, FastAPI, pytest, React 18, TypeScript, Vite

---

### Task 1: Lock the new usability contract with failing backend and frontend tests

**Files:**
- Modify: `tests/test_api_server.py`
- Modify: `tests/test_web_frontend_contract.py`
- Test: `tests/test_api_server.py`
- Test: `tests/test_web_frontend_contract.py`

- [ ] **Step 1: Add backend tests for environment status and classified login failures**

```python
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
```

- [ ] **Step 2: Add frontend contract tests for login-page environment status and smoke entry points**

```python
def test_login_page_shows_environment_status_and_demo_account_source():
    app = read(SRC / "App.tsx")
    login_page = read(SRC / "pages" / "LoginPage.tsx")
    client = read(SRC / "api" / "client.ts")

    assert "getEnvironmentStatus" in client
    assert "'/api/system/environment'" in client
    assert "environmentStatus" in app
    assert "mockApiAvailable" in app
    assert "isMockMode" in app
    assert "demoAccounts" in login_page
    assert "环境状态" in login_page
    assert "Mock API" in login_page
    assert "演示模式" in login_page


def test_frontend_defines_admin_smoke_test_targets():
    app = read(SRC / "App.tsx")
    tests = read(ROOT / "tests" / "test_web_frontend_contract.py")

    assert "/login" in app
    assert "/admin" in app
    assert "/admin/assets" in app
    assert "/admin/skills/" in app
    assert "/admin/mcps/" in app
    assert "smoke" in tests
```

- [ ] **Step 3: Run the focused contract suite to verify it fails before implementation**

Run: `python3 -m pytest tests/test_api_server.py tests/test_web_frontend_contract.py -q`
Expected: FAIL on missing `/api/system/environment`, missing classified login payloads, and missing login-page environment status strings.

- [ ] **Step 4: Commit the red-state tests**

```bash
git add tests/test_api_server.py tests/test_web_frontend_contract.py
git commit -m "test: lock admin environment status contract"
```

### Task 2: Expose backend environment status and classified auth failures

**Files:**
- Modify: `api_server.py`
- Modify: `permission_repository.py`
- Test: `tests/test_api_server.py`

- [ ] **Step 1: Add explicit environment-status payload helpers**

```python
def _environment_status_payload() -> dict[str, Any]:
    app_mode = os.getenv("APP_MODE", "mock")
    mock_enabled = os.getenv("MOCK_ENABLED", "true").lower() == "true"
    return {
        "appMode": app_mode,
        "mockApiAvailable": mock_enabled,
        "isMockMode": app_mode == "mock",
        "defaultLoginRoute": "/login",
        "demoAccounts": [
            {"username": "platform_admin", "displayName": "平台管理员", "passwordHint": "admin123", "canAccessAdmin": True},
            {"username": "chen_sales", "displayName": "销售员工", "passwordHint": "sales123", "canAccessAdmin": False},
            {"username": "lin_dev", "displayName": "AI 开发者", "passwordHint": "dev123", "canAccessAdmin": True},
        ],
    }
```

- [ ] **Step 2: Add a backend endpoint that returns the environment-status payload**

```python
@app.get("/api/system/environment")
def get_environment_status():
    return _environment_status_payload()
```

- [ ] **Step 3: Classify login failures instead of collapsing everything into one 401**

```python
@app.post("/api/auth/login")
def login(payload: LoginRequest):
    account = permission_repo.get_account_by_username(payload.username)
    if account is None or account["password"] != payload.password:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "账号或密码错误"},
        )

    account_view = permission_repo.account_view(account["id"])
    if account_view is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "backend_unavailable", "message": "权限账户服务暂不可用"},
        )
    if not account_view["canAccessAdmin"]:
        raise HTTPException(
            status_code=403,
            detail={"code": "admin_access_denied", "message": "当前账号无管理端访问权限"},
        )
    return {"token": account["id"], "account": account_view}
```

- [ ] **Step 4: Run backend tests until the new contract passes**

Run: `python3 -m pytest tests/test_api_server.py -q`
Expected: PASS with environment status and classified login failure assertions green.

- [ ] **Step 5: Commit the backend contract work**

```bash
git add api_server.py permission_repository.py tests/test_api_server.py
git commit -m "feat: expose admin environment status"
```

### Task 3: Surface environment state and login diagnostics in the frontend

**Files:**
- Modify: `web_frontend/src/api/client.ts`
- Modify: `web_frontend/src/App.tsx`
- Modify: `web_frontend/src/pages/LoginPage.tsx`
- Modify: `web_frontend/src/styles/app.css`
- Test: `tests/test_web_frontend_contract.py`

- [ ] **Step 1: Add a typed frontend client for environment status**

```ts
export type EnvironmentStatus = {
  appMode: string;
  mockApiAvailable: boolean;
  isMockMode: boolean;
  defaultLoginRoute: string;
  demoAccounts: {
    username: string;
    displayName: string;
    passwordHint: string;
    canAccessAdmin: boolean;
  }[];
};

getEnvironmentStatus: () => request<EnvironmentStatus>('/api/system/environment'),
```

- [ ] **Step 2: Track environment status separately from login errors in `App.tsx`**

```ts
const [environmentStatus, setEnvironmentStatus] = useState<EnvironmentStatus | null>(null);
const [environmentError, setEnvironmentError] = useState('');

useEffect(() => {
  api.getEnvironmentStatus()
    .then(setEnvironmentStatus)
    .catch(() => setEnvironmentError('Mock API 不可用，当前仅能查看静态前端原型。'));
}, []);
```

- [ ] **Step 3: Map backend error codes to user-facing login messages**

```ts
function loginMessageFromError(err: unknown) {
  if (!(err instanceof Error)) return '登录失败';
  if (err.message.includes('invalid_credentials')) return '账号密码错误，请检查演示账号或手动输入内容。';
  if (err.message.includes('admin_access_denied')) return '当前账号权限不足，无法进入管理端。';
  if (err.message.includes('backend_unavailable')) return '后端不可用，请先启动 mock API。';
  return '登录失败，请稍后重试。';
}
```

- [ ] **Step 4: Update `LoginPage.tsx` to render environment state and backend-sourced demo accounts**

```tsx
<aside className="login-environment-panel">
  <h2>环境状态</h2>
  <dl>
    <div><dt>Mock API</dt><dd>{environmentStatus?.mockApiAvailable ? '可用' : '不可用'}</dd></div>
    <div><dt>演示模式</dt><dd>{environmentStatus?.isMockMode ? '已开启' : '未开启'}</dd></div>
    <div><dt>当前来源</dt><dd>{environmentError || '后端状态已同步'}</dd></div>
  </dl>
</aside>

<div className="login-demo-users">
  {demoAccounts.map((account) => (
    <button key={account.username} type="button" onClick={() => useDemoAccount(account)}>
      {account.displayName} / {account.passwordHint}
    </button>
  ))}
</div>
```

- [ ] **Step 5: Add only the CSS needed for the new status panel and clearer error states**

```css
.login-environment-panel { border: 1px solid #d9e2ec; border-radius: 18px; padding: 16px; background: #f8fbff; }
.login-environment-panel dt { color: #52606d; font-size: 12px; }
.login-environment-panel dd { color: #102a43; font-weight: 600; margin: 4px 0 0; }
.login-error[data-kind="warning"] { background: #fff7ed; color: #9a3412; }
.login-error[data-kind="danger"] { background: #fef2f2; color: #b91c1c; }
```

- [ ] **Step 6: Run the frontend contract suite and typecheck/build**

Run: `python3 -m pytest tests/test_web_frontend_contract.py -q`
Expected: PASS.

Run: `cd /Users/leo/work/ai_model/Cot_research/web_frontend && node ./node_modules/typescript/bin/tsc -b && node ./node_modules/vite/bin/vite.js build`
Expected: successful production build.

- [ ] **Step 7: Commit the frontend usability work**

```bash
git add web_frontend/src/api/client.ts web_frontend/src/App.tsx web_frontend/src/pages/LoginPage.tsx web_frontend/src/styles/app.css tests/test_web_frontend_contract.py
git commit -m "feat: improve admin login diagnostics"
```

### Task 4: Add browser-level smoke coverage for the main admin routes

**Files:**
- Modify: `tests/test_web_frontend_contract.py`
- Create: `tests/test_admin_smoke.py`
- Test: `tests/test_admin_smoke.py`

- [ ] **Step 1: Add a smoke test file that covers login and the four admin route entry points**

```python
from fastapi.testclient import TestClient

from api_server import create_app


def test_admin_smoke_login_and_primary_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    login = client.post("/api/auth/login", json={"username": "platform_admin", "password": "admin123"})
    assets = client.get("/api/admin/assets")
    skills = client.get("/api/admin/skills/data_query")
    mcps = client.get("/api/admin/mcps/sql_executor")
    workbench = client.get("/api/admin/governance/tasks")

    assert login.status_code == 200
    assert assets.status_code == 200
    assert skills.status_code == 200
    assert mcps.status_code == 200
    assert workbench.status_code == 200
```

- [ ] **Step 2: Run the smoke suite**

Run: `python3 -m pytest tests/test_admin_smoke.py -q`
Expected: PASS.

- [ ] **Step 3: Run the minimum completion checks from the development doc**

Run: `python3 -m pytest tests/test_web_frontend_contract.py tests/test_api_server.py tests/test_admin_smoke.py -q`
Expected: PASS.

Run: `cd /Users/leo/work/ai_model/Cot_research/web_frontend && node ./node_modules/typescript/bin/tsc -b`
Expected: PASS.

Run: `cd /Users/leo/work/ai_model/Cot_research/web_frontend && node ./node_modules/vite/bin/vite.js build`
Expected: PASS.

- [ ] **Step 4: Commit the smoke coverage**

```bash
git add tests/test_admin_smoke.py tests/test_api_server.py tests/test_web_frontend_contract.py
git commit -m "test: add admin smoke coverage"
```

### Task 5: Close the loop in the development document

**Files:**
- Modify: `doc/广汽集团AI一体化平台_开发文档.md`

- [ ] **Step 1: Mark completed `6.2 P0` items and add the smoke-test status**

```markdown
- [x] 启动前端 preview 时自动提示 mock API 依赖
- [x] 在登录页增加环境状态提示
- [x] 为登录失败增加更清晰的错误分类
- [x] 将“平台管理员 / 销售员工 / AI 开发者”演示账号逻辑与后端 mock 数据一一对齐
- [x] 增加管理端页面基础 smoke test
```

- [ ] **Step 2: Record the verification commands under the latest status note**

```markdown
- [x] `python3 -m pytest tests/test_api_server.py tests/test_web_frontend_contract.py tests/test_admin_smoke.py -q`
- [x] `cd web_frontend && node ./node_modules/typescript/bin/tsc -b`
- [x] `cd web_frontend && node ./node_modules/vite/bin/vite.js build`
```

- [ ] **Step 3: Commit the plan closeout**

```bash
git add doc/广汽集团AI一体化平台_开发文档.md
git commit -m "docs: update admin usability progress"
```
