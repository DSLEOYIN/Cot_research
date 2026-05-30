from mcps import get_mcp, list_mcp_names, list_mcps
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
    expected = {"data_query", "chat", "yoy_yoy_analysis"}

    names = set(list_skill_names())

    assert expected.issubset(names)
    assert len(list_skills()) >= len(expected)
    for name in expected:
        config = get_skill(name)
        assert config is not None
        assert config["name"] == name
        assert "flow" in config
        assert "steps" in config["flow"]
