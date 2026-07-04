import { useMemo, useState } from 'react';
import { buildLifecycleMetrics, LifecycleStage, lifecycleStageOptions, stageLabel, UnifiedAssetRecord } from '../managementData';
import { MetricStrip, PageHeader, StatusBadge } from '../components/ManagementUi';

type Props = {
  assets: UnifiedAssetRecord[];
  onNavigate: (path: string) => void;
  onCreateSkill: () => void;
  onCreateMcp: () => void;
};

const lifecycleStageClassName = (stage: LifecycleStage) => `asset-stage-chip stage-${stage}`;

export function AssetDirectoryPage({ assets, onNavigate, onCreateSkill, onCreateMcp }: Props) {
  const [query, setQuery] = useState('');
  const [assetType, setAssetType] = useState<'全部类型' | 'skill' | 'mcp'>('全部类型');
  const [stage, setStage] = useState<'全部阶段' | LifecycleStage>('全部阶段');
  const lifecycleMetrics = buildLifecycleMetrics(assets);

  const filteredAssets = useMemo(() => assets.filter((asset) => {
    const haystack = `${asset.displayName}${asset.name}${asset.description}${asset.failureSummary || ''}${asset.dependencySummary}`.toLowerCase();
    const matchesQuery = haystack.includes(query.trim().toLowerCase());
    const matchesType = assetType === '全部类型' || asset.type === assetType;
    const matchesStage = stage === '全部阶段' || asset.lifecycleStage === stage;
    return matchesQuery && matchesType && matchesStage;
  }), [assets, query, assetType, stage]);

  return <section className="management-page asset-directory-page">
    <PageHeader
      eyebrow="Asset Directory"
      title="统一目录"
      description="把 Skill 与 MCP 放进同一张能力资产目录，先找到对象，再继续推进测试、提审与发布。"
      actions={<><button className="secondary-action" type="button" onClick={onCreateMcp}>＋ 接入 MCP</button><button className="primary-action" type="button" onClick={onCreateSkill}>＋ 新建 Skill</button></>}
    />
    <MetricStrip items={[
      { label: '能力资产总数', value: lifecycleMetrics.total },
      { label: '测试中', value: lifecycleMetrics.testing },
      { label: '待提审', value: lifecycleMetrics.review },
      { label: '可发布', value: lifecycleMetrics.publish, tone: 'success' },
    ]} />
    <div className="filter-bar">
      <label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索名称、标识、阻塞原因或依赖摘要" /></label>
      <select value={assetType} onChange={(event) => setAssetType(event.target.value as '全部类型' | 'skill' | 'mcp')}>
        <option>全部类型</option>
        <option value="skill">skill</option>
        <option value="mcp">mcp</option>
      </select>
      <select value={stage} onChange={(event) => setStage(event.target.value as '全部阶段' | LifecycleStage)}>
        <option>全部阶段</option>
        {lifecycleStageOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
      </select>
      <span className="filter-result">显示 {filteredAssets.length} / {assets.length}</span>
    </div>
    <div className="asset-directory-grid">
      {filteredAssets.map((asset) => <article className="asset-directory-card" key={asset.id} onClick={() => onNavigate(asset.route)}>
        <div className="asset-directory-top">
          <div>
            <span className="asset-type-pill">{asset.type.toUpperCase()}</span>
            <h2>{asset.displayName}</h2>
            <code>{asset.name}</code>
          </div>
          <StatusBadge status={asset.status} />
        </div>
        <p>{asset.description}</p>
        <div className="asset-directory-meta">
          <span className={lifecycleStageClassName(asset.lifecycleStage)}>{stageLabel[asset.lifecycleStage]}</span>
          <span>{asset.category}</span>
          <span>{asset.riskLabel}</span>
          <span>{asset.updatedAt}</span>
        </div>
        <div className="asset-directory-summary">
          <div><span>依赖关系摘要</span><strong>{asset.dependencySummary}</strong></div>
          <div><span>影响组织与风险提示</span><strong>{asset.organizationSummary}</strong></div>
        </div>
        {asset.failureSummary ? <div className="asset-directory-alert"><strong>最近阻塞原因或失败原因</strong><p>{asset.failureSummary}</p></div> : null}
        <footer>
          <span>负责人：{asset.owner}</span>
          <b>继续处理 →</b>
        </footer>
      </article>)}
    </div>
  </section>;
}
