import { useEffect, useMemo, useState } from 'react';
import { SkillDefinition } from '../managementData';
import { SkillCard } from '../components/SkillCard';

type Props = {
  skills: SkillDefinition[];
  onNavigate: (path: string) => void;
  recentlyInstalledSkillName?: string;
  onSeenRecentlyInstalled?: () => void;
  onToggleEnable: (name: string) => void;
};

const categories = ['全部类别', '数据与分析', '知识与检索', '效率办公'];

const categoryFor = (skill: SkillDefinition) => {
  if (skill.category === '数据分析' || skill.category === '联网分析') return '数据与分析';
  if (skill.category === '联网检索') return '知识与检索';
  return '效率办公';
};

const matchesQuery = (skill: SkillDefinition, query: string) =>
  `${skill.displayName}${skill.tagline}${skill.description}${skill.outcomes?.join('')}`.toLowerCase().includes(query.trim().toLowerCase());

export function SkillCenterPage({ skills, onNavigate, recentlyInstalledSkillName, onSeenRecentlyInstalled, onToggleEnable }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('全部类别');
  const [sort, setSort] = useState('最近使用');
  const installedSkills = skills.filter((skill) => skill.installed);
  const enabledCount = installedSkills.filter((skill) => skill.enabledForUser).length;
  const updateCount = installedSkills.filter((skill) => skill.updateAvailable).length;
  const totalSkillUsage = installedSkills.reduce((sum, skill) => sum + (skill.usageCount30d || 0), 0);
  const skillUsageMax = Math.max(...installedSkills.map((item) => item.usageCount30d || 1), 1);
  const mcpUsageRanking = Object.entries(installedSkills.reduce<Record<string, number>>((acc, skill) => {
    skill.mcpTools.forEach((mcp) => {
      acc[mcp] = (acc[mcp] || 0) + (skill.usageCount30d || 0);
    });
    return acc;
  }, {})).sort((a, b) => b[1] - a[1]);
  const mcpUsageMax = Math.max(...mcpUsageRanking.map(([, count]) => count), 1);
  const topSkill = [...installedSkills].sort((a, b) => (b.usageCount30d || 0) - (a.usageCount30d || 0))[0];
  const topMcp = mcpUsageRanking[0];

  useEffect(() => {
    if (!recentlyInstalledSkillName) return;
    const timer = window.setTimeout(() => onSeenRecentlyInstalled?.(), 2600);
    return () => window.clearTimeout(timer);
  }, [recentlyInstalledSkillName, onSeenRecentlyInstalled]);

  const managedSkills = useMemo(() => {
    const matched = installedSkills.filter((skill) => matchesQuery(skill, query)
      && (category === '全部类别' || categoryFor(skill) === category));
    if (sort === '名称') return [...matched].sort((a, b) => a.displayName.localeCompare(b.displayName, 'zh-CN'));
    if (sort === '更新优先') return [...matched].sort((a, b) => Number(!!b.updateAvailable) - Number(!!a.updateAvailable));
    return [...matched].sort((a, b) => (b.usageCount30d || 0) - (a.usageCount30d || 0));
  }, [installedSkills, query, category, sort]);

  const hasNoInstalledSkills = installedSkills.length === 0;

  return <section className="skill-center-page my-skill-home">
    <header className="my-skill-home-header">
      <div><span>CAPABILITY CENTER</span><h1>能力中心</h1><p>查看你已开通的集团 AI 能力、常用业务场景和最近使用热度，快速回到统一 AI 助手继续提问。</p></div>
      <button type="button" onClick={() => onNavigate('/skills/library')}>浏览能力目录 <b>→</b></button>
    </header>
    {recentlyInstalledSkillName && <div className="skill-inline-notice">
      <strong>能力已开通</strong>
      <span>{skills.find((skill) => skill.name === recentlyInstalledSkillName)?.displayName || recentlyInstalledSkillName} 已加入你的能力工作台，授权生效后即可在 AI 助手中调用。</span>
    </div>}
    {!hasNoInstalledSkills && <section className="usage-chart enhanced-usage-board">
      <header><div><span>ADOPTION</span><h2>近 30 天使用次数</h2></div><p>从业务能力和底层能力两个维度，查看最近最常用的集团 AI 能力与调用热度。</p></header>
      <div className="skill-health-strip">
        <article><span>常用能力</span><strong>{enabledCount}/{installedSkills.length}</strong><small>已加入常用工作台</small></article>
        <article><span>最近常用能力</span><strong>{topSkill?.displayName || '--'}</strong><small>{topSkill?.usageCount30d || 0} 次调用</small></article>
        <article><span>最近常用 MCP</span><strong>{topMcp?.[0] || '--'}</strong><small>{topMcp?.[1] || 0} 次调用</small></article>
      </div>
      <div className="skill-meta-board">
        <article><span>最近 30 天成功率</span><strong>{installedSkills[0]?.successRate || '--'}</strong><small>按最近常用能力聚合</small></article>
        <article><span>待更新能力</span><strong>{updateCount}</strong><small>平台有新版本待同步</small></article>
        <article><span>能力调用总次数</span><strong>{totalSkillUsage}</strong><small>近 30 天累计使用热度</small></article>
      </div>
      <div className="usage-split-grid">
        <section className="usage-subsection">
          <div className="usage-subsection-head"><strong>能力使用排行</strong><span>近 30 天调用次数</span></div>
          <div className="usage-ranking">{[...installedSkills].sort((a, b) => (b.usageCount30d || 0) - (a.usageCount30d || 0)).map((skill, index) => <article key={skill.name}>
            <b>{index + 1}</b><span>{skill.displayName}</span>
            <div><i className="usage-rank-fill" style={{ width: `${Math.max(18, ((skill.usageCount30d || 0) / skillUsageMax) * 100)}%` }} /></div>
            <strong>{skill.usageCount30d || 0}</strong>
          </article>)}</div>
        </section>
        <section className="usage-subsection">
          <div className="usage-subsection-head"><strong>MCP 调用排行</strong><span>近 30 天调用次数</span></div>
          <div className="usage-ranking mcp-usage-ranking">{mcpUsageRanking.slice(0, 5).map(([mcpName, count], index) => <article key={mcpName}>
            <b>{index + 1}</b><span>{mcpName}</span>
            <div><i className="usage-rank-fill usage-rank-fill-mcp" style={{ width: `${Math.max(18, (count / mcpUsageMax) * 100)}%` }} /></div>
            <strong>{count}</strong>
          </article>)}</div>
        </section>
      </div>
    </section>}
    <div className="store-section-title all-skills-title"><div><span>ENABLED</span><h2>已开通能力</h2></div><p>{installedSkills.length} 个已开通 · {managedSkills.length} 个结果</p></div>
    {!hasNoInstalledSkills && <div className="my-skill-toolbar">
      <label className="my-skill-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索已开通能力" /></label>
      <label className="filter-select-field"><span>类别</span><select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label className="filter-select-field"><span>排序</span><select value={sort} onChange={(event) => setSort(event.target.value)}><option>最近使用</option><option>更新优先</option><option>名称</option></select></label>
    </div>}
    {hasNoInstalledSkills ? <div className="skill-empty-state">
      <strong>你还没有开通任何能力</strong>
      <span>去能力目录选择适合你业务场景的集团能力。</span>
      <button type="button" onClick={() => onNavigate('/skills/library')}>前往能力目录</button>
    </div> : managedSkills.length ? <div className="all-skill-list">{managedSkills.map((skill) => <SkillCard key={skill.name} skill={skill} onNavigate={onNavigate} onToggleEnable={onToggleEnable} highlight={skill.name === recentlyInstalledSkillName} />)}</div> : <div className="skill-empty-state"><strong>没有找到已开通的能力</strong><span>试试更换搜索词或类别。</span></div>}
  </section>;
}
