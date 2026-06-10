import json

from mcps.llm_mcp import llm
from mcps.n2sql_mcp import n2sql
from skills import get_skill
from theme_loader import get_active_theme_table_info


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


class FakeClient:
    payloads = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, headers=None, json=None):
        self.payloads.append(json)
        return FakeResponse()


def test_llm_template_receives_structured_sql_context(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("MOCK_ENABLED", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr("httpx.Client", FakeClient)
    FakeClient.payloads = []

    raw = llm(
        prompt="本月中东公司销量多少？",
        prompt_type="data_analysis",
        template_vars={
            "sql_data": "| 区域 | 终端量 |\n| --- | --- |\n| 中东公司 | 1280 |",
            "sql": "SELECT SUM(terminal_qty) FROM v_dm_sal_wolesale_terminal_dly",
        },
    )

    assert json.loads(raw)["success"] is True
    sent_prompt = FakeClient.payloads[-1]["messages"][0]["content"]
    assert "数据结果：| 区域 | 终端量 |" in sent_prompt
    assert "SQL：SELECT SUM(terminal_qty)" in sent_prompt


def test_data_query_passes_retrieval_as_context_not_table_info():
    skill = get_skill("data_query")
    n2sql_step = next(step for step in skill["flow"]["steps"] if step["mcp"] == "n2sql")

    assert "context" in n2sql_step["arguments"]
    assert "table_info" not in n2sql_step["arguments"]


def test_n2sql_combines_active_theme_ddl_with_retrieval_context(monkeypatch):
    monkeypatch.setenv("APP_MODE", "real")
    monkeypatch.setenv("MOCK_ENABLED", "false")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr("httpx.Client", FakeClient)
    FakeClient.payloads = []

    raw = n2sql("本月中东公司销量多少？", context="终端量字段定义")

    assert json.loads(raw)["success"] is True
    sent_prompt = FakeClient.payloads[-1]["messages"][0]["content"]
    assert "CREATE TABLE `v_dm_sal_wolesale_terminal_dly`" in sent_prompt
    assert "补充上下文" in sent_prompt
    assert "终端量字段定义" in sent_prompt


def test_active_theme_uses_real_scheduling_table_columns():
    table_info = get_active_theme_table_info()

    assert "`product_qty`" in table_info
    assert "`delivery_qty`" in table_info
    assert "`scheduling_qty`" not in table_info
