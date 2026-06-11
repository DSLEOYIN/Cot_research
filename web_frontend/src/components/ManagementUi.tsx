import { ReactNode } from 'react';
import { RuntimeStatus, statusLabel } from '../managementData';

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
