import { useState } from 'react';
import { McpDefinition, SkillDefinition, skillDependenciesForMcp } from '../managementData';
import { DetailTabs, PageHeader, PrototypeToast, StatusBadge } from '../components/ManagementUi';

type Props = { mcp: McpDefinition; skills: SkillDefinition[]; onNavigate: (path: string) => void; onUpdate: (mcp: McpDefinition) => void };

export function McpDetailPage({ mcp, skills, onNavigate, onUpdate }: Props) {
  const [tab, setTab] = useState('概览');
  const [toast, setToast] = useState('');
  const [testResult, setTestResult] = useState('');
  const dependencies = skillDependenciesForMcp(mcp.name, skills);
  const notify = (text: string) => { setToast(text); window.setTimeout(() => setToast(''), 2200); };
  const toggle = () => { onUpdate({ ...mcp, status: mcp.status === 'enabled' ? 'disabled' : 'enabled' }); notify(dependencies.length ? `状态已更新，影响 ${dependencies.length} 个 Skill` : 'MCP 状态已更新'); };
  const runHealth = () => { onUpdate({ ...mcp, health: 'healthy', latency: `${Math.floor(80 + Math.random() * 600)} ms`, updatedAt: '刚刚' }); setTestResult(`${mcp.displayName} 连接正常，Schema 校验通过。`); notify('健康检查完成'); };

  return <section className="management-page detail-page">
    <button className="back-link" type="button" onClick={() => onNavigate('/admin/mcps')}>← 返回 MCP 列表</button>
    <PageHeader eyebrow={mcp.category} title={mcp.displayName} description={mcp.description} actions={<><StatusBadge status={mcp.status} /><button className="secondary-action" type="button" onClick={runHealth}>↻ 健康检查</button><button className="primary-action" type="button" onClick={toggle}>{mcp.status === 'enabled' ? '停用 MCP' : '启用 MCP'}</button></>} />
    <DetailTabs tabs={['概览', '连接与配置', 'Schema', '测试与日志']} active={tab} onChange={setTab} />
    {tab === '概览' && <div className="detail-grid"><article className="panel-card span-2"><h3>运行概览</h3><div className="definition-grid"><div><span>唯一标识</span><code>{mcp.name}</code></div><div><span>健康状态</span><strong><i className={`health-dot ${mcp.health}`} /> {mcp.health === 'healthy' ? '运行正常' : '需要检查'}</strong></div><div><span>最近耗时</span><strong>{mcp.latency}</strong></div><div><span>配置来源</span><strong>{mcp.source}</strong></div></div></article><article className="panel-card"><h3>引用此 MCP 的 Skill</h3><div className="dependency-list">{dependencies.length ? dependencies.map((skill) => <button key={skill.name} type="button" onClick={() => onNavigate(`/admin/skills/${skill.name}`)}>{skill.displayName}<b>→</b></button>) : <p className="muted">当前没有 Skill 引用该 MCP。</p>}</div></article><article className="panel-card"><h3>近 24 小时</h3><div className="stat-stack"><strong>98.7%</strong><span>调用成功率</span><strong>1,286</strong><span>执行次数</span></div></article></div>}
    {tab === '连接与配置' && <div className="detail-grid"><article className="panel-card span-2"><div className="section-toolbar"><div><h3>连接与配置</h3><p>敏感配置已加密保存，页面不会回显真实值。</p></div><button className="primary-action" type="button" onClick={() => notify('配置已保存到原型状态')}>保存配置</button></div><div className="config-form">{mcp.config.map((item) => <label key={item.label}><span>{item.label}</span><input defaultValue={item.sensitive ? '••••••••••••••••' : item.value} type={item.sensitive ? 'password' : 'text'} /><small>{item.sensitive ? '敏感字段仅支持覆盖更新' : '当前运行配置'}</small></label>)}</div></article></div>}
    {tab === 'Schema' && <div className="detail-grid"><article className="panel-card"><h3>输入字段</h3>{Object.entries(mcp.schema).map(([name, type]) => <div className="schema-field" key={name}><strong>{name}</strong><span>{type}</span></div>)}</article><article className="panel-card code-card"><h3>标准返回契约</h3><pre>{JSON.stringify({ success: true, data: {}, error: null, error_type: null }, null, 2)}</pre></article></div>}
    {tab === '测试与日志' && <div className="test-console"><div className="test-input"><h3>MCP 测试</h3><p>根据输入 Schema 生成测试参数并执行健康检查。</p><textarea defaultValue={JSON.stringify(Object.fromEntries(Object.keys(mcp.schema).map((key) => [key, key === 'query' ? '测试查询' : ''])), null, 2)} /><button className="primary-action" type="button" onClick={runHealth}>运行测试</button></div><div className="test-output"><h3>测试与日志</h3>{testResult ? <><span className="result-success">✓ 健康检查通过</span><p>{testResult}</p><pre>{JSON.stringify({ success: true, data: '测试返回正常', duration: mcp.latency }, null, 2)}</pre></> : <div className="empty-console">等待运行测试</div>}</div></div>}
    <PrototypeToast text={toast} />
  </section>;
}
