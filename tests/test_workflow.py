from langgraph_cot import run_agent


def test_mock_data_query_workflow_runs_to_final_answer(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    result = run_agent("本月中东公司销量多少？")

    assert "error" not in result
    assert result["selected_skill"] == "data_query"
    assert result["is_final"] is True
    assert result["messages"][-1]["content"]
    assert result["thought_process"][-1]["step_type"] == "final_answer"


def test_mock_yoy_workflow_routes_to_yoy_skill(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    result = run_agent("本月终端量同比去年怎么样？")

    assert "error" not in result
    assert result["selected_skill"] == "yoy_yoy_analysis"
    assert result["is_final"] is True
    assert "同比" in result["messages"][-1]["content"]


def test_mock_chat_workflow_routes_to_chat_skill(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    result = run_agent("汽车保养一般多少公里做一次？")

    assert "error" not in result
    assert result["selected_skill"] == "chat"
    assert result["is_final"] is True
    assert "保养" in result["messages"][-1]["content"]


def test_workflow_stops_on_mcp_failure(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("MOCK_ENABLED", "false")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = run_agent("本月中东公司销量多少？")

    assert "error" not in result
    assert result["is_final"] is True
    assert result["thought_process"][-1]["step_type"] == "workflow_error"
    assert "工作流已中断" in result["messages"][-1]["content"]
    assert "ConfigurationError" in result["messages"][-1]["content"]
