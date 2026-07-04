import { OperationsTask, ReleaseActivity, stageLabel, taskLifecycleStage } from '../managementData';

type Props = {
  task: OperationsTask;
  activities: ReleaseActivity[];
  onClose: () => void;
};

const releaseActionLabel: Record<ReleaseActivity['action'], string> = {
  submitted_for_review: '提交治理',
  review_approved: '审核通过',
  health_check_passed: '健康检查通过',
  published_to_catalog: '发布完成',
  dependency_unblocked: '依赖已解锁',
};

export function TaskDetailDrawer({ task, activities, onClose }: Props) {
  return <aside className="permission-drawer task-detail-drawer" aria-label="任务详情抽屉">
    <div className="permission-drawer-head">
      <div>
        <span>Task Detail</span>
        <h3>{task.title}</h3>
        <p>查看当前治理任务的状态迁移、责任人、依赖信息和最近动作。</p>
      </div>
      <button className="secondary-action compact-action" type="button" onClick={onClose}>关闭</button>
    </div>

    <div className="permission-profile-grid">
      <div><span>当前状态</span><strong>{stageLabel[taskLifecycleStage(task)]}</strong><small>{task.type === 'skill' ? 'Skill 任务' : 'MCP 子任务'} · {task.priority}</small></div>
      <div><span>负责人</span><strong>{task.owner}</strong><small>更新时间：{task.updatedAt}</small></div>
      <div><span>自动测试</span><strong>{task.autoTestPassRate}</strong><small>{task.failureReason || '当前无失败原因'}</small></div>
      <div><span>关联实体</span><strong>{task.entityName}</strong><small>{task.parentTaskId ? `父任务：${task.parentTaskId}` : '当前为主任务'}</small></div>
    </div>

    <div className="permission-detail-columns">
      <section>
        <h4>状态迁移原因</h4>
        <div className="release-confirm-card">
          <strong>任务摘要</strong>
          <span>{task.summary}</span>
        </div>
        {task.blockedBy ? <div className="task-blocked-note"><strong>依赖阻塞</strong><span>{task.blockedBy}</span></div> : null}
        {task.failureReason ? <div className="task-failure-note"><strong>失败原因</strong><span>{task.failureReason}</span></div> : null}
        {task.reviewNotes ? <div className="release-confirm-card"><strong>治理备注</strong><span>{task.reviewNotes}</span></div> : null}
      </section>

      <section>
        <h4>最近动作</h4>
        <div className="mini-timeline task-timeline">
          {activities.length ? activities.map((item) => <span key={item.id}>{releaseActionLabel[item.action]}<small>{item.operator} · {item.createdAt}</small></span>) : <span>暂无治理动作<small>等待新的状态变更</small></span>}
        </div>
      </section>
    </div>
  </aside>;
}
