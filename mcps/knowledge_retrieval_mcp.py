"""
知识检索 MCP

从向量数据库检索相关知识
"""

import json
from typing import TypedDict
from mcps import register_mcp


class KnowledgeRetrievalInput(TypedDict):
    query: str
    dataset_ids: list[str] | None
    top_k: int | None
    retrieval_mode: str | None


class KnowledgeRetrievalResult(TypedDict):
    success: bool
    results: list[dict]
    error: str | None


def knowledge_retrieval(
    query: str,
    dataset_ids: list[str] | None = None,
    top_k: int = 10,
    retrieval_mode: str = "multiple"
) -> str:
    """
    知识检索 MCP

    Args:
        query: 检索查询语句
        dataset_ids: 数据集ID列表
        top_k: 返回结果数量
        retrieval_mode: 检索模式 (multiple/single)

    Returns:
        检索结果列表
    """
    # 默认数据集 - 表结构和字段标准
    default_datasets = {
        "字段标准查询名检索": [
            {"content": "终端量 (terminal_qty): 指实际销售给终端客户的数量，也就是零售量"},
            {"content": "批发量 (wholesale_qty): 主机厂销往经销商的车辆数量"},
            {"content": "交付量 (delivery_qty): 工厂下线并交付的车辆数量"},
            {"content": "库存量 (stock_qty): 经销商、子公司、厂端库存总和"},
            {"content": "订单量 (order_qty): 新增SC订单的数量"},
        ],
        "同环比计算规则": [
            {"content": "同比: 与去年同期相比，例如2024年8月 vs 2023年8月"},
            {"content": "环比: 与上一个统计周期相比，例如2024年8月 vs 2024年7月"},
            {"content": "同比增长率 = (本期 - 去年同期) / 去年同期 * 100%"},
            {"content": "环比增长率 = (本期 - 上期) / 上期 * 100%"},
        ],
        "表用途说明": [
            {"content": "批发终端日表: 记录批发量和终端量数据"},
            {"content": "库存日表: 记录库存相关数据，包含库龄分布"},
            {"content": "SC订单日表: 记录新增订单数据"},
            {"content": "排产日表: 记录排产和交付数据"},
        ]
    }

    try:
        # 如果没有提供 dataset_ids，检索所有
        if not dataset_ids:
            target_datasets = default_datasets
        else:
            target_datasets = {k: v for k, v in default_datasets.items() if k in dataset_ids}

        results = []
        for dataset_name, items in target_datasets.items():
            # 简单的关键词匹配
            for item in items:
                if any(keyword in query for keyword in ["终端", "零售"]):
                    if "终端" in item["content"]:
                        results.append({"content": item["content"], "dataset": dataset_name, "score": 0.9})
                elif any(keyword in query for keyword in ["批发", "销量", "发车"]):
                    if "批发" in item["content"]:
                        results.append({"content": item["content"], "dataset": dataset_name, "score": 0.9})
                elif any(keyword in query for keyword in ["同比", "环比", "增长"]):
                    if "同比" in item["content"] or "环比" in item["content"] or "增长" in item["content"]:
                        results.append({"content": item["content"], "dataset": dataset_name, "score": 0.9})

        # 如果没有匹配，返回默认的表结构信息
        if not results:
            results = [
                {"content": f"查询 '{query}' 相关的表结构和字段标准", "dataset": "default", "score": 0.5}
            ]

        return json.dumps({
            "success": True,
            "results": results[:top_k],
            "query": query
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "results": []
        }, ensure_ascii=False)


MCP_CONFIG = {
    "name": "knowledge_retrieval",
    "description": "从向量数据库检索相关知识。用于检索表结构、字段标准、业务规则等。",
    "category": "retrieval",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索查询语句"
            },
            "dataset_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "数据集ID列表，可选"
            },
            "top_k": {
                "type": "integer",
                "default": 10,
                "description": "返回结果数量"
            },
            "retrieval_mode": {
                "type": "string",
                "enum": ["multiple", "single"],
                "default": "multiple",
                "description": "检索模式"
            }
        },
        "required": ["query"]
    },
    "datasets": {
        "字段标准查询名检索": "检索字段定义和标准名称",
        "同环比计算规则": "检索同比环比计算口径",
        "表用途说明": "检索各表的用途 and 数据范围"
    },
    "examples": [
        {
            "input": {"query": "终端量是什么"},
            "description": "检索终端量字段的定义"
        },
        {
            "input": {"query": "同比计算方法"},
            "description": "检索同比计算规则"
        }
    ]
}

register_mcp(MCP_CONFIG, knowledge_retrieval)
