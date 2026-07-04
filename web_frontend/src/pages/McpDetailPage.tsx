import { useState } from 'react';
import { lifecycleActionByStage, lifecycleStageForReleaseStatus, LifecycleStage, McpDefinition, ReleaseActivity, releaseStatusLabel, SkillDefinition, skillDependenciesForMcp, stageLabel } from '../managementData';
import { DetailTabs, LifecycleOverviewPanel, PageHeader, PrototypeToast, StatusBadge } from '../components/ManagementUi';

type Props = { mcp: McpDefinition; skills: SkillDefinition[]; recentActivities: ReleaseActivity[]; onNavigate: (path: string) => void; onUpdate: (mcp: McpDefinition) => void; onHealthCheck: (mcp: McpDefinition) => void; onPublish: (mcp: McpDefinition) => void };

export function McpDetailPage({ mcp, skills, recentActivities, onNavigate, onUpdate, onHealthCheck, onPublish }: Props) {
  const [tab, setTab] = useState('概览');
  const [toast, setToast] = useState('');
  const [testResult, setTestResult] = useState('');
  const dependencies = skillDependenciesForMcp(mcp.name, skills);
  const notify = (text: string) => { setToast(text); window.setTimeout(() => setToast(''), 2200); };
  const toggle = () => { onUpdate({ ...mcp, status: mcp.status === 'enabled' ? 'disabled' : 'enabled' }); notify(dependencies.length ? `状态已更新，影响 ${dependencies.length} 个 Skill` : 'MCP 状态已更新'); };
  const runHealth = () => { onHealthCheck(mcp); onUpdate({ ...mcp, health: 'healthy', latency: `${Math.floor(80 + Math.random() * 600)} ms`, updatedAt: '刚刚' }); setTestResult(`${mcp.displayName} 连接正常，Schema 校验通过。`); notify('健康检查完成'); };
  const readWriteRisk = mcp.name.includes('executor') || mcp.name.includes('submit') ? '写入或执行型能力，高风险动作需审批' : '只读查询型能力，需记录访问来源';
  const currentStage: LifecycleStage = lifecycleStageForReleaseStatus(mcp.releaseStatus, mcp.blockedBy);
  const stageSteps: LifecycleStage[] = ['draft', 'testing', 'review', 'publish'];
  const summaryItems = [
    { label: '当前阶段', value: stageLabel[currentStage], description: '当前阶段主操作始终留在此详情页中完成。' },
    { label: '依赖影响', value: `${dependencies.length} 个 Skill`, description: dependencies.length ? dependencies.map((skill) => skill.displayName).join(' / ') : '当前暂无 Skill 引用' },
    { label: '影响组织与风险提示', value: readWriteRisk, description: '敏感配置不回显，发布前治理配置需额外确认授权范围。' },
    { label: '发布前治理配置', value: '运行与权限辅助区', description: '上线前再配置组织授权、角色模板和审计策略。' },
  ];
  const focusAreas = [
    { label: '测试', value: '健康检查与结果回放', description: '在当前页直接运行测试、查看返回结构和日志。' },
    { label: '提审资料', value: 'Schema / 风险 / 依赖影响', description: '提交前确认输入输出契约、白名单策略和影响 Skill 范围。' },
    { label: '发布检查清单', value: '版本差异 / 回滚预案', description: '通过后在当前页执行发布确认，不再跳到平级发布页。' },
    { label: '运行记录', value: `${recentActivities.length} 条最近动作`, description: '回看健康检查、依赖解锁和发布动作。' },
  ];
  const publish = () => {
    onPublish(mcp);
    onUpdate({ ...mcp, releaseStatus: 'published', publishedVersion: mcp.latestVersion, blockedBy: undefined });
    notify('已手动发布到 MCP 目录');
  };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/assets')}>← 返回统一目录</button>
    <PageHeader eyebrow={mcp.category} title={mcp.displayName} description="单详情页推进测试、提审与发布，同时保留依赖影响、运行记录和发布前治理配置。" actions={<><StatusBadge status={mcp.status} /><button className="secondary-action" type="button" onClick={runHealth}>↻ 健康检查</button><button className="primary-action" type="button" onClick={toggle}>{mcp.status === 'enabled' ? '停用 MCP' : '启用 MCP'}</button></>} />
    {/* 阶段状态 / 当前阶段主操作 / 影响组织与风险提示由 LifecycleOverviewPanel 统一渲染 */}
    <LifecycleOverviewPanel
      summaryTitle="影响组织与风险提示"
      summaryDescription="这里只读展示影响面、依赖和风险；真正的授权与审计配置进入发布前治理配置处理。"
      currentStage={currentStage}
      currentStageAction={lifecycleActionByStage[currentStage]}
      summaryItems={summaryItems}
      stageSteps={stageSteps}
      focusAreas={focusAreas}
    />
    <DetailTabs tabs={['概览', '连接与配置', 'Schema', '测试与日志']} active={tab} onChange={setTab} />
    {tab === '概览' && <div className="detail-grid">
      <article className="panel-card span-2">
        <h3>运行概览</h3>
        <div className="definition-grid">
          <div><span>唯一标识</span><code>{mcp.name}</code></div>
          <div><span>健康状态</span><strong><i className={`health-dot ${mcp.health}`} /> {mcp.health === 'healthy' ? '运行正常' : '需要检查'}</strong></div>
          <div><span>最近耗时</span><strong>{mcp.latency}</strong></div>
          <div><span>配置来源</span><strong>{mcp.source}</strong></div>
        </div>
      </article>
      <article className="panel-card">
        <h3>发布状态</h3>
        <div className="release-state-card">
          <strong>{releaseStatusLabel[mcp.releaseStatus]}</strong>
          <span>当前版本：{mcp.publishedVersion}</span>
          <span>待发布版本：{mcp.latestVersion}</span>
          {mcp.blockedBy && <p>{mcp.blockedBy}</p>}
        </div>
      </article>
      <article className="panel-card">
        <h3>引用影响</h3>
        <div className="stat-stack">
          <strong>{dependencies.length}</strong>
          <span>引用此 MCP 的 Skill</span>
          <strong>{mcp.usageCount30d || 0}</strong>
          <span>近 30 天调用次数</span>
        </div>
      </article>
      <article className="panel-card">
        <h3>读写风险</h3>
        <div className="mini-timeline">
          <span>{readWriteRisk}<small>根据工具类型和数据影响面决定授权策略</small></span>
          <span>敏感配置不可回显<small>API Key、密码等字段仅允许覆盖更新</small></span>
          <span>影响面<small>{dependencies.length ? dependencies.map((skill) => skill.displayName).join(' / ') : '暂无业务 Skill 引用'}</small></span>
        </div>
      </article>
      <article className="panel-card">
        <h3>发布与灰度</h3>
        <div className="definition-grid">
          <div><span>灰度范围</span><strong>{dependencies.length ? '试点组织优先' : '平台内测'}</strong></div>
          <div><span>发布策略</span><strong>{mcp.releaseStatus === 'published' ? '已发布' : '发布前影响面确认'}</strong></div>
          <div><span>回滚方式</span><strong>保留上一稳定版本</strong></div>
          <div><span>审计日志</span><strong>配置变更与健康检查留痕</strong></div>
        </div>
      </article>
      <article className="panel-card">
        <h3>引用此 MCP 的 Skill</h3>
        <div className="dependency-list">{dependencies.length ? dependencies.map((skill) => <button key={skill.name} type="button" onClick={() => onNavigate(`/admin/skills/${skill.name}`)}>{skill.displayName}<b>→</b></button>) : <p className="muted">当前没有 Skill 引用该 MCP。</p>}</div>
      </article>
      <article className="panel-card">
        <h3>发布前检查</h3>
        <div className="mini-timeline">
          <span>✓ 输入 Schema 结构校验<small>inputSchema 与返回契约合法</small></span>
          <span>✓ Mock 调用验证<small>示例输入返回结构正常</small></span>
          <span>{mcp.blockedBy ? '!' : '✓'} 依赖与白名单<small>{mcp.blockedBy || '没有待处理阻塞项'}</small></span>
        </div>
        <button className="primary-action" type="button" onClick={publish}>手动发布</button>
      </article>
      <article className="panel-card">
        <h3>最近治理记录</h3>
        <div className="release-diff-list">
          {recentActivities.length ? recentActivities.map((item) => <span key={item.id}>{item.detail}</span>) : <span>暂无治理动作</span>}
        </div>
      </article>
    </div>}
    {tab === '连接与配置' && <div className="detail-grid"><article className="panel-card span-2"><div className="section-toolbar"><div><h3>连接与配置</h3><p>敏感配置已加密保存，页面不会回显真实值。</p></div><button className="primary-action" type="button" onClick={() => notify('配置已保存到原型状态')}>保存配置</button></div><div className="config-form">{mcp.config.map((item) => <label key={item.label}><span>{item.label}</span><input defaultValue={item.sensitive ? '••••••••••••••••' : item.value} type={item.sensitive ? 'password' : 'text'} /><small>{item.sensitive ? '敏感字段仅支持覆盖更新' : '当前运行配置'}</small></label>)}</div></article></div>}
    {tab === 'Schema' && <div className="detail-grid"><article className="panel-card"><h3>输入字段</h3>{Object.entries(mcp.schema).map(([name, type]) => <div className="schema-field" key={name}><strong>{name}</strong><span>{type}</span></div>)}</article><article className="panel-card code-card"><h3>标准返回契约</h3><pre>{JSON.stringify({ success: true, data: {}, error: null, error_type: null }, null, 2)}</pre></article></div>}
    {tab === '测试与日志' && <div className="test-console"><div className="test-input"><h3>MCP 测试</h3><p>根据输入 Schema 生成测试参数并执行健康检查。</p><textarea defaultValue={JSON.stringify(Object.fromEntries(Object.keys(mcp.schema).map((key) => [key, key === 'query' ? '测试查询' : ''])), null, 2)} /><button className="primary-action" type="button" onClick={runHealth}>运行测试</button></div><div className="test-output"><h3>测试与日志</h3>{testResult ? <><span className="result-success">✓ 健康检查通过</span><p>{testResult}</p><pre>{JSON.stringify({ success: true, data: '测试返回正常', duration: mcp.latency, audit: '审计日志已记录' }, null, 2)}</pre></> : <div className="empty-console">等待运行测试，审计日志将在执行后生成</div>}</div></div>}
    <PrototypeToast text={toast} />
  </section>;
}
