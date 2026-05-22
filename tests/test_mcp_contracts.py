import json

from mcps import execute_mcp


def parse_result(raw: str) -> dict:
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def assert_step_result(data: dict) -> None:
    assert "success" in data
    assert "error" in data
    assert "error_type" in data


def test_all_mcps_return_standard_contract_in_mock_mode(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    cases = [
        ("llm", {"prompt": "汽车保养一般多少公里做一次？", "prompt_type": "chat"}),
        ("n2sql", {"query": "本月中东公司销量多少？"}),
        ("sql_executor", {"query": "SELECT 1", "format": "md"}),
        ("knowledge_retrieval", {"query": "终端量", "dataset_ids": ["字段标准查询名检索"]}),
        ("time", {"format": "%Y-%m-%d %H:%M:%S", "timezone": "Asia/Shanghai"}),
        ("text_analysis", {"text": "本月销量同比增长15%", "task": "sentiment"}),
    ]

    for name, kwargs in cases:
        data = parse_result(execute_mcp(name, **kwargs))
        assert_step_result(data)
        assert data["success"] is True, name


def test_real_mode_missing_external_config_fails_cleanly(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("MOCK_ENABLED", "false")
    for key in [
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "DB_HOST",
        "DB_PORT",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
        "DB_URI",
    ]:
        monkeypatch.delenv(key, raising=False)

    cases = [
        ("llm", {"prompt": "hello", "prompt_type": "chat"}),
        ("n2sql", {"query": "本月中东公司销量多少？"}),
        ("sql_executor", {"query": "SELECT 1", "format": "md"}),
    ]

    for name, kwargs in cases:
        data = parse_result(execute_mcp(name, **kwargs))
        assert_step_result(data)
        assert data["success"] is False, name
        assert data["error"]
        assert data["error_type"] == "ConfigurationError"


def test_sql_executor_blocks_unsafe_sql(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    unsafe_queries = [
        "DROP TABLE users",
        "DELETE FROM users",
        "UPDATE users SET name = 'x'",
        "INSERT INTO users VALUES (1)",
        "ALTER TABLE users ADD COLUMN age INT",
    ]

    for query in unsafe_queries:
        data = parse_result(execute_mcp("sql_executor", query=query, format="md"))
        assert_step_result(data)
        assert data["success"] is False
        assert data["error_type"] == "SecurityError"


def test_sql_executor_rejects_non_select_sql(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    data = parse_result(execute_mcp("sql_executor", query="SHOW TABLES", format="md"))

    assert_step_result(data)
    assert data["success"] is False
    assert data["error_type"] == "SecurityError"


def test_sql_executor_rejects_multiple_statements(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")

    data = parse_result(execute_mcp("sql_executor", query="SELECT 1; SELECT 2", format="md"))

    assert_step_result(data)
    assert data["success"] is False
    assert data["error_type"] == "SecurityError"
    assert "单条" in data["error"]


def test_sql_executor_enforces_table_whitelist(monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    monkeypatch.setenv("MOCK_ENABLED", "true")
    monkeypatch.setenv("DB_ALLOWED_TABLES", "v_dm_sal_wolesale_terminal_dly")

    allowed = parse_result(
        execute_mcp(
            "sql_executor",
            query="SELECT area_name FROM v_dm_sal_wolesale_terminal_dly",
            format="md",
        )
    )
    blocked = parse_result(
        execute_mcp(
            "sql_executor",
            query="SELECT * FROM private_customer_table",
            format="md",
        )
    )

    assert allowed["success"] is True
    assert blocked["success"] is False
    assert blocked["error_type"] == "SecurityError"
    assert "白名单" in blocked["error"]
