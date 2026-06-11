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
    assert "preview_ready" in client
    assert "preview_ready" in app
    assert "step_started" in app
    assert "step_completed" in app
    assert "result_ready" in app
    assert "answer_delta" in app
    assert "answer_completed" in app


def test_workflow_stays_open_until_answer_output_then_collapses():
    bubble = read(SRC / "components" / "MessageBubble.tsx")
    thought = read(SRC / "components" / "ThoughtProcess.tsx")

    assert "answerStarted" in bubble
    assert "const shouldCollapseThoughts = answerStarted || !message.is_streaming;" in bubble
    assert "collapseSignal" in thought
    assert "useState(collapseSignal && !hasError)" in thought
    assert "setCollapsed(true)" in thought


def test_streaming_answer_uses_single_sse_driven_renderer():
    app = read(SRC / "App.tsx")
    bubble = read(SRC / "components" / "MessageBubble.tsx")

    assert "TypewriterResult" not in bubble
    assert "<ResultRenderer content={displayContent}" in bubble
    assert "const displayContent" in bubble
    assert "content: `${item.content || ''}${result.delta}`" in app


def test_message_list_follows_streaming_output_until_user_scrolls_up():
    message_list = read(SRC / "components" / "MessageList.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "useLayoutEffect" in message_list
    assert "listRef" in message_list
    assert "contentRef" in message_list
    assert "ResizeObserver" in message_list
    assert "userPausedRef" in message_list
    assert "activeStreamingIdRef" in message_list
    assert "latestStreamingId" in message_list
    assert "streamingActiveRef" in message_list
    assert "if (!streamingActiveRef.current)" in message_list
    assert "scrollTop = list.scrollHeight" in message_list
    assert "onWheel={handleWheel}" in message_list
    assert 'className="message-list-content"' in message_list
    assert "overflow-anchor: none;" in css


def test_new_conversation_button_is_before_online_status():
    header = read(SRC / "components" / "ChatHeader.tsx")

    assert header.index('title="新建对话"') < header.index('className="online-dot"')


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
    assert "parseBlocks" in renderer
    assert "block.type === 'table'" in renderer
    assert "categoryColumnIndex" in renderer
    assert "echarts.init" in chart
    assert "ResizeObserver" in chart
    assert "chart.dispose()" in chart
    assert "chartRef" in chart
    assert "dataKey" in chart
    assert "}, []);" in chart


def test_result_renderer_formats_markdown_emphasis_and_lists():
    renderer = read(SRC / "components" / "ResultRenderer.tsx")
    table = read(SRC / "components" / "DataTable.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "renderInlineMarkdown" in renderer
    assert "text.split('**')" in renderer
    assert "<strong" in renderer
    assert "<h4" in renderer
    assert "<hr" in renderer
    assert "<ol" in renderer
    assert "<ul" in renderer
    assert "stripInlineMarkdown" in table
    assert "renderCellContent(cell)" in table
    assert ".result-renderer strong" in css
    assert ".result-renderer h4" in css
    assert ".result-renderer hr" in css
    assert ".result-renderer ol" in css
    assert "if (!line.trim()) return null" in renderer
    assert "orderedStart" in renderer
    assert "start={orderedStart}" in renderer
    assert "elapsed * 0.065" in read(SRC / "components" / "TypewriterResult.tsx")


def test_user_message_text_remains_readable_and_answer_spacing_is_compact():
    css = read(SRC / "styles" / "app.css")

    assert ".message.user .result-renderer p" in css
    assert "color: #ffffff;" in css
    assert "line-height: 1.7;" in css
    assert "margin: 0 0 10px;" in css


def test_workflow_steps_show_duration_and_polished_running_state():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "formatDuration" in thought_step
    assert "step.duration_ms" in thought_step
    assert "workflow-running-pulse" in thought_step
    assert "@keyframes workflowPulse" in css


def test_workflow_steps_use_clean_blue_green_state_palette():
    css = read(SRC / "styles" / "app.css")

    assert ".workflow-step.done .workflow-step-main" in css
    assert "background: #f0fdfa;" in css
    assert "border-color: #ccfbf1;" in css
    assert ".workflow-step.done .workflow-step-name" in css
    assert "color: #0f766e;" in css
    assert ".workflow-step.loading .workflow-step-main" in css
    assert "border-color: #bfdbfe;" in css
    assert ".workflow-step.loading .workflow-step-name" in css
    assert "color: #1d4ed8;" in css
    assert ".workflow-step.failed .workflow-step-main" in css
    assert "background: #fff1f2;" in css
    assert "border-color: #fecdd3;" in css
    assert ".workflow-step.failed .workflow-step-name" in css
    assert "color: #be123c;" in css


def test_workflow_steps_use_user_facing_chinese_names_and_descriptions():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    labels = read(SRC / "stepLabels.ts")

    assert "stepDisplay" in thought_step
    assert "display.name" in thought_step
    assert "display.description" in thought_step
    assert "生成查询语句" in labels
    assert "执行数据查询" in labels
    assert "组织分析结论" in labels
    assert "'llm'" in labels


def test_workflow_step_details_use_coze_style_readable_input_output_sections():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    detail = read(SRC / "components" / "StepDetail.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "StepDetail" in thought_step
    assert "<StepDetail step={step}" in thought_step
    assert "步骤说明" in detail
    assert "输入" in detail
    assert "输出" in detail
    assert "技术详情" in detail
    assert "problem_type" in detail
    assert "数据查询与分析" in detail
    assert "prompt_type" in detail
    assert "HIDDEN_FIELDS" in detail
    assert "<details" in detail
    assert "step-detail-tabs" in css
    assert "step-detail-card" in css
    assert "{step.llm_output && <pre>" not in thought_step
    assert "{step.mcp_input && <pre>" not in thought_step
    assert "{step.mcp_output && <pre>" not in thought_step


def test_workflow_step_detail_aligns_with_full_node_width():
    css = read(SRC / "styles" / "app.css")

    assert ".workflow-step-detail {\n  width: 100%;\n  margin: 0;" in css


def test_workflow_steps_show_expand_chevron_and_accessible_state():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "aria-expanded={open}" in thought_step
    assert 'className="workflow-step-chevron"' in thought_step
    assert ".workflow-step-chevron::before" in css
    assert ".workflow-step-chevron" in css
    assert ".workflow-step.open .workflow-step-chevron" in css
    assert "transform: rotate(90deg);" in css


def test_workflow_step_status_and_chevron_share_aligned_action_area():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    css = read(SRC / "styles" / "app.css")

    assert 'className="workflow-step-actions"' in thought_step
    assert ".workflow-step-actions {" in css
    assert "align-items: center;" in css
    assert ".workflow-step-chevron::before" in css
    assert 'className="workflow-step-chevron" aria-hidden="true" />' in thought_step


def test_messages_have_copy_button_with_transient_feedback():
    bubble = read(SRC / "components" / "MessageBubble.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "copyMessage" in bubble
    assert "navigator.clipboard.writeText(message.content)" in bubble
    assert "已复制" in bubble
    assert 'aria-label="复制消息"' in bubble
    assert ".message-copy-button" in css


def test_data_table_copies_tsv_for_excel():
    table = read(SRC / "components" / "DataTable.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "copyTable" in table
    assert ".join('\\t')" in table
    assert ".join('\\n')" in table
    assert "navigator.clipboard.writeText(tsv)" in table
    assert "复制表格" in table
    assert "已复制，可粘贴到 Excel" in table
    assert ".data-table-copy" in css


def test_workspace_has_three_primary_pages_and_history_routing():
    app = read(SRC / "App.tsx")
    shell = read(SRC / "components" / "AppShell.tsx")
    nav = read(SRC / "components" / "GlobalNav.tsx")
    routing = read(SRC / "useWorkspaceRoute.ts")

    assert "<AppShell" in app
    assert "智能问答" in nav
    assert "Skill 商店" in nav
    assert "系统管理" in nav
    assert "window.history.pushState" in routing
    assert "popstate" in routing
    assert "prototype-mode" in shell


def test_skill_management_has_search_workflow_schema_and_test_console():
    listing = read(SRC / "pages" / "SkillsPage.tsx")
    detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "Skill 管理" in listing
    assert "搜索 Skill" in listing
    assert "新建 Skill" in listing
    assert "skill-card" in listing
    assert "工作流" in detail
    assert "Schema" in detail
    assert "测试" in detail
    assert "添加步骤" in detail
    assert "运行测试" in detail
    assert "data_web_compare_analysis" in data
    assert "mcpTools" in data


def test_mcp_management_has_health_checks_masked_config_and_dependencies():
    listing = read(SRC / "pages" / "McpsPage.tsx")
    detail = read(SRC / "pages" / "McpDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "MCP 管理" in listing
    assert "全部健康检查" in listing
    assert "mcp-table" in listing
    assert "连接与配置" in detail
    assert "健康检查" in detail
    assert "敏感配置已加密保存" in detail
    assert "引用此 MCP 的 Skill" in detail
    assert "sql_executor" in data
    assert "knowledge_retrieval" in data


def test_management_pages_cross_link_skill_and_mcp_details():
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")

    assert "onNavigate(`/admin/mcps/${mcpName}`)" in skill_detail
    assert "onNavigate(`/admin/skills/${skill.name}`)" in mcp_detail


def test_vite_proxy_uses_dedicated_chatbi_api_port():
    vite_config = read(ROOT / "web_frontend" / "vite.config.ts")

    assert "'http://127.0.0.1:8001'" in vite_config
    assert "'http://127.0.0.1:8000'" not in vite_config


def test_skill_center_is_user_facing_store_with_install_and_demo():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")

    assert "Skill 商店" in center
    assert "发现、安装并体验适合你的 ChatBI 能力" in center
    assert "已安装" in center
    assert "获取" in center
    assert "这个 Skill 能为你做什么" in showcase
    assert "在真实问答页面中，它会这样工作" in showcase
    assert "可以直接这样问" in showcase
    assert "安装前检查" in showcase
    assert "立即体验" in showcase
    assert "chat-demo-thinking" in showcase
    assert "MCP 依赖" not in showcase
    assert "Schema" not in showcase


def test_skill_and_mcp_configuration_live_under_admin_routes():
    app = read(SRC / "App.tsx")
    nav = read(SRC / "components" / "GlobalNav.tsx")
    admin = read(SRC / "components" / "AdminNav.tsx")
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")

    assert "系统管理" in nav
    assert "/admin/skills" in nav
    assert "Skill 管理" in admin
    assert "MCP 管理" in admin
    assert "path === '/admin/skills'" in app
    assert "path === '/admin/mcps'" in app
    assert "onNavigate(`/admin/mcps/${mcpName}`)" in skill_detail
    assert "onNavigate(`/admin/skills/${skill.name}`)" in mcp_detail


def test_skill_store_uses_app_store_style_sections_and_compact_install_rows():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    nav = read(SRC / "components" / "GlobalNav.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "Skill 商店" in center
    assert "精选推荐" in center
    assert "热门 Skill" in center
    assert "我的 Skill" in center
    assert "skill-app-row" in center
    assert "获取" in center
    assert "打开" in center
    assert "Skill 商店" in nav
    assert ".skill-store-title h1" in css
    assert "font-size: 38px;" in css
    assert ".skill-app-row" in css


def test_skill_store_is_wide_readable_and_has_consistent_animated_actions():
    css = read(SRC / "styles" / "app.css")

    assert ".app-store-layout {\n  width: 100%;" in css
    assert "max-width: 1220px;" not in css
    assert ".store-install-button {\n  width: 76px;" in css
    assert ".editorial-visual i {" in css
    assert "animation: featuredIconFloat" in css
    assert "@keyframes featuredIconFloat" in css
    assert "@keyframes featuredChipOrbit" in css


def test_skill_store_uses_readable_supporting_text_sizes():
    css = read(SRC / "styles" / "app.css")

    assert ".editorial-card p { margin: 0; color: #53667f; font-size: 15px;" in css
    assert ".editorial-visual b {" in css
    assert "font-size: 11px;" in css
    assert ".skill-app-copy p { margin: 0 0 6px;" in css
    assert "font-size: 14px;" in css
    assert ".skill-app-copy span { color: #98a2b3; font-size: 12px;" in css
    assert ".store-install-button {" in css
    assert "font-size: 13px;" in css


def test_skill_store_has_no_dead_view_all_and_only_lists_installed_skills_at_bottom():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "查看全部" not in center
    assert "我的 Skill" in center
    assert "已安装到你的助手" in center
    assert "const installedSkills" in center
    assert "installedSkills.filter" in center
    assert "store-filter-row" not in center
    assert ".store-install-button:hover" in css
    assert "transform: translateY(-2px);" in css
    assert ".store-install-button:active" in css
    assert ".store-install-button:focus-visible" in css


def test_skill_store_uses_three_columns_on_wide_screens():
    css = read(SRC / "styles" / "app.css")

    assert "@media (min-width: 1500px)" in css
    assert ".popular-skill-list,\n  .all-skill-list" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in css


def test_skill_store_rows_do_not_show_rank_numbers():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "skill-rank" not in center
    assert "skill-rank" not in css
    assert "skillRow(skill, index + 1)" not in center


def test_skill_store_supports_market_discovery_and_installed_skill_management():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "marketCategories" in center
    assert "数据与分析" in center
    assert "知识与检索" in center
    assert "内容创作" in center
    assert "效率办公" in center
    assert "开发工具" in center
    assert "自动化" in center
    assert "发现更多 Skill" in center
    assert 'placeholder="搜索名称、场景或能力"' in center
    assert 'placeholder="搜索已安装 Skill"' in center
    assert "mySkillSort" in center
    assert "my-skill-toolbar" in css
    assert "market-discovery-bar" in css


def test_skill_showcase_uses_chatbi_demo_and_actionable_requirements():
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "chat-demo-window" in showcase
    assert "chat-demo-message user" in showcase
    assert "chat-demo-thinking" in showcase
    assert "chat-demo-result" in showcase
    assert "安装前检查" in showcase
    assert "需要你做什么" in showcase
    assert "requirement-check-card" in showcase
    assert ".chat-demo-window" in css
    assert ".requirement-check-card" in css


def test_data_table_renders_html_break_markers_as_real_line_breaks():
    table = read(SRC / "components" / "DataTable.tsx")

    assert "renderCellContent" in table
    assert "/<br\\s*\\/?>/gi" in table
    assert "<br key=" in table
    assert "normalizeCellText" in table


def test_workflow_steps_use_compact_single_column_layout():
    css = read(SRC / "styles" / "app.css")

    assert ".workflow-process {\n  width: 100%;" in css
    assert "width: min(100%, 620px);" not in css
    assert "grid-template-columns: minmax(0, 1fr);" in css
    assert "repeat(2, minmax(0, 1fr))" not in css
    assert ".workflow-step.done .workflow-step-description" in css
    assert "display: none;" in css


def test_stream_completion_keeps_transient_message_until_typewriter_finishes():
    app = read(SRC / "App.tsx")

    assert "refreshSessionList" in app
    assert "await refreshSessionList(activeSession.id)" in app
    assert "id: item.id" in app
