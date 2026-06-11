import { useMemo, useState } from 'react';
import { McpDefinition, SkillDefinition, skillDependenciesForMcp } from '../managementData';
import { MetricStrip, PageHeader, StatusBadge } from '../components/ManagementUi';

type Props = { mcps: McpDefinition[]; skills: SkillDefinition[]; onNavigate: (path: string) => void; onCreate: () => void; onHealthCheck: () => void };

export function McpsPage({ mcps, skills, onNavigate, onCreate, onHealthCheck }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('全部分类');
  const filtered = useMemo(() => mcps.filter((mcp) => `${mcp.displayName}${mcp.name}${mcp.description}`.toLowerCase().includes(query.toLowerCase()) && (category === '全部分类' || mcp.category === category)), [mcps, query, category]);
  return <section className="management-page">
    <PageHeader eyebrow="原子工具" title="MCP 管理" description="管理工具连接、输入 Schema、健康状态与 Skill 引用。" actions={<><button className="secondary-action" type="button" onClick={onHealthCheck}>↻ 全部健康检查</button><button className="primary-action" type="button" onClick={onCreate}>＋ 接入 MCP</button></>} />
    <MetricStrip items={[{ label: 'MCP 总数', value: mcps.length }, { label: '运行正常', value: mcps.filter((m) => m.health === 'healthy').length, tone: 'success' }, { label: '配置异常', value: mcps.filter((m) => m.health === 'warning').length, tone: 'danger' }, { label: '被 Skill 引用', value: mcps.filter((m) => skillDependenciesForMcp(m.name, skills).length).length }]} />
    <div className="filter-bar"><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 MCP 名称、标识或描述" /></label><select value={category} onChange={(event) => setCategory(event.target.value)}><option>全部分类</option>{Array.from(new Set(mcps.map((m) => m.category))).map((item) => <option key={item}>{item}</option>)}</select><span className="filter-result">显示 {filtered.length} / {mcps.length}</span></div>
    <div className="table-shell"><table className="mcp-table"><thead><tr><th>MCP 工具</th><th>分类</th><th>状态</th><th>健康检查</th><th>被引用</th><th>来源</th><th /></tr></thead><tbody>{filtered.map((mcp) => <tr key={mcp.name} onClick={() => onNavigate(`/admin/mcps/${mcp.name}`)}><td><div className="mcp-name-cell"><span>{mcp.displayName.slice(0, 1)}</span><div><strong>{mcp.displayName}</strong><code>{mcp.name}</code><small>{mcp.description}</small></div></div></td><td><span className="category-pill">{mcp.category}</span></td><td><StatusBadge status={mcp.status} /></td><td><div className="health-cell"><span className={`health-dot ${mcp.health}`} /><strong>{mcp.health === 'healthy' ? '正常' : mcp.health === 'warning' ? '需检查' : '未检查'}</strong><small>{mcp.latency}</small></div></td><td>{skillDependenciesForMcp(mcp.name, skills).length} 个 Skill</td><td>{mcp.source}</td><td><button type="button">查看 →</button></td></tr>)}</tbody></table></div>
  </section>;
}
