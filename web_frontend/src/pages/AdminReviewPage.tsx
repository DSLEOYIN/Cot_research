import { OperationsTask, releaseStatusLabel } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  onNavigate: (path: string) => void;
};

export function AdminReviewPage({ tasks, onNavigate }: Props) {
  const [priority, setPriority] = useState('全部优先级');
  const reviewTasks = useMemo(() => tasks.filter((task) => task.releaseStatus === 'ready_for_review' && (priority === '全部优先级' || task.priority === priority)), [tasks, priority]);
  const blockedTasks = tasks.filter((task) => task.releaseStatus === 'blocked_by_dependency');

  return <section className="management-page">
    <PageHeader
      eyebrow="Review"
      title="审核中心"
      description="审核功能、流程、依赖 MCP 和示例输入输出，决定版本是否进入待发布。"
      actions={<button className="secondary-action" type="button" onClick={() => onNavigate('/admin/skills')}>返回 AI 开发台</button>}
    />
    <MetricStrip items={[
      { label: '待审核任务', value: reviewTasks.length },
      { label: '依赖阻塞', value: blockedTasks.length, tone: 'danger' },
      { label: '今日已处理', value: 6, tone: 'success' },
      { label: '平均审阅时长', value: '18 分钟' },
    ]} />
    <div className="filter-bar">
      <label><select value={priority} onChange={(event) => setPriority(event.target.value)}><option>全部优先级</option><option>P0</option><option>P1</option><option>P2</option></select></label>
      <span className="filter-result">当前显示 {reviewTasks.length} 个待审核任务</span>
    </div>
    <div className="task-stack">
      {reviewTasks.map((task) => <article className="task-card stage-ready_for_review" key={task.id}>
        <div className="task-card-top">
          <div><span>{task.type === 'skill' ? 'Skill 审核' : 'MCP 审核'} · {task.priority}</span><strong>{task.title}</strong></div>
          <i>{releaseStatusLabel[task.releaseStatus]}</i>
        </div>
        <p>{task.summary}</p>
        <div className="task-card-meta">
          <span>负责人：{task.owner}</span>
          <span>自动测试：{task.autoTestPassRate}</span>
          <span>更新时间：{task.updatedAt}</span>
        </div>
        {task.reviewNotes && <div className="task-child-link"><span>审核提示</span><b>{task.reviewNotes}</b></div>}
        <div className="review-action-strip">
          <div>
            <strong>驳回原因</strong>
            <span>示例输入输出不足、依赖说明不清或流程解释不完整时，退回编辑。</span>
          </div>
          <div className="review-buttons">
            <button type="button" className="secondary-action">驳回</button>
            <button type="button" className="primary-action">审核通过</button>
          </div>
        </div>
      </article>)}
    </div>
  </section>;
}
