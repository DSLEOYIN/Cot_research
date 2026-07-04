import { useMemo, useState } from 'react';
import { SkillDefinition } from '../managementData';
import { SkillCard } from '../components/SkillCard';

type Props = {
  skills: SkillDefinition[];
  onNavigate: (path: string) => void;
  onInstall: (name: string) => void;
  recentlyInstalledSkillName?: string;
};

const categories = ['全部类别', '数据与分析', '知识与检索', '效率办公'];

const categoryFor = (skill: SkillDefinition) => {
  if (skill.category === '数据分析' || skill.category === '联网分析') return '数据与分析';
  if (skill.category === '联网检索') return '知识与检索';
  return '效率办公';
};

export function SkillLibraryPage({ skills, onNavigate, onInstall, recentlyInstalledSkillName }: Props) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('全部类别');
  const [scope, setScope] = useState('全部能力');
  const featured = skills.filter((skill) => skill.featured).slice(0, 3);

  const filtered = useMemo(() => skills.filter((skill) => {
    const matchesText = `${skill.displayName}${skill.tagline}${skill.description}${skill.examples.join('')}`.toLowerCase().includes(query.trim().toLowerCase());
    const matchesCategory = category === '全部类别' || categoryFor(skill) === category;
    const matchesScope = scope === '全部能力' || (scope === '已开通' ? skill.installed : !skill.installed);
    return matchesText && matchesCategory && matchesScope;
  }), [skills, query, category, scope]);

  return <section className="skill-library-page">
    <button className="library-back" type="button" onClick={() => onNavigate('/skills')}>← 返回能力中心</button>
    <header className="library-header">
      <div><span>ENTERPRISE CAPABILITY DIRECTORY</span><h1>能力目录</h1><p>浏览集团内已认证的业务能力，按场景查看说明、适用组织和开通方式。</p></div>
      <strong>{filtered.length} 个能力</strong>
    </header>
    {recentlyInstalledSkillName && <div className="skill-inline-notice skill-inline-notice-store">
      <strong>能力已开通，可以立即查看，或返回“能力中心”继续使用</strong>
      <div>
        <span>{skills.find((skill) => skill.name === recentlyInstalledSkillName)?.displayName || recentlyInstalledSkillName} 已加入你的能力工作台。</span>
        <button type="button" onClick={() => onNavigate('/skills')}>返回能力中心</button>
      </div>
    </div>}
    <div className="store-section-title"><div><span>RECENT</span><h2>最近更新</h2></div><p>优先查看已有新版本的 Skill</p></div>
    <div className="task-stack compact">
      {skills.filter((skill) => skill.updateAvailable).slice(0, 2).map((skill) => <article className="task-card stage-ready_to_publish" key={skill.name}>
        <div className="task-card-top"><div><span>UPDATE</span><strong>{skill.displayName}</strong></div><i>{skill.publishedVersion} → {skill.latestVersion}</i></div>
        <p>{skill.tagline}</p>
      </article>)}
    </div>
    <div className="store-section-title library-featured-title"><div><span>FEATURED</span><h2>重点推荐</h2></div><p>适合在集团统一 AI 门户中优先开通的能力</p></div>
    <div className="editorial-grid library-editorial-grid">{featured.map((skill, index) => <article className={`editorial-card editorial-${index + 1}`} key={skill.name} onClick={() => onNavigate(`/skills/${skill.name}`)}>
      <div><span>{categoryFor(skill)}精选</span><h2>{skill.displayName}</h2><p>{skill.tagline}</p></div>
      <div className="editorial-visual"><i>{skill.displayName.slice(0, 1)}</i><div>{skill.outcomes?.slice(0, 2).map((outcome) => <span key={outcome}>✓ {outcome}</span>)}</div></div>
      <footer><div className="mini-app-icon">{skill.displayName.slice(0, 1)}</div><div><strong>{skill.displayName}</strong><span>{skill.outputType}</span></div><button className={`store-install-button ${skill.installed ? 'installed' : ''}`} type="button" onClick={(event) => { event.stopPropagation(); skill.installed ? onNavigate(`/skills/${skill.name}`) : onInstall(skill.name); }}>{skill.installed ? (skill.updateAvailable ? '查看更新' : '查看') : '申请开通'}</button></footer>
    </article>)}</div>
    <div className="store-section-title library-all-title"><div><span>ALL CAPABILITIES</span><h2>全部能力</h2></div><p>按分类或开通状态筛选</p></div>
    <div className="library-filter-bar">
      <label className="library-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索能力名称、用途或业务场景" /></label>
      <label><select aria-label="能力分类" value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item} value={item}>{item === '全部类别' ? '全部分类' : item}</option>)}</select></label>
      <label><select aria-label="开通状态" value={scope} onChange={(event) => setScope(event.target.value)}><option value="全部能力">全部开通状态</option><option>已开通</option><option>未开通</option></select></label>
    </div>
    {filtered.length ? <div className="library-skill-grid">{filtered.map((skill) => <SkillCard key={skill.name} skill={skill} onNavigate={onNavigate} onInstall={onInstall} highlight={skill.name === recentlyInstalledSkillName} />)}</div> : <div className="skill-empty-state"><strong>没有找到匹配的能力</strong><span>试试调整关键词或筛选条件。</span><button type="button" onClick={() => { setQuery(''); setCategory('全部类别'); setScope('全部能力'); }}>清空筛选</button></div>}
  </section>;
}
