"""Small HTML builders for the Streamlit ChatBI interface."""

from __future__ import annotations

import html
from collections.abc import Iterator


def build_result_panel_html(title: str, body: str, variant: str = "default") -> str:
    """Build a stable assistant result panel shell with escaped content."""
    safe_title = html.escape(title)
    safe_body = html.escape(body)
    safe_variant = "".join(ch for ch in variant.lower() if ch.isalnum() or ch == "-") or "default"
    return (
        f"<section class='chatbi-result-panel chatbi-result-panel-{safe_variant}'>"
        f"<div class='chatbi-result-panel-title'>{safe_title}</div>"
        f"<div class='chatbi-result-panel-body'>{safe_body}</div>"
        "</section>"
    )


def build_workspace_context_html(theme: str, session_title: str) -> str:
    """Build the compact context bar shown above active conversations."""
    safe_theme = html.escape(theme)
    safe_session = html.escape(session_title)
    return (
        "<div class='chatbi-context-bar'>"
        "<span>当前场景</span>"
        f"<strong>{safe_theme}</strong>"
        "<span>当前会话</span>"
        f"<strong>{safe_session}</strong>"
        "</div>"
    )


def build_empty_state_html() -> str:
    """Build the home empty-state shell."""
    return (
        "<section class='chatbi-empty-state'>"
        "<h1>你在忙什么？</h1>"
        "<p>基于 SOP & MCP 双层引擎的智能数据助理，产销存指标对话与决策分析平台</p>"
        "<div class='chatbi-suggestion-grid'></div>"
        "</section>"
    )


def iter_typewriter_chunks(text: str, chunk_size: int = 4) -> Iterator[str]:
    """Yield text in stable chunks for Streamlit's write_stream."""
    if chunk_size < 1:
        chunk_size = len(text) or 1
    for start in range(0, len(text), chunk_size):
        yield text[start : start + chunk_size]
