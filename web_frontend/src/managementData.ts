export type RuntimeStatus = 'enabled' | 'disabled' | 'warning' | 'draft';

export type WorkflowStep = {
  name: string;
  description: string;
  mcp: string;
  arguments: string;
};

export type SkillDefinition = {
  name: string;
  displayName: string;
  description: string;
  category: string;
  outputType: string;
  status: RuntimeStatus;
  mcpTools: string[];
  steps: WorkflowStep[];
  examples: string[];
  installed?: boolean;
  featured?: boolean;
  tagline?: string;
  outcomes?: string[];
  requirements?: string[];
  updatedAt: string;
};

export type McpDefinition = {
  name: string;
  displayName: string;
  description: string;
  category: string;
  status: RuntimeStatus;
  health: 'healthy' | 'warning' | 'unchecked';
  latency: string;
  source: string;
  config: { label: string; value: string; sensitive?: boolean }[];
  schema: Record<string, string>;
  updatedAt: string;
};

const step = (name: string, description: string, mcp: string, args: string): WorkflowStep => ({
  name, description, mcp, arguments: args,
});

export const initialSkills: SkillDefinition[] = [
  {
    name: 'data_query', displayName: '数据查询与分析', category: '数据分析', status: 'enabled',
    description: '查询内部销量、库存、订单、达成率等业务数据，并生成解读与口径说明。',
    outputType: '表格 / 图表 / 分析报告', mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor'],
    examples: ['本月中东公司销量多少？', '查询 2024 年各区域终端量'], installed: true, featured: true,
    tagline: '一句话查清企业数据，自动生成图表、结论与口径说明。',
    outcomes: ['自然语言查询业务数据', '自动生成可视化图表', '定位区域与车型差异', '输出可汇报的分析结论'],
    requirements: ['业务数据库只读权限', '已配置字段口径知识库'],
    steps: [
      step('intent_recognition', '识别数据查询意图', 'llm', '{{input.query}}'),
      step('knowledge_retrieval', '检索表结构与字段口径', 'knowledge_retrieval', '{{input.query}}'),
      step('n2sql_generation', '生成安全查询 SQL', 'n2sql', '{{steps.knowledge_retrieval.output}}'),
      step('sql_execution', '执行只读数据查询', 'sql_executor', '{{steps.n2sql_generation.output.sql}}'),
      step('data_interpretation', '组织数据分析结论', 'llm', '{{steps.sql_execution.output}}'),
    ], updatedAt: '今天 10:24',
  },
  {
    name: 'data_web_compare_analysis', displayName: '内部数据与联网分析', category: '数据分析', status: 'enabled',
    description: '查询内部真实业务数据，并结合公开市场和竞品信息完成综合分析。',
    outputType: '内外部综合分析', mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor', 'web_search'],
    examples: ['查询国际销量，并对比外部市场表现'], installed: true, featured: true,
    tagline: '把企业内部数据和公开市场信息放在一起，快速看清竞争位置。',
    outcomes: ['内部经营数据查询', '公开市场与竞品检索', '内外部差异对比', '综合趋势判断'],
    requirements: ['业务数据库只读权限', '联网搜索权限'],
    steps: [
      step('internal_query_extraction', '提取内部数据查询诉求', 'llm', '{{input.query}}'),
      step('knowledge_retrieval', '检索内部业务知识', 'knowledge_retrieval', '{{input.query}}'),
      step('sql_execution', '查询内部业务数据', 'sql_executor', '{{steps.n2sql_generation.output.sql}}'),
      step('web_search', '检索外部公开市场信息', 'web_search', '{{steps.competitor_search_query.output}}'),
      step('data_web_compare_analysis', '生成内外部对比结论', 'llm', '{{steps.web_search.output}}'),
    ], updatedAt: '今天 09:48',
  },
  {
    name: 'yoy_yoy_analysis', displayName: '同环比分析', category: '数据分析', status: 'enabled',
    description: '处理同比、环比、增长率和趋势变化分析。',
    outputType: '分析报告 / 百分比', mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor'],
    examples: ['本月终端量同比去年怎么样？'], installed: true, featured: true,
    tagline: '自动计算同比与环比，快速发现增长、下滑和异常波动。',
    outcomes: ['同比环比自动计算', '趋势拐点识别', '异常波动解释', '增长结论摘要'],
    requirements: ['业务数据库只读权限', '历史同期数据'],
    steps: [
      step('yoy_knowledge_retrieval', '获取同环比计算规则', 'knowledge_retrieval', '{{input.query}}'),
      step('yoy_n2sql', '生成同环比 SQL', 'n2sql', '{{steps.yoy_knowledge_retrieval.output}}'),
      step('sql_execution', '执行同环比查询', 'sql_executor', '{{steps.yoy_n2sql.output.sql}}'),
      step('yoy_analysis', '解读增长与波动', 'llm', '{{steps.sql_execution.output}}'),
    ], updatedAt: '昨天 18:32',
  },
  {
    name: 'web_search_answer', displayName: '联网检索问答', category: '联网检索', status: 'enabled',
    description: '检索最新新闻、公开资料和互联网信息，并给出来源化回答。',
    outputType: '联网资料摘要', mcpTools: ['web_search', 'llm'], examples: ['搜索最新新能源汽车政策'], installed: false,
    tagline: '搜索最新公开信息，自动提炼重点并保留资料来源。',
    outcomes: ['实时公开资料检索', '新闻与政策摘要', '来源化回答', '重点信息提炼'],
    requirements: ['联网搜索权限'],
    steps: [step('web_search', '检索公开网页信息', 'web_search', '{{input.query}}'), step('web_answer', '总结联网资料', 'llm', '{{steps.web_search.output}}')],
    updatedAt: '昨天 16:10',
  },
  {
    name: 'web_compare_analysis', displayName: '联网对比分析', category: '联网分析', status: 'enabled',
    description: '结合上文真实数据，与公开信息和行业趋势进行对比分析。',
    outputType: '外部对比分析', mcpTools: ['web_search', 'llm'], examples: ['和其他竞品对比呢？'], installed: false,
    tagline: '延续当前分析，快速补充竞品与行业趋势视角。',
    outcomes: ['复用当前对话数据', '竞品信息检索', '行业趋势对比', '差距与机会总结'],
    requirements: ['联网搜索权限', '已有对话上下文'],
    steps: [step('search_query_generation', '生成检索关键词', 'llm', '{{input.query}}'), step('web_search', '检索公开信息', 'web_search', '{{steps.search_query_generation.output}}'), step('web_compare_analysis', '输出对比结论', 'llm', '{{steps.web_search.output}}')],
    updatedAt: '06-08 14:25',
  },
  {
    name: 'chat', displayName: '智能问答', category: '闲聊', status: 'enabled',
    description: '处理非数据相关的日常对话与汽车专业知识问答。',
    outputType: '文本对话', mcpTools: ['llm'], examples: ['汽车保养一般多少公里做一次？'], installed: true,
    tagline: '处理日常问答和汽车专业知识咨询，给出清晰自然的回答。',
    outcomes: ['日常知识问答', '汽车专业咨询', '上下文追问', '内容总结'],
    requirements: ['大语言模型服务'],
    steps: [step('chat_response', '生成自然语言回答', 'llm', '{{input.query}}')], updatedAt: '06-07 11:06',
  },
];

export const initialMcps: McpDefinition[] = [
  { name: 'llm', displayName: '大语言模型', category: 'AI', status: 'enabled', health: 'healthy', latency: '820 ms', source: '内置', description: '用于意图识别、SQL 生成、数据解读和自然语言回答。', config: [{ label: '模型', value: 'deepseek-chat' }, { label: 'Base URL', value: 'https://api.deepseek.com' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { prompt: 'string · 必填', prompt_type: 'string', temperature: 'number · 0.2', max_tokens: 'integer · 4096' }, updatedAt: '2 分钟前' },
  { name: 'knowledge_retrieval', displayName: '知识检索', category: 'Retrieval', status: 'warning', health: 'warning', latency: '1.3 s', source: '内置', description: '从知识库检索表结构、字段标准和业务规则。', config: [{ label: 'Provider', value: 'Dify' }, { label: 'Dataset', value: '字段标准查询名检索' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', dataset_ids: 'array', top_k: 'integer · 5' }, updatedAt: '8 分钟前' },
  { name: 'n2sql', displayName: '自然语言转 SQL', category: 'N2SQL', status: 'enabled', health: 'healthy', latency: '940 ms', source: '内置', description: '将自然语言问题转换为安全只读 SQL。', config: [{ label: '运行方式', value: '本地注册' }, { label: '安全模式', value: '只读 SELECT' }], schema: { query: 'string · 必填', table_info: 'string', context: 'string' }, updatedAt: '12 分钟前' },
  { name: 'sql_executor', displayName: 'SQL 执行器', category: 'Database', status: 'enabled', health: 'healthy', latency: '286 ms', source: '内置', description: '执行安全只读 SQL，并应用表白名单和最大行数限制。', config: [{ label: '数据库', value: '业务 MySQL' }, { label: '最大行数', value: '500' }, { label: '密码', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', format: 'enum · md/json', db_uri: 'string' }, updatedAt: '刚刚' },
  { name: 'web_search', displayName: '联网检索', category: 'Retrieval', status: 'enabled', health: 'healthy', latency: '1.1 s', source: '内置', description: '通过 Tavily Search API 检索公开网页信息。', config: [{ label: 'Provider', value: 'Tavily' }, { label: 'Top K', value: '5' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', max_results: 'integer · 5', search_depth: 'enum · basic/advanced' }, updatedAt: '5 分钟前' },
  { name: 'time', displayName: '时间工具', category: 'Utility', status: 'enabled', health: 'healthy', latency: '12 ms', source: '内置', description: '获取指定时区和格式的当前时间。', config: [{ label: '默认时区', value: 'Asia/Shanghai' }, { label: '运行方式', value: '本地注册' }], schema: { format: 'string', timezone: 'string' }, updatedAt: '1 小时前' },
  { name: 'text_analysis', displayName: '文本分析', category: 'NLP', status: 'disabled', health: 'unchecked', latency: '--', source: '内置', description: '文本摘要、情感分析、关键词提取和分类。', config: [{ label: '运行方式', value: '本地注册' }], schema: { text: 'string · 必填', task: 'enum · summary/sentiment/keywords' }, updatedAt: '06-06 17:20' },
];

export const statusLabel: Record<RuntimeStatus, string> = {
  enabled: '已启用', disabled: '已停用', warning: '配置异常', draft: '草稿',
};

export const skillDependenciesForMcp = (mcpName: string, skills = initialSkills) =>
  skills.filter((skill) => skill.mcpTools.includes(mcpName));
