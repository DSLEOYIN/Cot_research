import { LifecycleStage, McpDefinition, OperationsTask, PlatformAlert, PlatformMetrics, PlatformOrganizationMetrics, PlatformSkillMetrics, ReleaseActivity, SkillDefinition, UnifiedAssetRecord } from '../managementData';
import { MetricStrip, PageHeader } from '../components/ManagementUi';
import { useMemo, useState } from 'react';

type Props = {
  tasks: OperationsTask[];
  assets: UnifiedAssetRecord[];
  skills: SkillDefinition[];
  mcps: McpDefinition[];
  platformMetrics: PlatformMetrics;
  platformSkillMetrics: PlatformSkillMetrics;
  platformOrganizationMetrics: PlatformOrganizationMetrics;
  platformAlerts: PlatformAlert[];
  releaseActivities: ReleaseActivity[];
  onNavigate: (path: string) => void;
  onPublishTask: (task: OperationsTask) => void;
};

const releaseActionLabel: Record<ReleaseActivity['action'], string> = {
  submitted_for_review: '提交治理',
  review_approved: '审核通过',
  health_check_passed: '健康检查通过',
  published_to_catalog: '发布完成',
  dependency_unblocked: '依赖已解锁',
};

export function AdminReleasePage({ tasks, assets, skills, mcps, platformMetrics, platformSkillMetrics, platformOrganizationMetrics, platformAlerts, releaseActivities, onNavigate, onPublishTask }: Props) {
  const [scope, setScope] = useState('全部待发布');
  const releaseAssets = useMemo(() => assets.filter((asset) => {
    if (asset.releaseStatus !== 'ready_to_publish') return false;
    if (scope === 'Skill 发布') return asset.type === 'skill';
    if (scope === 'MCP 发布') return asset.type === 'mcp';
    return true;
  }).map((asset) => ({
    asset,
    task: tasks.find((task) => task.type === asset.type && (
      task.entityName === asset.name
      || task.entityName === asset.displayName
      || task.title.includes(asset.displayName)
    )) || null,
  })), [assets, tasks, scope]);
  const publishedSkills = skills.filter((skill) => skill.releaseStatus === 'published');
  const stageCounts = assets.reduce<Record<LifecycleStage, number>>((counts, asset) => {
    counts[asset.lifecycleStage] = (counts[asset.lifecycleStage] || 0) + 1;
    return counts;
  }, { draft: 0, testing: 0, review: 0, review_rejected: 0, publish: 0, published: 0, blocked: 0 });
  const highRiskAssets = assets.filter((asset) => asset.riskLabel.includes('高'));
  const findAssetByActivity = (activity: ReleaseActivity) => assets.find((asset) => (
    asset.name === activity.entityName
    || asset.displayName === activity.entityName
    || activity.entityName.includes(asset.displayName)
  ));

  return <section className="management-page">
    <PageHeader
      eyebrow="Pipeline Overview"
      title="发布流水线"
      description="跨对象总览只负责查看阶段分布、待发布队列和风险提醒，真正操作统一回到对象详情页。"
    />
    <MetricStrip items={[
      { label: '待发布版本', value: releaseAssets.length },
      { label: '已纳入目录能力', value: publishedSkills.length, tone: 'success' },
      { label: '已发布 MCP', value: mcps.filter((mcp) => mcp.releaseStatus === 'published').length },
      { label: '高风险对象', value: highRiskAssets.length, tone: 'danger' },
    ]} />
    <div className="release-filter-tabs">
      {['全部待发布', 'Skill 发布', 'MCP 发布'].map((item) => <button key={item} type="button" className={scope === item ? 'active' : ''} onClick={() => setScope(item)}>{item}</button>)}
    </div>
    <div className="detail-grid">
      <article className="panel-card span-2">
        <h3>跨对象总览</h3>
        <div className="metric-strip">
          <div className="metric-card"><span>测试中</span><strong>{stageCounts.testing}</strong></div>
          <div className="metric-card"><span>待提审</span><strong>{stageCounts.review}</strong></div>
          <div className="metric-card success"><span>待发布</span><strong>{stageCounts.publish}</strong></div>
          <div className="metric-card danger"><span>依赖阻塞</span><strong>{stageCounts.blocked}</strong></div>
        </div>
        <div className="release-confirm-card">
          <strong>流水线观察</strong>
          <span>这里用于快速判断哪些对象停在测试、提审或发布前，不替代对象详情页里的当前阶段主操作。</span>
        </div>
      </article>
      <article className="panel-card">
        <h3>高关注问题</h3>
        <div className="mini-timeline task-timeline">
          {platformMetrics.riskAlerts.map((alert) => <span key={alert}>{alert}<small>需对象负责人在详情页处理</small></span>)}
        </div>
      </article>
    </div>
    <div className="detail-grid operations-insight-grid">
      <article className="panel-card">
        <h3>发布优先级参考</h3>
        <div className="release-diff-list">
          <strong>优先发布对象</strong>
          {platformSkillMetrics.topSkills.map((skill) => <span key={skill}>{skill}</span>)}
          <strong>统一资产规模</strong>
          <span>{assets.length} 个对象</span>
        </div>
        <div className="release-confirm-card">
          <strong>发布建议</strong>
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
            const matchedAsset = findAssetByActivity(item);
            return <button className="timeline-activity-button" key={item.id} type="button" onClick={() => matchedAsset && onNavigate(matchedAsset.route)}>{item.entityName} · {releaseActionLabel[item.action]}<small>{item.operator} · {item.createdAt}</small></button>;
          })}
        </div>
      </article>
    </div>
    <div className="task-stack">
      {releaseAssets.map(({ asset, task }) => <article className="task-card stage-ready_to_publish task-card-clickable" key={asset.id} onClick={() => onNavigate(asset.route)}>
        <div className="task-card-top">
          <div><span>{asset.type === 'skill' ? 'Skill 发布' : 'MCP 发布'}</span><strong>{asset.displayName}</strong></div>
          <i>待发布</i>
        </div>
        <p>{asset.description}</p>
        <div className="task-card-meta">
          <span>负责人：{asset.owner}</span>
          <span>风险等级：{asset.riskLabel}</span>
          <span>更新时间：{asset.updatedAt}</span>
        </div>
        <div className="release-compare-grid">
          <div>
            <strong>当前目录版本</strong>
            <span>{asset.type === 'skill' ? (skills.find((skill) => skill.name === asset.name)?.publishedVersion || '--') : (mcps.find((mcp) => mcp.name === asset.name)?.publishedVersion || '--')}</span>
          </div>
          <div>
            <strong>待发布版本</strong>
            <span>{asset.type === 'skill' ? (skills.find((skill) => skill.name === asset.name)?.latestVersion || '--') : (mcps.find((mcp) => mcp.name === asset.name)?.latestVersion || '--')}</span>
          </div>
        </div>
        <div className="release-confirm-card">
          <strong>发布确认</strong>
          <span>版本差异：已通过自动测试与人工复核，确认后将替换当前集团目录版本，并保留回滚预案。</span>
        </div>
        <div className="release-diff-list">
          <strong>差异预览</strong>
          <span>{asset.dependencySummary}</span>
          <span>{asset.organizationSummary}</span>
          <span>{asset.failureSummary || '当前无阻塞项，详情页可继续执行发布确认。'}</span>
          <strong>发布检查清单</strong>
          <span>{task?.autoTestPassRate || '自动测试通过'}</span>
          <span>{task?.reviewNotes || '人工审核通过'}</span>
          <span>回滚预案已确认</span>
        </div>
        <div className="review-buttons">
          <button type="button" className="secondary-action" onClick={(event) => {
            event.stopPropagation();
            onNavigate(asset.route);
          }}>查看对象详情</button>
          <button type="button" className="primary-action" onClick={(event) => {
            event.stopPropagation();
            if (task) onPublishTask(task);
          }}>手动发布</button>
        </div>
      </article>)}
    </div>
  </section>;
}
