import { ChatStep } from './api/client';

type StepDisplay = {
  name: string;
  description: string;
};

const LABELS: Record<string, StepDisplay> = {
  select_skill: { name: '理解问题', description: '识别您的问题类型，并选择合适的分析流程' },
  knowledge_retrieval: { name: '查找业务知识', description: '检索与问题相关的业务口径和知识资料' },
  n2sql: { name: '生成查询语句', description: '将业务问题转换为可执行的数据查询条件' },
  sql_executor: { name: '执行数据查询', description: '访问业务数据并获取本次分析所需结果' },
  sql_correction: { name: '修正查询语句', description: '检查并修正数据查询条件后重新执行' },
  web_search: { name: '检索公开资料', description: '从公开网络信息中查找相关资料' },
  final_answer: { name: '生成最终回答', description: '汇总数据与分析结论，组织为最终回答' },
  running: { name: '正在处理', description: '正在执行下一项分析任务' },
};

function titleKey(title: string) {
  const normalized = title.trim().toLowerCase();
  if (normalized === '意图识别') return 'select_skill';
  if (normalized.includes('knowledge_retrieval')) return 'knowledge_retrieval';
  if (normalized.includes('n2sql')) return 'n2sql';
  if (normalized.includes('sql_executor')) return 'sql_executor';
  if (normalized.includes('sql_correction')) return 'sql_correction';
  if (normalized.includes('web_search')) return 'web_search';
  if (normalized === '最终回答') return 'final_answer';
  if (normalized === '运行中' || normalized.includes('正在执行')) return 'running';
  return normalized;
}

export function stepDisplay(step: ChatStep): StepDisplay {
  const key = LABELS[step.step_type] ? step.step_type : titleKey(step.title);
  if (LABELS[key]) return LABELS[key];
  if (key === 'llm') {
    return step.step_index <= 2
      ? { name: '分析问题', description: '理解问题重点并提取关键分析条件' }
      : { name: '组织分析结论', description: '结合执行结果生成业务分析与解读' };
  }
  return { name: '处理分析任务', description: step.summary || '正在完成本次分析流程中的一项任务' };
}
