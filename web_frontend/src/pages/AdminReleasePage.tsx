import { McpDefinition, OperationsTask, PlatformAlert, PlatformMetrics, PlatformOrganizationMetrics, PlatformSkillMetrics, ReleaseActivity, SkillDefinition } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { TaskDetailDrawer } from '../components/TaskDetailDrawer';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
  platformMetrics: PlatformMetrics;
  platformSkillMetrics: PlatformSkillMetrics;
  platformOrganizationMetrics: PlatformOrganizationMetrics;
  platformAlerts: PlatformAlert[];
  releaseActivities: ReleaseActivity[];
  onPublishTask: (task: OperationsTask) => void;
};

const releaseActionLabel: Record<ReleaseActivity['action'], string> = {
  submitted_for_review: '提交治理',
  review_approved: '审核通过',
  health_check_passed: '健康检查通过',
  published_to_catalog: '发布完成',
  dependency_unblocked: '依赖已解锁',
};

export function AdminReleasePage({ tasks, skills, mcps, platformMetrics, platformSkillMetrics, platformOrganizationMetrics, platformAlerts, releaseActivities, onPublishTask }: Props) {
  const [scope, setScope] = useState('全部待发布');
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const releasableTasks = useMemo(() => tasks.filter((task) => {
    if (task.releaseStatus !== 'ready_to_publish') return false;
    if (scope === 'Skill 发布') return task.type === 'skill';
    if (scope === 'MCP 发布') return task.type === 'mcp';
    return true;
  }), [tasks, scope]);
  const publishedSkills = skills.filter((skill) => skill.releaseStatus === 'published');
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) || null;
  const findTaskByActivity = (activity: ReleaseActivity) => tasks.find((task) => (
    task.entityName === activity.entityName
    || task.title.includes(activity.entityName)
    || activity.entityName.includes(task.entityName)
  ));
  const selectedTaskActivities = selectedTask ? releaseActivities.filter((item) => (
    item.entityName === selectedTask.entityName
    || item.entityName === selectedTask.title
    || selectedTask.title.includes(item.entityName)
  )).slice(0, 5) : [];

  return <section className="management-page">
    <PageHeader
      eyebrow="Pipeline Overview"
      title="发布流水线"
      description="跨对象总览只负责查看阶段分布、待发布队列和风险提醒，真正操作仍回到对象详情页。"
    />
    <MetricStrip items={[
      { label: '待发布版本', value: releasableTasks.length },
      { label: '已纳入目录能力', value: publishedSkills.length, tone: 'success' },
      { label: '已发布 MCP', value: mcps.filter((mcp) => mcp.releaseStatus === 'published').length },
      { label: '已覆盖组织', value: platformMetrics.coverageOrganizations },
    ]} />
    <div className="release-filter-tabs">
      {['全部待发布', 'Skill 发布', 'MCP 发布'].map((item) => <button key={item} type="button" className={scope === item ? 'active' : ''} onClick={() => setScope(item)}>{item}</button>)}
    </div>
    <div className="detail-grid">
      <article className="panel-card span-2">
        <h3>跨对象总览</h3>
        <div className="metric-strip">
          <div className="metric-card"><span>月活用户</span><strong>{platformMetrics.monthlyActiveUsers.toLocaleString()}</strong></div>
          <div className="metric-card success"><span>整体成功率</span><strong>{platformMetrics.apiSuccessRate}</strong></div>
          <div className="metric-card"><span>最热能力</span><strong>{platformMetrics.topSkills[0]}</strong></div>
          <div className="metric-card"><span>组织覆盖</span><strong>{platformMetrics.coverageOrganizations} 家</strong></div>
        </div>
        <div className="release-confirm-card">
          <strong>流水线观察</strong>
          <span>这里用于快速判断哪些对象停在测试、提审或发布前，不替代对象详情页里的当前阶段主操作。</span>
        </div>
      </article>
      <article className="panel-card">
        <h3>高关注问题</h3>
        <div className="mini-timeline task-timeline">
          {platformMetrics.riskAlerts.map((alert) => <span key={alert}>{alert}<small>需运营与治理联合跟进</small></span>)}
        </div>
      </article>
    </div>
    <div className="detail-grid operations-insight-grid">
      <article className="panel-card">
        <h3>能力运营指标</h3>
        <div className="release-diff-list">
          <strong>最热能力</strong>
          {platformSkillMetrics.topSkills.map((skill) => <span key={skill}>{skill}</span>)}
          <strong>单次调用成本</strong>
          <span>{platformSkillMetrics.averageCostPerCall}</span>
        </div>
        <div className="release-confirm-card">
          <strong>运营建议</strong>
          <span>{platformSkillMetrics.recommendation}</span>
        </div>
      </article>
      <article className="panel-card">
        <h3>失败原因分布</h3>
        <div className="release-diff-list">
          {platformSkillMetrics.failureReasons.map((reason) => <span key={reason}>{reason}</span>)}
        </div>
      </article>
      <article className="panel-card">
        <h3>组织覆盖进展</h3>
        <div className="release-diff-list">
          {platformOrganizationMetrics.organizationItems.map((item) => <span key={item.organizationName}>{item.organizationName} · 覆盖 {item.coverageRate} · 月活 {item.activeUsers}</span>)}
        </div>
      </article>
      <article className="panel-card alert-list-card">
        <h3>告警与审计</h3>
        <div className="mini-timeline task-timeline">
          {platformAlerts.map((alert) => <span key={alert.id} className={`alert-${alert.level}`}>{alert.message}<small>{alert.source} · {alert.updatedAt} · {alert.level}</small></span>)}
        </div>
      </article>
      <article className="panel-card alert-list-card">
        <h3>最近发布动作</h3>
        <div className="mini-timeline task-timeline">
          {releaseActivities.slice(0, 5).map((item) => {
            const matchedTask = findTaskByActivity(item);
            return <button className="timeline-activity-button" key={item.id} type="button" onClick={() => matchedTask && setSelectedTaskId(matchedTask.id)}>{item.entityName} · {releaseActionLabel[item.action]}<small>{item.operator} · {item.createdAt}</small></button>;
          })}
        </div>
      </article>
    </div>
    <div className="task-stack">
      {releasableTasks.map((task) => <article className={`task-card stage-ready_to_publish task-card-clickable ${selectedTask?.id === task.id ? 'task-card-selected' : ''}`} key={task.id} onClick={() => setSelectedTaskId(task.id)}>
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
            <strong>当前目录版本</strong>
            <span>{task.type === 'skill' ? (skills.find((skill) => task.title.includes(skill.displayName))?.publishedVersion || '--') : (mcps.find((mcp) => task.title.includes(mcp.displayName))?.publishedVersion || '--')}</span>
          </div>
          <div>
            <strong>待发布版本</strong>
            <span>{task.type === 'skill' ? (skills.find((skill) => task.title.includes(skill.displayName))?.latestVersion || '--') : (mcps.find((mcp) => task.title.includes(mcp.displayName))?.latestVersion || '--')}</span>
          </div>
        </div>
        <div className="release-confirm-card">
          <strong>发布确认</strong>
          <span>版本差异：已通过自动测试与人工复核，确认后将替换当前集团目录版本，并保留回滚预案。</span>
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
          <button type="button" className="primary-action" onClick={(event) => {
            event.stopPropagation();
            onPublishTask(task);
          }}>手动发布</button>
        </div>
      </article>)}
    </div>
    {selectedTask ? <TaskDetailDrawer task={selectedTask} activities={selectedTaskActivities} onClose={() => setSelectedTaskId('')} /> : null}
  </section>;
}
