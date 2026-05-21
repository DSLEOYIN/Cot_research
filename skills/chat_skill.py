"""
闲聊 Skill

处理非数据查询的一般对话，如闲聊、常识问答等
"""

from skills import register_skill

SKILL_CONFIG = {
    "name": "chat",
    "description": "闲聊技能。处理非数据相关的日常对话、汽车专业知识问答等。",
    "category": "闲聊",
    "mcpTools": [
        "llm",                  # 闲聊对话生成
    ],
    "output_type": "文本对话",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的对话内容"
            }
        },
        "required": ["query"]
    },
    "examples": [
        "你好",
        "今天天气怎么样？",
        "汽车保养一般多少公里做一次？"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "chat_response",
                "description": "闲聊回复 - 根据用户输入生成回复",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.query}}",
                    "prompt_type": "chat"
                }
            }
        ]
    },
    "persona": {
        "role": "汽车行业专家",
        "style": "专业严谨、表达专业",
        "scope": "汽车领域专业知识闲聊机器人"
    }
}

register_skill(SKILL_CONFIG)

