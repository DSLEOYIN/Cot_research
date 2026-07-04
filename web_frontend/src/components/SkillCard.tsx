import { SkillDefinition } from '../managementData';

type Props = {
  skill: SkillDefinition;
  onNavigate: (path: string) => void;
  onInstall?: (name: string) => void;
  onToggleEnable?: (name: string) => void;
  highlight?: boolean;
};

const categoryFor = (skill: SkillDefinition) => {
  if (skill.category === '数据分析' || skill.category === '联网分析') return '数据与分析';
  if (skill.category === '联网检索') return '知识与检索';
  return '效率办公';
};

export function SkillCard({ skill, onNavigate, onInstall, onToggleEnable, highlight = false }: Props) {
  const open = () => onNavigate(`/skills/${skill.name}`);
  const actionLabel = skill.installed ? (skill.updateAvailable ? '查看更新' : '查看') : '申请开通';
  const isManagedInstalled = Boolean(onToggleEnable && skill.installed);
  const showInlineAction = isManagedInstalled || Boolean(onInstall);
  return <article className={`library-skill-card ${highlight ? 'recently-installed' : ''}`} onClick={open}>
    <header>
      <div className="skill-card-head">
        <div className={`skill-app-icon category-${skill.category}`}>{skill.displayName.slice(0, 1)}</div>
        <div className="skill-card-head-copy">
          <span>{categoryFor(skill)}</span>
          <div className="skill-version-badge"><span>最新版本</span><strong>{skill.latestVersion || '--'}</strong></div>
        </div>
      </div>
      <div className="skill-card-status-zone">
        <i className={`skill-status ${skill.installed ? 'installed' : 'uninstalled'}`}>{skill.installed ? (skill.updateAvailable ? '待更新' : '已开通') : '未开通'}</i>
        {isManagedInstalled ? <button
          type="button"
          aria-label={skill.enabledForUser ? '移出常用能力' : '加入常用能力'}
          aria-pressed={skill.enabledForUser}
          className={`skill-toggle ${skill.enabledForUser ? 'on' : 'off'}`}
          onClick={(event) => {
            event.stopPropagation();
            onToggleEnable?.(skill.name);
          }}
        >
          <i />
        </button> : null}
      </div>
    </header>
    <div className="skill-card-body">
      <h2>{skill.displayName}</h2>
      <p>{skill.tagline}</p>
    </div>
    <div className={`library-value-points ${showInlineAction ? 'with-inline-action' : ''}`}>
      <div className="library-value-points-copy">{skill.outcomes?.slice(0, 2).map((outcome) => <span key={outcome}>✓ {outcome}</span>)}</div>
      {showInlineAction ? <button type="button" className="skill-inline-action" onClick={(event) => {
        event.stopPropagation();
        skill.installed || !onInstall ? open() : onInstall(skill.name);
      }}>{actionLabel}</button> : null}
    </div>
    {showInlineAction ? null : <footer>
      <span>{skill.outputType}</span>
      <button type="button" onClick={(event) => {
        event.stopPropagation();
        skill.installed || !onInstall ? open() : onInstall(skill.name);
      }}>{actionLabel}</button>
    </footer>}
  </article>;
}
