const SKILL_LABELS: Record<string, string> = {
  chat: '智能问答',
  data_query: '数据查询与分析',
  yoy_yoy_analysis: '同环比分析',
  web_search_answer: '联网检索问答',
  web_compare_analysis: '联网对比分析',
  data_web_compare_analysis: '内部数据与联网分析',
  leave_request: '请假申请',
};

export function skillDisplayName(skill?: string | null) {
  if (!skill) return '';
  return SKILL_LABELS[skill] || '智能分析';
}
