from mcps import get_mcp, list_mcp_names, list_mcps
from prompt_loader import list_prompt_names, render_prompt
from skills import get_skill, list_skill_names, list_skills


def test_mcp_registry_loads_builtin_mcps():
    expected = {"sql_executor", "knowledge_retrieval", "llm", "time", "text_analysis", "n2sql", "web_search"}

    names = set(list_mcp_names())

    assert expected.issubset(names)
    assert len(list_mcps()) >= len(expected)
    for name in expected:
        config = get_mcp(name)
        assert config is not None
        assert config["name"] == name
        assert "inputSchema" in config


def test_skill_registry_loads_builtin_skills():
    expected = {
        "data_query",
        "chat",
        "yoy_yoy_analysis",
        "web_search_answer",
        "web_compare_analysis",
        "data_web_compare_analysis",
    }

    names = set(list_skill_names())

    assert expected.issubset(names)
    assert len(list_skills()) >= len(expected)
    for name in expected:
        config = get_skill(name)
        assert config is not None
        assert config["name"] == name
        assert "flow" in config
        assert "steps" in config["flow"]


def test_prompt_registry_loads_editable_json_prompts():
    expected = {
        "router",
        "n2sql",
        "data_analysis",
        "chat",
        "web_search_query",
        "web_search_answer",
        "web_compare_analysis",
        "data_web_compare_analysis",
        "internal_data_query",
        "sql_correction",
    }

    names = set(list_prompt_names())

    assert expected.issubset(names)
    rendered = render_prompt(
        "router",
        {
            "skill_list": "- data_query: 数据查询",
            "history": "无",
            "query": "国际24年的销量",
        },
    )
    assert rendered is not None
    assert "{{" not in rendered
    assert "data_query" in rendered
    assert "国际24年的销量" in rendered
