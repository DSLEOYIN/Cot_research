import { useState } from 'react';
import { ChatStep } from '../api/client';
import { ThoughtStep } from './ThoughtStep';

type Props = {
  steps: ChatStep[];
};

export function ThoughtProcess({ steps }: Props) {
  const hasError = steps.some((step) => step.status === 'failed');
  const [collapsed, setCollapsed] = useState(!hasError);
  const completed = steps.filter((step) => step.status !== 'running').length;

  return (
    <section className={`workflow-process ${collapsed ? 'collapsed' : ''}`}>
      <div className="workflow-process-header">
        <div className="workflow-process-heading">
          <img className="mode-icon-img" src="/assets/icons/mode-thinking.svg" alt="" />
          <span className="workflow-process-title">思考过程</span>
        </div>
        <div className="workflow-process-actions">
          <span className="workflow-process-state">{completed}/{steps.length} 完成</span>
          <button className="workflow-process-toggle" type="button" onClick={() => setCollapsed((value) => !value)} title={collapsed ? '展开' : '收起'}>
           ⌃
          </button>
        </div>
      </div>
      <div className="workflow-step-list">
        {steps.map((step) => <ThoughtStep key={step.id} step={step} />)}
      </div>
    </section>
  );
}
