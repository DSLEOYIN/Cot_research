"""
内部数据 + 联网竞品对比分析 Skill

当用户在同一轮问题中同时要求查询内部业务数据，并联网搜索竞品、公开市场
或行业数据进行对比分析时使用。
"""

from __future__ import annotations

from skills import register_skill

SKILL_CONFIG = {
    "name": "data_web_compare_analysis",
    "description": "内部数据与联网竞品对比分析技能。当用户同时要求查询内部销量、库存、订单等业务数据，并联网搜索竞品销量、公开市场或行业情况做对比分析时使用。",
    "category": "数据分析",
    "mcpTools": [
        "knowledge_retrieval",
        "n2sql",
        "sql_executor",
        "llm",
        "web_search",
    ],
    "output_type": "内部数据 + 外部竞品对比分析",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的内部数据与联网竞品对比问题"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "国际24年的销量情况，并在网上搜索一下竞品的销量情况",
        "查询今年中东公司终端量，再联网看看竞品表现并分析",
        "把广汽国际销量和网上公开的同业销量做个对比"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "internal_query_extraction",
                "description": "内部查询提取 - 从复合问题中提取只用于内部数据库查询的子问题",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "internal_data_query"
                }
            },
            {
                "step": 2,
                "name": "knowledge_retrieval",
                "description": "知识检索 - 检索内部表结构和字段标准",
                "mcp": "knowledge_retrieval",
                "arguments": {
                    "query": "{{steps.internal_query_extraction.output.text}}",
                    "dataset_ids": ["字段标准查询名检索", "表用途说明"]
                }
            },
            {
                "step": 3,
                "name": "n2sql_generation",
                "description": "N2SQL生成 - 生成内部业务数据查询 SQL",
                "mcp": "n2sql",
                "arguments": {
                    "query": "{{steps.internal_query_extraction.output.text}}",
                    "context": "{{steps.knowledge_retrieval.output}}"
                }
            },
            {
                "step": 4,
                "name": "sql_execution",
                "description": "SQL执行 - 查询内部真实业务数据",
                "mcp": "sql_executor",
                "arguments": {
                    "query": "{{steps.n2sql_generation.output.sql}}",
                    "format": "md"
                }
            },
            {
                "step": 5,
                "name": "competitor_search_query",
                "description": "竞品搜索词生成 - 将外部检索诉求压缩成搜索词",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "web_search_query",
                    "template_vars": {
                        "conversation_context": ""
                    }
                }
            },
            {
                "step": 6,
                "name": "web_search",
                "description": "联网检索 - 搜索竞品或公开市场销量信息",
                "mcp": "web_search",
                "arguments": {
                    "query": "{{steps.competitor_search_query.output.text}}",
                    "max_results": 5
                }
            },
            {
                "step": 7,
                "name": "data_web_compare_analysis",
                "description": "内外部对比分析 - 结合内部查询结果与联网资料生成分析",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "data_web_compare_analysis",
                    "template_vars": {
                        "sql": "{{steps.n2sql_generation.output.sql}}",
                        "sql_data": "{{steps.sql_execution.output.data}}",
                        "web_results": "{{steps.web_search.output}}"
                    }
                }
            }
        ]
    }
}

register_skill(SKILL_CONFIG)
