"""
同环比分析 Skill

专门处理同比、环比相关的查询与智能解读
"""

from __future__ import annotations

from skills import register_skill

SKILL_CONFIG = {
    "name": "yoy_yoy_analysis",
    "description": "同环比分析技能。当用户询问同比、环比、增长率等分析问题时使用。",
    "category": "数据分析",
    "mcpTools": [
        "llm",                  # 意图识别、数据解读
        "knowledge_retrieval",   # 知识检索
        "sql_executor",         # SQL执行
        "n2sql"                 # 自然语言转SQL
    ],
    "output_type": "分析报告/百分比",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的同环比分析查询语句"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "本月终端量同比去年怎么样？",
        "和上个月相比环比增长多少？",
        "今年销量同比增长了多少？"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "yoy_knowledge_retrieval",
                "description": "同环比知识检索 - 获取同环比计算口径与数据规则",
                "mcp": "knowledge_retrieval",
                "arguments": {
                    "query": "{{input.query}}",
                    "dataset_ids": ["同环比计算规则", "字段标准查询名检索", "表用途说明"]
                }
            },
            {
                "step": 2,
                "name": "yoy_n2sql",
                "description": "N2SQL同环比 - 生成包含同环比计算语句的SQL",
                "mcp": "n2sql",
                "arguments": {
                    "query": "{{input.query}}",
                    "table_info": "{{steps.yoy_knowledge_retrieval.output}}"
                }
            },
            {
                "step": 3,
                "name": "sql_execution",
                "description": "SQL执行 - 运行生成的同环比查询SQL",
                "mcp": "sql_executor",
                "arguments": {
                    "query": "{{steps.yoy_n2sql.output.sql}}",
                    "format": "md"
                }
            },
            {
                "step": 4,
                "name": "yoy_analysis",
                "description": "同环比分析解读 - 利用 LLM 进行增长与波动性解读",
                "mcp": "llm",
                "arguments": {
                    "prompt": "用户提问：{{input.query}}\n数据结果：{{steps.sql_execution.output.data}}",
                    "prompt_type": "yoy_analysis"
                }
            }
        ]
    },
    "yoy_rules": {
        "同比": "与去年同期相比",
        "环比": "与上一个统计周期相比",
        "calculation": "增长率 = (本期 - 上期) / 上期 * 100%"
    }
}

register_skill(SKILL_CONFIG)
