import { McpDefinition, OperationsTask, ReleaseStatus, SkillDefinition, releaseStatusLabel } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
  onNavigate: (path: string) => void;
};

const countByStage = (tasks: OperationsTask[], stage: ReleaseStatus) => tasks.filter((task) => task.stage === stage).length;

export function AdminWorkbenchPage({ tasks, skills, mcps, onNavigate }: Props) {
  const [scope, setScope] = useState('全部任务');
  const blockedTasks = tasks.filter((task) => task.stage === 'blocked_by_dependency');
  const reviewTasks = tasks.filter((task) => task.stage === 'ready_for_review');
  const publishTasks = tasks.filter((task) => task.stage === 'ready_to_publish');
  const visibleTasks = useMemo(() => {
    if (scope === '待审核') return tasks.filter((task) => task.stage === 'ready_for_review');
    if (scope === '待发布') return tasks.filter((task) => task.stage === 'ready_to_publish');
    if (scope === '依赖阻塞') return tasks.filter((task) => task.stage === 'blocked_by_dependency');
    return tasks;
  }, [tasks, scope]);

  return <section className="management-page admin-workbench-page">
    <PageHeader
      eyebrow="Operations"
      title="系统管理工作台"
      description="围绕生成、自动测试、审核和发布推进 Skill 与 MCP 任务。"
      actions={<><button className="secondary-action" type="button" onClick={() => onNavigate('/admin/mcps')}>查看 MCP 管理</button><button className="primary-action" type="button" onClick={() => onNavigate('/admin/skills')}>进入 AI 开发台</button></>}
    />
    <MetricStrip items={[
      { label: '待审核', value: countByStage(tasks, 'ready_for_review') },
      { label: '待发布', value: countByStage(tasks, 'ready_to_publish'), tone: 'success' },
      { label: '测试中', value: countByStage(tasks, 'testing') },
      { label: '依赖阻塞', value: countByStage(tasks, 'blocked_by_dependency'), tone: 'danger' },
    ]} />

    <section className="workbench-hero">
      <div className="workbench-hero-card hero-accent">
        <span>WORKBENCH</span>
        <h2>AI 开发台</h2>
        <p>运维人员通过混合输入提交目标、场景和期望输出，系统自动生成 Skill 或 MCP 草案。</p>
        <button type="button" className="primary-action" onClick={() => onNavigate('/admin/skills')}>新建开发任务</button>
      </div>
      <div className="workbench-hero-card">
        <span>PIPELINE</span>
        <h2>审核中心</h2>
        <p>{reviewTasks.length} 个任务待审核，重点查看功能、流程、依赖 MCP 和示例输入输出。</p>
        <button type="button" className="secondary-action" onClick={() => onNavigate('/admin/skills')}>处理待审核任务</button>
      </div>
      <div className="workbench-hero-card">
        <span>RELEASE</span>
        <h2>发布管理</h2>
        <p>{publishTasks.length} 个版本已通过审核但尚未发布，商城同名 Skill 仅展示一个当前版本。</p>
        <button type="button" className="secondary-action" onClick={() => onNavigate('/admin/mcps')}>查看发布依赖</button>
      </div>
    </section>

    <div className="detail-grid workbench-grid">
      <article className="panel-card span-2">
        <div className="section-toolbar">
          <div><h3>待处理任务</h3><p>优先展示测试失败、待审核和待发布任务。</p></div>
          <div className="task-filter-tabs">
            {['全部任务', '待审核', '待发布', '依赖阻塞'].map((item) => <button key={item} type="button" className={scope === item ? 'active' : ''} onClick={() => setScope(item)}>{item}</button>)}
          </div>
        </div>
        <div className="task-stack">
          {visibleTasks.map((task) => <article key={task.id} className={`task-card stage-${task.stage}`}>
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
          </article>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>依赖阻塞</h3>
        <div className="dependency-list">
          {blockedTasks.map((task) => <button type="button" key={task.id} onClick={() => onNavigate('/admin/mcps')}>
            {task.title}
            <b>查看依赖 →</b>
          </button>)}
        </div>
      </article>

      <article className="panel-card">
        <h3>发布概览</h3>
        <div className="stat-stack">
          <strong>{skills.filter((item) => item.releaseStatus === 'published').length}</strong>
          <span>已发布 Skill</span>
          <strong>{mcps.filter((item) => item.releaseStatus === 'published').length}</strong>
          <span>已发布 MCP</span>
        </div>
      </article>
    </div>
  </section>;
}
