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
    <section className="panel-card">
      <div className="section-toolbar">
        <div>
          <span>SUMMARY</span>
          <h3>{summaryTitle}</h3>
          <p>{summaryDescription}</p>
        </div>
      </div>
      <div className="generated-summary-grid">
        {summaryItems.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><p>{item.description}</p></div>)}
      </div>
    </section>

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

    <section className="panel-card asset-stage-panel">
      <div className="section-toolbar">
        <div>
          <span>NOW</span>
          <h3>当前阶段主操作</h3>
          <p>{currentStageAction}</p>
        </div>
      </div>
      <div className="generated-summary-grid">
        {focusAreas.map((item) => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><p>{item.description}</p></div>)}
      </div>
    </section>
  </>;
}
