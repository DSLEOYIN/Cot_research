import { ReactNode } from 'react';
import { LifecycleStage, stageLabel, RuntimeStatus, statusLabel } from '../managementData';

export function StatusBadge({ status }: { status: RuntimeStatus }) {
  return <span className={`status-badge ${status}`}><i />{statusLabel[status]}</span>;
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description: string; actions?: ReactNode }) {
  return <header className="management-header"><div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><div className="management-actions">{actions}</div></header>;
}

export function MetricStrip({ items }: { items: { label: string; value: string | number; tone?: string }[] }) {
  return <div className="metric-strip">{items.map((item) => <div className={`metric-card ${item.tone || ''}`} key={item.label}><span>{item.label}</span><strong>{item.value}</strong></div>)}</div>;
}

export function DetailTabs({ tabs, active, onChange }: { tabs: string[]; active: string; onChange: (tab: string) => void }) {
  return <div className="detail-tabs">{tabs.map((tab) => <button key={tab} className={tab === active ? 'active' : ''} type="button" onClick={() => onChange(tab)}>{tab}</button>)}</div>;
}

export function PrototypeToast({ text }: { text: string }) {
  return text ? <div className="prototype-toast">{text}</div> : null;
}

export function DetailSummaryPanel({ title, description, items }: { title: string; description: string; items: { label: string; value: string; description: string }[] }) {
  return <section className="panel-card">
    <div className="section-toolbar">
      <div>
        <span>SUMMARY</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
    <div className="generated-summary-grid">
      {items.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><p>{item.description}</p></div>)}
    </div>
  </section>;
}

export function FocusAreaPanel({ title, description, items }: { title: string; description: string; items: { label: string; value: string; description: string }[] }) {
  return <section className="panel-card asset-stage-panel">
    <div className="section-toolbar">
      <div>
        <span>NOW</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
    <div className="generated-summary-grid">
      {items.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><p>{item.description}</p></div>)}
    </div>
  </section>;
}

export function DetailTestPanel({ title, description, actionLabel, onAction, children }: { title: string; description: string; actionLabel: string; onAction: () => void; children: ReactNode }) {
  return <section className="panel-card skill-simple-test">
    <div className="section-toolbar">
      <div>
        <span>STEP 3</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <button className="primary-action" type="button" onClick={onAction}>{actionLabel}</button>
    </div>
    {children}
  </section>;
}

export function RecentActivityPanel({ title, description, items, emptyText }: { title: string; description: string; items: { id: string; detail: string }[]; emptyText: string }) {
  return <section className="panel-card">
    <div className="section-toolbar">
      <div>
        <span>RECENT</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
    <div className="release-diff-list">
      {items.length ? items.map((item) => <span key={item.id}>{item.detail}</span>) : <span>{emptyText}</span>}
    </div>
  </section>;
}

export function StageActionPanel({
  title,
  description,
  primaryLabel,
  onPrimary,
  secondaryLabel,
  onSecondary,
}: {
  title: string;
  description: string;
  primaryLabel: string;
  onPrimary: () => void;
  secondaryLabel: string;
  onSecondary: () => void;
}) {
  return <section className="panel-card">
    <div className="section-toolbar">
      <div>
        <span>ACTION</span>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <div className="review-buttons">
        <button className="secondary-action" type="button" onClick={onSecondary}>{secondaryLabel}</button>
        <button className="primary-action" type="button" onClick={onPrimary}>{primaryLabel}</button>
      </div>
    </div>
  </section>;
}

type LifecycleOverviewPanelProps = {
  summaryTitle: string;
  summaryDescription: string;
  currentStage: LifecycleStage;
  currentStageAction: string;
  summaryItems: { label: string; value: string; description: string }[];
  stageSteps: LifecycleStage[];
  focusAreas: { label: string; value: string; description: string }[];
};

export function LifecycleOverviewPanel({
  summaryTitle,
  summaryDescription,
  currentStage,
  currentStageAction,
  summaryItems,
  stageSteps,
  focusAreas,
}: LifecycleOverviewPanelProps) {
  return <>
    <DetailSummaryPanel title={summaryTitle} description={summaryDescription} items={summaryItems} />

    <section className="panel-card">
      <div className="section-toolbar">
        <div>
          <span>LIFECYCLE</span>
          <h3>阶段状态</h3>
          <p>测试 → 提审 → 发布</p>
        </div>
      </div>
      <div className="lifecycle-stage-strip">
        {stageSteps.map((step) => <div key={step} className={`lifecycle-stage-node ${step === currentStage ? 'active' : ''}`}>
          <strong>{stageLabel[step]}</strong>
        </div>)}
      </div>
    </section>
    <FocusAreaPanel title="当前阶段主操作" description={currentStageAction} items={focusAreas} />
  </>;
}
