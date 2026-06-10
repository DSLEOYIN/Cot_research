"""
知识检索 MCP

从向量数据库检索相关知识
"""

from __future__ import annotations

import json
from typing import TypedDict
from mcps import register_mcp
from app_config import get_config


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
            {"content": "交付量 (delivery_qty): 排产表中的车辆交付数量"},
            {"content": "产量/排产量/下线量 (product_qty): 排产表中的车辆下线数量"},
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
            {"content": "批发终端日表 (物理表名: v_dm_sal_wolesale_terminal_dly): 记录批发量和终端量数据。常用字段有 period_td (统计日期), area_name (大区/区域名称如中东公司), country_name (国家), model_name (车型), wholesale_qty (批发量), terminal_qty (终端量)"},
            {"content": "库存日表 (物理表名: v_dm_sal_stock_dly): 记录库存相关数据，包含库龄分布。常用字段有 period_td (统计日期), area_name (大区/区域名称如中东公司), country_name (国家), model_name (车型), stock_qty (库存量)"},
            {"content": "SC订单日表 (物理表名: v_dm_sal_sc_order_dly): 记录新增订单数据。常用字段有 period_td (统计日期), area_name (大区/区域名称如中东公司), country_name (国家), model_name (车型), order_qty (订单量)"},
            {"content": "排产日表 (物理表名: v_dm_sal_scheduling_dly): 记录排产和交付数据。常用字段有 period_td (统计日期), area_name (大区/区域名称如中东公司), country_name (国家), model_name (车型), delivery_qty (交付量), product_qty (排产量)"},
        ]
    }

    config = get_config()
    results = []

    # 1. 尝试直接请求 Dify 知识库接口
    if config.dify.enabled and not config.mock_enabled:
        import httpx
        from urllib.parse import urlparse
        parsed_url = urlparse(config.dify.base_url)
        dify_host = parsed_url.hostname
        dify_port = parsed_url.port or 9879
        if not dify_host:
            raise ValueError("DIFY_BASE_URL 缺少有效主机名")

        try:
            # 建立 SSH 隧道
            if config.ssh.enabled:
                from sshtunnel import SSHTunnelForwarder
                with SSHTunnelForwarder(
                    (config.ssh.host, config.ssh.port),
                    ssh_username=config.ssh.user,
                    ssh_password=config.ssh.password,
                    remote_bind_address=(dify_host, dify_port)
                ) as tunnel:
                    url = f"http://127.0.0.1:{tunnel.local_bind_port}/v1/datasets/{config.dify.dataset_id}/retrieve"
                    headers = {
                        "Authorization": f"Bearer {config.dify.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "query": query,
                        "retrieval_model": {
                            "search_method": "hybrid_search",
                            "top_k": top_k or 3,
                            "score_threshold_enabled": False,
                            "reranking_enable": True,
                            "reranking_model": {
                                "reranking_provider_name": "langgenius/siliconflow/siliconflow",
                                "reranking_model_name": "netease-youdao/bce-reranker-base_v1"
                            }
                        }
                    }
                    response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
                    response.raise_for_status()
                    data = response.json()
            else:
                url = f"{config.dify.base_url}/v1/datasets/{config.dify.dataset_id}/retrieve"
                headers = {
                    "Authorization": f"Bearer {config.dify.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "query": query,
                    "retrieval_model": {
                        "search_method": "hybrid_search",
                        "top_k": top_k or 3,
                        "score_threshold_enabled": False,
                        "reranking_enable": True,
                        "reranking_model": {
                            "reranking_provider_name": "langgenius/siliconflow/siliconflow",
                            "reranking_model_name": "netease-youdao/bce-reranker-base_v1"
                        }
                    }
                }
                response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
                response.raise_for_status()
                data = response.json()

            for record in data.get("records", []):
                segment = record.get("segment", {})
                content = segment.get("content", "")
                score = record.get("score", 0.0)
                results.append({
                    "content": content,
                    "dataset": segment.get("document", {}).get("name", "dify_knowledge"),
                    "score": score
                })

        except Exception as e:
            print(f"[Knowledge Retrieval] Dify API retrieve failed: {e}. Falling back to local memory.")
            results = []

    # 2. 如果 Dify 未启用、未查到结果或出错，降级为本地规则过滤
    if not results:
        try:
            if not dataset_ids:
                target_datasets = default_datasets
            else:
                target_datasets = {k: v for k, v in default_datasets.items() if k in dataset_ids}

            for dataset_name, items in target_datasets.items():
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

            if not results:
                results = [
                    {"content": f"查询 '{query}' 相关的表结构和字段标准", "dataset": "default", "score": 0.5}
                ]
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e),
                "results": []
            }, ensure_ascii=False)

    return json.dumps({
        "success": True,
        "results": results[:top_k],
        "query": query
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
