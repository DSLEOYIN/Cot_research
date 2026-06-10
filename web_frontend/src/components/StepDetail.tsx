import { useState } from 'react';
import { ChatStep } from '../api/client';

type Props = {
  step: ChatStep;
  description: string;
};

type DetailItem = {
  label: string;
  value: string;
};

const HIDDEN_FIELDS = new Set([
  'success',
  'error',
  'error_type',
  'prompt_type',
  'structured_output',
  'mock',
  'truncated',
  'max_rows',
]);

const FIELD_LABELS: Record<string, string> = {
  prompt: '用户问题',
  query: '查询内容',
  current_query: '当前问题',
  conversation_context: '会话背景',
  context: '参考信息',
  template_vars: '分析材料',
  sql: '查询语句',
  sql_data: '查询结果',
  data: '处理结果',
  text: '处理结果',
  result: '处理结果',
  answer: '回答内容',
  results: '检索结果',
  row_count: '返回数据量',
  problem_type: '问题类型',
  problem_alpha: '判断置信度',
  dataset_ids: '知识库范围',
};

function parseLoose(value?: string | null): unknown {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function cleanTaggedText(value: string) {
  const reason = value.match(/\[REASON\]([\s\S]*?)\[\/REASON\]/)?.[1]?.trim();
  if (reason) return reason;
  return value.replace(/\[(?:SKILL|REASON)\][\s\S]*?\[\/(?:SKILL|REASON)\]/g, '').trim() || value;
}

function friendlyValue(key: string, value: unknown): string {
  if (key === 'problem_type') {
    return String(value) === '1' ? '数据查询与分析' : String(value) === '2' ? '普通问答' : String(value);
  }
  if (key === 'problem_alpha' && typeof value === 'number') {
    return `${Math.round(value * 100)}%`;
  }
  if (typeof value === 'string') {
    const parsed = parseLoose(value);
    return parsed === value ? cleanTaggedText(value) : friendlyValue(key, parsed);
  }
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return value ? '是' : '否';
  if (Array.isArray(value)) {
    return value.map((item) => friendlyValue('', item)).filter(Boolean).join('\n');
  }
  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .filter(([childKey, childValue]) => !HIDDEN_FIELDS.has(childKey) && childValue != null && childValue !== '')
      .map(([childKey, childValue]) => `${FIELD_LABELS[childKey] || childKey}：${friendlyValue(childKey, childValue)}`)
      .join('\n');
  }
  return '';
}

function friendlyItems(raw?: string | null): DetailItem[] {
  const value = parseLoose(raw);
  if (!value) return [];
  if (typeof value !== 'object' || Array.isArray(value)) {
    const text = friendlyValue('', value);
    return text ? [{ label: '内容', value: text }] : [];
  }
  return Object.entries(value as Record<string, unknown>)
    .filter(([key, childValue]) => !HIDDEN_FIELDS.has(key) && childValue != null && childValue !== '')
    .map(([key, childValue]) => ({
      label: FIELD_LABELS[key] || key,
      value: friendlyValue(key, childValue),
    }))
    .filter((item) => item.value);
}

function outputItems(step: ChatStep) {
  const items = friendlyItems(step.mcp_output);
  if (items.length) return items;
  return friendlyItems(step.llm_output);
}

function TechnicalDetails({ step }: { step: ChatStep }) {
  const rawItems = [
    ['模型输出', step.llm_output],
    ['调用参数', step.mcp_input],
    ['原始结果', step.mcp_output],
    ['错误信息', step.error],
  ].filter((item): item is [string, string] => Boolean(item[1]));

  if (!rawItems.length) return null;
  return (
    <details className="step-technical-details">
      <summary>技术详情</summary>
      {rawItems.map(([label, value]) => (
        <div className="step-technical-block" key={label}>
          <span>{label}</span>
          <pre>{typeof parseLoose(value) === 'string' ? value : JSON.stringify(parseLoose(value), null, 2)}</pre>
        </div>
      ))}
    </details>
  );
}

export function StepDetail({ step, description }: Props) {
  const inputs = friendlyItems(step.mcp_input);
  const outputs = outputItems(step);
  const [activeTab, setActiveTab] = useState<'input' | 'output'>(outputs.length ? 'output' : 'input');
  const activeItems = activeTab === 'input' ? inputs : outputs;

  return (
    <div className="workflow-step-detail">
      <div className="step-detail-overview">
        <span>步骤说明</span>
        <strong>{description}</strong>
        {step.summary && <p>{step.summary}</p>}
      </div>
      {(inputs.length > 0 || outputs.length > 0) && (
        <>
          <div className="step-detail-tabs" role="tablist" aria-label="节点输入输出">
            <button type="button" className={activeTab === 'input' ? 'active' : ''} onClick={() => setActiveTab('input')} disabled={!inputs.length}>输入</button>
            <button type="button" className={activeTab === 'output' ? 'active' : ''} onClick={() => setActiveTab('output')} disabled={!outputs.length}>输出</button>
          </div>
          <div className="step-detail-cards">
            {activeItems.map((item, index) => (
              <div className="step-detail-card" key={`${item.label}-${index}`}>
                <span>{item.label}</span>
                <div>{item.value}</div>
              </div>
            ))}
          </div>
        </>
      )}
      <TechnicalDetails step={step} />
    </div>
  );
}
