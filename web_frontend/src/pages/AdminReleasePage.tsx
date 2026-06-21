import { McpDefinition, OperationsTask, SkillDefinition } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
};

export function AdminReleasePage({ tasks, skills, mcps }: Props) {
  const [scope, setScope] = useState('全部待发布');
  const releasableTasks = useMemo(() => tasks.filter((task) => {
    if (task.releaseStatus !== 'ready_to_publish') return false;
    if (scope === 'Skill 发布') return task.type === 'skill';
    if (scope === 'MCP 发布') return task.type === 'mcp';
    return true;
  }), [tasks, scope]);
  const publishedSkills = skills.filter((skill) => skill.releaseStatus === 'published');

  return <section className="management-page">
    <PageHeader
      eyebrow="Release"
      title="发布管理"
      description="审核通过后仍需人工确认发布，商城同名 Skill 仅保留一个当前版本。"
    />
    <MetricStrip items={[
      { label: '待发布版本', value: releasableTasks.length },
      { label: '当前商城版本', value: publishedSkills.length, tone: 'success' },
      { label: '已发布 MCP', value: mcps.filter((mcp) => mcp.releaseStatus === 'published').length },
      { label: '可回滚版本', value: 4 },
    ]} />
    <div className="release-filter-tabs">
      {['全部待发布', 'Skill 发布', 'MCP 发布'].map((item) => <button key={item} type="button" className={scope === item ? 'active' : ''} onClick={() => setScope(item)}>{item}</button>)}
    </div>
    <div className="task-stack">
      {releasableTasks.map((task) => <article className="task-card stage-ready_to_publish" key={task.id}>
        <div className="task-card-top">
          <div><span>{task.type === 'skill' ? 'Skill 发布' : 'MCP 发布'}</span><strong>{task.title}</strong></div>
          <i>待发布</i>
        </div>
        <p>{task.summary}</p>
        <div className="task-card-meta">
          <span>负责人：{task.owner}</span>
          <span>自动测试：{task.autoTestPassRate}</span>
          <span>更新时间：{task.updatedAt}</span>
        </div>
        <div className="release-compare-grid">
          <div>
            <strong>当前商城版本</strong>
            <span>{task.type === 'skill' ? (skills.find((skill) => task.title.includes(skill.displayName))?.publishedVersion || '--') : (mcps.find((mcp) => task.title.includes(mcp.displayName))?.publishedVersion || '--')}</span>
          </div>
          <div>
            <strong>待发布版本</strong>
            <span>{task.type === 'skill' ? (skills.find((skill) => task.title.includes(skill.displayName))?.latestVersion || '--') : (mcps.find((mcp) => task.title.includes(mcp.displayName))?.latestVersion || '--')}</span>
          </div>
        </div>
        <div className="release-confirm-card">
          <strong>发布确认</strong>
          <span>版本差异：已通过自动测试与人工审核，确认后将替换当前商城版本，并保留回滚预案。</span>
        </div>
        <div className="release-diff-list">
          <strong>差异预览</strong>
          <span>流程说明已补充业务口径</span>
          <span>示例输入输出已更新为可审核版本</span>
          <span>依赖检查结果已同步到发布前清单</span>
          <strong>发布检查清单</strong>
          <span>自动测试通过</span>
          <span>人工审核通过</span>
          <span>回滚预案已确认</span>
        </div>
        <div className="review-buttons">
          <button type="button" className="secondary-action">回滚预案</button>
          <button type="button" className="primary-action">手动发布</button>
        </div>
      </article>)}
    </div>
  </section>;
}
