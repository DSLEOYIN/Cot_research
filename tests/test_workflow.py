from langgraph_cot import run_agent
import json


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


def test_run_agent_injects_recent_session_memory(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    captured = {}

    def fake_execute_mcp(name, **kwargs):
        captured["name"] = name
        captured["kwargs"] = kwargs
        return json.dumps({
            "success": True,
            "text": "已结合会话上下文回答。",
            "structured_output": None,
            "error": None,
        }, ensure_ascii=False)

    monkeypatch.setattr("langgraph_cot.execute_mcp", fake_execute_mcp)

    history = [
        {"role": "user", "content": "2023年6月中东公司的销量是多少？"},
        {"role": "assistant", "content": "中东公司终端量 2311，批发量 2160。"},
    ]

    result = run_agent("刚才我问了什么？", history=history)

    assert result["selected_skill"] == "chat"
    assert captured["name"] == "llm"
    assert "最近会话上下文" in captured["kwargs"]["prompt"]
    assert "2023年6月中东公司的销量是多少？" in captured["kwargs"]["prompt"]
    assert "刚才我问了什么？" in captured["kwargs"]["prompt"]
    assert captured["kwargs"]["prompt"].count("刚才我问了什么？") == 1
    assert result["messages"][0]["content"] == history[0]["content"]
    assert result["messages"][-1]["content"] == "已结合会话上下文回答。"


def test_mock_chat_can_answer_from_session_memory(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    history = [
        {"role": "user", "content": "2023年6月中东公司的销量是多少？"},
        {"role": "assistant", "content": "中东公司终端量 2311，批发量 2160。"},
    ]

    result = run_agent("刚才我问了什么？", history=history)

    assert result["selected_skill"] == "chat"
    assert "2023年6月中东公司的销量是多少" in result["messages"][-1]["content"]


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


def test_workflow_retries_sql_execution_once_after_correction(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    calls = []

    def fake_execute_mcp(name, **kwargs):
        calls.append((name, kwargs))
        if name == "llm" and kwargs.get("prompt_type") == "intent_classification":
            return json.dumps({"success": True, "text": "{\"problem_type\":\"1\"}", "error": None, "error_type": None})
        if name == "knowledge_retrieval":
            return json.dumps({"success": True, "results": [{"content": "terminal_qty 是终端量"}], "error": None, "error_type": None})
        if name == "n2sql":
            return json.dumps({"success": True, "sql": "SELECT bad_col FROM v_dm_sal_wolesale_terminal_dly", "error": None, "error_type": None})
        if name == "sql_executor" and "bad_col" in kwargs["query"]:
            return json.dumps({
                "success": False,
                "data": None,
                "error": "Unknown column 'bad_col'",
                "error_type": "OperationalError",
                "row_count": None,
            })
        if name == "llm" and kwargs.get("prompt_type") == "sql_correction":
            return json.dumps({
                "success": True,
                "text": "SELECT terminal_qty AS '终端量' FROM v_dm_sal_wolesale_terminal_dly",
                "error": None,
                "error_type": None,
            })
        if name == "sql_executor":
            return json.dumps({
                "success": True,
                "data": "| 终端量 |\n| --- |\n| 1280 |",
                "error": None,
                "error_type": None,
                "row_count": 1,
            })
        if name == "llm" and kwargs.get("prompt_type") == "data_analysis":
            return json.dumps({"success": True, "text": "修正后查询成功。", "error": None, "error_type": None})
        if name == "llm" and kwargs.get("prompt_type") == "scope_explanation":
            return json.dumps({"success": True, "text": "统计终端量。", "error": None, "error_type": None})
        raise AssertionError(f"Unexpected MCP call: {name}, {kwargs}")

    monkeypatch.setattr("langgraph_cot.execute_mcp", fake_execute_mcp)

    result = run_agent("本月中东公司销量多少？")

    sql_calls = [kwargs["query"] for name, kwargs in calls if name == "sql_executor"]
    correction_calls = [kwargs for name, kwargs in calls if name == "llm" and kwargs.get("prompt_type") == "sql_correction"]

    assert "error" not in result
    assert result["is_final"] is True
    assert result["thought_process"][-1]["step_type"] == "final_answer"
    assert sql_calls == [
        "SELECT bad_col FROM v_dm_sal_wolesale_terminal_dly",
        "SELECT terminal_qty AS '终端量' FROM v_dm_sal_wolesale_terminal_dly",
    ]
    assert len(correction_calls) == 1
    assert "Unknown column" in correction_calls[0]["template_vars"]["error_message"]
    assert any(step.get("step_type") == "sql_correction" for step in result["thought_process"])
