export type ChatStep = {
  id: string;
  message_id: string;
  step_index: number;
  step_type: string;
  title: string;
  status: 'running' | 'completed' | 'failed';
  summary: string;
  mcp_name?: string | null;
  mcp_input?: string | null;
  mcp_output?: string | null;
  llm_output?: string;
  error?: string | null;
  duration_ms?: number | null;
  created_at: string;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  selected_skill?: string | null;
  web_search_enabled: boolean;
  trace_open: boolean;
  created_at: string;
  steps?: ChatStep[];
  stream_base?: string;
  stream_text?: string;
  answer_started?: boolean;
  is_streaming?: boolean;
};

export type ChatSession = {
  id: string;
  title: string;
  summary: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  last_mode?: string | null;
  last_web_search_enabled: boolean;
  pending_action_skill?: string | null;
  pending_action_message?: string | null;
  pending_action_status?: string | null;
  messages?: ChatMessage[];
};

export type CapabilitySummary = {
  name: string;
  displayName: string;
  category: string;
  description: string;
  outputType: string;
  applicableOrganizations?: string[];
  status?: string;
};

export type OrganizationPermissionProfile = {
  id?: string;
  organizationName: string;
  roleName: string;
  openSkills: string[];
  dataDomains: string[];
  actionPermissions: string[];
  approvalMode: string;
};

export type AccountPermissionProfile = {
  id: string;
  username: string;
  displayName: string;
  organizationId: string;
  organizationName: string;
  roleIds: string[];
  roleNames: string[];
  allowedSkills: string[];
  deniedSkills: string[];
  effectiveSkills: string[];
  effectiveDataDomains: string[];
  effectiveActionPermissions: string[];
  canAccessAdmin: boolean;
  permissionSources: {
    organization: {
      organizationName: string;
      openSkills: string[];
      dataDomains: string[];
      actionPermissions: string[];
    };
    roles: {
      roleName: string;
      openSkills: string[];
      dataDomains: string[];
      actionPermissions: string[];
    }[];
    accountOverride: {
      allowedSkills: string[];
      deniedSkills: string[];
    };
  };
};

export type AdminRoleProfile = {
  id: string;
  roleName: string;
  openSkills: string[];
  dataDomains: string[];
  actionPermissions: string[];
  canAccessAdmin: boolean;
};

export type LoginResponse = {
  token: string;
  account: AccountPermissionProfile;
};

export type EnvironmentStatus = {
  appMode: string;
  mockApiAvailable: boolean;
  isMockMode: boolean;
  defaultLoginRoute: string;
  demoAccounts: {
    username: string;
    displayName: string;
    passwordHint: string;
    canAccessAdmin: boolean;
  }[];
};

export type AdminSkillPayload = Record<string, unknown>;
export type AdminMcpPayload = Record<string, unknown>;
export type AdminAssetPayload = Record<string, unknown>;
export type AdminTaskPayload = Record<string, unknown>;
export type AdminAssetDetailPayload = {
  asset: AdminAssetPayload;
  detail: Record<string, unknown>;
  tasks: AdminTaskPayload[];
  activities: ReleaseActivityPayload[];
};
export type AdminAssetActionPayload = Record<string, unknown>;
export type PlatformMetricsPayload = Record<string, unknown>;
export type ActionGovernancePayload = Record<string, unknown>;
export type GovernanceTaskPayload = Record<string, unknown>;
export type ReleaseActivityPayload = Record<string, unknown>;
export type PermissionAuditLog = {
  id: number;
  entityType: string;
  entityId: string;
  entityName: string;
  changeSummary: string;
  createdAt: string;
};

export type ChatStreamEvent =
  | 'message_created'
  | 'step_started'
  | 'step_completed'
  | 'preview_ready'
  | 'result_ready'
  | 'answer_delta'
  | 'answer_completed'
  | 'error';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      const payload = await response.json() as { detail?: string | { code?: string; message?: string } };
      if (typeof payload.detail === 'string') {
        throw new Error(payload.detail || `HTTP ${response.status}`);
      }
      if (payload.detail && typeof payload.detail === 'object') {
        const code = payload.detail.code || `HTTP_${response.status}`;
        const message = payload.detail.message || `HTTP ${response.status}`;
        throw new Error(`${code}: ${message}`);
      }
    }
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request<void>('/api/auth/logout', { method: 'POST' }),
  getEnvironmentStatus: () => request<EnvironmentStatus>('/api/system/environment'),
  getCurrentAccount: (accountId: string) => request<AccountPermissionProfile>(`/api/auth/me?account_id=${encodeURIComponent(accountId)}`),
  listSessions: () => request<ChatSession[]>('/api/sessions'),
  createSession: (title?: string) =>
    request<ChatSession>('/api/sessions', { method: 'POST', body: JSON.stringify({ title }) }),
  getSession: (sessionId: string) => request<ChatSession>(`/api/sessions/${sessionId}`),
  updateSession: (sessionId: string, payload: Partial<Pick<ChatSession, 'title' | 'summary' | 'is_pinned'>>) =>
    request<ChatSession>(`/api/sessions/${sessionId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSession: (sessionId: string) => request<void>(`/api/sessions/${sessionId}`, { method: 'DELETE' }),
  chat: (session_id: string, message: string, web_search_enabled: boolean) =>
    request<{ user_message: ChatMessage; assistant_message: ChatMessage }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session_id, message, web_search_enabled }),
    }),
  listCapabilities: () => request<CapabilitySummary[]>('/api/capabilities'),
  getCapability: (skillId: string) => request<CapabilitySummary>(`/api/capabilities/${skillId}`),
  listMyCapabilities: () => request<CapabilitySummary[]>('/api/users/me/capabilities'),
  listOrganizations: () => request<OrganizationPermissionProfile[]>('/api/organizations'),
  getOrganizationPermissions: (orgId: string) => request<OrganizationPermissionProfile>(`/api/organizations/${orgId}/permissions`),
  updateOrganizationPermissions: (orgId: string, payload: Partial<OrganizationPermissionProfile>) =>
    request<OrganizationPermissionProfile>(`/api/organizations/${orgId}/permissions`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listAdminRoles: () => request<AdminRoleProfile[]>('/api/admin/roles'),
  updateAdminRole: (roleId: string, payload: Partial<AdminRoleProfile>) =>
    request<AdminRoleProfile>(`/api/admin/roles/${roleId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listAccounts: () => request<AccountPermissionProfile[]>('/api/admin/accounts'),
  createAccount: (payload: Partial<AccountPermissionProfile> & { password?: string }) =>
    request<AccountPermissionProfile>('/api/admin/accounts', { method: 'POST', body: JSON.stringify(payload) }),
  getAccountPermissions: (accountId: string) => request<AccountPermissionProfile>(`/api/admin/accounts/${accountId}/permissions`),
  updateAccountPermissions: (accountId: string, payload: Partial<AccountPermissionProfile>) =>
    request<AccountPermissionProfile>(`/api/admin/accounts/${accountId}/permissions`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listAdminSkills: () => request<AdminSkillPayload[]>('/api/admin/skills'),
  listAdminAssets: () => request<AdminAssetPayload[]>('/api/admin/assets'),
  listAdminTasks: () => request<AdminTaskPayload[]>('/api/admin/tasks'),
  getAdminAssetDetail: (assetId: string) => request<AdminAssetDetailPayload>(`/api/admin/assets/${assetId}`),
  testAdminAsset: (assetId: string, payload: AdminAssetActionPayload = {}) =>
    request<AdminAssetActionPayload>(`/api/admin/assets/${assetId}/test`, { method: 'POST', body: JSON.stringify(payload) }),
  submitAdminAsset: (assetId: string) =>
    request<AdminAssetActionPayload>(`/api/admin/assets/${assetId}/submit`, { method: 'POST' }),
  publishAdminAsset: (assetId: string) =>
    request<AdminAssetActionPayload>(`/api/admin/assets/${assetId}/publish`, { method: 'POST' }),
  getAdminSkill: (skillId: string) => request<AdminSkillPayload>(`/api/admin/skills/${skillId}`),
  createAdminSkill: (payload: AdminSkillPayload) =>
    request<AdminSkillPayload>('/api/admin/skills', { method: 'POST', body: JSON.stringify(payload) }),
  updateAdminSkill: (skillId: string, payload: AdminSkillPayload) =>
    request<AdminSkillPayload>(`/api/admin/skills/${skillId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  testAdminSkill: (skillId: string, payload: AdminSkillPayload) =>
    request<AdminSkillPayload>(`/api/admin/skills/${skillId}/test`, { method: 'POST', body: JSON.stringify(payload) }),
  listGovernanceTasks: () => request<GovernanceTaskPayload[]>('/api/admin/governance/tasks'),
  listReleaseActivities: () => request<ReleaseActivityPayload[]>('/api/admin/governance/activities'),
  submitSkillGovernance: (skillId: string) =>
    request<Record<string, unknown>>(`/api/admin/governance/skills/${skillId}/submit`, { method: 'POST' }),
  approveGovernanceTask: (taskId: string) =>
    request<Record<string, unknown>>(`/api/admin/governance/tasks/${taskId}/approve`, { method: 'POST' }),
  publishGovernanceTask: (taskId: string) =>
    request<Record<string, unknown>>(`/api/admin/governance/tasks/${taskId}/publish`, { method: 'POST' }),
  listAdminMcps: () => request<AdminMcpPayload[]>('/api/admin/mcps'),
  getAdminMcp: (mcpId: string) => request<AdminMcpPayload>(`/api/admin/mcps/${mcpId}`),
  createAdminMcp: (payload: AdminMcpPayload) =>
    request<AdminMcpPayload>('/api/admin/mcps', { method: 'POST', body: JSON.stringify(payload) }),
  updateAdminMcp: (mcpId: string, payload: AdminMcpPayload) =>
    request<AdminMcpPayload>(`/api/admin/mcps/${mcpId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  runAdminMcpHealthCheck: (mcpId: string) =>
    request<AdminMcpPayload>(`/api/admin/mcps/${mcpId}/health-check`, { method: 'POST' }),
  getPlatformMetricsOverview: () => request<PlatformMetricsPayload>('/api/admin/metrics/overview'),
  getPlatformSkillMetrics: () => request<PlatformMetricsPayload>('/api/admin/metrics/skills'),
  getPlatformOrganizationMetrics: () => request<PlatformMetricsPayload>('/api/admin/metrics/organizations'),
  listPlatformAlerts: () => request<PlatformMetricsPayload[]>('/api/admin/alerts'),
  listPermissionAuditLogs: () => request<PermissionAuditLog[]>('/api/admin/audit/permissions'),
  listActionGovernanceCases: () => request<ActionGovernancePayload[]>('/api/admin/action-governance'),
  chatStream: async (
    session_id: string,
    message: string,
    web_search_enabled: boolean,
    onEvent: (
      event: ChatStreamEvent,
      data: ChatMessage | ChatStep | { message: string } | { content: string } | { delta: string },
    ) => void,
  ) => {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, message, web_search_enabled }),
    });
    if (!response.ok) {
      throw new Error(await response.text() || `HTTP ${response.status}`);
    }
    if (!response.body) {
      throw new Error('当前浏览器不支持流式响应');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n');
      let boundary = buffer.indexOf('\n\n');
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = block.split('\n').find((line) => line.startsWith('event: '))?.slice(7) as ChatStreamEvent | undefined;
        const data = block.split('\n').filter((line) => line.startsWith('data: ')).map((line) => line.slice(6)).join('\n');
        if (event && data) {
          onEvent(event, JSON.parse(data));
        }
        boundary = buffer.indexOf('\n\n');
      }
      if (done) break;
    }
  },
};
