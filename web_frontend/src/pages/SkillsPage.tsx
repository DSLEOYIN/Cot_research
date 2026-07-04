import { useMemo, useState } from 'react';
import { OperationsTask, SkillDefinition, skillGovernanceTags, statusLabel } from '../managementData';
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
      eyebrow="Skill Orchestration"
      title="Skill 编排"
      description="把集团业务需求沉淀为 Skill，统一定义场景、流程、依赖 MCP、适用组织和测试状态。"
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
        <p>名称、目标、适用组织、业务场景和期望输出加上自然语言命令，系统自动按规范生成 Skill 草案。</p>
      </article>
      <article className="ops-banner-card">
        <span>GOVERN</span>
        <h2>组织授权</h2>
        <p>在能力完成测试后，为不同子公司、部门和角色定义开通范围、数据域权限和动作授权。</p>
      </article>
      <article className="ops-banner-card">
        <span>OPERATE</span>
        <h2>平台运营</h2>
        <p>关注使用热度、成功率、组织覆盖和异常情况，确保能力真正被集团业务使用起来。</p>
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
        {skillGovernanceTags[skill.name] && <div className="tag-row">
          <span>{skillGovernanceTags[skill.name].businessDomain}</span>
          <span>风险：{skillGovernanceTags[skill.name].riskLevel}</span>
          <span>{skillGovernanceTags[skill.name].requiresApproval ? '需组织审批' : '标准授权'}</span>
          <span>{skillGovernanceTags[skill.name].writesData ? '包含写入动作' : '只读能力'}</span>
        </div>}
        {skillGovernanceTags[skill.name] && <p className="skill-card-orgs">适用组织：{skillGovernanceTags[skill.name].applicableOrganizations.join(' / ')}</p>}
        <div className="dependency-row">{skill.mcpTools.slice(0, 4).map((mcp) => <code key={mcp}>{mcp}</code>)}{skill.mcpTools.length > 4 && <code>+{skill.mcpTools.length - 4}</code>}</div>
        <footer><span>{skill.steps.length} 个步骤</span><span>{skill.releaseStatus === 'published' ? '已纳入集团能力目录' : '待处理版本'}</span><b>进入编排详情 →</b></footer>
      </article>)}
    </div>
  </section>;
}
