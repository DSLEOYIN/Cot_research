import { AccountPermissionProfile, AdminRoleProfile, PermissionAuditLog } from '../api/client';
import { ActionGovernanceCase, OperationsTask, OrganizationAccessProfile, releaseStatusLabel, SkillDefinition } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  accounts: AccountPermissionProfile[];
  skills: SkillDefinition[];
  roles: AdminRoleProfile[];
  organizationProfiles: OrganizationAccessProfile[];
  actionGovernanceCases: ActionGovernanceCase[];
  permissionAuditLogs: PermissionAuditLog[];
  onNavigate: (path: string) => void;
  onCreateAccount: (payload: Partial<AccountPermissionProfile> & { password?: string }) => Promise<AccountPermissionProfile>;
  onSaveAccountPermissions: (account: AccountPermissionProfile, allowedSkills: string[], deniedSkills: string[]) => void;
  onSaveProfile: (profile: OrganizationAccessProfile, nextProfile: OrganizationAccessProfile) => void;
  onBulkGrantSkills: (accountIds: string[], skillName: string) => Promise<void>;
  onBulkDenySkills: (accountIds: string[], skillName: string) => Promise<void>;
  onExportPermissionReport: (accounts: AccountPermissionProfile[]) => void;
  onSaveRoleTemplate: (roleId: string, payload: AdminRoleProfile) => Promise<void>;
  onApproveTask: (task: OperationsTask) => void;
};

const approvalModeOptions = ['部门管理员复核', '动作型能力二次确认', '高风险操作留痕审计', '平台管理员复核'];
const defaultDataDomainOptions = ['销售', '库存', '人力', 'OA', '平台配置', '监控', '审计', '知识库'];
const defaultActionPermissionOptions = ['查询', '下载', '提交', '审批', '发布', '回滚', '授权', '测试'];

export function AdminReviewPage({ tasks, accounts, skills, roles, organizationProfiles, actionGovernanceCases, permissionAuditLogs, onNavigate, onCreateAccount, onSaveAccountPermissions, onSaveProfile, onBulkGrantSkills, onBulkDenySkills, onExportPermissionReport, onSaveRoleTemplate, onApproveTask }: Props) {
  const [priority, setPriority] = useState('全部优先级');
  const [viewMode, setViewMode] = useState<'account' | 'role' | 'organization' | 'audit'>('account');
  const [selectedAccountId, setSelectedAccountId] = useState(accounts[0]?.id || '');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchText, setSearchText] = useState('');
  const [organizationFilter, setOrganizationFilter] = useState('全部组织');
  const [roleFilter, setRoleFilter] = useState('全部角色');
  const [bulkMode, setBulkMode] = useState<'grant' | 'deny'>('grant');
  const [bulkSkill, setBulkSkill] = useState('');
  const [auditTypeFilter, setAuditTypeFilter] = useState('全部类型');
  const [auditWindow, setAuditWindow] = useState('最近 7 天');
  const [auditSearch, setAuditSearch] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [newAccount, setNewAccount] = useState({
    username: '',
    password: '123456',
    displayName: '',
    organizationId: organizationProfiles[0]?.id || '',
    roleId: 'sales-analyst',
    allowedSkill: '',
    deniedSkill: '',
  });
  const [nextApprovalMode, setNextApprovalMode] = useState<Record<string, string>>({});
  const [nextAccountOverrides, setNextAccountOverrides] = useState<Record<string, { allowedSkills: string[]; deniedSkills: string[] }>>({});
  const [organizationDrafts, setOrganizationDrafts] = useState<Record<string, OrganizationAccessProfile>>({});
  const reviewTasks = useMemo(() => tasks.filter((task) => task.releaseStatus === 'ready_for_review' && (priority === '全部优先级' || task.priority === priority)), [tasks, priority]);
  const blockedTasks = tasks.filter((task) => task.releaseStatus === 'blocked_by_dependency');
  const roleTemplates = Array.from(new Set(accounts.flatMap((account) => account.roleNames)));
  const [roleDrafts, setRoleDrafts] = useState<Record<string, AdminRoleProfile>>({});
  const organizationOptions = Array.from(new Set(accounts.map((account) => account.organizationName)));
  const roleOptions = roleTemplates.map((roleName) => {
    const matchedRole = roles.find((role) => role.roleName === roleName);
    return { id: matchedRole?.id || roleName, label: roleName };
  });
  const filteredAccounts = accounts.filter((account) => {
    const keyword = searchText.trim().toLowerCase();
    const matchesSearch = !keyword || [account.displayName, account.username, account.organizationName, account.roleNames.join(' ')].join(' ').toLowerCase().includes(keyword);
    const matchesOrganization = organizationFilter === '全部组织' || account.organizationName === organizationFilter;
    const matchesRole = roleFilter === '全部角色' || account.roleNames.includes(roleFilter);
    return matchesSearch && matchesOrganization && matchesRole;
  });
  const filteredAuditLogs = permissionAuditLogs.filter((item) => {
    const matchesType = auditTypeFilter === '全部类型' || item.entityType === auditTypeFilter;
    const keyword = auditSearch.trim().toLowerCase();
    const matchesKeyword = !keyword || [item.entityName, item.changeSummary, item.entityType].join(' ').toLowerCase().includes(keyword);
    if (!matchesType || !matchesKeyword) return false;
    if (auditWindow === '全部时间') return true;
    const createdAt = new Date(item.createdAt).getTime();
    const now = Date.now();
    const diffDays = (now - createdAt) / (1000 * 60 * 60 * 24);
    if (auditWindow === '今天') return diffDays < 1;
    if (auditWindow === '最近 3 天') return diffDays < 3;
    return diffDays < 7;
  });
  const auditGroups = filteredAuditLogs.reduce<Record<string, PermissionAuditLog[]>>((groups, item) => {
    const dateKey = item.createdAt.slice(0, 10);
    groups[dateKey] = groups[dateKey] || [];
    groups[dateKey].push(item);
    return groups;
  }, {});
  const accountsByOrganization = organizationProfiles.map((profile) => ({
    profile,
    accounts: filteredAccounts.filter((account) => account.organizationId === profile.id || account.organizationName === profile.organizationName),
  }));
  const selectedAccount = filteredAccounts.find((account) => account.id === selectedAccountId) || filteredAccounts[0] || accounts.find((account) => account.id === selectedAccountId) || accounts[0];
  const accountOverride = selectedAccount ? nextAccountOverrides[selectedAccount.id] || { allowedSkills: selectedAccount.allowedSkills, deniedSkills: selectedAccount.deniedSkills } : { allowedSkills: [], deniedSkills: [] };
  const selectedOrganization = selectedAccount ? organizationProfiles.find((profile) => profile.id === selectedAccount.organizationId || profile.organizationName === selectedAccount.organizationName) : undefined;

  const submitNewAccount = async () => {
    const created = await onCreateAccount({
      username: newAccount.username,
      password: newAccount.password,
      displayName: newAccount.displayName,
      organizationId: newAccount.organizationId,
      roleIds: [newAccount.roleId],
      allowedSkills: newAccount.allowedSkill ? [newAccount.allowedSkill] : [],
      deniedSkills: newAccount.deniedSkill ? [newAccount.deniedSkill] : [],
    });
    setSelectedAccountId(created.id);
    setSelectedIds([created.id]);
    setCreateOpen(false);
    setNewAccount((current) => ({ ...current, username: '', displayName: '', allowedSkill: '', deniedSkill: '' }));
  };

  const toggleSelected = (accountId: string) => {
    setSelectedIds((items) => items.includes(accountId) ? items.filter((item) => item !== accountId) : [...items, accountId]);
  };
  const toggleOrganizationDraftValue = (profile: OrganizationAccessProfile, field: 'openSkills' | 'dataDomains' | 'actionPermissions', value: string) => {
    const profileKey = profile.id || `${profile.organizationName}-${profile.roleName}`;
    setOrganizationDrafts((items) => {
      const current = items[profileKey] || profile;
      const currentValues = current[field];
      const nextValues = currentValues.includes(value) ? currentValues.filter((item) => item !== value) : [...currentValues, value];
      return { ...items, [profileKey]: { ...current, [field]: nextValues } };
    });
  };
  const toggleRoleDraftValue = (role: AdminRoleProfile, field: 'openSkills' | 'dataDomains' | 'actionPermissions', value: string) => {
    setRoleDrafts((items) => {
      const current = items[role.id] || role;
      const currentValues = current[field];
      const nextValues = currentValues.includes(value) ? currentValues.filter((item) => item !== value) : [...currentValues, value];
      return { ...items, [role.id]: { ...current, [field]: nextValues } };
    });
  };

  const applyBulkAction = async () => {
    if (selectedIds.length === 0 || !bulkSkill) return;
    if (bulkMode === 'grant') {
      await onBulkGrantSkills(selectedIds, bulkSkill);
    } else {
      await onBulkDenySkills(selectedIds, bulkSkill);
    }
  };
  const exportTargets = selectedIds.length > 0 ? accounts.filter((account) => selectedIds.includes(account.id)) : filteredAccounts;

  return <section className="management-page permission-page">
    <PageHeader
      eyebrow="Operations Center"
      title="运行与权限"
      description="发布前治理配置集中在这里处理，包括组织授权、角色模板、审计记录和动作型能力闭环。"
      actions={<button className="secondary-action" type="button" onClick={() => onNavigate('/admin/assets')}>返回统一目录</button>}
    />
    <MetricStrip items={[
      { label: '账号数', value: accounts.length },
      { label: '角色模板', value: roleTemplates.length },
      { label: '已覆盖组织', value: organizationProfiles.length, tone: 'success' },
      { label: '高风险策略', value: blockedTasks.length, tone: 'danger' },
    ]} />

    <section className="permission-summary-strip">
      <div><span>权限优先级</span><strong>账号级禁用 ＞ 账号级开通 ＞ 组织 / 角色默认</strong></div>
      <div><span>目录规模策略</span><strong>搜索筛选 + 分页加载，不平铺全部账号</strong></div>
      <div><span>待处理</span><strong>{reviewTasks.length} 个授权事项</strong></div>
    </section>

    <section className="permission-console">
      <div className="directory-toolbar">
        <div className="directory-tabs" aria-label="权限对象类型">
          <button className={viewMode === 'account' ? 'active' : ''} type="button" onClick={() => setViewMode('account')}>账号目录</button>
          <button className={viewMode === 'role' ? 'active' : ''} type="button" onClick={() => setViewMode('role')}>角色模板</button>
          <button className={viewMode === 'organization' ? 'active' : ''} type="button" onClick={() => setViewMode('organization')}>组织树</button>
          <button className={viewMode === 'audit' ? 'active' : ''} type="button" onClick={() => setViewMode('audit')}>策略审计</button>
        </div>
        <label className="directory-search"><span>搜索账号</span><input value={searchText} onChange={(event) => setSearchText(event.target.value)} placeholder="姓名 / username / 组织 / 角色" /></label>
        <label><span>组织筛选</span><select value={organizationFilter} onChange={(event) => setOrganizationFilter(event.target.value)}><option>全部组织</option>{organizationOptions.map((organization) => <option key={organization}>{organization}</option>)}</select></label>
        <label><span>角色筛选</span><select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}><option>全部角色</option>{roleTemplates.map((role) => <option key={role}>{role}</option>)}</select></label>
        <button className="primary-action" type="button" onClick={() => setCreateOpen(true)}>创建账号</button>
      </div>

      <div className="bulk-action-bar">
        <span>已选 {selectedIds.length} 个账号</span>
        <div className="bulk-editor">
          <select value={bulkMode} onChange={(event) => setBulkMode(event.target.value === 'deny' ? 'deny' : 'grant')}>
            <option value="grant">批量开通所选能力</option>
            <option value="deny">批量禁用所选能力</option>
          </select>
          <select value={bulkSkill} onChange={(event) => setBulkSkill(event.target.value)}>
            <option value="">选择一个 Skill</option>
            {skills.map((skill) => <option key={skill.name} value={skill.displayName}>{skill.displayName}</option>)}
          </select>
          <button type="button" disabled={selectedIds.length === 0 || !bulkSkill} onClick={applyBulkAction}>
            {bulkMode === 'grant' ? '批量授权' : '批量禁用'}
          </button>
        </div>
        <button type="button" onClick={() => onExportPermissionReport(exportTargets)}>导出权限清单</button>
        <small>账号目录表格 · 当前显示 {filteredAccounts.length} 条 · 每页 50 条</small>
      </div>

      {viewMode === 'audit' ? <div className="permission-audit-console">
        <div className="permission-audit-toolbar">
          <div>
            <strong>权限审计中心</strong>
            <p>按实体类型、时间范围和关键词追踪最近权限变更。</p>
          </div>
          <label><span>实体类型</span><select value={auditTypeFilter} onChange={(event) => setAuditTypeFilter(event.target.value)}><option>全部类型</option><option value="account">account</option><option value="organization">organization</option><option value="role">role</option></select></label>
          <label><span>时间范围</span><select value={auditWindow} onChange={(event) => setAuditWindow(event.target.value)}><option>今天</option><option>最近 3 天</option><option>最近 7 天</option><option>全部时间</option></select></label>
          <label className="directory-search"><span>关键词</span><input value={auditSearch} onChange={(event) => setAuditSearch(event.target.value)} placeholder="实体名 / 变更摘要 / 类型" /></label>
        </div>
        <div className="permission-audit-list grouped">
          {Object.entries(auditGroups).map(([date, items]) => <section className="permission-audit-group" key={date}>
            <h4>{date}</h4>
            {items.map((item) => <div key={item.id}>
              <strong>{item.entityName} · {item.entityType}</strong>
              <span>{item.changeSummary}</span>
              <small>{item.createdAt}</small>
            </div>)}
          </section>)}
          {filteredAuditLogs.length === 0 ? <div className="organization-member-empty">当前筛选条件下暂无审计记录</div> : null}
        </div>
      </div> : viewMode === 'organization' ? <div className="organization-tree-grid" aria-label="组织树视图">
        {accountsByOrganization.map(({ profile, accounts: organizationAccounts }) => {
          const profileKey = profile.id || `${profile.organizationName}-${profile.roleName}`;
          const organizationDraft = organizationDrafts[profileKey] || profile;
          return <article className="organization-tree-card" key={profileKey}>
          <div className="organization-tree-head">
            <div>
              <span>组织树视图</span>
              <strong>{profile.organizationName}</strong>
              <p>按组织汇总账号、角色与默认能力范围。</p>
            </div>
            <i>{organizationAccounts.length} 个账号</i>
          </div>
          <div className="organization-tree-meta">
            <span>默认能力：{organizationDraft.openSkills.join(' / ') || '未配置'}</span>
            <span>数据域：{organizationDraft.dataDomains.join('、') || '未配置'}</span>
            <span>动作权限：{organizationDraft.actionPermissions.join('、') || '未配置'}</span>
          </div>
          <div className="organization-policy-editor">
            <div>
              <span>默认能力配置</span>
              <div className="permission-chip-row editable">
                {skills.map((skill) => <button className={organizationDraft.openSkills.includes(skill.displayName) ? 'active' : ''} type="button" key={skill.name} onClick={() => toggleOrganizationDraftValue(profile, 'openSkills', skill.displayName)}>{skill.displayName}</button>)}
              </div>
            </div>
            <div>
              <span>数据域权限</span>
              <div className="permission-chip-row editable">
                {defaultDataDomainOptions.map((domain) => <button className={organizationDraft.dataDomains.includes(domain) ? 'active' : ''} type="button" key={domain} onClick={() => toggleOrganizationDraftValue(profile, 'dataDomains', domain)}>{domain}</button>)}
              </div>
            </div>
            <div>
              <span>动作权限</span>
              <div className="permission-chip-row editable">
                {defaultActionPermissionOptions.map((permission) => <button className={organizationDraft.actionPermissions.includes(permission) ? 'active' : ''} type="button" key={permission} onClick={() => toggleOrganizationDraftValue(profile, 'actionPermissions', permission)}>{permission}</button>)}
              </div>
            </div>
            <div className="permission-save-cell">
              <select value={organizationDraft.approvalMode} onChange={(event) => setOrganizationDrafts((items) => ({ ...items, [profileKey]: { ...organizationDraft, approvalMode: event.target.value } }))}>
                {approvalModeOptions.map((option) => <option key={option}>{option}</option>)}
              </select>
              <button className="primary-action compact-action" type="button" onClick={() => onSaveProfile(profile, organizationDraft)}>保存组织策略</button>
            </div>
          </div>
          <div className="organization-tree-members">
            {organizationAccounts.length ? organizationAccounts.map((account) => <button className={`organization-member-chip ${selectedIds.includes(account.id) ? 'selected' : ''}`} type="button" key={account.id} onClick={() => {
              setSelectedAccountId(account.id);
              toggleSelected(account.id);
            }}>
              <strong>{account.displayName}</strong>
              <span>{account.roleNames.join(' / ')}</span>
              <small>{account.effectiveSkills.length} 个有效 Skill</small>
            </button>) : <div className="organization-member-empty">当前筛选条件下暂无账号</div>}
          </div>
        </article>;
        })}
      </div> : <div className="permission-directory-layout">
        <article className="account-directory-panel">
          <div className="account-directory-table" role="table" aria-label="账号目录表格">
            <div className="account-directory-row table-head" role="row">
              <span>选择</span>
              <span>账号</span>
              <span>组织</span>
              <span>角色</span>
              <span>有效 Skill</span>
              <span>账号级覆盖</span>
              <span>状态</span>
            </div>
            {filteredAccounts.map((account) => <button className={`account-directory-row ${account.id === selectedAccount?.id ? 'active' : ''}`} type="button" key={account.id} onClick={() => setSelectedAccountId(account.id)} role="row">
              <span onClick={(event) => event.stopPropagation()}><input type="checkbox" checked={selectedIds.includes(account.id)} onChange={() => toggleSelected(account.id)} aria-label={`选择 ${account.displayName}`} /></span>
              <span><strong>{account.displayName}</strong><small>{account.username}</small></span>
              <span>{account.organizationName}</span>
              <span>{account.roleNames.join(' / ')}</span>
              <span>{account.effectiveSkills.length} 个</span>
              <span>{account.allowedSkills.length || account.deniedSkills.length ? `开通 ${account.allowedSkills.length} / 禁用 ${account.deniedSkills.length}` : '无覆盖'}</span>
              <span>{account.canAccessAdmin ? '治理账号' : '普通账号'}</span>
            </button>)}
          </div>
        </article>

        {selectedAccount && <aside className="permission-drawer">
          <div className="permission-drawer-head">
            <div><span>权限详情</span><h3>账号权限</h3><p>{selectedAccount.displayName} 的最终权限由组织、角色模板和账号级覆盖合并得到。</p></div>
            <button className="primary-action" type="button" onClick={() => onSaveAccountPermissions(selectedAccount, accountOverride.allowedSkills, accountOverride.deniedSkills)}>保存账号权限</button>
          </div>
          <div className="permission-profile-grid">
            <div><span>账号</span><strong>{selectedAccount.displayName}</strong><small>{selectedAccount.username}</small></div>
            <div><span>组织</span><strong>{selectedAccount.organizationName}</strong></div>
            <div><span>角色</span><strong>{selectedAccount.roleNames.join(' / ')}</strong></div>
            <div><span>管理员权限</span><strong>{selectedAccount.canAccessAdmin ? '可进入平台治理' : '仅使用前台能力'}</strong></div>
          </div>
          <div className="permission-detail-columns">
            <section>
              <h4>有效 Skill 权限</h4>
              <div className="permission-chip-row">{selectedAccount.effectiveSkills.map((skill) => <span key={skill}>{skill}</span>)}</div>
            </section>
            <section>
              <h4>权限来源</h4>
              <div className="permission-source-list">
                <p><strong>组织默认能力</strong><span>{selectedAccount.permissionSources.organization.openSkills.join(' / ') || '未配置'}</span></p>
                <p><strong>角色默认能力</strong><span>{selectedAccount.permissionSources.roles.map((role) => `${role.roleName}：${role.openSkills.join(' / ') || '无'}`).join('；') || '无角色默认能力'}</span></p>
                <p><strong>账号级开通</strong><span>{selectedAccount.permissionSources.accountOverride.allowedSkills.join(' / ') || '无'}</span></p>
                <p><strong>账号级禁用</strong><span>{selectedAccount.permissionSources.accountOverride.deniedSkills.join(' / ') || '无'}</span></p>
              </div>
            </section>
            <section>
              <h4>账号级覆盖</h4>
              <div className="account-permission-editor refined">
                <label><span>单独开通</span><select value={accountOverride.allowedSkills[0] || ''} onChange={(event) => setNextAccountOverrides((items) => ({ ...items, [selectedAccount.id]: { ...accountOverride, allowedSkills: event.target.value ? [event.target.value] : [] } }))}><option value="">不覆盖</option>{skills.map((skill) => <option key={skill.displayName}>{skill.displayName}</option>)}</select></label>
                <label><span>单独禁用</span><select value={accountOverride.deniedSkills[0] || ''} onChange={(event) => setNextAccountOverrides((items) => ({ ...items, [selectedAccount.id]: { ...accountOverride, deniedSkills: event.target.value ? [event.target.value] : [] } }))}><option value="">不覆盖</option>{skills.map((skill) => <option key={skill.displayName}>{skill.displayName}</option>)}</select></label>
              </div>
            </section>
          </div>
        </aside>}
      </div>}
    </section>

    {createOpen && <section className="account-create-panel permission-create-drawer" aria-label="创建账号抽屉">
      <div className="section-toolbar">
        <div><h3>创建账号抽屉</h3><p>账号基础信息、组织、角色和初始 Skill 覆盖在一个动作里完成。</p></div>
        <button className="secondary-action compact-action" type="button" onClick={() => setCreateOpen(false)}>关闭</button>
      </div>
      <div className="account-create-grid">
        <label><span>账号基础信息</span><input value={newAccount.username} onChange={(event) => setNewAccount((current) => ({ ...current, username: event.target.value }))} placeholder="username" /></label>
        <label><span>姓名</span><input value={newAccount.displayName} onChange={(event) => setNewAccount((current) => ({ ...current, displayName: event.target.value }))} placeholder="显示名称" /></label>
        <label><span>初始密码</span><input value={newAccount.password} onChange={(event) => setNewAccount((current) => ({ ...current, password: event.target.value }))} /></label>
        <label><span>组织</span><select value={newAccount.organizationId} onChange={(event) => setNewAccount((current) => ({ ...current, organizationId: event.target.value }))}>{organizationProfiles.map((profile) => <option value={profile.id} key={profile.id}>{profile.organizationName}</option>)}</select></label>
        <label><span>角色</span><select value={newAccount.roleId} onChange={(event) => setNewAccount((current) => ({ ...current, roleId: event.target.value }))}>{roleOptions.map((role) => <option value={role.id} key={role.id}>{role.label}</option>)}</select></label>
        <label><span>初始 Skill 覆盖</span><select value={newAccount.allowedSkill} onChange={(event) => setNewAccount((current) => ({ ...current, allowedSkill: event.target.value }))}><option value="">不单独开通</option>{skills.map((skill) => <option key={skill.displayName}>{skill.displayName}</option>)}</select></label>
      </div>
      <button className="primary-action" type="button" disabled={!newAccount.username || !newAccount.displayName} onClick={submitNewAccount}>创建账号</button>
    </section>}

    <div className="policy-reference-grid">
      <article className={`panel-card ${viewMode === 'role' ? 'panel-card-emphasis' : ''}`}>
        <div className="section-toolbar">
          <div><h3>角色模板</h3><p>角色决定岗位默认能力，账号可以在此基础上单独覆盖。</p></div>
        </div>
        <div className="role-template-list editable">
          {roles.map((role) => {
            const roleDraft = roleDrafts[role.id] || role;
            return <article className="role-template-card" key={role.id}>
              <div className="role-template-head">
                <div>
                  <strong>{roleDraft.roleName}</strong>
                  <span>{roleDraft.canAccessAdmin ? '治理角色' : '普通业务角色'}</span>
                </div>
                <label className="role-admin-toggle"><input type="checkbox" checked={roleDraft.canAccessAdmin} onChange={(event) => setRoleDrafts((items) => ({ ...items, [role.id]: { ...roleDraft, canAccessAdmin: event.target.checked } }))} />可进治理后台</label>
              </div>
              <div className="organization-policy-editor">
                <div>
                  <span>角色默认能力</span>
                  <div className="permission-chip-row editable">
                    {skills.map((skill) => <button className={roleDraft.openSkills.includes(skill.displayName) ? 'active' : ''} type="button" key={`${role.id}-${skill.name}`} onClick={() => toggleRoleDraftValue(role, 'openSkills', skill.displayName)}>{skill.displayName}</button>)}
                  </div>
                </div>
                <div>
                  <span>角色数据域</span>
                  <div className="permission-chip-row editable">
                    {defaultDataDomainOptions.map((domain) => <button className={roleDraft.dataDomains.includes(domain) ? 'active' : ''} type="button" key={`${role.id}-${domain}`} onClick={() => toggleRoleDraftValue(role, 'dataDomains', domain)}>{domain}</button>)}
                  </div>
                </div>
                <div>
                  <span>角色动作权限</span>
                  <div className="permission-chip-row editable">
                    {defaultActionPermissionOptions.map((permission) => <button className={roleDraft.actionPermissions.includes(permission) ? 'active' : ''} type="button" key={`${role.id}-${permission}`} onClick={() => toggleRoleDraftValue(role, 'actionPermissions', permission)}>{permission}</button>)}
                  </div>
                </div>
                <div className="permission-save-cell">
                  <button className="primary-action compact-action" type="button" onClick={() => onSaveRoleTemplate(role.id, roleDraft)}>保存角色模板</button>
                </div>
              </div>
            </article>;
          })}
        </div>
      </article>

      <article className={`panel-card ${viewMode === 'audit' ? 'panel-card-emphasis' : ''}`}>
        <div className="section-toolbar">
          <div><h3>组织授权矩阵</h3><p>组织负责默认能力、数据域、动作权限和审批模式。</p></div>
          <label><select value={priority} onChange={(event) => setPriority(event.target.value)}><option>全部优先级</option><option>P0</option><option>P1</option><option>P2</option></select></label>
        </div>
        <div className="organization-policy-list">
          {organizationProfiles.map((profile) => {
            const profileKey = profile.id || `${profile.organizationName}-${profile.roleName}`;
            const selectedApprovalMode = nextApprovalMode[profileKey] || profile.approvalMode;
            return <div className="organization-policy-row" key={profileKey}>
              <div><strong>{profile.organizationName}</strong><span>{profile.roleName}</span></div>
              <p>{profile.openSkills.join(' / ')}</p>
              <small>{profile.dataDomains.join('、')} · {profile.actionPermissions.join('、')}</small>
              <div className="permission-save-cell">
                <select value={selectedApprovalMode} onChange={(event) => setNextApprovalMode((items) => ({ ...items, [profileKey]: event.target.value }))}>
                  {approvalModeOptions.map((option) => <option key={option}>{option}</option>)}
                </select>
                <button className="secondary-action compact-action" type="button" onClick={() => onSaveProfile(profile, { ...profile, approvalMode: selectedApprovalMode })}>保存权限变更</button>
              </div>
            </div>;
          })}
        </div>
      </article>
    </div>

    <div className="policy-reference-grid">
      <article className="panel-card">
        <h3>动作型 Skill 闭环</h3>
        <div className="release-diff-list">
          {actionGovernanceCases.map((item) => <span key={item.id}>{item.skillName} · {item.organizationName} · {item.approvalStatus}</span>)}
        </div>
        <div className="release-confirm-card">
          <strong>二次确认</strong>
          <span>{actionGovernanceCases[0]?.confirmationRule || '待补动作型能力确认规则'}</span>
        </div>
        <div className="release-confirm-card">
          <strong>失败回溯</strong>
          <span>{actionGovernanceCases[0]?.rollbackStatus || '待补失败回退策略'}</span>
        </div>
        <div className="mini-timeline task-timeline">
          {(actionGovernanceCases[0]?.auditTrail || []).map((item) => <span key={item}>{item}<small>审计轨迹</small></span>)}
        </div>
      </article>
      <article className="panel-card">
        <h3>高风险动作</h3>
        <div className="mini-timeline task-timeline">
          <span>请假提单<small>需组织授权 + 提交权限</small></span>
          <span>审批流触发<small>需主管角色 + 审计记录</small></span>
          <span>外部通知<small>需白名单 + 审批前置</small></span>
        </div>
      </article>
      <article className="panel-card">
        <h3>待处理授权事项</h3>
        <div className="task-stack compact">
          {reviewTasks.map((task) => <article className="task-card stage-ready_for_review" key={task.id}>
            <div className="task-card-top">
              <div><span>{task.type === 'skill' ? '能力授权' : '底座授权'} · {task.priority}</span><strong>{task.title}</strong></div>
              <i>{releaseStatusLabel[task.releaseStatus]}</i>
            </div>
            <p>{task.summary}</p>
            <div className="task-card-meta">
              <span>负责人：{task.owner}</span>
              <span>自动测试：{task.autoTestPassRate}</span>
              <span>更新时间：{task.updatedAt}</span>
            </div>
            <div className="task-card-actions">
              <button className="primary-action compact-action" type="button" onClick={() => onApproveTask(task)}>审核通过，进入待发布</button>
            </div>
          </article>)}
        </div>
      </article>
      <article className="panel-card">
        <h3>权限审计记录</h3>
        <div className="permission-audit-list">
          {permissionAuditLogs.slice(0, 6).map((item) => <div key={item.id}>
            <strong>{item.entityName} · {item.entityType}</strong>
            <span>{item.changeSummary}</span>
            <small>{item.createdAt}</small>
          </div>)}
        </div>
      </article>
    </div>
  </section>;
}
