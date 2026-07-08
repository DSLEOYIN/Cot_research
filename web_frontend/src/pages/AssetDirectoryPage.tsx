import { useEffect, useMemo, useState } from 'react';
import { buildLifecycleMetrics, LifecycleStage, lifecycleStageOptions, stageLabel, UnifiedAssetRecord } from '../managementData';
import { MetricStrip, PageHeader, StatusBadge } from '../components/ManagementUi';

type Props = {
  assets: UnifiedAssetRecord[];
  currentOwner?: string;
  onNavigate: (path: string) => void;
  onCreateSkill: () => void;
  onCreateMcp: () => void;
};

const lifecycleStageClassName = (stage: LifecycleStage) => `asset-stage-chip stage-${stage}`;
const riskValue = (asset: UnifiedAssetRecord) => asset.riskLabel.replace('风险：', '').trim();
const hasDependency = (asset: UnifiedAssetRecord) => asset.dependencySummary !== '待补依赖摘要' && asset.dependencySummary !== '无' && asset.dependencySummary.trim().length > 0;
const isDependencyBlocked = (asset: UnifiedAssetRecord) => asset.lifecycleStage === 'blocked' || asset.dependencySummary.includes('阻塞') || asset.dependencySummary.includes('等待');
const isPendingAsset = (asset: UnifiedAssetRecord) => asset.lifecycleStage !== 'published';
const assetDirectoryAlertTone = (asset: UnifiedAssetRecord) => asset.lifecycleStage === 'blocked' || (asset.failureSummary || '').includes('失败') ? 'tone-danger' : 'tone-warning';

export function AssetDirectoryPage({ assets, currentOwner = '', onNavigate, onCreateSkill, onCreateMcp }: Props) {
  const [query, setQuery] = useState('');
  const [assetType, setAssetType] = useState<'全部类型' | 'skill' | 'mcp'>('全部类型');
  const [stage, setStage] = useState<'全部阶段' | LifecycleStage>('全部阶段');
  const [risk, setRisk] = useState<'全部风险' | '低' | '中' | '高'>('全部风险');
  const [owner, setOwner] = useState('全部负责人');
  const [dependency, setDependency] = useState<'全部依赖' | '有依赖' | '依赖阻塞' | '无依赖'>('全部依赖');
  const [pending, setPending] = useState<'全部状态' | '仅待处理' | '仅已发布'>('全部状态');
  const [groupBy, setGroupBy] = useState<'不分组' | '按阶段分组' | '按类型分组' | '按风险分组'>('不分组');
  const [onlyMinePending, setOnlyMinePending] = useState(false);
  const [pageSize, setPageSize] = useState<6 | 12 | 24>(12);
  const [page, setPage] = useState(1);
  const lifecycleMetrics = buildLifecycleMetrics(assets);
  const ownerOptions = useMemo(() => ['全部负责人', ...Array.from(new Set(assets.map((asset) => asset.owner)))], [assets]);

  const filteredAssets = useMemo(() => assets.filter((asset) => {
    const haystack = `${asset.displayName}${asset.name}${asset.description}${asset.failureSummary || ''}${asset.dependencySummary}`.toLowerCase();
    const matchesQuery = haystack.includes(query.trim().toLowerCase());
    const matchesType = assetType === '全部类型' || asset.type === assetType;
    const matchesStage = stage === '全部阶段' || asset.lifecycleStage === stage;
    const matchesRisk = risk === '全部风险' || riskValue(asset) === risk;
    const matchesOwner = owner === '全部负责人' || asset.owner === owner;
    const matchesDependency = dependency === '全部依赖'
      || (dependency === '有依赖' && hasDependency(asset))
      || (dependency === '依赖阻塞' && isDependencyBlocked(asset))
      || (dependency === '无依赖' && !hasDependency(asset));
    const matchesPending = pending === '全部状态'
      || (pending === '仅待处理' && isPendingAsset(asset))
      || (pending === '仅已发布' && !isPendingAsset(asset));
    const matchesMinePending = !onlyMinePending || (asset.owner === currentOwner && isPendingAsset(asset));
    return matchesQuery && matchesType && matchesStage && matchesRisk && matchesOwner && matchesDependency && matchesPending && matchesMinePending;
  }), [assets, query, assetType, stage, risk, owner, dependency, pending, onlyMinePending, currentOwner]);

  const totalPages = Math.max(1, Math.ceil(filteredAssets.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedAssets = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAssets.slice(start, start + pageSize);
  }, [filteredAssets, currentPage, pageSize]);

  useEffect(() => {
    setPage(1);
  }, [query, assetType, stage, risk, owner, dependency, pending, groupBy, onlyMinePending, pageSize]);

  const groupedAssets = useMemo(() => {
    if (groupBy === '不分组') {
      return [{ key: 'all', title: '全部能力资产', items: pagedAssets }];
    }
    const groups = new Map<string, UnifiedAssetRecord[]>();
    pagedAssets.forEach((asset) => {
      const key = groupBy === '按阶段分组'
        ? stageLabel[asset.lifecycleStage]
        : groupBy === '按类型分组'
          ? asset.type.toUpperCase()
          : riskValue(asset);
      groups.set(key, [...(groups.get(key) || []), asset]);
    });
    return Array.from(groups.entries()).map(([key, items]) => ({ key, title: key, items }));
  }, [pagedAssets, groupBy]);

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
    <div className="filter-bar asset-directory-toolbar">
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
      <select aria-label="风险等级" value={risk} onChange={(event) => setRisk(event.target.value as '全部风险' | '低' | '中' | '高')}>
        <option>全部风险</option>
        <option value="低">风险等级：低</option>
        <option value="中">风险等级：中</option>
        <option value="高">风险等级：高</option>
      </select>
      <select aria-label="负责人" value={owner} onChange={(event) => setOwner(event.target.value)}>
        {ownerOptions.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>
      <select aria-label="依赖状态" value={dependency} onChange={(event) => setDependency(event.target.value as '全部依赖' | '有依赖' | '依赖阻塞' | '无依赖')}>
        <option>全部依赖</option>
        <option value="有依赖">依赖状态：有依赖</option>
        <option value="依赖阻塞">依赖状态：依赖阻塞</option>
        <option value="无依赖">依赖状态：无依赖</option>
      </select>
      <select aria-label="待处理状态" value={pending} onChange={(event) => setPending(event.target.value as '全部状态' | '仅待处理' | '仅已发布')}>
        <option>全部状态</option>
        <option value="仅待处理">待处理状态：仅待处理</option>
        <option value="仅已发布">待处理状态：仅已发布</option>
      </select>
      <select aria-label="分组方式" value={groupBy} onChange={(event) => setGroupBy(event.target.value as '不分组' | '按阶段分组' | '按类型分组' | '按风险分组')}>
        <option>不分组</option>
        <option value="按阶段分组">按阶段分组</option>
        <option value="按类型分组">按类型分组</option>
        <option value="按风险分组">按风险分组</option>
      </select>
      <label className="asset-directory-toggle">
        <input type="checkbox" checked={onlyMinePending} onChange={(event) => setOnlyMinePending(event.target.checked)} />
        <span>仅看我的待处理</span>
      </label>
      <label className="asset-directory-page-size">
        <span>每页显示</span>
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value) as 6 | 12 | 24)}>
          <option value={6}>6</option>
          <option value={12}>12</option>
          <option value={24}>24</option>
        </select>
      </label>
      <span className="filter-result">显示 {filteredAssets.length} / {assets.length}</span>
    </div>
    {assets.length === 0 ? <div className="asset-directory-empty">
      <strong>暂无能力资产</strong>
      <p>统一资产接口暂未返回对象，可先创建 Skill 或接入 MCP。</p>
    </div> : filteredAssets.length === 0 ? <div className="asset-directory-empty">
      <strong>未找到符合条件的能力资产</strong>
      <p>可以放宽筛选条件，或关闭“仅看我的待处理”后重试。</p>
    </div> : groupedAssets.map((group) => <section className="asset-directory-group" key={group.key}>
      {groupBy !== '不分组' ? <header><h2>{group.title}</h2><span>{group.items.length} 个对象</span></header> : null}
      <div className="asset-directory-grid">
        {group.items.map((asset) => <article className="asset-directory-card" key={asset.id} onClick={() => onNavigate(asset.route)}>
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
          {asset.failureSummary ? <div className={`asset-directory-alert ${assetDirectoryAlertTone(asset)}`}><strong>{assetDirectoryAlertTone(asset) === 'tone-danger' ? '最近失败原因' : '最近阻塞原因'}</strong><p>{asset.failureSummary}</p></div> : null}
          <footer>
            <span>负责人：{asset.owner}</span>
            <b>继续处理 →</b>
          </footer>
        </article>)}
      </div>
    </section>)}
    {filteredAssets.length > 0 ? <div className="asset-directory-pagination">
      <button className="secondary-action" type="button" disabled={currentPage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>上一页</button>
      <span>第 {currentPage} / {totalPages} 页</span>
      <button className="secondary-action" type="button" disabled={currentPage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>下一页</button>
    </div> : null}
  </section>;
}
