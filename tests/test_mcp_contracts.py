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
        ("web_search", {"query": "Tavily search MCP", "max_results": 2}),
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
        "WEB_MCP_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)

    cases = [
        ("llm", {"prompt": "hello", "prompt_type": "chat"}),
        ("n2sql", {"query": "本月中东公司销量多少？"}),
        ("sql_executor", {"query": "SELECT 1", "format": "md"}),
        ("web_search", {"query": "latest EV news"}),
    ]

    for name, kwargs in cases:
        data = parse_result(execute_mcp(name, **kwargs))
        assert_step_result(data)
        assert data["success"] is False, name
        assert data["error"]
        assert data["error_type"] == "ConfigurationError"


def test_web_search_calls_tavily_when_configured(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("MOCK_ENABLED", "false")
    monkeypatch.setenv("WEB_MCP_ENABLED", "true")
    monkeypatch.setenv("WEB_MCP_PROVIDER", "tavily")
    monkeypatch.setenv("WEB_MCP_API_KEY", "test-tavily-key")
    monkeypatch.setenv("WEB_MCP_BASE_URL", "https://api.tavily.com")
    monkeypatch.setenv("WEB_MCP_SEARCH_ENDPOINT", "/search")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "answer": "summary",
                "results": [
                    {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1", "score": 0.9}
                ],
            }

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    data = parse_result(execute_mcp("web_search", query="latest EV news", max_results=1))

    assert data["success"] is True
    assert captured["url"] == "https://api.tavily.com/search"
    assert captured["headers"]["Authorization"] == "Bearer test-tavily-key"
    assert captured["json"]["query"] == "latest EV news"
    assert captured["json"]["max_results"] == 1
    assert data["results"][0]["url"] == "https://example.com/1"


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
