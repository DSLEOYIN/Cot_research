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
    assert body.index("event: message_created") < body.index("event: step_completed")
    assert body.count("event: step_completed") == 2
    assert body.index("event: step_completed") < body.index("event: answer_completed")

    detail = client.get(f"/api/sessions/{session['id']}").json()
    assert detail["messages"][-1]["content"] == "流式回答"
    assert len(detail["messages"][-1]["steps"]) == 2


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
