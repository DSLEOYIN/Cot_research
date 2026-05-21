"""
文本分析 MCP

文本摘要、情感分析、关键词提取等
"""

import json
from typing import TypedDict, Literal
from mcps import register_mcp


class TextAnalysisInput(TypedDict):
    text: str
    task: Literal["summarize", "sentiment", "keywords", "classify"]


class TextAnalysisResult(TypedDict):
    success: bool
    result: str
    task: str
    confidence: float | None


def text_analysis(
    text: str,
    task: Literal["summarize", "sentiment", "keywords", "classify"] = "summarize"
) -> str:
    """
    文本分析 MCP

    Args:
        text: 待分析的文本
        task: 分析任务类型
            - summarize: 文本摘要
            - sentiment: 情感分析
            - keywords: 关键词提取
            - classify: 文本分类

    Returns:
        分析结果
    """
    # 简单的 Mock 实现，实际项目中可以接入 NLP 服务
    mock_results = {
        "summarize": f"文本摘要：这段话主要讨论了数据分析相关内容，核心观点是围绕业务指标查询和解读。",
        "sentiment": "情感分析：中性偏正面，表达较为理性，主要目的是获取信息支持决策。",
        "keywords": "关键词：数据、分析、销量、库存、趋势、建议、风险、预警",
        "classify": "文本分类：数据分析类咨询 - 涉及业务指标查询和解读"
    }

    result = mock_results.get(task, "未知任务类型")

    return json.dumps({
        "success": True,
        "result": result,
        "task": task,
        "text_preview": text[:100] + "..." if len(text) > 100 else text,
        "confidence": 0.85
    }, ensure_ascii=False)


MCP_CONFIG = {
    "name": "text_analysis",
    "description": "分析文本内容。用于文本摘要、情感分析、关键词提取、文本分类等NLP任务。",
    "category": "nlp",
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "待分析的文本"
            },
            "task": {
                "type": "string",
                "enum": ["summarize", "sentiment", "keywords", "classify"],
                "description": "分析任务类型"
            }
        },
        "required": ["text", "task"]
    },
    "task_types": {
        "summarize": "文本摘要",
        "sentiment": "情感分析",
        "keywords": "关键词提取",
        "classify": "文本分类"
    },
    "examples": [
        {
            "input": {"text": "本月销量数据表现良好，同比增长15%", "task": "sentiment"},
            "description": "情感分析"
        }
    ]
}

register_mcp(MCP_CONFIG, text_analysis)
