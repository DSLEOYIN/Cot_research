"""
联网对比分析 Skill

当用户要求把上文真实数据、刚才结果与网上公开资料进行对比或解释时使用。
"""

from __future__ import annotations

from skills import register_skill

SKILL_CONFIG = {
    "name": "web_compare_analysis",
    "description": "联网对比分析技能。当用户要求结合上文数据、真实数据或刚才结果，并与网上公开信息、行业趋势进行对比分析时使用。",
    "category": "联网分析",
    "mcpTools": [
        "llm",
        "web_search",
    ],
    "output_type": "内外部数据对比分析",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的联网对比分析问题"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "和网上公开的行业情况对比一下，分析为什么会这样",
        "结合刚才的真实数据和网上资料做个分析",
        "拿上面的销量结果和最新行业趋势对比一下"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "search_query_generation",
                "description": "搜索词生成 - 将当前问题和上文摘要压缩成简洁搜索词",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "web_search_query",
                    "template_vars": {
                        "conversation_context": "{{input.conversation_context}}"
                    }
                }
            },
            {
                "step": 2,
                "name": "web_search",
                "description": "联网检索 - 使用生成的搜索词查询公开网页信息",
                "mcp": "web_search",
                "arguments": {
                    "query": "{{steps.search_query_generation.output.text}}",
                    "max_results": 5
                }
            },
            {
                "step": 3,
                "name": "web_compare_analysis",
                "description": "联网对比分析 - 结合上文真实数据和公开资料进行深度分析",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "web_compare_analysis",
                    "template_vars": {
                        "conversation_context": "{{input.conversation_context}}",
                        "web_results": "{{steps.web_search.output}}"
                    }
                }
            }
        ]
    }
}

register_skill(SKILL_CONFIG)
