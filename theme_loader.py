"""
Scenario Theme Configuration Loader

Handles reading, writing, and formatting of multi-scenario theme schemas (theme_config.json).
Provides environment-level hot reload of active tables and DDLs at runtime.
"""

from __future__ import annotations

import os
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "theme_config.json"


def load_config() -> dict:
    """Loads themes from theme_config.json"""
    if not CONFIG_PATH.exists():
        # Fallback default configuration if the file is missing
        return {
            "产销存 (生产-销售-库存)": {
                "tables": [
                    "v_dm_sal_wolesale_terminal_dly",
                    "v_dm_sal_stock_dly",
                    "v_dm_sal_sc_order_dly",
                    "v_dm_sal_scheduling_dly"
                ],
                "schemas": {
                    "v_dm_sal_wolesale_terminal_dly": "CREATE TABLE `v_dm_sal_wolesale_terminal_dly` (\n    `id` bigint COMMENT '主键ID',\n    `period_td` varchar(10) COMMENT '统计日期 (如 2024-08-01)',\n    `area_name` varchar(50) COMMENT '大区名称 (例如: 中东公司、巴拿马公司等)',\n    `country_name` varchar(50) COMMENT '国家名称',\n    `model_name` varchar(50) COMMENT '车型名称',\n    `wholesale_qty` int COMMENT '批发量',\n    `terminal_qty` int COMMENT '终端量'\n) COMMENT='批发终端日销量数据表，记录各区域各车型批发与实际销售情况';",
                    "v_dm_sal_stock_dly": "CREATE TABLE `v_dm_sal_stock_dly` (\n    `id` bigint COMMENT '主键ID',\n    `period_td` varchar(10) COMMENT '统计日期 (如 2024-08-01)',\n    `area_name` varchar(50) COMMENT '大区名称',\n    `country_name` varchar(50) COMMENT '国家名称',\n    `model_name` varchar(50) COMMENT '车型名称',\n    `stock_qty` int COMMENT '总库存数量'\n) COMMENT='库存日数据表，记录海外各区域车型库存量';",
                    "v_dm_sal_sc_order_dly": "CREATE TABLE `v_dm_sal_sc_order_dly` (\n    `id` bigint COMMENT '主键ID',\n    `period_td` varchar(10) COMMENT '统计日期',\n    `area_name` varchar(50) COMMENT '大区名称',\n    `country_name` varchar(50) COMMENT '国家名称',\n    `order_qty` int COMMENT 'SC订单数量'\n) COMMENT='SC海外订货日表，记录各区域订单提报详情';",
                    "v_dm_sal_scheduling_dly": "CREATE TABLE `v_dm_sal_scheduling_dly` (\n    `id` bigint COMMENT '主键ID',\n    `period_td` varchar(10) COMMENT '统计日期',\n    `area_name` varchar(50) COMMENT '大区名称',\n    `scheduling_qty` int COMMENT '排产下线数量'\n) COMMENT='排产日数据表，记录每日海外排产下线量数据';说明：本表不支持车型和国家颗粒度，仅支持按大区分组。"
                }
            }
        }
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config: dict) -> bool:
    """Saves themes dictionary to theme_config.json"""
    try:
        CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False


def get_themes() -> list[str]:
    """Returns the list of all available scenario theme names"""
    return list(load_config().keys())


def get_theme_details(theme_name: str) -> dict:
    """Returns the details of a specific scenario theme"""
    config = load_config()
    return config.get(theme_name, {"tables": [], "schemas": {}})


def save_theme(theme_name: str, tables: list[str], schemas: dict[str, str]) -> bool:
    """Saves or updates a scenario theme"""
    config = load_config()
    config[theme_name] = {
        "tables": [t.strip().lower() for t in tables if t.strip()],
        "schemas": {k.strip().lower(): v.strip() for k, v in schemas.items() if k.strip()}
    }
    return save_config(config)


def get_active_theme() -> str:
    """Returns the currently active theme name from environment variable, defaulting to the first theme"""
    themes = get_themes()
    if not themes:
        return ""
    return os.environ.get("ACTIVE_THEME", themes[0])


def get_active_theme_tables() -> tuple[str, ...]:
    """Returns the list of allowed tables for the active theme"""
    active_theme = get_active_theme()
    if not active_theme:
        return ()
    details = get_theme_details(active_theme)
    return tuple(details.get("tables", []))


def get_active_theme_table_info() -> str:
    """Generates the DDL prompt string for the active theme's schemas"""
    active_theme = get_active_theme()
    if not active_theme:
        return "No schema loaded."
    details = get_theme_details(active_theme)
    schemas = details.get("schemas", {})
    
    formatted_schemas = []
    for table_name, ddl in schemas.items():
        formatted_schemas.append(f"### 表名: {table_name}\n建表语句 DDL:\n```sql\n{ddl}\n```")
        
    return "\n\n".join(formatted_schemas)
