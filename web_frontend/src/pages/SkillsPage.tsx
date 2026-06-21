import { useMemo, useState } from 'react';
import { OperationsTask, SkillDefinition, statusLabel } from '../managementData';
import { MetricStrip, PageHeader, StatusBadge } from '../components/ManagementUi';

type Props = {
  skills: SkillDefinition[];
  tasks: OperationsTask[];
  onNavigate: (path: string) => void;
  onCreate: () => void;
};

export function SkillsPage({ skills, tasks, onNavigate, onCreate }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('全部分类');
  const filtered = useMemo(() => skills.filter((skill) => {
    const matchesQuery = `${skill.displayName}${skill.name}${skill.description}${skill.tagline || ''}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (category === '全部分类' || skill.category === category);
  }), [skills, query, category]);

  const reviewCount = tasks.filter((task) => task.releaseStatus === 'ready_for_review').length;
  const publishCount = tasks.filter((task) => task.releaseStatus === 'ready_to_publish').length;

  return <section className="management-page">
    <PageHeader
      eyebrow="Skill Ops"
      title="Skill 管理"
      description="用混合输入驱动 AI 开发台生成 Skill 草案，再进入自动测试、审核中心和发布管理。"
      actions={<button className="primary-action" type="button" onClick={onCreate}>＋ 新建 Skill</button>}
    />
    <MetricStrip items={[
      { label: 'Skill 总数', value: skills.length },
      { label: '待审核', value: reviewCount },
      { label: '待发布', value: publishCount, tone: 'success' },
      { label: '更新可用', value: skills.filter((s) => s.updateAvailable).length },
    ]} />
    <section className="ops-banner-grid">
      <article className="ops-banner-card">
        <span>CREATE</span>
        <h2>AI 开发台</h2>
        <p>名称、目标、适用场景、期望输出加上自然语言命令，系统自动按规范生成 Skill。</p>
      </article>
      <article className="ops-banner-card">
        <span>REVIEW</span>
        <h2>审核中心</h2>
        <p>重点审功能、作用、流程、依赖 MCP 和示例输入输出，驳回后可回流编辑。</p>
      </article>
      <article className="ops-banner-card">
        <span>RELEASE</span>
        <h2>发布管理</h2>
        <p>审核通过不自动上架，需手动发布；同名 Skill 仅一个版本在商城可见。</p>
      </article>
    </section>
    <div className="filter-bar">
      <label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索 Skill 名称、标识或描述" aria-label="搜索 Skill" /></label>
      <select value={category} onChange={(event) => setCategory(event.target.value)}><option>全部分类</option>{Array.from(new Set(skills.map((s) => s.category))).map((item) => <option key={item}>{item}</option>)}</select>
      <span className="filter-result">显示 {filtered.length} / {skills.length}</span>
    </div>
    <div className="skill-grid">
      {filtered.map((skill) => <article className="skill-card ops-skill-card" key={skill.name} onClick={() => onNavigate(`/admin/skills/${skill.name}`)}>
        <div className="skill-card-top"><div className="skill-icon">{skill.displayName.slice(0, 1)}</div><StatusBadge status={skill.status} /></div>
        <div className="skill-title"><h2>{skill.displayName}</h2><code>{skill.name}</code></div>
        <p>{skill.description}</p>
        <div className="tag-row"><span>{skill.category}</span><span>{skill.outputType}</span><span>{statusLabel[skill.status]}</span></div>
        <div className="dependency-row">{skill.mcpTools.slice(0, 4).map((mcp) => <code key={mcp}>{mcp}</code>)}{skill.mcpTools.length > 4 && <code>+{skill.mcpTools.length - 4}</code>}</div>
        <footer><span>{skill.steps.length} 个步骤</span><span>{skill.releaseStatus === 'published' ? '商城可见' : '待处理版本'}</span><b>进入任务详情 →</b></footer>
      </article>)}
    </div>
  </section>;
}
