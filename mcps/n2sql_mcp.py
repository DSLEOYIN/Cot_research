"""
N2SQL MCP

将自然语言转换为 SQL 语句
"""

from __future__ import annotations

import json
from typing import TypedDict
from app_config import get_config, require_real_mode_config
from mcps import register_mcp


class N2SQLInput(TypedDict):
    query: str
    table_info: str | None
    context: str | None


class N2SQLResult(TypedDict):
    success: bool
    sql: str | None
    error: str | None


def n2sql(
    query: str,
    table_info: str | None = None,
    context: str | None = None
) -> str:
    """
    N2SQL MCP - 自然语言转 SQL

    Args:
        query: 用户的自然语言查询
        table_info: 表结构信息（建表语句等）
        context: 额外的上下文信息

    Returns:
        生成的 SQL 语句
    """
    # 从 theme_loader 中动态加载当前激活主题的表结构 DDL
    try:
        import theme_loader
        default_table_info = theme_loader.get_active_theme_table_info()
    except Exception:
        default_table_info = """
        ### 批发终端日表（v_dm_sal_wolesale_terminal_dly）
        - period_td: 统计日期
        - area_name: 大区名称（中东公司、巴拿马公司等）
        - country_name: 国家名称
        - model_name: 车型名称
        - wholesale_qty: 批发量
        - terminal_qty: 终端量

        ### 库存日表（v_dm_sal_stock_dly）
        - period_td: 统计日期
        - area_name: 大区名称
        - country_name: 国家名称
        - model_name: 车型名称
        - stock_qty: 总库存

        ### SC订单日表（v_dm_sal_sc_order_dly）
        - period_td: 统计日期
        - area_name: 大区名称
        - country_name: 国家名称
        - order_qty: 订单量
        """

    info = table_info or default_table_info
    context_section = f"\n补充上下文：\n{context}\n" if context else ""

    # 构建 Prompt
    prompt = f"""你是一个 SQL 生成专家。

用户问题：{query}

表结构信息：
{info}
{context_section}

生成规则：
1. 只返回 SQL，不要包含任何解释。
2. 为每个列指定中文别名。
3. 严禁使用 JOIN，用子查询实现多表查询。
4. 默认返回时间周期内的聚合总值。
5. 必须且只能使用物理英文表名（如 v_dm_sal_wolesale_terminal_dly），绝对禁止在 SQL 中直接使用中文表名（如“批发终端日表”）或拼音表名（如“xiaoshou_biao”）。
6. 必须且只能使用物理英文列名（如 period_td、area_name、country_name、model_name、wholesale_qty、terminal_qty），绝对禁止使用中文列名。

SQL："""

    try:
        import httpx

        config = get_config()
        if config.mock_enabled:
            return json.dumps({
                "success": True,
                "sql": _mock_sql(query),
                "original_query": query,
                "error": None,
                "mock": True
            }, ensure_ascii=False)

        config_error = require_real_mode_config(config, need_model=True)
        if config_error:
            return json.dumps({
                "success": False,
                "sql": None,
                "original_query": query,
                "error": config_error,
                "error_type": "ConfigurationError"
            }, ensure_ascii=False)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.model.api_key}"
        }

        payload = {
            "model": config.model.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2048
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(config.model.base_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 提取 SQL（去掉可能的markdown代码块）
            sql = content.strip()
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()

            return json.dumps({
                "success": True,
                "sql": sql,
                "original_query": query,
                "error": None
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "sql": None,
            "error": str(e),
            "error_type": type(e).__name__
        }, ensure_ascii=False)


def _mock_sql(query: str) -> str:
    if any(keyword in query for keyword in ["同比", "环比", "增长"]):
        return (
            "SELECT area_name AS '区域', "
            "SUM(terminal_qty) AS '本月终端量', "
            "ROUND(12.4, 2) AS '同比增长率' "
            "FROM v_dm_sal_wolesale_terminal_dly "
            "WHERE area_name = '中东公司' "
            "GROUP BY area_name"
        )

    if any(keyword in query for keyword in ["库存", "存货"]):
        return (
            "SELECT area_name AS '区域', SUM(stock_qty) AS '库存量' "
            "FROM v_dm_sal_stock_dly "
            "WHERE area_name = '中东公司' "
            "GROUP BY area_name"
        )

    return (
        "SELECT area_name AS '区域', "
        "SUM(terminal_qty) AS '终端量', "
        "SUM(wholesale_qty) AS '批发量' "
        "FROM v_dm_sal_wolesale_terminal_dly "
        "WHERE area_name = '中东公司' "
        "GROUP BY area_name"
    )


MCP_CONFIG = {
    "name": "n2sql",
    "description": "将自然语言查询转换为 SQL 语句。用于数据查询场景的第一步。",
    "category": "n2sql",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的自然语言查询"
            },
            "table_info": {
                "type": "string",
                "description": "表结构信息（可选，默认使用配置的表结构）"
            },
            "context": {
                "type": "string",
                "description": "额外的上下文信息（可选）"
            }
        },
        "required": ["query"]
    },
    "default_tables": [
        "v_dm_sal_wolesale_terminal_dly (批发终端日表)",
        "v_dm_sal_sc_order_dly (SC订单日表)",
        "v_dm_sal_stock_dly (库存日表)",
        "v_dm_sal_scheduling_dly (排产日表)"
    ],
    "examples": [
        {
            "input": {"query": "2024年8月中东公司的终端量是多少？"},
            "description": "生成查询中东公司8月终端量的SQL"
        }
    ]
}

register_mcp(MCP_CONFIG, n2sql)
