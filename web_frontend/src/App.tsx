import { useEffect, useMemo, useRef, useState } from 'react';
import { AccountPermissionProfile, AdminAssetPayload, AdminRoleProfile, api, ChatMessage, ChatSession, PermissionAuditLog } from './api/client';
import { ChatHeader } from './components/ChatHeader';
import { ChatInput } from './components/ChatInput';
import { DeleteDialog } from './components/DeleteDialog';
import { HistoryPanel } from './components/HistoryPanel';
import { MessageList } from './components/MessageList';
import { RenameDialog } from './components/RenameDialog';
import { AppShell } from './components/AppShell';
import { ActionGovernanceCase, actionGovernanceCases, buildUnifiedAssets, initialMcps, initialReleaseActivities, initialSkills, McpDefinition, OperationsTask, operationsTasks, OrganizationAccessProfile, organizationAccessProfiles, PlatformAlert, platformAlerts, PlatformMetrics, platformMetrics, PlatformOrganizationMetrics, platformOrganizationMetrics, PlatformSkillMetrics, platformSkillMetrics, ReleaseActivity, SkillDefinition, UnifiedAssetRecord } from './managementData';
import { useWorkspaceRoute } from './useWorkspaceRoute';
import { SkillsPage } from './pages/SkillsPage';
import { SkillDetailPage } from './pages/SkillDetailPage';
import { McpsPage } from './pages/McpsPage';
import { McpDetailPage } from './pages/McpDetailPage';
import { SkillCenterPage } from './pages/SkillCenterPage';
import { SkillShowcasePage } from './pages/SkillShowcasePage';
import { SkillLibraryPage } from './pages/SkillLibraryPage';
import { AdminNav } from './components/AdminNav';
import { AdminWorkbenchPage } from './pages/AdminWorkbenchPage';
import { AdminReviewPage } from './pages/AdminReviewPage';
import { AdminReleasePage } from './pages/AdminReleasePage';
import { LoginPage } from './pages/LoginPage';
import { SkillCreatorPage } from './pages/SkillCreatorPage';
import { McpCreatorPage } from './pages/McpCreatorPage';
import { AssetDirectoryPage } from './pages/AssetDirectoryPage';

type ApiRecord = Record<string, unknown>;

const stringValue = (value: unknown) => typeof value === 'string' ? value : undefined;
const arrayOfStrings = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];

const mergeSkillFromApi = (skill: SkillDefinition, payload: ApiRecord): SkillDefinition => ({
  ...skill,
  displayName: stringValue(payload.displayName) || skill.displayName,
  description: stringValue(payload.description) || skill.description,
  category: stringValue(payload.category) || skill.category,
  outputType: stringValue(payload.outputType) || skill.outputType,
  releaseStatus: stringValue(payload.releaseStatus) as SkillDefinition['releaseStatus'] || skill.releaseStatus,
});

const mergeMcpFromApi = (mcp: McpDefinition, payload: ApiRecord): McpDefinition => ({
  ...mcp,
  displayName: stringValue(payload.displayName) || mcp.displayName,
  description: stringValue(payload.description) || mcp.description,
  category: stringValue(payload.category) || mcp.category,
  health: stringValue(payload.health) as McpDefinition['health'] || mcp.health,
  releaseStatus: stringValue(payload.releaseStatus) as McpDefinition['releaseStatus'] || mcp.releaseStatus,
});

const skillFromApi = (payload: ApiRecord): SkillDefinition | null => {
  const name = stringValue(payload.name);
  const displayName = stringValue(payload.displayName);
  if (!name || !displayName) return null;
  const outputType = stringValue(payload.outputType) || '文本 / 报告';
  const description = stringValue(payload.description) || '等待补充业务能力说明';
  return {
    name,
    displayName,
    description,
    category: stringValue(payload.category) || '未分类',
    outputType,
    status: 'draft',
    releaseStatus: stringValue(payload.releaseStatus) as SkillDefinition['releaseStatus'] || 'draft',
    mcpTools: arrayOfStrings(payload.mcpTools),
    steps: [{ name: 'draft_generation', description: '根据业务目标生成 Skill 草案', mcp: 'llm', arguments: '{{input.goal}}' }],
    examples: [description],
    installed: false,
    enabledForUser: false,
    featured: false,
    tagline: description,
    outcomes: ['生成业务能力草案', '进入治理与测试流程'],
    requirements: ['待补治理要求'],
    scenes: ['平台原型创建'],
    expectedOutput: [outputType],
    exampleOutput: description,
    usageCount30d: 0,
    successRate: '--',
    mcpUsageHeat: '低',
    latestVersion: 'v0.1.0-draft',
    publishedVersion: '--',
    updatedAt: '刚刚',
  };
};

const mcpFromApi = (payload: ApiRecord): McpDefinition | null => {
  const name = stringValue(payload.name);
  const displayName = stringValue(payload.displayName);
  if (!name || !displayName) return null;
  const description = stringValue(payload.description) || '等待补充连接说明';
  return {
    name,
    displayName,
    description,
    category: stringValue(payload.category) || 'Utility',
    status: 'draft',
    releaseStatus: stringValue(payload.releaseStatus) as McpDefinition['releaseStatus'] || 'draft',
    health: stringValue(payload.health) as McpDefinition['health'] || 'unchecked',
    latency: '--',
    source: '外部服务',
    usageCount30d: 0,
    publishedVersion: '--',
    latestVersion: 'v0.1.0-draft',
    config: [{ label: '接入来源', value: '外部服务' }],
    schema: { input: 'string · 待补调用参数', output: 'string · 待补返回结构' },
    updatedAt: '刚刚',
  };
};

const governanceTasksFromApi = (payload: unknown, fallback: OperationsTask[]): OperationsTask[] => (
  Array.isArray(payload)
    ? payload
      .filter((item): item is ApiRecord => typeof item === 'object' && item !== null)
      .map((item, index) => ({
        id: stringValue(item.id) || `task-${index}`,
        title: stringValue(item.title) || '未命名任务',
        type: stringValue(item.type) === 'mcp' ? 'mcp' : 'skill',
        entityName: stringValue(item.entityName) || 'unknown',
        priority: stringValue(item.priority) === 'P0' || stringValue(item.priority) === 'P2' ? stringValue(item.priority) as OperationsTask['priority'] : 'P1',
        stage: stringValue(item.stage) as OperationsTask['stage'] || 'draft',
        owner: stringValue(item.owner) || '平台管理员',
        updatedAt: stringValue(item.updatedAt) || '刚刚',
        summary: stringValue(item.summary) || '待补任务摘要',
        blockedBy: stringValue(item.blockedBy),
        parentTaskId: stringValue(item.parentTaskId),
        releaseStatus: stringValue(item.releaseStatus) as OperationsTask['releaseStatus'] || 'draft',
        autoTestPassRate: stringValue(item.autoTestPassRate) || '待补',
        failureReason: stringValue(item.failureReason),
        reviewNotes: stringValue(item.reviewNotes),
      }))
    : fallback
);

const releaseActivitiesFromApi = (payload: unknown, fallback: ReleaseActivity[]): ReleaseActivity[] => (
  Array.isArray(payload)
    ? payload
      .filter((item): item is ApiRecord => typeof item === 'object' && item !== null)
      .map((item, index) => ({
        id: stringValue(item.id) || `release-${index}`,
        entityType: stringValue(item.entityType) === 'mcp' ? 'mcp' : 'skill',
        entityName: stringValue(item.entityName) || '未知实体',
        action: stringValue(item.action) as ReleaseActivity['action'] || 'submitted_for_review',
        operator: stringValue(item.operator) || '平台管理员',
        detail: stringValue(item.detail) || '待补动作说明',
        createdAt: stringValue(item.createdAt) || new Date().toISOString(),
      }))
    : fallback
);

const platformMetricsFromApi = (payload: ApiRecord, fallback: PlatformMetrics): PlatformMetrics => ({
  monthlyActiveUsers: typeof payload.monthlyActiveUsers === 'number' ? payload.monthlyActiveUsers : fallback.monthlyActiveUsers,
  apiSuccessRate: stringValue(payload.apiSuccessRate) || fallback.apiSuccessRate,
  topSkills: Array.isArray(payload.topSkills) ? payload.topSkills.filter((item): item is string => typeof item === 'string') : fallback.topSkills,
  coverageOrganizations: typeof payload.coverageOrganizations === 'number' ? payload.coverageOrganizations : fallback.coverageOrganizations,
  riskAlerts: Array.isArray(payload.riskAlerts) ? payload.riskAlerts.filter((item): item is string => typeof item === 'string') : fallback.riskAlerts,
});

const platformSkillMetricsFromApi = (payload: ApiRecord, fallback: PlatformSkillMetrics): PlatformSkillMetrics => ({
  topSkills: Array.isArray(payload.topSkills) ? payload.topSkills.filter((item): item is string => typeof item === 'string') : fallback.topSkills,
  averageCostPerCall: stringValue(payload.averageCostPerCall) || fallback.averageCostPerCall,
  failureReasons: Array.isArray(payload.failureReasons) ? payload.failureReasons.filter((item): item is string => typeof item === 'string') : fallback.failureReasons,
  recommendation: stringValue(payload.recommendation) || fallback.recommendation,
});

const platformOrganizationMetricsFromApi = (payload: ApiRecord, fallback: PlatformOrganizationMetrics): PlatformOrganizationMetrics => ({
  coverageOrganizations: typeof payload.coverageOrganizations === 'number' ? payload.coverageOrganizations : fallback.coverageOrganizations,
  organizationItems: Array.isArray(payload.organizationItems)
    ? payload.organizationItems
      .filter((item): item is ApiRecord => typeof item === 'object' && item !== null)
      .map((item) => ({
        organizationName: stringValue(item.organizationName) || '未知组织',
        coverageRate: stringValue(item.coverageRate) || '--',
        activeUsers: typeof item.activeUsers === 'number' ? item.activeUsers : 0,
      }))
    : fallback.organizationItems,
});

const platformAlertsFromApi = (payload: unknown, fallback: PlatformAlert[]): PlatformAlert[] => (
  Array.isArray(payload)
    ? payload
      .filter((item): item is ApiRecord => typeof item === 'object' && item !== null)
      .map((item, index) => ({
        id: stringValue(item.id) || `alert-${index}`,
        level: stringValue(item.level) === 'critical' || stringValue(item.level) === 'info' ? stringValue(item.level) as PlatformAlert['level'] : 'warning',
        message: stringValue(item.message) || '待补告警说明',
        source: stringValue(item.source) || '平台治理',
        updatedAt: stringValue(item.updatedAt) || '刚刚',
      }))
    : fallback
);

const actionGovernanceCasesFromApi = (payload: unknown, fallback: ActionGovernanceCase[]): ActionGovernanceCase[] => (
  Array.isArray(payload)
    ? payload
      .filter((item): item is ApiRecord => typeof item === 'object' && item !== null)
      .map((item, index) => ({
        id: stringValue(item.id) || `action-${index}`,
        skillName: stringValue(item.skillName) || '未知动作能力',
        organizationName: stringValue(item.organizationName) || '未知组织',
        approvalStatus: stringValue(item.approvalStatus) === '已通过' || stringValue(item.approvalStatus) === '已回退' ? stringValue(item.approvalStatus) as ActionGovernanceCase['approvalStatus'] : '待审批',
        confirmationRule: stringValue(item.confirmationRule) || '待补二次确认规则',
        rollbackStatus: stringValue(item.rollbackStatus) || '待补失败回溯策略',
        auditTrail: Array.isArray(item.auditTrail) ? item.auditTrail.filter((entry): entry is string => typeof entry === 'string') : [],
      }))
    : fallback
);

const adminAssetsFromApi = (payload: unknown, fallback: UnifiedAssetRecord[]): UnifiedAssetRecord[] => (
  Array.isArray(payload)
    ? payload
      .filter((item): item is AdminAssetPayload => typeof item === 'object' && item !== null)
      .map((item, index) => ({
        id: stringValue(item.asset_id) || `asset-${index}`,
        type: stringValue(item.asset_type) === 'mcp' ? 'mcp' : 'skill',
        name: stringValue(item.name) || 'unknown',
        displayName: stringValue(item.display_name) || '未命名资产',
        description: stringValue(item.description) || '待补能力说明',
        category: stringValue(item.category) || '未分类',
        status: (stringValue(item.status) as UnifiedAssetRecord['status']) || 'draft',
        releaseStatus: (stringValue(item.release_status) as UnifiedAssetRecord['releaseStatus']) || 'draft',
        lifecycleStage: (stringValue(item.current_stage) as UnifiedAssetRecord['lifecycleStage']) || 'draft',
        updatedAt: stringValue(item.updated_at) || '刚刚',
        owner: stringValue(item.owner) || '平台管理员',
        dependencySummary: stringValue(item.dependency_status) || '待补依赖摘要',
        failureSummary: stringValue(item.failure_summary),
        riskLabel: `风险：${stringValue(item.risk_level) || '中'}`,
        organizationSummary: stringValue(item.organization_summary) || '待配置组织范围',
        route: stringValue(item.action_url) || '/admin/assets',
      }))
    : fallback
);

function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [historyCollapsed, setHistoryCollapsed] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [renameTarget, setRenameTarget] = useState<ChatSession | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ChatSession | null>(null);
  const [skills, setSkills] = useState<SkillDefinition[]>(initialSkills);
  const [mcps, setMcps] = useState<McpDefinition[]>(initialMcps);
  const [organizationProfiles, setOrganizationProfiles] = useState<OrganizationAccessProfile[]>(organizationAccessProfiles);
  const [accounts, setAccounts] = useState<AccountPermissionProfile[]>([]);
  const [roles, setRoles] = useState<AdminRoleProfile[]>([]);
  const [permissionAuditLogs, setPermissionAuditLogs] = useState<PermissionAuditLog[]>([]);
  const [currentAccount, setCurrentAccount] = useState<AccountPermissionProfile | null>(null);
  const [loginError, setLoginError] = useState('');
  const [platformMetricsState, setPlatformMetricsState] = useState<PlatformMetrics>(platformMetrics);
  const [platformSkillMetricsState, setPlatformSkillMetricsState] = useState<PlatformSkillMetrics>(platformSkillMetrics);
  const [platformOrganizationMetricsState, setPlatformOrganizationMetricsState] = useState<PlatformOrganizationMetrics>(platformOrganizationMetrics);
  const [platformAlertsState, setPlatformAlertsState] = useState<PlatformAlert[]>(platformAlerts);
  const [releaseActivities, setReleaseActivities] = useState<ReleaseActivity[]>(initialReleaseActivities);
  const [actionGovernanceCasesState, setActionGovernanceCasesState] = useState<ActionGovernanceCase[]>(actionGovernanceCases);
  const [opsTasks, setOpsTasks] = useState<OperationsTask[]>(operationsTasks);
  const [assetDirectoryState, setAssetDirectoryState] = useState<UnifiedAssetRecord[]>(buildUnifiedAssets(initialSkills, initialMcps, operationsTasks));
  const [managementNotice, setManagementNotice] = useState('');
  const [skillTryText, setSkillTryText] = useState('');
  const [recentlyInstalledSkillName, setRecentlyInstalledSkillName] = useState('');
  const bootstrapped = useRef(false);
  const { path, navigate } = useWorkspaceRoute();

  const activeId = activeSession?.id;

  async function refreshSessions(nextActiveId?: string) {
    const nextSessions = await api.listSessions();
    setSessions(nextSessions);
    const target = nextSessions.find((item) => item.id === (nextActiveId || activeId)) || nextSessions[0] || null;
    if (target) {
      const detail = await api.getSession(target.id);
      setActiveSession(detail);
      setMessages(detail.messages || []);
      setWebSearchEnabled(detail.last_web_search_enabled || false);
    } else {
      setActiveSession(null);
      setMessages([]);
    }
  }

  async function refreshSessionList(nextActiveId?: string) {
    const nextSessions = await api.listSessions();
    setSessions(nextSessions);
    const target = nextSessions.find((item) => item.id === (nextActiveId || activeId));
    if (target) {
      setActiveSession((current) => current?.id === target.id ? { ...current, ...target } : current);
    }
  }

  async function createSession() {
    const session = await api.createSession('新对话');
    await refreshSessions(session.id);
  }

  async function hydratePlatformPrototypeData() {
    const [adminAssets, adminSkills, adminMcps, governanceTasks, governanceActivities] = await Promise.all([
      api.listAdminAssets(),
      api.listAdminSkills(),
      api.listAdminMcps(),
      api.listGovernanceTasks(),
      api.listReleaseActivities(),
    ]);
    const [organizations, metrics, skillMetricsPayload, organizationMetricsPayload, alertsPayload, actionGovernancePayload] = await Promise.all([
      api.listOrganizations(),
      api.getPlatformMetricsOverview(),
      api.getPlatformSkillMetrics(),
      api.getPlatformOrganizationMetrics(),
      api.listPlatformAlerts(),
      api.listActionGovernanceCases(),
    ]);
    const [nextAccounts, nextRoles, nextPermissionAuditLogs] = await Promise.all([api.listAccounts(), api.listAdminRoles(), api.listPermissionAuditLogs()]);
    const nextGovernanceTasks = governanceTasksFromApi(governanceTasks, operationsTasks);
    const mergedSkills = skills.map((item) => {
      const payload = adminSkills.find((skill) => stringValue(skill.name) === item.name);
      return payload ? mergeSkillFromApi(item, payload) : item;
    });
    const addedSkills = adminSkills
      .filter((skill) => !mergedSkills.some((item) => item.name === stringValue(skill.name)))
      .map((skill) => skillFromApi(skill))
      .filter((skill): skill is SkillDefinition => Boolean(skill));
    const nextSkills = [...addedSkills, ...mergedSkills];
    const mergedMcps = mcps.map((item) => {
      const payload = adminMcps.find((mcp) => stringValue(mcp.name) === item.name);
      return payload ? mergeMcpFromApi(item, payload) : item;
    });
    const addedMcps = adminMcps
      .filter((mcp) => !mergedMcps.some((item) => item.name === stringValue(mcp.name)))
      .map((mcp) => mcpFromApi(mcp))
      .filter((mcp): mcp is McpDefinition => Boolean(mcp));
    const nextMcps = [...addedMcps, ...mergedMcps];
    setSkills((items) => {
      const merged = items.map((item) => {
        const payload = adminSkills.find((skill) => stringValue(skill.name) === item.name);
        return payload ? mergeSkillFromApi(item, payload) : item;
      });
      const additions = adminSkills
        .filter((skill) => !merged.some((item) => item.name === stringValue(skill.name)))
        .map((skill) => skillFromApi(skill))
        .filter((skill): skill is SkillDefinition => Boolean(skill));
      return [...additions, ...merged];
    });
    setMcps((items) => {
      const merged = items.map((item) => {
        const payload = adminMcps.find((mcp) => stringValue(mcp.name) === item.name);
        return payload ? mergeMcpFromApi(item, payload) : item;
      });
      const additions = adminMcps
        .filter((mcp) => !merged.some((item) => item.name === stringValue(mcp.name)))
        .map((mcp) => mcpFromApi(mcp))
        .filter((mcp): mcp is McpDefinition => Boolean(mcp));
      return [...additions, ...merged];
    });
    setOpsTasks(nextGovernanceTasks);
    setAssetDirectoryState(adminAssetsFromApi(adminAssets, assetDirectory.length ? assetDirectory : buildUnifiedAssets(nextSkills, nextMcps, nextGovernanceTasks)));
    setReleaseActivities(releaseActivitiesFromApi(governanceActivities, initialReleaseActivities));
    setOrganizationProfiles(organizations);
    setAccounts(nextAccounts);
    setRoles(nextRoles);
    setPermissionAuditLogs(nextPermissionAuditLogs);
    setPlatformMetricsState(platformMetricsFromApi(metrics, platformMetrics));
    setPlatformSkillMetricsState(platformSkillMetricsFromApi(skillMetricsPayload, platformSkillMetrics));
    setPlatformOrganizationMetricsState(platformOrganizationMetricsFromApi(organizationMetricsPayload, platformOrganizationMetrics));
    setPlatformAlertsState(platformAlertsFromApi(alertsPayload, platformAlerts));
    setActionGovernanceCasesState(actionGovernanceCasesFromApi(actionGovernancePayload, actionGovernanceCases));
  }

  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;
    const accountId = window.localStorage.getItem('gac_ai_account_id');
    if (accountId) {
      api.getCurrentAccount(accountId).then(setCurrentAccount).catch(() => window.localStorage.removeItem('gac_ai_account_id'));
    }
    hydratePlatformPrototypeData().catch(() => undefined);
    refreshSessions().then(async () => {
      const latest = await api.listSessions();
      if (latest.length === 0) {
        await createSession();
      }
    }).catch((err) => setError(err.message));
  }, []);

  async function login(username: string, password: string) {
    try {
      setLoginError('');
      const result = await api.login(username, password);
      window.localStorage.setItem('gac_ai_account_id', result.token);
      setCurrentAccount(result.account);
      await hydratePlatformPrototypeData();
      if (path === '/login') navigate('/chat');
    } catch (err) {
      setLoginError(err instanceof Error ? '账号或密码错误' : '登录失败');
    }
  }

  async function logout() {
    await api.logout().catch(() => undefined);
    window.localStorage.removeItem('gac_ai_account_id');
    setCurrentAccount(null);
    setMessages([]);
    setActiveSession(null);
    navigate('/login');
  }

  async function selectSession(sessionId: string) {
    const detail = await api.getSession(sessionId);
    setActiveSession(detail);
    setMessages(detail.messages || []);
    setWebSearchEnabled(detail.last_web_search_enabled || false);
  }

  async function sendMessage(text: string) {
    if (!activeSession || !text.trim()) return;
    setIsSending(true);
    setError('');
    const optimisticUser: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      session_id: activeSession.id,
      role: 'user',
      content: text,
      web_search_enabled: webSearchEnabled,
      trace_open: false,
      created_at: new Date().toISOString(),
    };
    const optimisticAssistant: ChatMessage = {
      id: `temp-assistant-${Date.now()}`,
      session_id: activeSession.id,
      role: 'assistant',
      content: '',
      selected_skill: null,
      web_search_enabled: webSearchEnabled,
      trace_open: true,
      created_at: new Date().toISOString(),
      steps: [],
      stream_base: '',
      stream_text: '',
      answer_started: false,
      is_streaming: true,
    };
    setMessages((items) => [...items, optimisticUser, optimisticAssistant]);

    try {
      await api.chatStream(activeSession.id, text, webSearchEnabled, (event, data) => {
        if (event === 'message_created') {
          const userMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => item.id === optimisticUser.id ? userMessage : item));
        }
        if (event === 'step_started') {
          const step = data as NonNullable<ChatMessage['steps']>[number];
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id && !item.answer_started
              ? { ...item, steps: [...(item.steps || []).filter((existing) => existing.status !== 'running'), step] }
              : item
          )));
        }
        if (event === 'step_completed') {
          const step = data as NonNullable<ChatMessage['steps']>[number];
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? { ...item, steps: [...(item.steps || []).filter((existing) => existing.status !== 'running'), step] }
              : item
          )));
        }
        if (event === 'preview_ready') {
          const preview = data as { content: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  content: preview.content,
                  stream_base: preview.content,
                }
              : item
          )));
        }
        if (event === 'result_ready') {
          const result = data as { content: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  content: result.content,
                  stream_base: result.content,
                  answer_started: true,
                  steps: (item.steps || []).filter((existing) => existing.status !== 'running'),
                }
              : item
          )));
        }
        if (event === 'answer_delta') {
          const result = data as { delta: string };
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...item,
                  answer_started: true,
                  content: `${item.content || ''}${result.delta}`,
                  stream_text: `${item.stream_text || ''}${result.delta}`,
                }
              : item
          )));
        }
        if (event === 'answer_completed') {
          const assistantMessage = data as ChatMessage;
          setMessages((items) => items.map((item) => (
            item.id === optimisticAssistant.id
              ? {
                  ...assistantMessage,
                  id: item.id,
                  stream_base: item.stream_base,
                  stream_text: item.stream_text,
                  answer_started: true,
                  is_streaming: false,
                }
              : item
          )));
        }
        if (event === 'error') {
          const streamError = data as { message: string };
          throw new Error(streamError.message);
        }
      });
      await refreshSessionList(activeSession.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : '请求失败';
      setError(message);
      setMessages((items) => items.map((item) => (
        item.id === optimisticAssistant.id
          ? { ...item, content: `请求失败：${message}`, steps: [{ ...(item.steps?.[0] as any), status: 'failed', title: '执行错误', summary: message, error: message }] }
          : item
      )));
    } finally {
      setIsSending(false);
    }
  }

  async function renameSession(title: string) {
    if (!renameTarget) return;
    await api.updateSession(renameTarget.id, { title });
    setRenameTarget(null);
    await refreshSessions(renameTarget.id);
  }

  async function togglePin(session: ChatSession) {
    await api.updateSession(session.id, { is_pinned: !session.is_pinned });
    await refreshSessions(session.id);
  }

  async function deleteSession() {
    if (!deleteTarget) return;
    await api.deleteSession(deleteTarget.id);
    setDeleteTarget(null);
    await refreshSessions();
  }

  const emptyHint = useMemo(() => messages.length === 0, [messages]);
  const showcaseSkillName = path.startsWith('/skills/') ? decodeURIComponent(path.slice('/skills/'.length)) : '';
  const adminSkillName = path.startsWith('/admin/skills/') ? decodeURIComponent(path.slice('/admin/skills/'.length)) : '';
  const mcpName = path.startsWith('/admin/mcps/') ? decodeURIComponent(path.slice('/admin/mcps/'.length)) : '';
  const selectedShowcaseSkill = skills.find((skill) => skill.name === showcaseSkillName);
  const selectedSkill = skills.find((skill) => skill.name === adminSkillName);
  const selectedMcp = mcps.find((mcp) => mcp.name === mcpName);
  const assetDirectory = useMemo(() => buildUnifiedAssets(skills, mcps, opsTasks), [skills, mcps, opsTasks]);
  const notifyManagement = (text: string) => {
    setManagementNotice(text);
    window.setTimeout(() => setManagementNotice(''), 2400);
  };
  const updateSkill = (next: SkillDefinition) => setSkills((items) => items.map((item) => item.name === next.name ? next : item));
  const updateMcp = (next: McpDefinition) => setMcps((items) => items.map((item) => item.name === next.name ? next : item));
  const upsertSkillReviewTask = (skill: SkillDefinition) => {
    setOpsTasks((items) => {
      const existingIndex = items.findIndex((item) => item.type === 'skill' && (
        item.entityName === skill.name
        || item.entityName === skill.displayName
        || item.title.includes(skill.displayName)
      ));
      if (existingIndex >= 0) {
        return items.map((item, index) => index === existingIndex ? {
          ...item,
          stage: 'ready_for_review',
          releaseStatus: 'ready_for_review',
          blockedBy: undefined,
          failureReason: undefined,
          updatedAt: '刚刚',
          summary: `Skill ${skill.displayName} 已提交治理复核，等待人工确认。`,
          reviewNotes: item.reviewNotes || '请重点确认组织适用范围、示例输出与风险标签。',
        } : item);
      }
      return [{
        id: `skill-task-${Date.now()}`,
        title: `治理复核 ${skill.displayName} Skill`,
        type: 'skill',
        entityName: skill.name,
        priority: 'P1',
        stage: 'ready_for_review',
        releaseStatus: 'ready_for_review',
        owner: currentAccount?.displayName || '平台管理员',
        updatedAt: '刚刚',
        summary: `Skill ${skill.displayName} 已提交治理复核，等待人工确认。`,
        autoTestPassRate: '待补',
        reviewNotes: '请重点确认组织适用范围、示例输出与风险标签。',
      }, ...items];
    });
  };
  const approveGovernanceTask = async (task: OperationsTask) => {
    await api.approveGovernanceTask(task.id);
    await hydratePlatformPrototypeData();
    notifyManagement('治理任务已审核通过');
  };
  const unblockDependentTasks = (publishedTask: OperationsTask, entity: SkillDefinition | McpDefinition) => {
    const unlockedTasks = opsTasks.filter((item) => {
      const dependsOnParent = item.parentTaskId === publishedTask.id;
      const mentionsDependency = Boolean(item.blockedBy) && [
        entity.name,
        entity.displayName,
        publishedTask.entityName,
        publishedTask.title,
      ].some((keyword) => item.blockedBy?.includes(keyword));
      return (dependsOnParent || mentionsDependency) && item.releaseStatus === 'blocked_by_dependency';
    });
    if (unlockedTasks.length === 0) return;
    setOpsTasks((items) => items.map((item) => {
      const shouldUnlock = unlockedTasks.some((candidate) => candidate.id === item.id);
      if (!shouldUnlock) return item;
      return {
        ...item,
        stage: 'testing',
        releaseStatus: 'testing',
        blockedBy: undefined,
        failureReason: undefined,
        updatedAt: '刚刚',
        summary: `${item.type === 'skill' ? 'Skill' : 'MCP'} ${item.title} 的依赖已发布，自动恢复联调测试。`,
        reviewNotes: '依赖发布后已自动解锁，请继续执行联调与回归验证。',
      };
    }));
    if (publishedTask.parentTaskId) {
      const parentTask = opsTasks.find((item) => item.id === publishedTask.parentTaskId);
      if (parentTask?.type === 'skill') {
        const parentSkill = skills.find((skill) => (
          parentTask.entityName === skill.name
          || parentTask.entityName === skill.displayName
          || parentTask.title.includes(skill.displayName)
        ));
        if (parentSkill) {
          updateSkill({
            ...parentSkill,
            releaseStatus: 'testing',
            updatedAt: '刚刚',
          });
        }
      }
    }
    unlockedTasks.forEach((item) => appendReleaseActivity({
      entityType: item.type,
      entityName: item.title,
      action: 'dependency_unblocked',
      operator: currentAccount?.displayName || '平台管理员',
      detail: `${item.title} 因依赖 ${entity.displayName} 发布成功，已自动从依赖阻塞恢复到联调测试。`,
    }));
    notifyManagement(`已自动解锁 ${unlockedTasks.length} 个依赖任务，恢复联调测试`);
  };
  const markOpsTaskPublished = (entityType: 'skill' | 'mcp', entity: SkillDefinition | McpDefinition) => {
    setOpsTasks((items) => items.map((item) => {
      const matchesType = item.type === entityType;
      const matchesEntity = item.entityName === entity.name
        || item.entityName === entity.displayName
        || item.title.includes(entity.displayName);
      if (!matchesType || !matchesEntity) return item;
      return {
        ...item,
        stage: 'published',
        releaseStatus: 'published',
        blockedBy: undefined,
        failureReason: undefined,
        updatedAt: '刚刚',
        reviewNotes: item.reviewNotes || '发布动作已完成，记录已同步到治理台账。',
      };
    }));
  };
  const appendReleaseActivity = (activity: Omit<ReleaseActivity, 'id' | 'createdAt'>) => {
    setReleaseActivities((items) => [{
      ...activity,
      id: `release-${Date.now()}`,
      createdAt: new Date().toISOString(),
    }, ...items]);
  };
  const saveOrganizationProfile = async (profile: OrganizationAccessProfile, nextProfileDraft: OrganizationAccessProfile) => {
    const organizationId = profile.id || profile.organizationName;
    const { approvalMode, openSkills, dataDomains, actionPermissions } = nextProfileDraft;
    const nextProfile = await api.updateOrganizationPermissions(organizationId, { approvalMode, openSkills, dataDomains, actionPermissions });
    setOrganizationProfiles((items) => items.map((item) => {
      const sameOrganization = (item.id || item.organizationName) === organizationId;
      return sameOrganization ? { ...item, ...nextProfile } : item;
    }));
    setPermissionAuditLogs(await api.listPermissionAuditLogs());
    notifyManagement('授权变更已保存');
  };
  const saveAccountPermissions = async (account: AccountPermissionProfile, allowedSkills: string[], deniedSkills: string[]) => {
    const nextAccount = await api.updateAccountPermissions(account.id, { allowedSkills, deniedSkills });
    setAccounts((items) => items.map((item) => item.id === nextAccount.id ? nextAccount : item));
    setCurrentAccount((current) => current?.id === nextAccount.id ? nextAccount : current);
    setPermissionAuditLogs(await api.listPermissionAuditLogs());
    notifyManagement('账号级 Skill 权限已保存');
  };
  const bulkGrantSkills = async (accountIds: string[], skillName: string) => {
    const accountMap = new Map(accounts.map((account) => [account.id, account]));
    const updatedAccounts = await Promise.all(accountIds.map(async (accountId) => {
      const account = accountMap.get(accountId);
      if (!account) return null;
      const allowedSkills = account.allowedSkills.includes(skillName) ? account.allowedSkills : [...account.allowedSkills, skillName];
      const deniedSkills = account.deniedSkills.filter((item) => item !== skillName);
      return api.updateAccountPermissions(accountId, { allowedSkills, deniedSkills });
    }));
    const nextAccounts = updatedAccounts.filter((item): item is AccountPermissionProfile => Boolean(item));
    setAccounts((items) => items.map((item) => nextAccounts.find((next) => next.id === item.id) || item));
    setCurrentAccount((current) => current ? nextAccounts.find((item) => item.id === current.id) || current : current);
    notifyManagement(`已为 ${nextAccounts.length} 个账号批量开通能力`);
  };
  const bulkDenySkills = async (accountIds: string[], skillName: string) => {
    const accountMap = new Map(accounts.map((account) => [account.id, account]));
    const updatedAccounts = await Promise.all(accountIds.map(async (accountId) => {
      const account = accountMap.get(accountId);
      if (!account) return null;
      const allowedSkills = account.allowedSkills.filter((item) => item !== skillName);
      const deniedSkills = account.deniedSkills.includes(skillName) ? account.deniedSkills : [...account.deniedSkills, skillName];
      return api.updateAccountPermissions(accountId, { allowedSkills, deniedSkills });
    }));
    const nextAccounts = updatedAccounts.filter((item): item is AccountPermissionProfile => Boolean(item));
    setAccounts((items) => items.map((item) => nextAccounts.find((next) => next.id === item.id) || item));
    setCurrentAccount((current) => current ? nextAccounts.find((item) => item.id === current.id) || current : current);
    notifyManagement(`已为 ${nextAccounts.length} 个账号批量禁用能力`);
  };
  const exportPermissionReport = (items: AccountPermissionProfile[]) => {
    const rows = [
      ['账号ID', '用户名', '显示名称', '组织', '角色', '账号级开通', '账号级禁用', '有效Skill', '有效数据域', '有效动作权限', '可进入治理后台'],
      ...items.map((item) => [
        item.id,
        item.username,
        item.displayName,
        item.organizationName,
        item.roleNames.join(' / '),
        item.allowedSkills.join(' / '),
        item.deniedSkills.join(' / '),
        item.effectiveSkills.join(' / '),
        item.effectiveDataDomains.join(' / '),
        item.effectiveActionPermissions.join(' / '),
        item.canAccessAdmin ? '是' : '否',
      ]),
    ];
    const csv = `\ufeff${rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `permission-report-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    notifyManagement(`已导出 ${items.length} 条权限记录`);
  };
  const saveRoleTemplate = async (roleId: string, payload: AdminRoleProfile) => {
    const { openSkills, dataDomains, actionPermissions, canAccessAdmin } = payload;
    const nextRole = await api.updateAdminRole(roleId, { openSkills, dataDomains, actionPermissions, canAccessAdmin });
    setRoles((items) => items.map((item) => item.id === nextRole.id ? nextRole : item));
    const nextAccounts = await api.listAccounts();
    setAccounts(nextAccounts);
    setCurrentAccount((current) => current ? nextAccounts.find((item) => item.id === current.id) || current : current);
    setPermissionAuditLogs(await api.listPermissionAuditLogs());
    notifyManagement('角色模板已保存并已刷新账号权限');
  };
  const submitSkillGovernance = async (skill: SkillDefinition) => {
    await api.submitSkillGovernance(skill.name);
    await hydratePlatformPrototypeData();
    notifyManagement('Skill 已提交治理复核');
  };
  const runMcpHealthCheck = async (mcp: McpDefinition) => {
    await api.runAdminMcpHealthCheck(mcp.name);
    await hydratePlatformPrototypeData();
    notifyManagement('MCP 健康检查已完成');
  };
  const publishGovernanceTask = async (taskOrEntity: OperationsTask | SkillDefinition | McpDefinition) => {
    if ('type' in taskOrEntity) {
      await api.publishGovernanceTask(taskOrEntity.id);
      await hydratePlatformPrototypeData();
      notifyManagement('治理任务已发布');
      return;
    }
    const matchedTask = opsTasks.find((item) => {
      const matchesEntity = item.entityName === taskOrEntity.name || item.title.includes(taskOrEntity.displayName);
      const matchesType = 'schema' in taskOrEntity ? item.type === 'mcp' : item.type === 'skill';
      return matchesType && matchesEntity;
    });
    if (!matchedTask) return;
    await api.publishGovernanceTask(matchedTask.id);
    await hydratePlatformPrototypeData();
    notifyManagement('治理任务已发布');
  };
  const createAccount = async (payload: Partial<AccountPermissionProfile> & { password?: string }) => {
    const nextAccount = await api.createAccount(payload);
    setAccounts((items) => [...items, nextAccount]);
    notifyManagement('账号已创建，可继续配置 Skill 权限');
    return nextAccount;
  };
  const installSkill = (name: string) => {
    setSkills((items) => items.map((item) => item.name === name ? { ...item, installed: true, enabledForUser: false } : item));
    setRecentlyInstalledSkillName(name);
    notifyManagement('能力已开通到你的工作台');
  };
  const toggleSkillEnable = (name: string) => {
    setSkills((items) => items.map((item) => item.name === name ? { ...item, enabledForUser: !item.enabledForUser } : item));
    notifyManagement('常用工作台状态已更新');
  };
  const trySkill = (example: string) => {
    setSkillTryText(example);
    navigate('/chat');
  };
  const createSkillDraft = async (payload: Record<string, unknown>) => {
    const created = await api.createAdminSkill(payload);
    const name = stringValue(created.name) || stringValue(payload.name) || `skill_${Date.now()}`;
    const displayName = stringValue(created.displayName) || stringValue(payload.displayName) || '未命名 Skill';
    const description = stringValue(created.description) || stringValue(payload.description) || '等待补充业务能力说明';
    const category = stringValue(created.category) || stringValue(payload.category) || '数据分析';
    const outputType = stringValue(created.outputType) || stringValue(payload.outputType) || '文本 / 报告';
    const applicableOrganizations = arrayOfStrings(created.applicableOrganizations).length ? arrayOfStrings(created.applicableOrganizations) : arrayOfStrings(payload.applicableOrganizations);
    const nextSkill: SkillDefinition = {
      name,
      displayName,
      description,
      category,
      outputType,
      status: 'draft',
      releaseStatus: 'draft',
      mcpTools: ['llm'],
      steps: [{ name: 'draft_generation', description: '根据业务目标生成 Skill 草案', mcp: 'llm', arguments: '{{input.goal}}' }],
      examples: [description],
      installed: false,
      enabledForUser: false,
      featured: false,
      tagline: description,
      outcomes: ['生成业务能力草案', '进入治理与测试流程'],
      requirements: [applicableOrganizations.length ? `适用组织：${applicableOrganizations.join(' / ')}` : '待补组织授权'],
      scenes: ['平台原型创建'],
      expectedOutput: [outputType],
      exampleOutput: description,
      usageCount30d: 0,
      successRate: '--',
      mcpUsageHeat: '低',
      latestVersion: 'v0.1.0-draft',
      publishedVersion: '--',
      updatedAt: '刚刚',
    };
    setSkills((items) => items.some((item) => item.name === name) ? items.map((item) => item.name === name ? nextSkill : item) : [nextSkill, ...items]);
    notifyManagement('Skill 草案已创建');
    navigate(`/admin/skills/${name}`);
  };
  const createMcpDraft = async (payload: Record<string, unknown>) => {
    const created = await api.createAdminMcp(payload);
    const name = stringValue(created.name) || stringValue(payload.name) || `mcp_${Date.now()}`;
    const displayName = stringValue(created.displayName) || stringValue(payload.displayName) || '未命名 MCP';
    const description = stringValue(created.description) || stringValue(payload.description) || '等待补充连接说明';
    const category = stringValue(created.category) || stringValue(payload.category) || 'Utility';
    const source = stringValue(created.source) || stringValue(payload.source) || '外部服务';
    const targetSystem = stringValue(created.targetSystem) || stringValue(payload.targetSystem) || '待指定系统';
    const writesData = Boolean(created.writesData ?? payload.writesData);
    const nextMcp: McpDefinition = {
      name,
      displayName,
      description,
      category,
      status: 'draft',
      releaseStatus: 'draft',
      health: 'unchecked',
      latency: '--',
      source,
      usageCount30d: 0,
      publishedVersion: '--',
      latestVersion: 'v0.1.0-draft',
      config: [
        { label: '目标系统', value: targetSystem },
        { label: '接入来源', value: source },
        { label: '读写属性', value: writesData ? '读写受控' : '只读 / 查询' },
      ],
      schema: {
        input: 'string · 待补调用参数',
        output: 'string · 待补返回结构',
      },
      updatedAt: '刚刚',
    };
    setMcps((items) => items.some((item) => item.name === name) ? items.map((item) => item.name === name ? nextMcp : item) : [nextMcp, ...items]);
    notifyManagement('MCP 草案已创建');
    navigate(`/admin/mcps/${name}`);
  };

  let page = (
    <div className={`chat-workspace app-shell ${historyCollapsed ? 'history-collapsed' : ''}`}>
      <HistoryPanel
        sessions={sessions}
        activeSessionId={activeSession?.id}
        onNew={createSession}
        onSelect={selectSession}
        onRename={setRenameTarget}
        onDelete={setDeleteTarget}
        onTogglePin={togglePin}
      />
      <section className="assistant-panel-page">
        <ChatHeader
          session={activeSession}
          historyCollapsed={historyCollapsed}
          onToggleHistory={() => setHistoryCollapsed((collapsed) => !collapsed)}
          onNew={createSession}
        />
        {error && <div className="api-error">{error}</div>}
        <MessageList messages={messages} emptyHint={emptyHint} onAction={sendMessage} />
        <ChatInput
          disabled={isSending || !activeSession}
          webSearchEnabled={webSearchEnabled}
          onWebSearchChange={setWebSearchEnabled}
          onSend={sendMessage}
          initialText={skillTryText}
        />
      </section>
      {renameTarget && <RenameDialog session={renameTarget} onCancel={() => setRenameTarget(null)} onConfirm={renameSession} />}
      {deleteTarget && <DeleteDialog session={deleteTarget} onCancel={() => setDeleteTarget(null)} onConfirm={deleteSession} />}
    </div>
  );

  if (path === '/skills') page = <SkillCenterPage skills={skills} onNavigate={navigate} recentlyInstalledSkillName={recentlyInstalledSkillName} onSeenRecentlyInstalled={() => setRecentlyInstalledSkillName('')} onToggleEnable={toggleSkillEnable} />;
  if (path === '/skills/library') page = <SkillLibraryPage skills={skills} onNavigate={navigate} onInstall={installSkill} recentlyInstalledSkillName={recentlyInstalledSkillName} />;
  if (selectedShowcaseSkill) page = <SkillShowcasePage skill={selectedShowcaseSkill} onNavigate={navigate} onInstall={installSkill} onTry={trySkill} />;
  if (path === '/admin') page = <><AdminNav path={path} onNavigate={navigate} /><AdminWorkbenchPage tasks={opsTasks} skills={skills} mcps={mcps} platformMetrics={platformMetricsState} releaseActivities={releaseActivities} onNavigate={navigate} /></>;
  if (path === '/admin/assets') page = <><AdminNav path={path} onNavigate={navigate} /><AssetDirectoryPage assets={assetDirectoryState} onNavigate={navigate} onCreateSkill={() => navigate('/admin/skills/new')} onCreateMcp={() => navigate('/admin/mcps/new')} /></>;
  if (path === '/admin/pipeline') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReleasePage tasks={opsTasks} skills={skills} mcps={mcps} platformMetrics={platformMetricsState} platformSkillMetrics={platformSkillMetricsState} platformOrganizationMetrics={platformOrganizationMetricsState} platformAlerts={platformAlertsState} releaseActivities={releaseActivities} onPublishTask={publishGovernanceTask} /></>;
  if (path === '/admin/operations-center') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReviewPage tasks={opsTasks} accounts={accounts} roles={roles} skills={skills} organizationProfiles={organizationProfiles} actionGovernanceCases={actionGovernanceCasesState} permissionAuditLogs={permissionAuditLogs} onNavigate={navigate} onCreateAccount={createAccount} onSaveAccountPermissions={saveAccountPermissions} onSaveProfile={saveOrganizationProfile} onBulkGrantSkills={bulkGrantSkills} onBulkDenySkills={bulkDenySkills} onExportPermissionReport={exportPermissionReport} onSaveRoleTemplate={saveRoleTemplate} onApproveTask={approveGovernanceTask} /></>;
  if (path === '/admin/permissions') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReviewPage tasks={opsTasks} accounts={accounts} roles={roles} skills={skills} organizationProfiles={organizationProfiles} actionGovernanceCases={actionGovernanceCasesState} permissionAuditLogs={permissionAuditLogs} onNavigate={navigate} onCreateAccount={createAccount} onSaveAccountPermissions={saveAccountPermissions} onSaveProfile={saveOrganizationProfile} onBulkGrantSkills={bulkGrantSkills} onBulkDenySkills={bulkDenySkills} onExportPermissionReport={exportPermissionReport} onSaveRoleTemplate={saveRoleTemplate} onApproveTask={approveGovernanceTask} /></>;
  if (path === '/admin/reviews') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReviewPage tasks={opsTasks} accounts={accounts} roles={roles} skills={skills} organizationProfiles={organizationProfiles} actionGovernanceCases={actionGovernanceCasesState} permissionAuditLogs={permissionAuditLogs} onNavigate={navigate} onCreateAccount={createAccount} onSaveAccountPermissions={saveAccountPermissions} onSaveProfile={saveOrganizationProfile} onBulkGrantSkills={bulkGrantSkills} onBulkDenySkills={bulkDenySkills} onExportPermissionReport={exportPermissionReport} onSaveRoleTemplate={saveRoleTemplate} onApproveTask={approveGovernanceTask} /></>;
  if (path === '/admin/operations') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReleasePage tasks={opsTasks} skills={skills} mcps={mcps} platformMetrics={platformMetricsState} platformSkillMetrics={platformSkillMetricsState} platformOrganizationMetrics={platformOrganizationMetricsState} platformAlerts={platformAlertsState} releaseActivities={releaseActivities} onPublishTask={publishGovernanceTask} /></>;
  if (path === '/admin/releases') page = <><AdminNav path={path} onNavigate={navigate} /><AdminReleasePage tasks={opsTasks} skills={skills} mcps={mcps} platformMetrics={platformMetricsState} platformSkillMetrics={platformSkillMetricsState} platformOrganizationMetrics={platformOrganizationMetricsState} platformAlerts={platformAlertsState} releaseActivities={releaseActivities} onPublishTask={publishGovernanceTask} /></>;
  if (path === '/admin/skills') page = <><AdminNav path={path} onNavigate={navigate} /><SkillsPage skills={skills} tasks={opsTasks} onNavigate={navigate} onCreate={() => navigate('/admin/skills/new')} /></>;
  if (path === '/admin/skills/new') page = <><AdminNav path={path} onNavigate={navigate} /><SkillCreatorPage organizations={organizationProfiles} onNavigate={navigate} onCreate={createSkillDraft} /></>;
  if (selectedSkill) page = <><AdminNav path={path} onNavigate={navigate} /><SkillDetailPage skill={selectedSkill} tasks={opsTasks} recentActivities={releaseActivities.filter((item) => item.entityType === 'skill' && item.entityName === selectedSkill.displayName).slice(0, 4)} onNavigate={navigate} onUpdate={updateSkill} onSubmitGovernance={submitSkillGovernance} /></>;
  if (path === '/admin/mcps') page = <><AdminNav path={path} onNavigate={navigate} /><McpsPage mcps={mcps} skills={skills} onNavigate={navigate} onCreate={() => navigate('/admin/mcps/new')} onHealthCheck={() => { setMcps((items) => items.map((item) => item.status === 'disabled' ? item : { ...item, health: 'healthy', updatedAt: '刚刚' })); appendReleaseActivity({ entityType: 'mcp', entityName: '全部 MCP', action: 'health_check_passed', operator: currentAccount?.displayName || '平台管理员', detail: '已对全部启用中的 MCP 执行健康检查。' }); notifyManagement('全部健康检查已完成'); }} /></>;
  if (path === '/admin/mcps/new') page = <><AdminNav path={path} onNavigate={navigate} /><McpCreatorPage skills={skills} onNavigate={navigate} onCreate={createMcpDraft} /></>;
  if (selectedMcp) page = <><AdminNav path={path} onNavigate={navigate} /><McpDetailPage mcp={selectedMcp} skills={skills} recentActivities={releaseActivities.filter((item) => item.entityType === 'mcp' && item.entityName === selectedMcp.displayName).slice(0, 4)} onNavigate={navigate} onUpdate={updateMcp} onHealthCheck={runMcpHealthCheck} onPublish={publishGovernanceTask} /></>;

  if (!currentAccount) {
    return <LoginPage error={loginError} onLogin={login} />;
  }

  if (path.startsWith('/admin') && !currentAccount.canAccessAdmin) {
    page = <section className="management-page"><div className="panel-card"><h3>无平台治理权限</h3><p>当前账号没有进入平台治理的权限。请联系平台管理员调整角色或账号级授权。</p><button className="primary-action" type="button" onClick={() => navigate('/chat')}>返回 AI 助手</button></div></section>;
  }

  return (
    <AppShell path={path} currentAccount={currentAccount} onLogout={logout} onNavigate={navigate}>
      {page}
      {managementNotice && <div className="prototype-toast">{managementNotice}</div>}
    </AppShell>
  );
}

export default App;
