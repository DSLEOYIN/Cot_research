import { countTasksByLifecycleStage, LifecycleStage, McpDefinition, OperationsTask, ReleaseActivity, resolveActivityRoute, resolveTaskRoute, SkillDefinition, stageLabel, taskLifecycleStage, UnifiedAssetRecord } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { TaskDetailDrawer } from '../components/TaskDetailDrawer';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  assets: UnifiedAssetRecord[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
  releaseActivities: ReleaseActivity[];
  onNavigate: (path: string) => void;
};

const releaseActionLabel: Record<ReleaseActivity['action'], string> = {
  submitted_for_review: '提交治理',
  review_approved: '审核通过',
  health_check_passed: '健康检查通过',
  published_to_catalog: '发布完成',
  dependency_unblocked: '依赖已解锁',
};

export function AdminWorkbenchPage({ tasks, assets, skills, mcps, releaseActivities, onNavigate }: Props) {
  const [scope, setScope] = useState('全部任务');
  const [selectedTaskId, setSelectedTaskId] = useState(tasks[0]?.id || '');
  const isLifecycleTask = (task: OperationsTask, stage: LifecycleStage) => taskLifecycleStage(task) === stage;
  const findAssetByTask = (task: OperationsTask) => assets.find((asset) => (
    asset.type === task.type
    && (task.entityName === asset.name || task.entityName === asset.displayName || task.title.includes(asset.displayName))
  ));
  const blockedTasks = tasks.filter((task) => isLifecycleTask(task, 'blocked'));
  const publishTasks = tasks.filter((task) => isLifecycleTask(task, 'publish'));
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) || null;
  const reviewReturnAssets = assets.filter((asset) => asset.lifecycleStage === 'review_rejected' || (asset.failureSummary || '').length > 0).slice(0, 4);
  const recentObjects = releaseActivities.map((activity) => assets.find((asset) => (
    asset.type === activity.entityType
    && (activity.entityName === asset.name || activity.entityName === asset.displayName)
  ))).filter((asset, index, list): asset is UnifiedAssetRecord => Boolean(asset) && list.findIndex((item) => item?.id === asset?.id) === index).slice(0, 4);
  const dependencyRecoveryActivities = releaseActivities.filter((activity) => activity.action === 'dependency_unblocked').slice(0, 3);
  const visibleTasks = useMemo(() => {
    if (scope === '待审核') return tasks.filter((task) => isLifecycleTask(task, 'review'));
    if (scope === '待发布') return tasks.filter((task) => isLifecycleTask(task, 'publish'));
    if (scope === '依赖阻塞') return tasks.filter((task) => isLifecycleTask(task, 'blocked'));
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
  const assetStageLabel = (task: OperationsTask) => findAssetByTask(task)?.lifecycleStage ? stageLabel[findAssetByTask(task)!.lifecycleStage] : stageLabel[taskLifecycleStage(task)];
  const taskRoute = (task: OperationsTask) => resolveTaskRoute(task, skills, mcps);
  const timelineActivityRoute = (activity: ReleaseActivity) => resolveActivityRoute(activity, assets);

  return <section className="management-page admin-workbench-page">
    <PageHeader
      eyebrow="Developer Workbench"
      title="工作台"
      description="我的待处理事项会直接告诉你当前卡在哪一步，并把你带到可继续处理的位置。"
      actions={<><button className="secondary-action" type="button" onClick={() => onNavigate('/admin/pipeline')}>查看发布流水线</button><button className="primary-action" type="button" onClick={() => onNavigate('/admin/assets')}>进入统一目录</button></>}
    />
    <MetricStrip items={[
      { label: '待处理治理事项', value: assets.filter((item) => ['review', 'publish', 'review_rejected'].includes(item.lifecycleStage)).length },
      { label: '按资产阶段继续处理', value: assets.filter((item) => ['testing', 'review', 'publish', 'blocked', 'review_rejected'].includes(item.lifecycleStage)).length, tone: 'success' },
      { label: '测试中能力', value: assets.filter((item) => item.lifecycleStage === 'testing').length },
      { label: '依赖阻塞', value: assets.filter((item) => item.lifecycleStage === 'blocked').length, tone: 'danger' },
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
              <i>{assetStageLabel(task)}</i>
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
                onNavigate(taskRoute(task));
              }}>继续处理</button>
            </div>
          </article>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>最近我操作过的对象</h3>
        <div className="workbench-recent-grid">
          {recentObjects.map((asset) => <button key={asset.id} type="button" onClick={() => onNavigate(asset.route)}>
            <span>{asset.type.toUpperCase()} · {stageLabel[asset.lifecycleStage]}</span>
            <strong>{asset.displayName}</strong>
            <small>{asset.updatedAt}</small>
          </button>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>关键阻塞</h3>
        <div className="dependency-list">
          {blockedTasks.map((task) => <button type="button" key={task.id} onClick={() => onNavigate(taskRoute(task))}>
            {task.title}
            <b>继续处理 →</b>
          </button>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>审核退回待补充</h3>
        <div className="review-return-list">
          {reviewReturnAssets.map((asset) => <button key={asset.id} type="button" onClick={() => onNavigate(asset.route)}>
            <strong>{asset.displayName}</strong>
            <span>{asset.failureSummary || '待补充审核资料'}</span>
          </button>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>最近状态时间线</h3>
        <div className="mini-timeline task-timeline">
          {releaseActivities.slice(0, 5).map((item) => {
            return <button className="timeline-activity-button" key={item.id} type="button" onClick={() => onNavigate(timelineActivityRoute(item))}>{item.entityName} · {releaseActionLabel[item.action]}<small>{item.operator} · {item.createdAt}</small></button>;
          })}
        </div>
      </article>

      <article className="panel-card">
        <h3>依赖解锁后恢复测试</h3>
        <div className="dependency-list">
          {dependencyRecoveryActivities.length === 0 ? <span>当前没有刚解锁的依赖对象。</span> : dependencyRecoveryActivities.map((item) => <button type="button" key={item.id} onClick={() => onNavigate(timelineActivityRoute(item))}>
            {item.entityName}
            <b>恢复测试 →</b>
          </button>)}
        </div>
      </article>
      {selectedTask ? <TaskDetailDrawer task={selectedTask} activities={selectedTaskActivities} onClose={() => setSelectedTaskId('')} /> : null}
    </div>
  </section>;
}
