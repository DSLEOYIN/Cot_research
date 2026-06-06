from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "web_frontend" / "src"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_history_panel_has_explicit_collapse_control():
    app = read(SRC / "App.tsx")
    header = read(SRC / "components" / "ChatHeader.tsx")

    assert "historyCollapsed" in app
    assert "history-collapsed" in app
    assert "onToggleHistory" in header
    assert 'aria-label={historyCollapsed ? "展开历史对话" : "收起历史对话"}' in header


def test_input_toolbar_only_contains_prototype_network_search_toggle():
    chat_input = read(SRC / "components" / "ChatInput.tsx")

    assert "network-search-toggle" in chat_input
    assert "network-search-icon" in chat_input
    assert "network-search-state" in chat_input
    assert "智能问答" not in chat_input
    assert "web-toggle-track" not in chat_input


def test_user_message_and_enabled_send_button_use_prototype_black_gradient():
    css = read(SRC / "styles" / "app.css")

    assert ".message.user .msg-content,\n.send-btn {" in css
    assert "background: linear-gradient(135deg, #252525 0%, #050505 100%);" in css
    assert ".network-search-toggle.active" in css


def test_frontend_consumes_live_sse_steps():
    app = read(SRC / "App.tsx")
    client = read(SRC / "api" / "client.ts")

    assert "chatStream" in client
    assert "step_completed" in app
    assert "answer_completed" in app


def test_frontend_displays_user_facing_skill_labels_and_conversation_summary():
    bubble = read(SRC / "components" / "MessageBubble.tsx")
    history = read(SRC / "components" / "HistoryCard.tsx")
    labels = read(SRC / "skillLabels.ts")

    assert "skillDisplayName(message.selected_skill)" in bubble
    assert "同环比分析" in labels
    assert "内部数据与联网分析" in labels
    assert "session.summary || '暂无对话内容'" in history
    assert "session.last_mode" not in history


def test_result_renderer_builds_and_disposes_echarts_for_numeric_tables():
    renderer = read(SRC / "components" / "ResultRenderer.tsx")
    chart = read(SRC / "components" / "EChartsPanel.tsx")

    assert "DataTable" in renderer
    assert "EChartsPanel" in renderer
    assert "buildChartData" in renderer
    assert "echarts.init" in chart
    assert "ResizeObserver" in chart
    assert "chart.dispose()" in chart
