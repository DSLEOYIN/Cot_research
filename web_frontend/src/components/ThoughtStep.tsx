import { useState } from 'react';
import { ChatStep } from '../api/client';
import { stepDisplay } from '../stepLabels';
import { StepDetail } from './StepDetail';

type Props = {
  step: ChatStep;
};

function formatDuration(duration?: number | null) {
  if (duration == null) return '';
  if (duration < 1000) return `${duration} ms`;
  return `${(duration / 1000).toFixed(duration < 10000 ? 1 : 0)} s`;
}

export function ThoughtStep({ step }: Props) {
  const [open, setOpen] = useState(step.status === 'failed');
  const display = stepDisplay(step);
  const stateClass = step.status === 'running' ? 'loading' : step.status === 'failed' ? 'failed' : 'done';
  const statusText = step.status === 'running'
    ? '运行中'
    : step.status === 'failed'
      ? '失败'
      : formatDuration(step.duration_ms) || '完成';

  return (
    <div className={`workflow-step ${stateClass} ${open ? 'open' : ''}`}>
      <button className="workflow-step-main" type="button" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        <span className="workflow-step-icon" />
        <span className="workflow-step-copy">
          <span className="workflow-step-name">{display.name}</span>
          <span className="workflow-step-description">{display.description}</span>
        </span>
        <span className="workflow-step-actions">
          {step.status === 'running' && <span className="workflow-running-pulse" aria-hidden="true"><i /><i /><i /></span>}
          <span className="workflow-step-status">{statusText}</span>
          <span className="workflow-step-chevron" aria-hidden="true" />
        </span>
      </button>
      {open && (
        <StepDetail step={step} description={display.description} />
      )}
    </div>
  );
}
