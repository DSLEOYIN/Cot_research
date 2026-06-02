from streamlit_ui_helpers import (
    build_empty_state_html,
    build_result_panel_html,
    build_workspace_context_html,
    iter_typewriter_chunks,
    session_action_specs,
)


def test_result_panel_escapes_content_and_sets_variant_class():
    html = build_result_panel_html("业务分析", "<script>alert(1)</script>", "analysis")

    assert "chatbi-result-panel chatbi-result-panel-analysis" in html
    assert "业务分析" in html
    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_workspace_context_escapes_session_metadata():
    html = build_workspace_context_html("售后<场景>", "会话&1")

    assert "chatbi-context-bar" in html
    assert "售后&lt;场景&gt;" in html
    assert "会话&amp;1" in html


def test_empty_state_uses_stable_layout_classes():
    html = build_empty_state_html()

    assert "chatbi-empty-state" in html
    assert "chatbi-suggestion-grid" not in html


def test_typewriter_chunks_preserve_text_order():
    chunks = list(iter_typewriter_chunks("abcdefg", chunk_size=3))

    assert chunks == ["abc", "def", "g"]
    assert "".join(chunks) == "abcdefg"


def test_typewriter_chunks_reject_invalid_chunk_size():
    chunks = list(iter_typewriter_chunks("abc", chunk_size=0))

    assert chunks == ["abc"]


def test_session_action_specs_use_icons_and_tooltips():
    specs = session_action_specs(is_pinned=False)

    assert [spec["action"] for spec in specs] == ["pin", "rename", "delete"]
    assert [spec["icon"] for spec in specs] == ["↑", "✎", "×"]
    assert specs[0]["help"] == "置顶会话"


def test_session_action_specs_toggle_pin_tooltip():
    specs = session_action_specs(is_pinned=True)

    assert specs[0]["help"] == "取消置顶"
