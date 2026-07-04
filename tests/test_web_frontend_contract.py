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


def test_frontend_client_defines_platform_api_entry_points_from_dev_doc():
    client = read(SRC / "api" / "client.ts")

    assert "login" in client
    assert "getCurrentAccount" in client
    assert "pending_action_skill" in client
    assert "pending_action_message" in client
    assert "pending_action_status" in client
    assert "listAccounts" in client
    assert "createAccount" in client
    assert "updateAccountPermissions" in client
    assert "listCapabilities" in client
    assert "getCapability" in client
    assert "listMyCapabilities" in client
    assert "listOrganizations" in client
    assert "getOrganizationPermissions" in client
    assert "updateOrganizationPermissions" in client
    assert "listAdminSkills" in client
    assert "listAdminAssets" in client
    assert "getAdminSkill" in client
    assert "testAdminSkill" in client
    assert "listAdminMcps" in client
    assert "getAdminMcp" in client
    assert "runAdminMcpHealthCheck" in client
    assert "listAdminRoles" in client
    assert "updateAdminRole" in client
    assert "getPlatformMetricsOverview" in client
    assert "getPlatformSkillMetrics" in client
    assert "getPlatformOrganizationMetrics" in client
    assert "listPlatformAlerts" in client
    assert "listActionGovernanceCases" in client
    assert "listPermissionAuditLogs" in client
    assert "'/api/capabilities'" in client
    assert "'/api/auth/login'" in client
    assert "'/api/admin/accounts'" in client
    assert "'/api/admin/assets'" in client
    assert "'/api/organizations'" in client
    assert "'/api/admin/metrics/overview'" in client
    assert "'/api/admin/action-governance'" in client


def test_login_page_and_app_auth_gate_protect_admin_routes():
    app = read(SRC / "App.tsx")
    login_page = read(SRC / "pages" / "LoginPage.tsx")
    shell = read(SRC / "components" / "AppShell.tsx")

    assert "LoginPage" in app
    assert "currentAccount" in app
    assert "api.login" in app
    assert "api.getCurrentAccount" in app
    assert "canAccessAdmin" in app
    assert "setCurrentAccount(null)" in app
    assert "账号登录" in login_page
    assert "platform_admin" in login_page
    assert "admin123" in login_page
    assert "currentAccount" in shell
    assert "退出登录" in shell


def test_app_hydrates_platform_mock_api_without_breaking_local_prototype_fallback():
    app = read(SRC / "App.tsx")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")

    assert "hydratePlatformPrototypeData" in app
    assert "api.listAdminAssets()" in app
    assert "api.listAdminSkills()" in app
    assert "api.listAdminMcps()" in app
    assert "api.listOrganizations()" in app
    assert "api.getPlatformMetricsOverview()" in app
    assert "api.getPlatformSkillMetrics()" in app
    assert "api.getPlatformOrganizationMetrics()" in app
    assert "api.listPlatformAlerts()" in app
    assert "api.listActionGovernanceCases()" in app
    assert "mergeSkillFromApi" in app
    assert "mergeMcpFromApi" in app
    assert "adminAssetsFromApi" in app
    assert "catch(() => undefined)" in app
    assert "setAssetDirectoryState" in app
    assert "setSkills((items)" in app
    assert "setMcps((items)" in app
    assert "setOrganizationProfiles" in app
    assert "setPlatformMetricsState" in app
    assert "setPlatformSkillMetricsState" in app
    assert "setPlatformOrganizationMetricsState" in app
    assert "setPlatformAlertsState" in app
    assert "setActionGovernanceCasesState" in app
    assert "organizationProfiles={organizationProfiles}" in app
    assert "platformMetrics={platformMetricsState}" in app
    assert "platformSkillMetrics={platformSkillMetricsState}" in app
    assert "platformOrganizationMetrics={platformOrganizationMetricsState}" in app
    assert "platformAlerts={platformAlertsState}" in app
    assert "actionGovernanceCases={actionGovernanceCasesState}" in app
    assert "assets={assetDirectoryState}" in app
    assert "organizationProfiles.map" in review_page
    assert "platformMetrics.monthlyActiveUsers" in release_page
    assert "platformMetrics.monthlyActiveUsers" in workbench


def test_organization_permission_page_saves_profile_changes_through_api():
    app = read(SRC / "App.tsx")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")

    assert "saveAccountPermissions" in app
    assert "createAccount" in app
    assert "api.createAccount" in app
    assert "api.updateAccountPermissions" in app
    assert "setAccounts((items)" in app
    assert "saveOrganizationProfile" in app
    assert "api.updateOrganizationPermissions" in app
    assert "setOrganizationProfiles((items)" in app
    assert "onSaveProfile={saveOrganizationProfile}" in app
    assert "onSaveProfile" in review_page
    assert "授权变更已保存" in app
    assert "保存权限变更" in review_page
    assert "账号目录" in review_page
    assert "搜索账号" in review_page
    assert "组织筛选" in review_page
    assert "角色筛选" in review_page
    assert "每页 50 条" in review_page
    assert "批量授权" in review_page
    assert "权限详情" in review_page
    assert "动作型 Skill 闭环" in review_page
    assert "二次确认" in review_page
    assert "失败回溯" in review_page
    assert "审计轨迹" in review_page
    assert "actionGovernanceCases" in review_page
    assert "permissionAuditLogs" in review_page
    assert "auditTypeFilter" in review_page
    assert "auditWindow" in review_page
    assert "auditSearch" in review_page
    assert "viewMode === 'audit'" in review_page
    assert "filteredAuditLogs" in review_page
    assert "auditGroups" in review_page
    assert "最近 7 天" in review_page
    assert "全部类型" in review_page
    assert "权限审计中心" in review_page
    assert "按实体类型、时间范围和关键词追踪最近权限变更。" in review_page
    assert "创建账号抽屉" in review_page
    assert "账号权限" in review_page
    assert "创建账号" in review_page
    assert "账号基础信息" in review_page
    assert "初始 Skill 覆盖" in review_page
    assert "onCreateAccount" in review_page
    assert "账号目录表格" in review_page
    assert "权限来源" in review_page
    assert "permissionSources" in review_page
    assert "组织默认能力" in review_page
    assert "角色默认能力" in review_page
    assert "账号级开通" in review_page
    assert "有效 Skill 权限" in review_page
    assert "账号级覆盖" in review_page
    assert "角色模板" in review_page
    assert "roleDrafts" in review_page
    assert "toggleRoleDraftValue" in review_page
    assert "角色默认能力" in review_page
    assert "角色动作权限" in review_page
    assert "保存角色模板" in review_page
    assert "api.updateAdminRole(roleId, { openSkills, dataDomains, actionPermissions, canAccessAdmin })" in app
    assert "roleOptions = roleTemplates.map" in review_page
    assert "onSaveAccountPermissions" in review_page
    assert "nextApprovalMode" in review_page
    assert "bulkSkill" in review_page
    assert "bulkMode" in review_page
    assert "onBulkGrantSkills" in review_page
    assert "onBulkDenySkills" in review_page
    assert "onExportPermissionReport" in review_page
    assert "onBulkGrantSkills={bulkGrantSkills}" in app
    assert "onBulkDenySkills={bulkDenySkills}" in app
    assert "onExportPermissionReport={exportPermissionReport}" in app
    assert "onSaveRoleTemplate={saveRoleTemplate}" in app
    assert "api.listPermissionAuditLogs()" in app
    assert "Promise.all" in app
    assert "new Blob" in app
    assert "URL.createObjectURL" in app
    assert "permission-report-" in app
    assert "selectedIds.length === 0" in review_page
    assert "批量开通所选能力" in review_page
    assert "批量禁用所选能力" in review_page
    assert "导出权限清单" in review_page
    assert "selectedIds.length > 0 ? accounts.filter" in review_page
    assert "组织树视图" in review_page
    assert "viewMode === 'organization'" in review_page
    assert "按组织汇总账号、角色与默认能力范围" in review_page
    assert "organizationDrafts" in review_page
    assert "toggleOrganizationDraftValue" in review_page
    assert "默认能力配置" in review_page
    assert "数据域权限" in review_page
    assert "动作权限" in review_page
    assert "保存组织策略" in review_page
    assert "api.updateOrganizationPermissions(organizationId, { approvalMode, openSkills, dataDomains, actionPermissions })" in app
    css = read(SRC / "styles" / "app.css")
    assert "permission-console" in css
    assert "directory-toolbar" in css
    assert "account-directory-table" in css
    assert "permission-drawer" in css
    assert "bulk-action-bar" in css
    assert "account-create-panel" in css
    assert "permission-summary-strip" in css
    assert "organization-tree-grid" in css
    assert "bulk-editor" in css
    assert "organization-policy-editor" in css
    assert "permission-audit-list" in css
    assert "permission-audit-console" in css
    assert "permission-audit-toolbar" in css
    assert "permission-audit-group" in css


def test_admin_redesign_uses_unified_asset_directory_and_stage_driven_detail_views():
    app = read(SRC / "App.tsx")
    nav = read(SRC / "components" / "AdminNav.tsx")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")
    management_data = read(SRC / "managementData.ts")
    css = read(SRC / "styles" / "app.css")

    assert "AssetType" in management_data
    assert "LifecycleStage" in management_data
    assert "UnifiedAssetRecord" in management_data
    assert "buildUnifiedAssets" in management_data
    assert "stageLabel" in management_data
    assert "review_rejected" in management_data
    assert "operationsCenter" in management_data
    assert "assetDirectory" in app
    assert "buildUnifiedAssets(skills, mcps, opsTasks)" in app
    assert "path === '/admin/assets'" in app
    assert "path === '/admin/pipeline'" in app
    assert "path === '/admin/operations-center'" in app
    assert "统一目录" in nav
    assert "发布流水线" in nav
    assert "运行与权限" in nav
    assert "我的待处理事项" in workbench
    assert "继续处理" in workbench
    assert "统一目录" in workbench
    assert "影响组织与风险提示" in skill_detail
    assert "阶段状态" in skill_detail
    assert "测试 → 提审 → 发布" in skill_detail
    assert "当前阶段主操作" in skill_detail
    assert "提审资料" in skill_detail
    assert "发布检查清单" in skill_detail
    assert "影响组织与风险提示" in mcp_detail
    assert "阶段状态" in mcp_detail
    assert "当前阶段主操作" in mcp_detail
    assert "依赖影响" in mcp_detail
    assert "发布前治理配置" in review_page
    assert "跨对象总览" in release_page
    assert "asset-directory-page" in css
    assert "lifecycle-stage-strip" in css
    assert "asset-stage-panel" in css
    assert "workbench-task-list" in css


def test_unified_asset_directory_prioritizes_actionable_skill_and_mcp_records():
    management_data = read(SRC / "managementData.ts")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")
    asset_directory = read(SRC / "pages" / "AssetDirectoryPage.tsx")
    drawer = read(SRC / "components" / "TaskDetailDrawer.tsx")

    assert "global_policy_watch" in management_data
    assert "channel_inventory_diagnosis" in management_data
    assert "inventory_snapshot_mcp" in management_data
    assert "lifecycleStagePriority" in management_data
    assert "buildLifecycleMetrics" in management_data
    assert "lifecycleStageOptions" in management_data
    assert "taskLifecycleStage" in management_data
    assert "left.type === 'mcp' ? -1 : 1" in management_data
    assert "buildLifecycleMetrics(assets)" in asset_directory
    assert "lifecycleStageOptions.map" in asset_directory
    assert "taskLifecycleStage(task)" in workbench
    assert "stageLabel[taskLifecycleStage(task)]" in workbench
    assert "taskLifecycleStage(task)" in drawer
    assert "stageLabel[taskLifecycleStage(task)]" in drawer
    assert "resolveTaskRoute" in workbench
    assert "task.entityName === skill.name" in workbench
    assert "task.entityName === mcp.name" in workbench
    assert "onNavigate(resolveTaskRoute(task))" in workbench


def test_skill_and_mcp_detail_pages_share_lifecycle_overview_component():
    management_ui = read(SRC / "components" / "ManagementUi.tsx")
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")
    management_data = read(SRC / "managementData.ts")
    doc = read(ROOT / "doc" / "广汽集团AI一体化平台_开发文档.md")

    assert "LifecycleOverviewPanel" in management_ui
    assert "summaryTitle" in management_ui
    assert "stageSteps" in management_ui
    assert "focusAreas" in management_ui
    assert "LifecycleOverviewPanel" in skill_detail
    assert "LifecycleOverviewPanel" in mcp_detail
    assert "lifecycleStageForReleaseStatus" in management_data
    assert "lifecycleActionByStage" in management_data
    assert "tasksForAsset" in management_data
    assert "tasksForAsset('skill', skill.name, skill.displayName, tasks)" in skill_detail
    assert "lifecycleStageForReleaseStatus(skill.releaseStatus, failureSummary)" in skill_detail
    assert "lifecycleActionByStage[currentStage]" in skill_detail
    assert "lifecycleStageForReleaseStatus(mcp.releaseStatus, mcp.blockedBy)" in mcp_detail
    assert "lifecycleActionByStage[currentStage]" in mcp_detail
    assert "task.parentTaskId && directTaskIds.has(task.parentTaskId)" in management_data
    assert "- [x] 统一目录与单详情页主流程重构" in doc
    assert "- [x] 将 Skill/MCP 详情页的阶段逻辑抽到统一状态工具" in doc
    assert "- [x] 将工作台、统一目录、详情页全部改为复用同一套生命周期状态工具" in doc
    assert "- [x] 接入真实统一资产 API" in doc
    assert "- [x] 为统一资产增加稳定字段" in doc


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
    message_list = read(SRC / "components" / "MessageList.tsx")
    app = read(SRC / "App.tsx")
    history = read(SRC / "components" / "HistoryCard.tsx")
    header = read(SRC / "components" / "ChatHeader.tsx")
    labels = read(SRC / "skillLabels.ts")

    assert "skillDisplayName(message.selected_skill)" in bubble
    assert "isActionSkillMessage" in bubble
    assert "需确认后提交" in bubble
    assert "确认提交" in bubble
    assert "取消" in bubble
    assert "onAction" in bubble
    assert "onAction={onAction}" in message_list
    assert "onAction={sendMessage}" in app
    assert "session.pending_action_status === 'pending_confirmation'" in history
    assert "待确认动作" in history
    assert "pending_action_message" in history
    assert "session?.pending_action_status === 'pending_confirmation'" in header
    assert "待确认动作" in header
    assert "同环比分析" in labels
    assert "内部数据与联网分析" in labels
    assert "请假申请" in labels
    assert "session.summary || '暂无对话内容'" in history
    assert "session.last_mode" not in history


def test_chat_input_guides_action_skill_requests_with_clear_placeholder():
    chat_input = read(SRC / "components" / "ChatInput.tsx")

    assert "placeholderText" in chat_input
    assert "发消息、发起流程或输入 / 选择技能" in chat_input


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


def test_skill_center_surfaces_enable_update_and_usage_visibility():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")

    assert "常用能力" in center
    assert "待更新能力" in center
    assert "MCP 调用排行" in center
    assert "已加入常用工作台" in center
    assert "查看更新" in library
    assert "组织授权生效后" in showcase
    assert "示例输入 / 输出" in showcase


def test_admin_workspace_exposes_workbench_generation_review_and_release_flow():
    app = read(SRC / "App.tsx")
    admin_nav = read(SRC / "components" / "AdminNav.tsx")
    skills_page = read(SRC / "pages" / "SkillsPage.tsx")
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcps_page = read(SRC / "pages" / "McpsPage.tsx")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")

    assert "AdminWorkbenchPage" in app
    assert "平台总览" in admin_nav
    assert "组织与权限" in admin_nav
    assert "平台运营" in admin_nav
    assert "AI 开发台" in skills_page
    assert "组织授权" in skills_page
    assert "平台运营" in skills_page
    assert "描述你想做什么 Skill" in skill_detail
    assert "AI 生成 Skill 草案" in skill_detail
    assert "一键测试" in skill_detail
    assert "阻塞原因" in mcps_page
    assert "技术预览" in skill_detail
    assert "待处理治理事项" in workbench
    assert "自动测试：" in workbench


def test_admin_workspace_exposes_skill_and_mcp_creation_wizards():
    app = read(SRC / "App.tsx")
    client = read(SRC / "api" / "client.ts")
    skill_creator = read(SRC / "pages" / "SkillCreatorPage.tsx")
    mcp_creator = read(SRC / "pages" / "McpCreatorPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "path === '/admin/skills/new'" in app
    assert "path === '/admin/mcps/new'" in app
    assert "api.createAdminSkill" in app
    assert "api.createAdminMcp" in app
    assert "createAdminMcp" in client
    assert "'/api/admin/mcps'" in client
    assert "新建 Skill 向导" in skill_creator
    assert "生成 Skill 草案" in skill_creator
    assert "创建并进入编排" in skill_creator
    assert "接入 MCP 向导" in mcp_creator
    assert "生成接入草案" in mcp_creator
    assert "创建并进入治理" in mcp_creator
    assert "creator-shell" in css
    assert "creator-preview-grid" in css


def test_mcp_detail_surfaces_release_readiness_dependency_impact_and_publish_gate():
    detail = read(SRC / "pages" / "McpDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "发布状态" in detail
    assert "待发布版本" in detail
    assert "引用影响" in detail
    assert "发布前检查" in detail
    assert "手动发布" in detail
    assert "recentActivities" in detail
    assert "最近治理记录" in detail
    assert "blocked_by_dependency" in data


def test_platform_details_surface_access_risk_gray_release_and_audit_context():
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")

    assert "业务能力说明" in skill_detail
    assert "recentActivities" in skill_detail
    assert "提交治理" in skill_detail
    assert "最近治理记录" in skill_detail
    assert "生成的 Skill 草案" in skill_detail
    assert "适用组织" in skill_detail
    assert "数据域权限" in skill_detail
    assert "动作权限" in skill_detail
    assert "skillGovernanceTags[skill.name]" in skill_detail
    assert "读写风险" in mcp_detail
    assert "发布与灰度" in mcp_detail
    assert "灰度范围" in mcp_detail
    assert "审计日志" in mcp_detail
    assert "高风险动作需审批" in mcp_detail
    assert "platformMetrics.monthlyActiveUsers" in workbench
    assert "platformMetrics.apiSuccessRate" in workbench
    assert "platformMetrics.coverageOrganizations" in workbench


def test_review_and_release_pages_exist_as_separate_operations_views():
    app = read(SRC / "App.tsx")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")

    assert "AdminReviewPage" in app
    assert "AdminReleasePage" in app
    assert "待处理授权事项" in review_page
    assert "组织授权矩阵" in review_page
    assert "待发布版本" in release_page
    assert "当前目录版本" in release_page
    assert "手动发布" in release_page
    assert "releaseActivities" in release_page
    assert "最近发布动作" in release_page


def test_legacy_admin_review_and_release_routes_remain_compatible_aliases():
    app = read(SRC / "App.tsx")
    admin_nav = read(SRC / "components" / "AdminNav.tsx")

    assert "path === '/admin/reviews'" in app
    assert "path === '/admin/releases'" in app
    assert "const isPermissionsActive" in admin_nav
    assert "const isOperationsActive" in admin_nav
    assert "path === '/admin/reviews'" in admin_nav
    assert "path === '/admin/releases'" in admin_nav


def test_skill_detail_uses_prompt_first_generation_and_test_flow():
    detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "描述你想做什么 Skill" in detail
    assert "让大模型生成" in detail
    assert "AI 生成 Skill 草案" in detail
    assert "测试这个 Skill" in detail
    assert "运行测试" in detail
    assert "skill-prompt-builder" in css
    assert "skill-simple-test" in css
    assert "关键文档" not in detail
    assert "Schema" not in detail


def test_skill_detail_simulates_action_skill_approval_confirmation_and_rollback():
    detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "isActionSkill" in detail
    assert "审批命中" in detail
    assert "二次确认" in detail
    assert "失败回退" in detail
    assert "审计输出" in detail
    assert "test-guard-grid" in css
    assert "test-guard-status" in css


def test_user_skill_pages_surface_update_feedback_usage_and_version_context():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")
    card = read(SRC / "components" / "SkillCard.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "最近 30 天成功率" in center
    assert "待更新能力" in center
    assert "最近使用" in center
    assert "版本信息" in showcase
    assert "开通后反馈" in showcase
    assert "平台基础能力" in showcase
    assert "查看更新" in card
    assert "skill-meta-board" in css
    assert "showcase-usage-grid" in css


def test_action_skills_surface_confirmation_and_rollback_context():
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")
    data = read(SRC / "managementData.ts")
    css = read(SRC / "styles" / "app.css")

    assert "请假申请" in data
    assert "actionSkillHint" in showcase
    assert "二次确认后提交" in showcase
    assert "失败回退" in showcase
    assert "showcase-action-guard" in css


def test_release_page_surfaces_publish_confirmation_and_version_diff_context():
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "发布确认" in release_page
    assert "版本差异" in release_page
    assert "回滚预案" in release_page
    assert "release-confirm-card" in css


def test_release_page_surfaces_cost_failure_and_alert_operation_views():
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "能力运营指标" in release_page
    assert "单次调用成本" in release_page
    assert "失败原因分布" in release_page
    assert "组织覆盖进展" in release_page
    assert "告警与审计" in release_page
    assert "最近发布动作" in release_page
    assert "alert.level" in release_page
    assert "platformSkillMetrics.failureReasons" in release_page
    assert "platformOrganizationMetrics.organizationItems" in release_page
    assert "operations-insight-grid" in css
    assert "alert-list-card" in css


def test_release_page_has_publish_filters_diff_preview_and_checklist():
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "全部待发布" in release_page
    assert "Skill 发布" in release_page
    assert "MCP 发布" in release_page
    assert "差异预览" in release_page
    assert "发布检查清单" in release_page
    assert "onPublishTask" in release_page
    assert "release-filter-tabs" in css
    assert "release-diff-list" in css


def test_release_flow_records_skill_and_mcp_governance_activity():
    app = read(SRC / "App.tsx")
    skill_detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    mcp_detail = read(SRC / "pages" / "McpDetailPage.tsx")
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")
    workbench = read(SRC / "pages" / "AdminWorkbenchPage.tsx")
    drawer = read(SRC / "components" / "TaskDetailDrawer.tsx")
    data = read(SRC / "managementData.ts")

    assert "releaseActivities" in app
    assert "appendReleaseActivity" in app
    assert "submitSkillGovernance" in app
    assert "approveGovernanceTask" in app
    assert "unblockDependentTasks" in app
    assert "runMcpHealthCheck" in app
    assert "publishGovernanceTask" in app
    assert "onSubmitGovernance={submitSkillGovernance}" in app
    assert "onApproveTask={approveGovernanceTask}" in app
    assert "onHealthCheck={runMcpHealthCheck}" in app
    assert "onPublish={publishGovernanceTask}" in app
    assert "onPublishTask={publishGovernanceTask}" in app
    assert "ReleaseActivity" in data
    assert "submitted_for_review" in data
    assert "review_approved" in data
    assert "published_to_catalog" in data
    assert "health_check_passed" in data
    assert "dependency_unblocked" in data
    assert "recentActivities" in skill_detail
    assert "recentActivities" in mcp_detail
    assert "releaseActivities" in release_page
    assert "releaseActivities" in workbench
    assert "releaseActionLabel" in release_page
    assert "releaseActionLabel" in workbench
    assert "TaskDetailDrawer" in release_page
    assert "TaskDetailDrawer" in workbench
    assert "timeline-activity-button" in release_page
    assert "timeline-activity-button" in workbench
    assert "task-card-clickable" in release_page
    assert "task-card-clickable" in workbench
    assert "任务详情抽屉" in drawer
    assert "状态迁移原因" in drawer
    assert "最近动作" in drawer
    assert "审核通过，进入待发布" in review_page
    assert "onApproveTask(task)" in review_page
    assert "setOpsTasks" in app
    assert "upsertSkillReviewTask" in app
    assert "api.listGovernanceTasks()" in app
    assert "api.listReleaseActivities()" in app
    assert "api.submitSkillGovernance(skill.name)" in app
    assert "api.approveGovernanceTask(task.id)" in app
    assert "api.publishGovernanceTask(taskOrEntity.id)" in app
    assert "api.runAdminMcpHealthCheck(mcp.name)" in app
    assert "governanceTasksFromApi" in app
    assert "releaseActivitiesFromApi" in app


def test_skill_cards_and_store_surface_version_and_update_badges():
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    card = read(SRC / "components" / "SkillCard.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "最近更新" in library
    assert "最新版本" in card
    assert "updateAvailable" in card
    assert "skill-version-badge" in css


def test_management_data_models_parent_child_dependency_release_states():
    data = read(SRC / "managementData.ts")
    css = read(SRC / "styles" / "app.css")

    assert "updateAvailable" in data
    assert "enabledForUser" in data
    assert "usageCount30d" in data
    assert "releaseStatus" in data
    assert "blockedBy" in data
    assert "parentTaskId" in data
    assert "operationsTasks" in data
    assert ".workflow-step-chevron" in css
    assert ".workflow-step.open .workflow-step-chevron" in css
    assert "transform: rotate(90deg);" in css


def test_platform_prototype_data_models_support_governance_metrics_and_access():
    data = read(SRC / "managementData.ts")
    review_page = read(SRC / "pages" / "AdminReviewPage.tsx")
    release_page = read(SRC / "pages" / "AdminReleasePage.tsx")
    skills_page = read(SRC / "pages" / "SkillsPage.tsx")
    mcps_page = read(SRC / "pages" / "McpsPage.tsx")

    assert "organizationAccessProfiles" in data
    assert "platformMetrics" in data
    assert "skillGovernanceTags" in data
    assert "organizationName" in data
    assert "coverageOrganizations" in data
    assert "applicableOrganizations" in data
    assert "organizationProfiles.map" in review_page
    assert "platformMetrics.monthlyActiveUsers" in release_page
    assert "skillGovernanceTags[skill.name]" in skills_page
    assert "读写属性" in mcps_page


def test_workflow_step_status_and_chevron_share_aligned_action_area():
    thought_step = read(SRC / "components" / "ThoughtStep.tsx")
    css = read(SRC / "styles" / "app.css")

    assert 'className="workflow-step-actions"' in thought_step
    assert ".workflow-step-actions {" in css
    assert "align-items: center;" in css
    assert ".workflow-step-chevron::before" in css
    assert 'className="workflow-step-chevron" aria-hidden="true" />' in thought_step


def test_skill_center_focuses_on_installed_workspace_and_empty_state_guidance():
    page = read(SRC / "pages" / "SkillCenterPage.tsx")

    assert "浏览能力目录" in page
    assert "已开通能力" in page
    assert "全部 Skill" not in page
    assert "你还没有开通任何能力" in page
    assert "前往能力目录" in page
    assert "最近使用" in page


def test_skill_library_handles_install_feedback_without_reusing_my_skills_layout():
    page = read(SRC / "pages" / "SkillLibraryPage.tsx")
    app = read(SRC / "App.tsx")

    assert "重点推荐" in page
    assert "全部能力" in page
    assert "已开通" in page
    assert "未开通" in page
    assert "已安装" not in page
    assert "未安装" not in page
    assert "能力已开通，可以立即查看，或返回“能力中心”继续使用" in page
    assert "清空筛选" in page
    assert "recentlyInstalledSkillName" in app
    assert "setRecentlyInstalledSkillName(name)" in app


def test_showcase_page_returns_to_library_and_offers_install_decision_flow():
    page = read(SRC / "pages" / "SkillShowcasePage.tsx")

    assert "← 返回能力目录" in page
    assert "申请开通" in page
    assert "立即体验" in page
    assert "带着示例去提问" in page
    assert "这个 Skill 能为你做什么" in page


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
    assert "AI 助手" in nav
    assert "能力中心" in nav
    assert "平台治理" in nav
    assert "window.history.pushState" in routing
    assert "popstate" in routing
    assert "prototype-mode" in shell


def test_platform_shell_uses_group_ai_platform_branding():
    index = read(ROOT / "web_frontend" / "index.html")
    header = read(SRC / "components" / "ChatHeader.tsx")
    nav = read(SRC / "components" / "GlobalNav.tsx")
    message_list = read(SRC / "components" / "MessageList.tsx")

    assert "<title>广汽集团 AI 一体化平台</title>" in index
    assert "广汽集团 AI 助手" in header
    assert "统一 AI 门户" in header
    assert "AI 一体化平台" in nav
    assert "能力工作台" in nav
    assert "你好，我是广汽集团 AI 助手" in message_list
    assert "广汽国际 AI 助手" not in index
    assert "广汽国际 AI 助手" not in header
    assert "<strong>ChatBI</strong>" not in nav


def test_skill_management_has_search_workflow_schema_and_test_console():
    listing = read(SRC / "pages" / "SkillsPage.tsx")
    detail = read(SRC / "pages" / "SkillDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "Skill 编排" in listing
    assert "搜索 Skill" in listing
    assert "新建 Skill" in listing
    assert "skill-card" in listing
    assert "技术预览" in detail
    assert "生成的 Skill 草案" in detail
    assert "测试这个 Skill" in detail
    assert "添加步骤" not in detail
    assert "运行测试" in detail
    assert "data_web_compare_analysis" in data
    assert "mcpTools" in data


def test_mcp_management_has_health_checks_masked_config_and_dependencies():
    listing = read(SRC / "pages" / "McpsPage.tsx")
    detail = read(SRC / "pages" / "McpDetailPage.tsx")
    data = read(SRC / "managementData.ts")

    assert "MCP 治理" in listing
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


def test_skill_center_is_user_facing_installed_skill_home_with_store_entry():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")

    assert "能力中心" in center
    assert "浏览能力目录" in center
    assert "<h1>能力目录</h1>" not in center
    assert "精选推荐" not in center
    assert "热门 Skill" not in center
    assert "能力目录" in library
    assert "重点推荐" in library
    assert "这个 Skill 能为你做什么" in showcase
    assert "在真实问答页面中，它会这样工作" in showcase
    assert "可以直接这样问" in showcase
    assert "开通前检查" in showcase
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

    assert "平台治理" in nav
    assert "/admin/skills" in nav
    assert "Skill 编排" in admin
    assert "MCP 治理" in admin
    assert "path === '/admin/skills'" in app
    assert "path === '/admin/mcps'" in app
    assert "onNavigate(`/admin/mcps/${mcpName}`)" in skill_detail
    assert "onNavigate(`/admin/skills/${skill.name}`)" in mcp_detail


def test_skill_store_uses_app_store_style_sections_and_compact_install_rows():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    nav = read(SRC / "components" / "GlobalNav.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "能力中心" in center
    assert "SkillCard" in center
    assert "能力目录" in library
    assert "重点推荐" in library
    assert "能力中心" in nav
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


def test_skill_store_links_to_library_and_only_lists_installed_skills_at_bottom():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "浏览能力目录" in center
    assert "onNavigate('/skills/library')" in center
    assert "能力中心" in center
    assert "能力工作台" in center
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


def test_skill_store_keeps_discovery_simple_and_installed_skill_management_large():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "market-discovery-bar" not in center
    assert "market-category-grid" not in center
    assert 'placeholder="搜索名称、场景或能力"' not in center
    assert 'placeholder="搜索已开通能力"' in center
    assert "setSort" in center
    assert "my-skill-toolbar" in css
    assert ".my-skills-section" in css


def test_skill_library_has_workflow_cards_search_and_filters():
    app = read(SRC / "App.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "path === '/skills/library'" in app
    assert "SkillLibraryPage" in app
    assert "能力目录" in library
    assert "重点推荐" in library
    assert "热门 Skill" not in library
    assert 'placeholder="搜索能力名称、用途或业务场景"' in library
    assert "SkillCard" in library
    assert "library-filter-bar" in css
    assert ".library-skill-grid" in css
    assert ".library-skill-card" in css
    assert ".skill-library-page {\n  width: 100%;\n  height: 100%;\n  padding:" in css
    assert "overflow-y: auto;" in css
    assert "min-height: 292px;" not in css


def test_my_skill_usage_chart_replaces_summary_and_filtered_list_does_not_stretch():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "近 30 天使用次数" in center
    assert "usage-chart" in center
    assert "<span>数据与分析</span>" not in center
    assert "<span>最近更新</span>" not in center
    assert ".my-skill-home .all-skill-list { min-height:" not in css


def test_my_skill_home_shows_usage_visualization_and_four_column_cards():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "使用次数" in center
    assert "usage-chart" in center
    assert "usage-rank-fill" in center
    assert "已开通能力" in center
    assert "installedSkills.length" in center
    assert ".my-skill-home .all-skill-list" in css
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in css


def test_skill_store_uses_three_featured_and_four_column_value_cards():
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "slice(0, 3)" in library
    assert "SkillCard" in library
    assert "工作流步骤" not in library
    assert "library-workflow-preview" not in library
    assert ".library-editorial-grid" in css
    assert ".library-skill-grid" in css
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in css


def test_skill_cards_are_shared_with_consistent_install_status_and_interaction():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    card = read(SRC / "components" / "SkillCard.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "SkillCard" in center
    assert "SkillCard" in library
    assert "已开通" in card
    assert "未开通" in card
    assert "skill-status ${" in card
    assert "'installed' : 'uninstalled'" in card
    assert ".skill-status.installed" in css
    assert ".skill-status.uninstalled" in css


def test_usage_chart_is_ranked_horizontal_and_store_filters_are_compact():
    center = read(SRC / "pages" / "SkillCenterPage.tsx")
    library = read(SRC / "pages" / "SkillLibraryPage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "usage-ranking" in center
    assert "usage-rank-fill" in center
    assert "usage-chart-bars" not in center
    assert "<span>能力分类</span>" not in library
    assert "<span>安装状态</span>" not in library
    assert "全部分类" in library
    assert "全部开通状态" in library
    assert ".library-filter-bar label > span" not in css


def test_skill_showcase_uses_chatbi_demo_and_actionable_requirements():
    showcase = read(SRC / "pages" / "SkillShowcasePage.tsx")
    css = read(SRC / "styles" / "app.css")

    assert "安装" not in showcase
    assert "启用" not in showcase
    assert "AI 助手" in showcase
    assert "授权生效后自动参与执行" in showcase
    assert "chat-demo-window" in showcase
    assert "chat-demo-message user" in showcase
    assert "chat-demo-thinking" in showcase
    assert "chat-demo-result" in showcase
    assert "开通前检查" in showcase
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
