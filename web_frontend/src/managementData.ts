export type RuntimeStatus = 'enabled' | 'disabled' | 'warning' | 'draft';
export type ReleaseStatus = 'draft' | 'testing' | 'ready_for_review' | 'review_approved' | 'ready_to_publish' | 'published' | 'blocked_by_dependency';
export type AssetType = 'skill' | 'mcp';
export type LifecycleStage = 'draft' | 'testing' | 'review' | 'review_rejected' | 'publish' | 'published' | 'blocked';

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
  releaseStatus: ReleaseStatus;
  mcpTools: string[];
  steps: WorkflowStep[];
  examples: string[];
  installed?: boolean;
  enabledForUser?: boolean;
  updateAvailable?: boolean;
  featured?: boolean;
  tagline?: string;
  outcomes?: string[];
  requirements?: string[];
  scenes?: string[];
  expectedOutput?: string[];
  exampleOutput?: string;
  usageCount30d?: number;
  successRate?: string;
  mcpUsageHeat?: string;
  latestVersion?: string;
  publishedVersion?: string;
  updatedAt: string;
};

export type McpDefinition = {
  name: string;
  displayName: string;
  description: string;
  category: string;
  status: RuntimeStatus;
  releaseStatus: ReleaseStatus;
  health: 'healthy' | 'warning' | 'unchecked';
  latency: string;
  source: string;
  blockedBy?: string;
  usageCount30d?: number;
  publishedVersion?: string;
  latestVersion?: string;
  config: { label: string; value: string; sensitive?: boolean }[];
  schema: Record<string, string>;
  updatedAt: string;
};

export type OperationsTask = {
  id: string;
  title: string;
  type: 'skill' | 'mcp';
  entityName: string;
  priority: 'P0' | 'P1' | 'P2';
  stage: ReleaseStatus;
  owner: string;
  updatedAt: string;
  summary: string;
  blockedBy?: string;
  parentTaskId?: string;
  releaseStatus: ReleaseStatus;
  autoTestPassRate: string;
  failureReason?: string;
  reviewNotes?: string;
};

export type OrganizationAccessProfile = {
  id?: string;
  organizationName: string;
  roleName: string;
  openSkills: string[];
  dataDomains: string[];
  actionPermissions: string[];
  approvalMode: string;
};

export type PlatformMetrics = {
  monthlyActiveUsers: number;
  apiSuccessRate: string;
  topSkills: string[];
  coverageOrganizations: number;
  riskAlerts: string[];
};

export type PlatformSkillMetrics = {
  topSkills: string[];
  averageCostPerCall: string;
  failureReasons: string[];
  recommendation: string;
};

export type PlatformOrganizationMetrics = {
  coverageOrganizations: number;
  organizationItems: { organizationName: string; coverageRate: string; activeUsers: number }[];
};

export type PlatformAlert = {
  id: string;
  level: 'warning' | 'critical' | 'info';
  message: string;
  source: string;
  updatedAt: string;
};

export type ActionGovernanceCase = {
  id: string;
  skillName: string;
  organizationName: string;
  approvalStatus: '待审批' | '已通过' | '已回退';
  confirmationRule: string;
  rollbackStatus: string;
  auditTrail: string[];
};

export type ReleaseActivity = {
  id: string;
  entityType: 'skill' | 'mcp';
  entityName: string;
  action: 'submitted_for_review' | 'review_approved' | 'health_check_passed' | 'published_to_catalog' | 'dependency_unblocked';
  operator: string;
  detail: string;
  createdAt: string;
};

export type UnifiedAssetRecord = {
  id: string;
  type: AssetType;
  name: string;
  displayName: string;
  description: string;
  category: string;
  status: RuntimeStatus;
  releaseStatus: ReleaseStatus;
  lifecycleStage: LifecycleStage;
  updatedAt: string;
  owner: string;
  dependencySummary: string;
  failureSummary?: string;
  riskLabel: string;
  organizationSummary: string;
  route: string;
};

export type SkillGovernanceTag = {
  businessDomain: string;
  riskLevel: '低' | '中' | '高';
  applicableOrganizations: string[];
  requiresApproval: boolean;
  writesData: boolean;
};

const step = (name: string, description: string, mcp: string, args: string): WorkflowStep => ({
  name, description, mcp, arguments: args,
});

export const initialSkills: SkillDefinition[] = [
  {
    name: 'global_policy_watch',
    displayName: '海外政策追踪',
    category: '政策分析',
    status: 'draft',
    releaseStatus: 'ready_to_publish',
    description: '搜集海外汽车行业相关政策，提取市场范围、生效时间、影响车型和跟进行动。',
    outputType: '政策摘要 / 风险提示 / 时间线',
    mcpTools: ['web_search', 'llm', 'text_analysis'],
    examples: ['梳理欧盟本月新能源汽车相关政策变化'],
    installed: false,
    enabledForUser: false,
    featured: true,
    tagline: '把海外政策更新整理成可直接提审发布的分析能力。',
    outcomes: ['自动抓取政策更新', '提炼生效时间与影响范围', '生成行动建议'],
    requirements: ['联网搜索权限', '政策来源白名单'],
    scenes: ['出海政策研判', '市场准入跟踪'],
    expectedOutput: ['政策更新时间线', '市场影响摘要', '跟进建议'],
    exampleOutput: '输出欧盟政策变化时间线、波及车型与建议跟进动作。',
    usageCount30d: 11,
    successRate: '95.1%',
    mcpUsageHeat: '低',
    latestVersion: 'v0.9.0',
    publishedVersion: '--',
    steps: [
      step('policy_search', '检索海外政策来源', 'web_search', '{{input.query}}'),
      step('policy_extract', '提炼政策关键字段', 'text_analysis', '{{steps.policy_search.output}}'),
      step('policy_summary', '生成政策影响总结', 'llm', '{{steps.policy_extract.output}}'),
    ],
    updatedAt: '今天 09:16',
  },
  {
    name: 'channel_inventory_diagnosis',
    displayName: '渠道库存诊断',
    category: '数据分析',
    status: 'warning',
    releaseStatus: 'blocked_by_dependency',
    description: '结合库存快照与销量节奏，诊断经销商和区域库存积压风险。',
    outputType: '库存诊断报告 / 风险分层',
    mcpTools: ['inventory_snapshot_mcp', 'llm'],
    examples: ['帮我看华南区域当前库存积压风险'],
    installed: false,
    enabledForUser: false,
    featured: true,
    tagline: '用库存快照快速识别高风险渠道和去库存压力。',
    outcomes: ['诊断区域库存风险', '发现积压渠道', '输出处置建议'],
    requirements: ['库存快照数据接入'],
    scenes: ['月度库存复盘', '渠道健康巡检'],
    expectedOutput: ['库存风险分层', '异常经销商列表', '处置建议'],
    exampleOutput: '列出高风险区域、库存周转天数和建议动作。',
    usageCount30d: 0,
    successRate: '--',
    mcpUsageHeat: '低',
    latestVersion: 'v0.3.0-draft',
    publishedVersion: '--',
    steps: [
      step('inventory_snapshot', '拉取库存快照数据', 'inventory_snapshot_mcp', '{{input.query}}'),
      step('inventory_diagnosis', '生成库存诊断结论', 'llm', '{{steps.inventory_snapshot.output}}'),
    ],
    updatedAt: '今天 10:42',
  },
  {
    name: 'data_query',
    displayName: '数据查询与分析',
    category: '数据分析',
    status: 'enabled',
    releaseStatus: 'published',
    description: '查询内部销量、库存、订单、达成率等业务数据，并生成解读与口径说明。',
    outputType: '表格 / 图表 / 分析报告',
    mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor'],
    examples: ['本月中东公司销量多少？', '查询 2024 年各区域终端量'],
    installed: true,
    enabledForUser: true,
    updateAvailable: true,
    featured: true,
    tagline: '一句话查清企业数据，自动生成图表、结论与口径说明。',
    outcomes: ['自然语言查询业务数据', '自动生成可视化图表', '定位区域与车型差异', '输出可汇报的分析结论'],
    requirements: ['业务数据库只读权限', '已配置字段口径知识库'],
    scenes: ['日常经营复盘', '销售例会准备', '领导临时追问'],
    expectedOutput: ['按口径整理的数据表', '自动生成的图表', '可继续追问的业务结论'],
    exampleOutput: '输出本月销量表、环比柱状图，并用三段话解释区域变化原因。',
    usageCount30d: 128,
    successRate: '98.6%',
    mcpUsageHeat: '高',
    latestVersion: 'v1.4.0',
    publishedVersion: 'v1.3.2',
    steps: [
      step('intent_recognition', '识别数据查询意图', 'llm', '{{input.query}}'),
      step('knowledge_retrieval', '检索表结构与字段口径', 'knowledge_retrieval', '{{input.query}}'),
      step('n2sql_generation', '生成安全查询 SQL', 'n2sql', '{{steps.knowledge_retrieval.output}}'),
      step('sql_execution', '执行只读数据查询', 'sql_executor', '{{steps.n2sql_generation.output.sql}}'),
      step('data_interpretation', '组织数据分析结论', 'llm', '{{steps.sql_execution.output}}'),
    ],
    updatedAt: '今天 10:24',
  },
  {
    name: 'data_web_compare_analysis',
    displayName: '内部数据与联网分析',
    category: '数据分析',
    status: 'enabled',
    releaseStatus: 'published',
    description: '查询内部真实业务数据，并结合公开市场和竞品信息完成综合分析。',
    outputType: '内外部综合分析',
    mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor', 'web_search'],
    examples: ['查询国际销量，并对比外部市场表现'],
    installed: true,
    enabledForUser: true,
    featured: true,
    tagline: '把企业内部数据和公开市场信息放在一起，快速看清竞争位置。',
    outcomes: ['内部经营数据查询', '公开市场与竞品检索', '内外部差异对比', '综合趋势判断'],
    requirements: ['业务数据库只读权限', '联网搜索权限'],
    scenes: ['竞品分析', '月度经营复盘', '市场判断'],
    expectedOutput: ['内部数据摘要', '外部搜索引用', '综合分析结论'],
    exampleOutput: '生成内部销量趋势图，并附上三条外部市场变化信号进行解释。',
    usageCount30d: 86,
    successRate: '96.8%',
    mcpUsageHeat: '高',
    latestVersion: 'v1.1.0',
    publishedVersion: 'v1.1.0',
    steps: [
      step('internal_query_extraction', '提取内部数据查询诉求', 'llm', '{{input.query}}'),
      step('knowledge_retrieval', '检索内部业务知识', 'knowledge_retrieval', '{{input.query}}'),
      step('sql_execution', '查询内部业务数据', 'sql_executor', '{{steps.n2sql_generation.output.sql}}'),
      step('web_search', '检索外部公开市场信息', 'web_search', '{{steps.competitor_search_query.output}}'),
      step('data_web_compare_analysis', '生成内外部对比结论', 'llm', '{{steps.web_search.output}}'),
    ],
    updatedAt: '今天 09:48',
  },
  {
    name: 'yoy_yoy_analysis',
    displayName: '同环比分析',
    category: '数据分析',
    status: 'enabled',
    releaseStatus: 'published',
    description: '处理同比、环比、增长率和趋势变化分析。',
    outputType: '分析报告 / 百分比',
    mcpTools: ['llm', 'knowledge_retrieval', 'n2sql', 'sql_executor'],
    examples: ['本月终端量同比去年怎么样？'],
    installed: true,
    enabledForUser: false,
    featured: true,
    tagline: '自动计算同比与环比，快速发现增长、下滑和异常波动。',
    outcomes: ['同比环比自动计算', '趋势拐点识别', '异常波动解释', '增长结论摘要'],
    requirements: ['业务数据库只读权限', '历史同期数据'],
    scenes: ['经营分析会', '销量复盘', '同比专题追问'],
    expectedOutput: ['同比环比百分比', '波动点解释', '风险提醒'],
    exampleOutput: '输出同比环比百分比并标记异常月份，附带简要解释。',
    usageCount30d: 64,
    successRate: '97.9%',
    mcpUsageHeat: '中',
    latestVersion: 'v1.0.4',
    publishedVersion: 'v1.0.4',
    steps: [
      step('yoy_knowledge_retrieval', '获取同环比计算规则', 'knowledge_retrieval', '{{input.query}}'),
      step('yoy_n2sql', '生成同环比 SQL', 'n2sql', '{{steps.yoy_knowledge_retrieval.output}}'),
      step('sql_execution', '执行同环比查询', 'sql_executor', '{{steps.yoy_n2sql.output.sql}}'),
      step('yoy_analysis', '解读增长与波动', 'llm', '{{steps.sql_execution.output}}'),
    ],
    updatedAt: '昨天 18:32',
  },
  {
    name: 'web_search_answer',
    displayName: '联网检索问答',
    category: '联网检索',
    status: 'enabled',
    releaseStatus: 'published',
    description: '检索最新新闻、公开资料和互联网信息，并给出来源化回答。',
    outputType: '联网资料摘要',
    mcpTools: ['web_search', 'llm'],
    examples: ['搜索最新新能源汽车政策'],
    installed: false,
    enabledForUser: false,
    featured: false,
    tagline: '搜索最新公开信息，自动提炼重点并保留资料来源。',
    outcomes: ['实时公开资料检索', '新闻与政策摘要', '来源化回答', '重点信息提炼'],
    requirements: ['联网搜索权限'],
    scenes: ['政策检索', '快速资料查证'],
    expectedOutput: ['来源列表', '三段式摘要', '关键结论'],
    exampleOutput: '按时间线列出最新政策，并总结三条核心变化。',
    usageCount30d: 22,
    successRate: '94.2%',
    mcpUsageHeat: '中',
    latestVersion: 'v1.2.0',
    publishedVersion: 'v1.2.0',
    steps: [
      step('web_search', '检索公开网页信息', 'web_search', '{{input.query}}'),
      step('web_answer', '总结联网资料', 'llm', '{{steps.web_search.output}}'),
    ],
    updatedAt: '昨天 16:10',
  },
  {
    name: 'web_compare_analysis',
    displayName: '联网对比分析',
    category: '联网分析',
    status: 'enabled',
    releaseStatus: 'published',
    description: '结合上文真实数据，与公开信息和行业趋势进行对比分析。',
    outputType: '外部对比分析',
    mcpTools: ['web_search', 'llm'],
    examples: ['和其他竞品对比呢？'],
    installed: false,
    enabledForUser: false,
    featured: false,
    tagline: '延续当前分析，快速补充竞品与行业趋势视角。',
    outcomes: ['复用当前对话数据', '竞品信息检索', '行业趋势对比', '差距与机会总结'],
    requirements: ['联网搜索权限', '已有对话上下文'],
    scenes: ['竞品复盘', '外部趋势补充'],
    expectedOutput: ['竞品对比表', '外部证据摘要', '机会差距总结'],
    exampleOutput: '补充外部引用来源，并说明本品与竞品差异。',
    usageCount30d: 17,
    successRate: '93.5%',
    mcpUsageHeat: '低',
    latestVersion: 'v0.9.8',
    publishedVersion: 'v0.9.8',
    steps: [
      step('search_query_generation', '生成检索关键词', 'llm', '{{input.query}}'),
      step('web_search', '检索公开信息', 'web_search', '{{steps.search_query_generation.output}}'),
      step('web_compare_analysis', '输出对比结论', 'llm', '{{steps.web_search.output}}'),
    ],
    updatedAt: '06-08 14:25',
  },
  {
    name: 'chat',
    displayName: '智能问答',
    category: '闲聊',
    status: 'enabled',
    releaseStatus: 'published',
    description: '处理非数据相关的日常对话与汽车专业知识问答。',
    outputType: '文本对话',
    mcpTools: ['llm'],
    examples: ['汽车保养一般多少公里做一次？'],
    installed: true,
    enabledForUser: true,
    featured: false,
    tagline: '处理日常问答和汽车专业知识咨询，给出清晰自然的回答。',
    outcomes: ['日常知识问答', '汽车专业咨询', '上下文追问', '内容总结'],
    requirements: ['大语言模型服务'],
    scenes: ['基础问答', '行业知识咨询'],
    expectedOutput: ['简洁回答', '步骤建议', '扩展说明'],
    exampleOutput: '给出保养里程建议，并补充不同工况差异。',
    usageCount30d: 42,
    successRate: '99.1%',
    mcpUsageHeat: '中',
    latestVersion: 'v1.0.1',
    publishedVersion: 'v1.0.1',
    steps: [step('chat_response', '生成自然语言回答', 'llm', '{{input.query}}')],
    updatedAt: '06-07 11:06',
  },
  {
    name: 'leave_request',
    displayName: '请假申请',
    category: '流程办理',
    status: 'enabled',
    releaseStatus: 'testing',
    description: '发起请假申请、补全请假信息，并在提交前完成审批校验与二次确认。',
    outputType: '流程表单 / 提交结果',
    mcpTools: ['llm', 'time'],
    examples: ['帮我提交下周三到周五的年假申请'],
    installed: false,
    enabledForUser: false,
    featured: true,
    tagline: '把请假信息补全后再提交，提交前自动检查审批规则和确认项。',
    outcomes: ['识别请假时间与类型', '补全表单必填项', '提交前二次确认', '失败后给出回退与补提建议'],
    requirements: ['OA 提交流程权限', '审批人配置完整'],
    scenes: ['请假申请', '补卡与人事流程'],
    expectedOutput: ['提交流程表单', '审批路径提醒', '提交结果与回退说明'],
    exampleOutput: '显示请假区间、审批人和二次确认提示，确认后再提交到 OA。',
    usageCount30d: 9,
    successRate: '91.4%',
    mcpUsageHeat: '低',
    latestVersion: 'v0.8.0',
    publishedVersion: '--',
    steps: [
      step('request_parse', '识别请假申请信息', 'llm', '{{input.query}}'),
      step('time_validation', '校验请假日期与时长', 'time', '{{steps.request_parse.output}}'),
      step('submission_confirmation', '提交前二次确认', 'llm', '{{steps.time_validation.output}}'),
    ],
    updatedAt: '今天 11:20',
  },
];

export const initialMcps: McpDefinition[] = [
  { name: 'inventory_snapshot_mcp', displayName: '库存快照 MCP', category: 'Database', status: 'draft', releaseStatus: 'ready_for_review', health: 'unchecked', latency: '--', source: '集团内部系统', usageCount30d: 0, publishedVersion: '--', latestVersion: 'v0.3.0', description: '汇总区域、渠道和车型库存快照，为库存诊断类 Skill 提供标准化输入。', config: [{ label: '目标系统', value: '库存中台' }, { label: '更新频率', value: '每 30 分钟' }, { label: '访问令牌', value: '已配置', sensitive: true }], schema: { region: 'string', dealer_scope: 'string', snapshot_at: 'datetime' }, updatedAt: '今天 10:38' },
  { name: 'llm', displayName: '大语言模型', category: 'AI', status: 'enabled', releaseStatus: 'published', health: 'healthy', latency: '820 ms', source: '内置', usageCount30d: 3260, publishedVersion: 'v3.2.0', latestVersion: 'v3.2.0', description: '用于意图识别、SQL 生成、数据解读和自然语言回答。', config: [{ label: '模型', value: 'deepseek-chat' }, { label: 'Base URL', value: 'https://api.deepseek.com' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { prompt: 'string · 必填', prompt_type: 'string', temperature: 'number · 0.2', max_tokens: 'integer · 4096' }, updatedAt: '2 分钟前' },
  { name: 'knowledge_retrieval', displayName: '知识检索', category: 'Retrieval', status: 'warning', releaseStatus: 'published', health: 'warning', latency: '1.3 s', source: '内置', usageCount30d: 1402, publishedVersion: 'v2.1.0', latestVersion: 'v2.2.0', description: '从知识库检索表结构、字段标准和业务规则。', config: [{ label: 'Provider', value: 'Dify' }, { label: 'Dataset', value: '字段标准查询名检索' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', dataset_ids: 'array', top_k: 'integer · 5' }, updatedAt: '8 分钟前' },
  { name: 'n2sql', displayName: '自然语言转 SQL', category: 'N2SQL', status: 'enabled', releaseStatus: 'published', health: 'healthy', latency: '940 ms', source: '内置', usageCount30d: 876, publishedVersion: 'v1.8.1', latestVersion: 'v1.8.1', description: '将自然语言问题转换为安全只读 SQL。', config: [{ label: '运行方式', value: '本地注册' }, { label: '安全模式', value: '只读 SELECT' }], schema: { query: 'string · 必填', table_info: 'string', context: 'string' }, updatedAt: '12 分钟前' },
  { name: 'sql_executor', displayName: 'SQL 执行器', category: 'Database', status: 'enabled', releaseStatus: 'published', health: 'healthy', latency: '286 ms', source: '内置', usageCount30d: 920, publishedVersion: 'v1.5.4', latestVersion: 'v1.5.4', description: '执行安全只读 SQL，并应用表白名单和最大行数限制。', config: [{ label: '数据库', value: '业务 MySQL' }, { label: '最大行数', value: '500' }, { label: '密码', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', format: 'enum · md/json', db_uri: 'string' }, updatedAt: '刚刚' },
  { name: 'web_search', displayName: '联网检索', category: 'Retrieval', status: 'enabled', releaseStatus: 'published', health: 'healthy', latency: '1.1 s', source: '内置', usageCount30d: 486, publishedVersion: 'v1.3.0', latestVersion: 'v1.3.0', description: '通过 Tavily Search API 检索公开网页信息。', config: [{ label: 'Provider', value: 'Tavily' }, { label: 'Top K', value: '5' }, { label: 'API Key', value: '已配置', sensitive: true }], schema: { query: 'string · 必填', max_results: 'integer · 5', search_depth: 'enum · basic/advanced' }, updatedAt: '5 分钟前' },
  { name: 'time', displayName: '时间工具', category: 'Utility', status: 'enabled', releaseStatus: 'published', health: 'healthy', latency: '12 ms', source: '内置', usageCount30d: 94, publishedVersion: 'v1.0.2', latestVersion: 'v1.0.2', description: '获取指定时区和格式的当前时间。', config: [{ label: '默认时区', value: 'Asia/Shanghai' }, { label: '运行方式', value: '本地注册' }], schema: { format: 'string', timezone: 'string' }, updatedAt: '1 小时前' },
  { name: 'text_analysis', displayName: '文本分析', category: 'NLP', status: 'disabled', releaseStatus: 'blocked_by_dependency', health: 'unchecked', latency: '--', source: '内置', blockedBy: '等待 llm v3.2.0 正式发布能力白名单', usageCount30d: 0, publishedVersion: '--', latestVersion: 'v0.4.0-draft', description: '文本摘要、情感分析、关键词提取和分类。', config: [{ label: '运行方式', value: '本地注册' }], schema: { text: 'string · 必填', task: 'enum · summary/sentiment/keywords' }, updatedAt: '06-06 17:20' },
];

export const operationsTasks: OperationsTask[] = [
  {
    id: 'skill-task-001',
    title: '生成渠道库存诊断 Skill',
    type: 'skill',
    entityName: 'channel_inventory_diagnosis',
    priority: 'P0',
    stage: 'blocked_by_dependency',
    releaseStatus: 'blocked_by_dependency',
    owner: '运维-王敏',
    updatedAt: '今天 10:42',
    summary: 'AI 已完成 Skill 流程草案，等待依赖 MCP 发布后继续联调测试。',
    blockedBy: '依赖 MCP `inventory_snapshot_mcp` 尚未发布',
    autoTestPassRate: '4/6',
    failureReason: 'Skill 集成测试被未发布 MCP 阻塞',
  },
  {
    id: 'mcp-task-014',
    title: '生成库存快照 MCP 子任务',
    type: 'mcp',
    entityName: 'inventory_snapshot_mcp',
    priority: 'P1',
    stage: 'ready_for_review',
    releaseStatus: 'ready_for_review',
    owner: '运维-王敏',
    updatedAt: '今天 10:38',
    summary: '已生成 Python 模块、inputSchema 与 mock 返回，自动测试通过。',
    parentTaskId: 'skill-task-001',
    autoTestPassRate: '8/8',
    reviewNotes: '重点确认返回结构命名是否与 Skill 编排一致。',
  },
  {
    id: 'skill-task-002',
    title: '生成海外政策追踪 Skill',
    type: 'skill',
    entityName: 'global_policy_watch',
    priority: 'P1',
    stage: 'ready_to_publish',
    releaseStatus: 'ready_to_publish',
    owner: '运维-李哲',
    updatedAt: '今天 09:16',
    summary: '审核通过，等待手动发布到集团能力目录。',
    autoTestPassRate: '7/7',
    reviewNotes: '已确认作用说明、流程和示例输入输出。',
  },
  {
    id: 'mcp-task-009',
    title: '升级知识检索 MCP',
    type: 'mcp',
    entityName: 'knowledge_retrieval',
    priority: 'P0',
    stage: 'testing',
    releaseStatus: 'testing',
    owner: '运维-陈雪',
    updatedAt: '今天 08:54',
    summary: 'AI 正在根据失败日志自动修复重试，重点解决字段映射缺失。',
    autoTestPassRate: '5/8',
    failureReason: '字段映射缺失，导致示例 query 返回空结果。',
  },
];

export const organizationAccessProfiles: OrganizationAccessProfile[] = [
  {
    id: 'gac-international',
    organizationName: '广汽国际',
    roleName: '销售分析岗',
    openSkills: ['数据查询与分析', '同环比分析', '内部数据与联网分析'],
    dataDomains: ['销售', '库存'],
    actionPermissions: ['查询', '下载'],
    approvalMode: '部门管理员复核',
  },
  {
    id: 'gac-passenger-vehicle',
    organizationName: '广汽乘用车',
    roleName: 'HR 管理员',
    openSkills: ['智能问答', '制度问答', '请假申请'],
    dataDomains: ['人力', 'OA'],
    actionPermissions: ['查询', '提交', '审批'],
    approvalMode: '动作型能力二次确认',
  },
  {
    id: 'gac-headquarters',
    organizationName: '集团总部',
    roleName: '平台管理员',
    openSkills: ['全部治理能力'],
    dataDomains: ['平台配置', '监控', '审计'],
    actionPermissions: ['发布', '回滚', '授权'],
    approvalMode: '高风险操作留痕审计',
  },
];

export const platformMetrics: PlatformMetrics = {
  monthlyActiveUsers: 2486,
  apiSuccessRate: '97.8%',
  topSkills: ['数据查询与分析', '内部数据与联网分析', '同环比分析'],
  coverageOrganizations: 12,
  riskAlerts: ['请假类 Skill 待权限模型接入', '知识检索字段映射需复核', '海外政策能力待灰度发布'],
};

export const platformSkillMetrics: PlatformSkillMetrics = {
  topSkills: ['数据查询与分析', '内部数据与联网分析', '同环比分析'],
  averageCostPerCall: '¥0.42',
  failureReasons: ['知识检索字段映射缺失', '依赖 MCP 未发布', '组织授权未开通'],
  recommendation: '优先补齐知识检索映射和依赖 MCP 发布，可直接提升当前高频能力的稳定性。',
};

export const platformOrganizationMetrics: PlatformOrganizationMetrics = {
  coverageOrganizations: 12,
  organizationItems: [
    { organizationName: '广汽国际', coverageRate: '92%', activeUsers: 186 },
    { organizationName: '集团总部', coverageRate: '88%', activeUsers: 124 },
    { organizationName: '广汽乘用车', coverageRate: '61%', activeUsers: 83 },
  ],
};

export const platformAlerts: PlatformAlert[] = [
  { id: 'alert-001', level: 'critical', message: '知识检索字段映射缺失，影响高频数据分析链路。', source: '知识检索 MCP', updatedAt: '今天 08:54' },
  { id: 'alert-002', level: 'warning', message: '海外政策能力待灰度发布，需确认首批组织范围。', source: 'Skill 发布', updatedAt: '今天 09:16' },
  { id: 'alert-003', level: 'info', message: '组织权限 PATCH 写入链路运行稳定，近 24 小时无保存失败。', source: '权限治理', updatedAt: '今天 10:10' },
];

export const actionGovernanceCases: ActionGovernanceCase[] = [
  {
    id: 'action-001',
    skillName: '请假申请',
    organizationName: '广汽乘用车',
    approvalStatus: '待审批',
    confirmationRule: '提交前必须展示请假区间、审批人和影响考勤天数，并由本人二次确认。',
    rollbackStatus: '若 OA 提交失败，回退为草稿并保留上次填写内容。',
    auditTrail: ['10:05 发起请假申请', '10:06 命中动作型能力规则', '10:07 等待主管审批'],
  },
  {
    id: 'action-002',
    skillName: '外部通知发送',
    organizationName: '集团总部',
    approvalStatus: '已回退',
    confirmationRule: '发送外部通知前需校验白名单并完成平台管理员确认。',
    rollbackStatus: '外部接口失败后已自动取消发送，并生成补发建议。',
    auditTrail: ['09:40 发起外部通知', '09:41 白名单校验通过', '09:42 外部接口超时，自动回退'],
  },
];

export const skillGovernanceTags: Record<string, SkillGovernanceTag> = {
  data_query: {
    businessDomain: '销售经营',
    riskLevel: '中',
    applicableOrganizations: ['广汽国际', '集团总部', '试点子公司'],
    requiresApproval: true,
    writesData: false,
  },
  data_web_compare_analysis: {
    businessDomain: '市场分析',
    riskLevel: '中',
    applicableOrganizations: ['广汽国际', '品牌与市场部'],
    requiresApproval: true,
    writesData: false,
  },
  yoy_yoy_analysis: {
    businessDomain: '经营分析',
    riskLevel: '低',
    applicableOrganizations: ['广汽国际', '销售管理部'],
    requiresApproval: false,
    writesData: false,
  },
  web_search_answer: {
    businessDomain: '公开资料检索',
    riskLevel: '低',
    applicableOrganizations: ['全集团'],
    requiresApproval: false,
    writesData: false,
  },
  web_compare_analysis: {
    businessDomain: '竞品分析',
    riskLevel: '低',
    applicableOrganizations: ['品牌与市场部', '广汽国际'],
    requiresApproval: false,
    writesData: false,
  },
  leave_request: {
    businessDomain: '人事流程',
    riskLevel: '高',
    applicableOrganizations: ['广汽乘用车', '集团总部'],
    requiresApproval: true,
    writesData: true,
  },
  chat: {
    businessDomain: '通用问答',
    riskLevel: '低',
    applicableOrganizations: ['全集团'],
    requiresApproval: false,
    writesData: false,
  },
  global_policy_watch: {
    businessDomain: '政策分析',
    riskLevel: '中',
    applicableOrganizations: ['广汽国际', '法务与政策研究组'],
    requiresApproval: true,
    writesData: false,
  },
  channel_inventory_diagnosis: {
    businessDomain: '渠道库存',
    riskLevel: '中',
    applicableOrganizations: ['广汽国际', '销售运营中心'],
    requiresApproval: true,
    writesData: false,
  },
};

export const statusLabel: Record<RuntimeStatus, string> = {
  enabled: '已启用',
  disabled: '已停用',
  warning: '配置异常',
  draft: '草稿',
};

export const releaseStatusLabel: Record<ReleaseStatus, string> = {
  draft: '草稿',
  testing: '测试中',
  ready_for_review: '待审核',
  review_approved: '审核通过',
  ready_to_publish: '待发布',
  published: '已发布',
  blocked_by_dependency: '依赖阻塞',
};

export const stageLabel: Record<LifecycleStage, string> = {
  draft: '草稿',
  testing: '测试',
  review: '提审',
  review_rejected: '审核退回',
  publish: '发布',
  published: '已发布',
  blocked: '阻塞',
};

export const lifecycleStageOptions = Object.entries(stageLabel).map(([value, label]) => ({
  value: value as LifecycleStage,
  label,
}));

export const lifecycleActionByStage: Record<LifecycleStage, string> = {
  draft: '先补齐业务目标和草案，再进入测试。',
  testing: '继续运行示例输入、检查依赖和定位失败原因。',
  review: '补齐提审资料并查看审核反馈。',
  review_rejected: '根据退回原因补齐资料后重新提审。',
  publish: '确认发布检查项和回滚预案后执行发布。',
  published: '当前版本已发布，可回看运行记录或准备下一版。',
  blocked: '先解除阻塞，再恢复测试。',
};

export const initialReleaseActivities: ReleaseActivity[] = [
  {
    id: 'release-001',
    entityType: 'skill',
    entityName: '库存快照助手',
    action: 'submitted_for_review',
    operator: '平台管理员',
    detail: '已提交人工复核，等待确认业务口径与组织范围。',
    createdAt: '2026-06-24T09:20:00+08:00',
  },
  {
    id: 'release-002',
    entityType: 'mcp',
    entityName: 'SQL 执行器',
    action: 'health_check_passed',
    operator: '平台管理员',
    detail: '健康检查通过，连接与 Schema 校验正常。',
    createdAt: '2026-06-24T10:10:00+08:00',
  },
  {
    id: 'release-003',
    entityType: 'skill',
    entityName: '海外政策追踪',
    action: 'published_to_catalog',
    operator: '平台管理员',
    detail: '已发布到集团能力目录，并保留上一稳定版本回滚预案。',
    createdAt: '2026-06-24T11:05:00+08:00',
  },
];

export const skillDependenciesForMcp = (mcpName: string, skills = initialSkills) =>
  skills.filter((skill) => skill.mcpTools.includes(mcpName));

export const lifecycleStageForReleaseStatus = (
  releaseStatus: ReleaseStatus,
  failureReason?: string,
): LifecycleStage => {
  if (releaseStatus === 'draft') return 'draft';
  if (releaseStatus === 'testing') return 'testing';
  if (releaseStatus === 'ready_for_review' || releaseStatus === 'review_approved') return 'review';
  if (releaseStatus === 'ready_to_publish') return 'publish';
  if (releaseStatus === 'published') return 'published';
  if (failureReason) return 'review_rejected';
  return 'blocked';
};

const matchesTaskEntity = (
  task: OperationsTask,
  type: AssetType,
  entityName: string,
  displayName: string,
) => task.type === type && (
  task.entityName === entityName
  || task.entityName === displayName
  || task.title.includes(displayName)
);

export const tasksForAsset = (
  type: AssetType,
  entityName: string,
  displayName: string,
  tasks: OperationsTask[],
) => {
  const directTasks = tasks.filter((task) => matchesTaskEntity(task, type, entityName, displayName));
  if (type !== 'skill') {
    return directTasks;
  }
  const directTaskIds = new Set(directTasks.map((task) => task.id));
  const childTasks = tasks.filter((task) => Boolean(task.parentTaskId && directTaskIds.has(task.parentTaskId)));
  return [...directTasks, ...childTasks];
};

export const taskLifecycleStage = (
  task: Pick<OperationsTask, 'releaseStatus' | 'failureReason' | 'blockedBy'>,
) => lifecycleStageForReleaseStatus(task.releaseStatus, task.failureReason || task.blockedBy);

export const countTasksByLifecycleStage = (
  tasks: Pick<OperationsTask, 'releaseStatus' | 'failureReason' | 'blockedBy'>[],
  stage: LifecycleStage,
) => tasks.filter((task) => taskLifecycleStage(task) === stage).length;

export const buildLifecycleMetrics = (
  assets: Pick<UnifiedAssetRecord, 'lifecycleStage'>[],
) => ({
  total: assets.length,
  testing: assets.filter((asset) => asset.lifecycleStage === 'testing').length,
  review: assets.filter((asset) => asset.lifecycleStage === 'review').length,
  publish: assets.filter((asset) => asset.lifecycleStage === 'publish').length,
});

const ownerForEntity = (
  type: AssetType,
  entityName: string,
  displayName: string,
  tasks: OperationsTask[],
) => tasksForAsset(type, entityName, displayName, tasks)[0]?.owner || '平台管理员';

const lifecycleStagePriority: Record<LifecycleStage, number> = {
  blocked: 0,
  review_rejected: 1,
  testing: 2,
  review: 3,
  publish: 4,
  draft: 5,
  published: 6,
};

export const buildUnifiedAssets = (
  skills = initialSkills,
  mcps = initialMcps,
  tasks = operationsTasks,
): UnifiedAssetRecord[] => {
  const skillAssets = skills.map((skill) => {
    const governance = skillGovernanceTags[skill.name];
    const linkedTask = tasks.find((task) => (
      task.type === 'skill'
      && (
        task.entityName === skill.name
        || task.entityName === skill.displayName
        || task.title.includes(skill.displayName)
      )
    ));
    const failureSummary = linkedTask?.failureReason || linkedTask?.blockedBy;
    return {
      id: `skill-${skill.name}`,
      type: 'skill' as const,
      name: skill.name,
      displayName: skill.displayName,
      description: skill.description,
      category: skill.category,
      status: skill.status,
      releaseStatus: skill.releaseStatus,
      lifecycleStage: lifecycleStageForReleaseStatus(skill.releaseStatus, failureSummary),
      updatedAt: skill.updatedAt,
      owner: ownerForEntity('skill', skill.name, skill.displayName, tasks),
      dependencySummary: skill.mcpTools.length ? `${skill.mcpTools.length} 个 MCP 依赖` : '无外部依赖',
      failureSummary,
      riskLabel: governance ? `风险：${governance.riskLevel}` : '风险：标准',
      organizationSummary: governance?.applicableOrganizations.join(' / ') || '待配置组织范围',
      route: `/admin/skills/${skill.name}`,
    };
  });
  const mcpAssets = mcps.map((mcp) => {
    const dependencies = skillDependenciesForMcp(mcp.name, skills);
    return {
      id: `mcp-${mcp.name}`,
      type: 'mcp' as const,
      name: mcp.name,
      displayName: mcp.displayName,
      description: mcp.description,
      category: mcp.category,
      status: mcp.status,
      releaseStatus: mcp.releaseStatus,
      lifecycleStage: lifecycleStageForReleaseStatus(mcp.releaseStatus, mcp.blockedBy),
      updatedAt: mcp.updatedAt,
      owner: ownerForEntity('mcp', mcp.name, mcp.displayName, tasks),
      dependencySummary: dependencies.length ? `被 ${dependencies.length} 个 Skill 引用` : '尚未被 Skill 引用',
      failureSummary: mcp.blockedBy,
      riskLabel: mcp.name.includes('executor') ? '风险：高' : '风险：中',
      organizationSummary: '发布前治理配置',
      route: `/admin/mcps/${mcp.name}`,
    };
  });
  return [...skillAssets, ...mcpAssets].sort((left, right) => {
    const stageDiff = lifecycleStagePriority[left.lifecycleStage] - lifecycleStagePriority[right.lifecycleStage];
    if (stageDiff !== 0) return stageDiff;
    if (left.type !== right.type) return left.type === 'mcp' ? -1 : 1;
    return left.displayName.localeCompare(right.displayName, 'zh-CN');
  });
};

export const operationsCenter = {
  title: '运行与权限',
};
