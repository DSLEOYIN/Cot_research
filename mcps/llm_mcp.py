"""
LLM 调用 MCP

封装大语言模型调用，支持多种 Prompt 类型
"""

import json
import os
from typing import TypedDict, Literal, NotRequired
from app_config import get_config, require_real_mode_config
from mcps import register_mcp


class LLMInput(TypedDict):
    prompt: str
    prompt_type: NotRequired[Literal[
        "intent_classification",
        "n2sql",
        "sql_correction",
        "data_analysis",
        "scope_explanation",
        "chat",
        "yoy_analysis"
    ]]
    model: NotRequired[str]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]


class LLMResult(TypedDict):
    success: bool
    text: str | None
    structured_output: dict | None
    error: str | None


# 默认 Prompt 模板
PROMPT_TEMPLATES = {
    "intent_classification": """根据用户输入，判断用户目的。
- 如果用户目的是查询数据相关的，problem_type=1
- 如果用户目的是闲聊，problem_type=2

参考示例：
- "中东和中国有几个小时的时差？" → 闲聊
- "8月终端量是多少？" → 数据分析
- "特斯拉最新动态" → 闲聊
- "哪个国家销售最好？" → 数据分析

用户输入：{user_input}

输出格式（JSON）：
{{
    "problem_type": "1或2",
    "problem_alpha": "置信度0-1"
}}""",

    "n2sql": """你是一个 SQL 生成专家，生成SQL用于查询MYSQL数据库。

黄金准则：
0. 优先参考提供的表结构和字段说明
1. 当用户提问对象是"广汽国际"时，不针对大区加where条件
2. 只返回 SQL，禁止包含任何解释性文字
3. 严禁使用 left join、join、right join，多表查询需通过子查询实现
4. 为每个输出列指定清晰的中文别名
5. 默认返回完整时间段聚合总值，除非用户明确要求按月/按周/按天
6. 库存查询：当年取最后一天，非当年取该年最后一天
7. 达成率等比例指标保留两位小数并带百分号%

表结构信息：
{table_info}

请根据以上信息和用户问题生成 SQL。""",

    "sql_correction": """你是一个 SQL 调试专家。

原始用户问题：{original_query}
错误的SQL：{wrong_sql}
执行报错信息：{error_message}
错误类型：{error_type}

请分析错误原因并修正 SQL。只输出修正后的 SQL，不要包含解释。""",

    "data_analysis": """你是熟悉广汽国际业务的数据分析师。

用户输入：{user_query}
数据结果：{sql_data}
SQL：{sql}

请结合以上信息进行深度分析，给出数据解读。注意：
- 不要执行数据计算
- 不要复述已有内容
- 直接给出分析结论""",

    "scope_explanation": """你是熟悉广汽国际的数据分析师。

用户输入：{user_query}
SQL：{sql}
建表语句：{table_info}

请写一段数据口径解释说明，包含：统计大区或国家、统计指标、统计时间和条件限制。
要求：精简完整，不超过50字。

格式：统计组织+时间范围+指标+口径+统计范围""",

    "chat": """你是专注于汽车领域的专业知识闲聊机器人，人设定位为"具备系统知识体系、逻辑严谨、表达专业"的汽车行业专家。

用户输入：{user_input}

请以专业视角解答疑问，同时维持适度互动性。""",

    "yoy_analysis": """你是数据分析专家。

用户问题：{user_query}
数据结果：{data}

请分析同比/环比数据，给出：
1. 增长还是下降
2. 变化幅度
3. 可能的原因分析"""
}


def llm(
    prompt: str,
    prompt_type: Literal[
        "intent_classification",
        "n2sql",
        "sql_correction",
        "data_analysis",
        "scope_explanation",
        "chat",
        "yoy_analysis"
    ] | None = None,
    model: str = "DeepSeek-V3.1",
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """
    LLM 调用 MCP

    Args:
        prompt: 提示词内容
        prompt_type: 提示词类型，用于选择对应模板
        model: 模型名称
        temperature: 温度参数
        max_tokens: 最大Token数

    Returns:
        LLM 生成的文本或结构化输出
    """
    # 如果有 prompt_type，使用对应模板
    if prompt_type and prompt_type in PROMPT_TEMPLATES:
        full_prompt = PROMPT_TEMPLATES[prompt_type].format(
            user_query=prompt,
            user_input=prompt,
            table_info="",  # 由调用方填充
            sql="",
            sql_data="",
            original_query="",
            wrong_sql="",
            error_message="",
            error_type="",
            data=""
        )
    else:
        full_prompt = prompt

    config = get_config()
    if config.mock_enabled:
        return json.dumps(_mock_llm_response(prompt, prompt_type), ensure_ascii=False)

    config_error = require_real_mode_config(config, need_model=True)
    if config_error:
        return json.dumps({
            "success": False,
            "text": None,
            "structured_output": None,
            "error": config_error,
            "error_type": "ConfigurationError"
        }, ensure_ascii=False)

    try:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.model.api_key}"
        }

        payload = {
            "model": model or config.model.model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(config.model.base_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 尝试解析 JSON 输出
            try:
                structured_output = json.loads(content)
                return json.dumps({
                    "success": True,
                    "text": content,
                    "structured_output": structured_output,
                    "error": None
                }, ensure_ascii=False)
            except:
                return json.dumps({
                    "success": True,
                    "text": content,
                    "structured_output": None,
                    "error": None
                }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "text": None,
            "structured_output": None,
            "error": str(e),
            "error_type": type(e).__name__
        }, ensure_ascii=False)


def _mock_llm_response(prompt: str, prompt_type: str | None) -> dict:
    if prompt_type == "intent_classification":
        structured_output = {"problem_type": "1", "problem_alpha": "0.92"}
        return {
            "success": True,
            "text": json.dumps(structured_output, ensure_ascii=False),
            "structured_output": structured_output,
            "error": None,
            "mock": True,
        }

    if prompt_type == "data_analysis":
        return {
            "success": True,
            "text": "Mock 数据显示：中东公司本月终端量为 1280，批发量为 1460，整体表现稳健。终端量同比增长 12.4%，说明零售需求有明显改善。",
            "structured_output": None,
            "error": None,
            "mock": True,
        }

    if prompt_type == "scope_explanation":
        return {
            "success": True,
            "text": "统计中东公司本月终端量与批发量，口径为 mock 演示数据。",
            "structured_output": None,
            "error": None,
            "mock": True,
        }

    if prompt_type == "yoy_analysis":
        return {
            "success": True,
            "text": "Mock 同环比分析：本月终端量同比增长 12.4%，增长主要来自中东区域终端需求恢复；建议继续跟踪订单转化和库存消化节奏。",
            "structured_output": None,
            "error": None,
            "mock": True,
        }

    if prompt_type == "chat":
        return {
            "success": True,
            "text": "一般家用车建议每 5000 到 10000 公里或每 6 到 12 个月保养一次，具体以车辆保养手册、机油类型和实际使用环境为准。",
            "structured_output": None,
            "error": None,
            "mock": True,
        }

    return {
        "success": True,
        "text": f"Mock LLM 已处理请求：{prompt[:120]}",
        "structured_output": None,
        "error": None,
        "mock": True,
    }


MCP_CONFIG = {
    "name": "llm",
    "description": "调用大语言模型。用于意图识别、SQL生成、SQL修正、数据解读、数据口径生成等。",
    "category": "ai",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "提示词内容"
            },
            "prompt_type": {
                "type": "string",
                "enum": [
                    "intent_classification",
                    "n2sql",
                    "sql_correction",
                    "data_analysis",
                    "scope_explanation",
                    "chat",
                    "yoy_analysis"
                ],
                "description": "提示词类型"
            },
            "model": {
                "type": "string",
                "default": "DeepSeek-V3.1",
                "description": "模型名称"
            },
            "temperature": {
                "type": "number",
                "default": 0.7,
                "description": "温度参数"
            },
            "max_tokens": {
                "type": "integer",
                "default": 4096,
                "description": "最大Token数"
            }
        },
        "required": ["prompt"]
    },
    "prompt_templates": list(PROMPT_TEMPLATES.keys()),
    "examples": [
        {
            "input": {"prompt": "8月终端量是多少？", "prompt_type": "intent_classification"},
            "description": "意图识别"
        }
    ]
}

register_mcp(MCP_CONFIG, llm)
