import { McpDefinition, OperationsTask, PlatformMetrics, ReleaseActivity, ReleaseStatus, SkillDefinition, releaseStatusLabel } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { TaskDetailDrawer } from '../components/TaskDetailDrawer';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
  platformMetrics: PlatformMetrics;
  releaseActivities: ReleaseActivity[];
  onNavigate: (path: string) => void;
};

const countByStage = (tasks: OperationsTask[], stage: ReleaseStatus) => tasks.filter((task) => task.stage === stage).length;

const releaseActionLabel: Record<ReleaseActivity['action'], string> = {
  submitted_for_review: '提交治理',
  review_approved: '审核通过',
  health_check_passed: '健康检查通过',
  published_to_catalog: '发布完成',
  dependency_unblocked: '依赖已解锁',
};

export function AdminWorkbenchPage({ tasks, skills, mcps, platformMetrics, releaseActivities, onNavigate }: Props) {
  const [scope, setScope] = useState('全部任务');
  const [selectedTaskId, setSelectedTaskId] = useState(tasks[0]?.id || '');
  const blockedTasks = tasks.filter((task) => task.stage === 'blocked_by_dependency');
  const reviewTasks = tasks.filter((task) => task.stage === 'ready_for_review');
  const publishTasks = tasks.filter((task) => task.stage === 'ready_to_publish');
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) || null;
  const visibleTasks = useMemo(() => {
    if (scope === '待审核') return tasks.filter((task) => task.stage === 'ready_for_review');
    if (scope === '待发布') return tasks.filter((task) => task.stage === 'ready_to_publish');
    if (scope === '依赖阻塞') return tasks.filter((task) => task.stage === 'blocked_by_dependency');
    return tasks;
  }, [tasks, scope]);
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
  const resolveTaskRoute = (task: OperationsTask) => {
    if (task.type === 'skill') {
      const matchedSkill = skills.find((skill) => (
        task.entityName === skill.name
        || task.entityName === skill.displayName
        || task.title.includes(skill.displayName)
      ));
      return matchedSkill ? `/admin/skills/${matchedSkill.name}` : '/admin/assets';
    }
    const matchedMcp = mcps.find((mcp) => (
      task.entityName === mcp.name
      || task.entityName === mcp.displayName
      || task.title.includes(mcp.displayName)
    ));
    return matchedMcp ? `/admin/mcps/${matchedMcp.name}` : '/admin/assets';
  };

  return <section className="management-page admin-workbench-page">
    <PageHeader
      eyebrow="Developer Workbench"
      title="工作台"
      description="我的待处理事项会直接告诉你当前卡在哪一步，并把你带到可继续处理的位置。"
      actions={<><button className="secondary-action" type="button" onClick={() => onNavigate('/admin/pipeline')}>查看发布流水线</button><button className="primary-action" type="button" onClick={() => onNavigate('/admin/assets')}>进入统一目录</button></>}
    />
    <MetricStrip items={[
      { label: '待处理治理事项', value: countByStage(tasks, 'ready_for_review') + countByStage(tasks, 'ready_to_publish') },
      { label: '集团已发布 Skill', value: skills.filter((item) => item.releaseStatus === 'published').length, tone: 'success' },
      { label: '测试中能力', value: countByStage(tasks, 'testing') },
      { label: '依赖阻塞', value: countByStage(tasks, 'blocked_by_dependency'), tone: 'danger' },
    ]} />

    <section className="workbench-hero">
      <div className="workbench-hero-card hero-accent">
        <span>WORKBENCH</span>
        <h2>我的待处理事项</h2>
        <p>优先回到测试失败、依赖阻塞、待提审和可发布对象，不再先看泛运营指标。</p>
        <button type="button" className="primary-action" onClick={() => onNavigate('/admin/assets')}>进入统一目录</button>
      </div>
      <div className="workbench-hero-card">
        <span>PIPELINE</span>
        <h2>发布流水线</h2>
        <p>{publishTasks.length} 个对象可继续推进发布，跨对象总览只负责排队和切换，不取代对象详情操作。</p>
        <button type="button" className="secondary-action" onClick={() => onNavigate('/admin/pipeline')}>查看发布流水线</button>
      </div>
      <div className="workbench-hero-card">
        <span>OPERATIONS</span>
        <h2>运行与权限</h2>
        <p>影响组织与风险提示在详情页只读展示，真正的授权与审计放到辅助区处理。</p>
        <button type="button" className="secondary-action" onClick={() => onNavigate('/admin/operations-center')}>查看运行与权限</button>
      </div>
    </section>

    <div className="detail-grid workbench-grid">
      <article className="panel-card span-2">
        <div className="section-toolbar">
          <div><h3>我的待处理事项</h3><p>优先展示测试失败、待提审、待发布和依赖阻塞的对象，并提供继续处理入口。</p></div>
          <div className="task-filter-tabs">
            {['全部任务', '待审核', '待发布', '依赖阻塞'].map((item) => <button key={item} type="button" className={scope === item ? 'active' : ''} onClick={() => setScope(item)}>{item}</button>)}
          </div>
        </div>
        <div className="task-stack workbench-task-list">
          {visibleTasks.map((task) => <article key={task.id} className={`task-card stage-${task.stage} task-card-clickable ${selectedTask?.id === task.id ? 'task-card-selected' : ''}`} onClick={() => setSelectedTaskId(task.id)}>
            <div className="task-card-top">
              <div><span>{task.type === 'skill' ? 'Skill 任务' : 'MCP 子任务'} · {task.priority}</span><strong>{task.title}</strong></div>
              <i>{releaseStatusLabel[task.releaseStatus]}</i>
            </div>
            <p>{task.summary}</p>
            <div className="task-card-meta">
              <span>负责人：{task.owner}</span>
              <span>自动测试：{task.autoTestPassRate}</span>
              <span>更新时间：{task.updatedAt}</span>
            </div>
            {task.failureReason && <div className="task-failure-note"><strong>失败原因</strong><span>{task.failureReason}</span></div>}
            {task.blockedBy && <div className="task-blocked-note"><strong>阻塞原因</strong><span>{task.blockedBy}</span></div>}
            {task.parentTaskId && <div className="task-child-link"><span>MCP 子任务</span><b>{task.parentTaskId}</b></div>}
            <div className="review-buttons">
              <button type="button" className="secondary-action" onClick={(event) => {
                event.stopPropagation();
                onNavigate('/admin/assets');
              }}>统一目录</button>
              <button type="button" className="primary-action" onClick={(event) => {
                event.stopPropagation();
                onNavigate(resolveTaskRoute(task));
              }}>继续处理</button>
            </div>
          </article>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>关键阻塞</h3>
        <div className="dependency-list">
          {blockedTasks.map((task) => <button type="button" key={task.id} onClick={() => onNavigate(resolveTaskRoute(task))}>
            {task.title}
            <b>继续处理 →</b>
          </button>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>能力供给概览</h3>
        <div className="stat-stack">
          <strong>{skills.filter((item) => item.releaseStatus === 'published').length}</strong>
          <span>已发布 Skill</span>
          <strong>{mcps.filter((item) => item.releaseStatus === 'published').length}</strong>
          <span>已发布 MCP</span>
        </div>
      </article>

      <article className="panel-card">
        <h3>最近状态时间线</h3>
        <div className="mini-timeline task-timeline">
          {releaseActivities.slice(0, 5).map((item) => {
            const matchedTask = findTaskByActivity(item);
            return <button className="timeline-activity-button" key={item.id} type="button" onClick={() => matchedTask && setSelectedTaskId(matchedTask.id)}>{item.entityName} · {releaseActionLabel[item.action]}<small>{item.operator} · {item.createdAt}</small></button>;
          })}
        </div>
      </article>

      <article className="panel-card span-2">
        <h3>平台活跃与覆盖</h3>
        <div className="definition-grid">
          <div><span>月活用户</span><strong>{platformMetrics.monthlyActiveUsers.toLocaleString()}</strong></div>
          <div><span>调用成功率</span><strong>{platformMetrics.apiSuccessRate}</strong></div>
          <div><span>覆盖组织</span><strong>{platformMetrics.coverageOrganizations} 家</strong></div>
          <div><span>热门能力</span><strong>{platformMetrics.topSkills.join(' / ')}</strong></div>
        </div>
      </article>

      {selectedTask ? <TaskDetailDrawer task={selectedTask} activities={selectedTaskActivities} onClose={() => setSelectedTaskId('')} /> : null}
    </div>
  </section>;
}
