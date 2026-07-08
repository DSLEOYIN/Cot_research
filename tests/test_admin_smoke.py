from fastapi.testclient import TestClient

from api_server import create_app


def test_admin_smoke_login_and_primary_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    app = create_app(db_path=tmp_path / "chat.db")
    client = TestClient(app)

    login = client.post("/api/auth/login", json={"username": "platform_admin", "password": "admin123"})
    assets = client.get("/api/admin/assets")
    skill_detail = client.get("/api/admin/skills/data_query")
    mcp_detail = client.get("/api/admin/mcps/sql_executor")
    workbench = client.get("/api/admin/governance/tasks")

    assert login.status_code == 200
    assert assets.status_code == 200
    assert skill_detail.status_code == 200
    assert mcp_detail.status_code == 200
    assert workbench.status_code == 200
