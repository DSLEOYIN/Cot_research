import { useMemo, useState } from 'react';
import { SkillDefinition, statusLabel } from '../managementData';
import { MetricStrip, PageHeader, StatusBadge } from '../components/ManagementUi';

type Props = { skills: SkillDefinition[]; onNavigate: (path: string) => void; onCreate: () => void };

export function SkillsPage({ skills, onNavigate, onCreate }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('全部分类');
  const filtered = useMemo(() => skills.filter((skill) => {
    const matchesQuery = `${skill.displayName}${skill.name}${skill.description}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (category === '全部分类' || skill.category === category);
  }), [skills, query, category]);

  return <section className="management-page">
    <PageHeader eyebrow="能力编排" title="Skill 管理" description="管理业务能力、执行流程与 MCP 依赖关系。" actions={<button className="primary-action" type="button" onClick={onCreate}>＋ 新建 Skill</button>} />
    <MetricStrip items={[
      { label: 'Skill 总数', value: skills.length }, { label: '已启用', value: skills.filter((s) => s.status === 'enabled').length, tone: 'success' },
      { label: '工作流步骤', value: skills.reduce((sum, s) => sum + s.steps.length, 0) }, { label: '依赖异常', value: skills.filter((s) => s.status === 'warning').length, tone: 'danger' },
    ]} />
    <div className="filter-bar">
      <label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 Skill 名称、标识或描述" /></label>
      <select value={category} onChange={(event) => setCategory(event.target.value)}><option>全部分类</option>{Array.from(new Set(skills.map((s) => s.category))).map((item) => <option key={item}>{item}</option>)}</select>
      <span className="filter-result">显示 {filtered.length} / {skills.length}</span>
    </div>
    <div className="skill-grid">
      {filtered.map((skill) => <article className="skill-card" key={skill.name} onClick={() => onNavigate(`/admin/skills/${skill.name}`)}>
        <div className="skill-card-top"><div className="skill-icon">{skill.displayName.slice(0, 1)}</div><StatusBadge status={skill.status} /></div>
        <div className="skill-title"><h2>{skill.displayName}</h2><code>{skill.name}</code></div>
        <p>{skill.description}</p>
        <div className="tag-row"><span>{skill.category}</span><span>{skill.outputType}</span></div>
        <div className="dependency-row">{skill.mcpTools.slice(0, 4).map((mcp) => <code key={mcp}>{mcp}</code>)}{skill.mcpTools.length > 4 && <code>+{skill.mcpTools.length - 4}</code>}</div>
        <footer><span>{skill.steps.length} 个步骤</span><span>{statusLabel[skill.status]} · {skill.updatedAt}</span><b>查看详情 →</b></footer>
      </article>)}
    </div>
  </section>;
}
