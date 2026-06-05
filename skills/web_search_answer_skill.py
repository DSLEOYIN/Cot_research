"""
联网检索问答 Skill

当用户明确要求联网搜索、查网上资料、查新闻或最新公开信息时使用。
"""

from __future__ import annotations

from skills import register_skill

SKILL_CONFIG = {
    "name": "web_search_answer",
    "description": "联网检索问答技能。当用户明确要求搜索网上资料、最新消息、新闻或公开信息时使用。",
    "category": "联网检索",
    "mcpTools": [
        "web_search",
        "llm",
    ],
    "output_type": "联网资料摘要/问答",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的联网检索问题"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "帮我网上搜一下最近中东汽车销量趋势",
        "查一下今天有什么汽车行业新闻",
        "联网搜索广汽国际最近公开信息"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "web_search",
                "description": "联网检索 - 使用用户问题作为搜索词查询公开网页信息",
                "mcp": "web_search",
                "arguments": {
                    "query": "{{input.current_query}}",
                    "max_results": 5
                }
            },
            {
                "step": 2,
                "name": "web_answer",
                "description": "联网资料总结 - 基于搜索结果回答用户问题",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.current_query}}",
                    "prompt_type": "web_search_answer",
                    "template_vars": {
                        "web_results": "{{steps.web_search.output}}"
                    }
                }
            }
        ]
    }
}

register_skill(SKILL_CONFIG)
