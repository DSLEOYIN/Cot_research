import { useMemo, useState } from 'react';
import { SkillDefinition } from '../managementData';

type Props = { skills: SkillDefinition[]; onNavigate: (path: string) => void; onInstall: (name: string) => void };

const marketCategories = [
  { name: '全部类别', icon: '✦', description: '浏览市场中的全部能力' },
  { name: '数据与分析', icon: '数', description: '查询、洞察与可视化' },
  { name: '知识与检索', icon: '知', description: '知识库与联网搜索' },
  { name: '内容创作', icon: '文', description: '写作、设计与多媒体' },
  { name: '效率办公', icon: '效', description: '文档、会议与协作' },
  { name: '开发工具', icon: '码', description: '编码、测试与运维' },
  { name: '自动化', icon: '自', description: '流程编排与任务执行' },
];

const marketCategoryFor = (skill: SkillDefinition) => {
  if (skill.category === '数据分析' || skill.category === '联网分析') return '数据与分析';
  if (skill.category === '联网检索') return '知识与检索';
  if (skill.category === '闲聊') return '效率办公';
  return '自动化';
};

const matchesQuery = (skill: SkillDefinition, query: string) =>
  `${skill.displayName}${skill.tagline}${skill.description}${skill.outcomes?.join('')}`.toLowerCase().includes(query.trim().toLowerCase());

export function SkillCenterPage({ skills, onNavigate, onInstall }: Props) {
  const [storeQuery, setStoreQuery] = useState('');
  const [marketCategory, setMarketCategory] = useState('全部类别');
  const [recommendation, setRecommendation] = useState('为你推荐');
  const [mySkillQuery, setMySkillQuery] = useState('');
  const [mySkillCategory, setMySkillCategory] = useState('全部类别');
  const [mySkillSort, setMySkillSort] = useState('最近更新');

  const featured = skills.filter((skill) => skill.featured).slice(0, 2);
  const installedSkills = skills.filter((skill) => skill.installed);
  const discoveredSkills = useMemo(() => {
    const matched = skills.filter((skill) => matchesQuery(skill, storeQuery)
      && (marketCategory === '全部类别' || marketCategoryFor(skill) === marketCategory));
    if (recommendation === '已安装优先') return [...matched].sort((a, b) => Number(Boolean(b.installed)) - Number(Boolean(a.installed)));
    if (recommendation === '最新上架') return [...matched].reverse();
    return matched;
  }, [skills, storeQuery, marketCategory, recommendation]);
  const popular = discoveredSkills.slice(0, 4);
  const managedSkills = useMemo(() => {
    const matched = installedSkills.filter((skill) => matchesQuery(skill, mySkillQuery)
      && (mySkillCategory === '全部类别' || marketCategoryFor(skill) === mySkillCategory));
    if (mySkillSort === '名称排序') return [...matched].sort((a, b) => a.displayName.localeCompare(b.displayName, 'zh-CN'));
    if (mySkillSort === '最近安装') return [...matched].reverse();
    return matched;
  }, [installedSkills, mySkillQuery, mySkillCategory, mySkillSort]);

  const installButton = (skill: SkillDefinition) => (
    <button className={`store-install-button ${skill.installed ? 'installed' : ''}`} type="button" onClick={(event) => {
      event.stopPropagation();
      skill.installed ? onNavigate(`/skills/${skill.name}`) : onInstall(skill.name);
    }}>{skill.installed ? '打开' : '获取'}</button>
  );

  const skillRow = (skill: SkillDefinition) => (
    <article className="skill-app-row" key={skill.name} onClick={() => onNavigate(`/skills/${skill.name}`)}>
      <div className={`skill-app-icon category-${skill.category}`}>{skill.displayName.slice(0, 1)}</div>
      <div className="skill-app-copy"><h3>{skill.displayName}</h3><p>{skill.tagline}</p><span>{marketCategoryFor(skill)} · {skill.outputType}</span></div>
      {installButton(skill)}
    </article>
  );

  return <section className="skill-center-page app-store-layout">
    <header className="skill-store-title">
      <div><span>企业内部能力市场</span><h1>Skill 商店</h1><p>发现、安装并体验适合你的 ChatBI 能力。</p></div>
    </header>
    <label className="skill-store-search prominent"><span>⌕</span><input value={storeQuery} onChange={(e) => setStoreQuery(e.target.value)} placeholder="搜索名称、场景或能力" /><kbd>搜索 Skill</kbd></label>

    {!storeQuery && marketCategory === '全部类别' && <>
      <div className="store-section-title"><div><span>FEATURED</span><h2>精选推荐</h2></div><p>经过企业审核、适合快速上手的能力</p></div>
      <div className="editorial-grid">{featured.map((skill, index) => <article className={`editorial-card editorial-${index + 1}`} key={skill.name} onClick={() => onNavigate(`/skills/${skill.name}`)}>
        <div><span>{marketCategoryFor(skill)}精选</span><h2>{skill.displayName}</h2><p>{skill.tagline}</p></div>
        <div className="editorial-visual"><i>{skill.displayName.slice(0, 1)}</i><b>{skill.outcomes?.[0]}</b><b>{skill.outcomes?.[1]}</b></div>
        <footer><div className="mini-app-icon">{skill.displayName.slice(0, 1)}</div><div><strong>{skill.displayName}</strong><span>{skill.outputType}</span></div>{installButton(skill)}</footer>
      </article>)}</div>
    </>}

    <div className="store-section-title"><div><span>DISCOVER</span><h2>热门 Skill</h2></div><p>不知道选什么？从大家常用和平台推荐开始</p></div>
    <div className="market-discovery-bar">
      <label><span>市场分类</span><select value={marketCategory} onChange={(e) => setMarketCategory(e.target.value)}>{marketCategories.map((category) => <option key={category.name}>{category.name}</option>)}</select></label>
      <label><span>推荐方式</span><select value={recommendation} onChange={(e) => setRecommendation(e.target.value)}><option>为你推荐</option><option>最新上架</option><option>已安装优先</option></select></label>
      <strong>{discoveredSkills.length} 个可用 Skill</strong>
    </div>
    {popular.length ? <div className="popular-skill-list">{popular.map(skillRow)}</div> : <div className="skill-empty-state"><strong>这个分类正在扩充</strong><span>目前还没有上架的 Skill，可以先浏览其他市场分类。</span></div>}

    <div className="store-section-title catalog-title"><div><span>MARKET CATEGORIES</span><h2>发现更多 Skill</h2></div><p>按照通用 AI 能力市场分类浏览</p></div>
    <div className="market-category-grid">{marketCategories.slice(1).map((category) => <button type="button" className={marketCategory === category.name ? 'active' : ''} key={category.name} onClick={() => setMarketCategory(category.name)}><i>{category.icon}</i><strong>{category.name}</strong><span>{category.description}</span><b>{skills.filter((skill) => marketCategoryFor(skill) === category.name).length}</b></button>)}</div>

    <div className="store-section-title all-skills-title"><div><span>MY SKILLS</span><h2>我的 Skill</h2></div><p>{installedSkills.length} 个已安装到你的助手</p></div>
    <div className="my-skill-toolbar">
      <label className="my-skill-search"><span>⌕</span><input value={mySkillQuery} onChange={(e) => setMySkillQuery(e.target.value)} placeholder="搜索已安装 Skill" /></label>
      <label><span>类别</span><select value={mySkillCategory} onChange={(e) => setMySkillCategory(e.target.value)}>{marketCategories.map((category) => <option key={category.name}>{category.name}</option>)}</select></label>
      <label><span>排序</span><select value={mySkillSort} onChange={(e) => setMySkillSort(e.target.value)}><option>最近更新</option><option>最近安装</option><option>名称排序</option></select></label>
    </div>
    {managedSkills.length ? <div className="all-skill-list">{managedSkills.map(skillRow)}</div> : <div className="skill-empty-state"><strong>没有找到已安装的 Skill</strong><span>试试更换搜索词或类别。</span></div>}
  </section>;
}
