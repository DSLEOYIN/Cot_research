import { useState } from 'react';
import { ChatStep } from '../api/client';

type Props = {
  step: ChatStep;
};

function pretty(value?: string | null) {
  if (!value) return '';
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

export function ThoughtStep({ step }: Props) {
  const [open, setOpen] = useState(step.status === 'failed');
  const stateClass = step.status === 'running' ? 'loading' : step.status === 'failed' ? 'failed' : 'done';
  const statusText = step.status === 'running' ? '运行中' : step.status === 'failed' ? '失败' : '完成';

  return (
    <div className={`workflow-step ${stateClass}`}>
      <button className="workflow-step-main" type="button" onClick={() => setOpen((value) => !value)}>
        <span className="workflow-step-icon" />
        <span className="workflow-step-name">{step.title}</span>
        <span className="workflow-step-status">{statusText}</span>
      </button>
      {open && (
        <div className="workflow-step-detail">
          {step.summary && <p>{step.summary}</p>}
          {step.llm_output && <pre>{step.llm_output}</pre>}
          {step.mcp_input && <pre>{pretty(step.mcp_input)}</pre>}
          {step.mcp_output && <pre>{pretty(step.mcp_output)}</pre>}
          {step.error && <pre className="error-text">{step.error}</pre>}
        </div>
      )}
    </div>
  );
}
