"""
数据查询 Skill

完整的数据分析流程（基于行业标准声明式双层架构）：
意图识别 → 知识检索 → N2SQL → SQL生成 → SQL执行 → 数据解读 → 数据口径
"""

from skills import register_skill

SKILL_CONFIG = {
    "name": "data_query",
    "description": "数据查询与分析技能。当用户询问销量、库存、订单、达成率、排产等业务数据时使用。",
    "category": "数据分析",
    "mcpTools": [
        "llm",                  # 意图识别、SQL生成、数据解读、数据口径
        "knowledge_retrieval",   # 知识检索
        "sql_executor",         # SQL执行
        "n2sql",                # 自然语言转SQL
    ],
    "output_type": "表格/数值/分析报告",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的自然语言查询"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "2024年中东公司销量如何？",
        "哪个国家销售最好？",
        "库存情况如何？",
        "今年SC订单有多少量？"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "intent_recognition",
                "description": "意图识别 - 判断是否数据查询",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.query}}",
                    "prompt_type": "intent_classification"
                }
            },
            {
                "step": 2,
                "name": "knowledge_retrieval",
                "description": "知识检索 - 检索表结构和字段标准",
                "mcp": "knowledge_retrieval",
                "arguments": {
                    "query": "{{input.query}}",
                    "dataset_ids": ["字段标准查询名检索", "表用途说明"]
                }
            },
            {
                "step": 3,
                "name": "n2sql_generation",
                "description": "N2SQL生成 - 根据检索结果与表结构生成SQL",
                "mcp": "n2sql",
                "arguments": {
                    "query": "{{input.query}}",
                    "table_info": "{{steps.knowledge_retrieval.output}}"
                }
            },
            {
                "step": 4,
                "name": "sql_execution",
                "description": "SQL执行 - 安全查询数据库",
                "mcp": "sql_executor",
                "arguments": {
                    "query": "{{steps.n2sql_generation.output.sql}}",
                    "format": "md"
                }
            },
            {
                "step": 5,
                "name": "data_interpretation",
                "description": "数据解读 - LLM分析查询结果",
                "mcp": "llm",
                "arguments": {
                    "prompt": "用户输入：{{input.query}}\n数据结果：{{steps.sql_execution.output.data}}\nSQL：{{steps.n2sql_generation.output.sql}}",
                    "prompt_type": "data_analysis"
                }
            },
            {
                "step": 6,
                "name": "data_scope_explanation",
                "description": "数据口径 - 生成统计解释说明",
                "mcp": "llm",
                "arguments": {
                    "prompt": "用户输入：{{input.query}}\nSQL：{{steps.n2sql_generation.output.sql}}",
                    "prompt_type": "scope_explanation"
                }
            }
        ]
    },
    "table_configs": {
        "批发终端日表": "v_dm_sal_wolesale_terminal_dly",
        "SC订单日表": "v_dm_sal_sc_order_dly",
        "库存日表": "v_dm_sal_stock_dly",
        "排产日表": "v_dm_sal_scheduling_dly"
    },
    "sql_rules": {
        "forbidden_joins": ["LEFT JOIN", "RIGHT JOIN", "JOIN"],
        "must_use_subquery": "多表查询需通过子查询先聚合",
        "time_aggregation": "默认返回完整时间段聚合总值，除非用户明确要求按月/按周/按天"
    }
}

register_skill(SKILL_CONFIG)

