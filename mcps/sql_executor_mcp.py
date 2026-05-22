"""
SQL执行器 MCP

执行 SQL 查询，支持重试机制
"""

import json
import re
from typing import TypedDict, Literal
from app_config import get_config, require_real_mode_config
from mcps import register_mcp


class SQLExecuteInput(TypedDict):
    query: str
    db_uri: str | None
    format: Literal["json", "csv", "yaml", "md", "xlsx", "html"]


class SQLExecuteResult(TypedDict):
    success: bool
    data: str | None
    error: str | None
    error_type: str | None
    row_count: int | None


def sql_executor(
    query: str,
    db_uri: str | None = None,
    format: Literal["json", "csv", "yaml", "md", "xlsx", "html"] = "md"
) -> str:
    """
    SQL执行器 MCP

    Args:
        query: SQL查询语句
        db_uri: 数据库连接URI（可选，默认使用配置的数据库）
        format: 输出格式

    Returns:
        JSON格式的执行结果

    安全规则:
        - 禁止执行: DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, CREATE, GRANT, REVOKE
    """
    if not query or not isinstance(query, str):
        return json.dumps({
            "success": False,
            "error": "SQL 查询参数为空或非字符串",
            "error_type": "ArgumentError",
            "data": None,
            "row_count": None
        }, ensure_ascii=False)

    config = get_config(db_uri)
    validation_error = validate_select_sql(query, config.database.allowed_tables)
    if validation_error:
        return json.dumps({
            "success": False,
            "error": validation_error,
            "error_type": "SecurityError",
            "data": None,
            "row_count": None
        }, ensure_ascii=False)

    query_upper = query.strip().upper()

    if config.mock_enabled:
        mock_rows = [
            {"区域": "中东公司", "指标": "终端量", "本月数量": 1280, "同比": "12.4%"},
            {"区域": "中东公司", "指标": "批发量", "本月数量": 1460, "同比": "9.8%"},
        ]
        columns = list(mock_rows[0].keys())
        if format == "json":
            output = json.dumps({"columns": columns, "rows": mock_rows, "row_count": len(mock_rows)}, ensure_ascii=False)
        else:
            md_lines = [
                "| " + " | ".join(columns) + " |",
                "| " + " | ".join(["---"] * len(columns)) + " |",
            ]
            for row in mock_rows:
                md_lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
            output = "\n".join(md_lines)

        return json.dumps({
            "success": True,
            "data": output,
            "error": None,
            "error_type": None,
            "row_count": len(mock_rows),
            "mock": True
        }, ensure_ascii=False)

    config_error = require_real_mode_config(config, need_db=True)
    if config_error:
        return json.dumps({
            "success": False,
            "data": None,
            "error": config_error,
            "error_type": "ConfigurationError",
            "row_count": None
        }, ensure_ascii=False)

    db = config.database

    # 执行查询
    try:
        import pymysql

        connection = pymysql.connect(
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            database=db.name,
            charset=db.charset,
            connect_timeout=db.connect_timeout,
            read_timeout=db.read_timeout,
            write_timeout=db.write_timeout
        )

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)

            if query_upper.strip().startswith('SELECT'):
                results = cursor.fetchmany(config.database.max_rows + 1)
                truncated = len(results) > config.database.max_rows
                if truncated:
                    results = results[:config.database.max_rows]
                columns = list(results[0].keys()) if results else []

                if format == "json":
                    output = json.dumps({"columns": columns, "rows": results, "row_count": len(results)}, ensure_ascii=False)
                elif format == "md":
                    # Markdown 表格格式
                    md_lines = ["| " + " | ".join(columns) + " |",
                               "| " + " | ".join(["---"] * len(columns)) + " |"]
                    for row in results:
                        md_lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
                    output = "\n".join(md_lines)
                else:
                    output = json.dumps({"columns": columns, "rows": results, "row_count": len(results)}, ensure_ascii=False)

                return json.dumps({
                    "success": True,
                    "data": output,
                    "error": None,
                    "error_type": None,
                    "row_count": len(results),
                    "truncated": truncated,
                    "max_rows": config.database.max_rows
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "success": False,
                    "data": None,
                    "error": "只支持 SELECT 查询",
                    "error_type": "SecurityError",
                    "row_count": None
                }, ensure_ascii=False)

    except Exception as e:
        error_type = type(e).__name__
        return json.dumps({
            "success": False,
            "data": None,
            "error": str(e),
            "error_type": error_type,
            "row_count": None
        }, ensure_ascii=False)


def validate_select_sql(query: str, allowed_tables: tuple[str, ...]) -> str | None:
    statements = _split_sql_statements(query)
    if len(statements) != 1:
        return "只允许执行单条 SELECT SQL"

    statement = statements[0].strip().rstrip(";")
    if not statement.upper().startswith("SELECT"):
        return "只支持 SELECT 查询"

    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for keyword in forbidden_keywords:
        if re.search(rf"\b{keyword}\b", statement, flags=re.IGNORECASE):
            return f"禁止执行危险SQL: 包含 {keyword} 关键字"

    referenced_tables = extract_table_names(statement)
    if allowed_tables and "*" not in allowed_tables:
        disallowed = sorted(table for table in referenced_tables if table.lower() not in allowed_tables)
        if disallowed:
            return f"SQL 引用了未加入白名单的表: {', '.join(disallowed)}"

    return None


def _split_sql_statements(query: str) -> list[str]:
    try:
        import sqlparse

        return [statement for statement in sqlparse.split(query) if statement.strip()]
    except Exception:
        return [statement for statement in query.split(";") if statement.strip()]


def extract_table_names(query: str) -> set[str]:
    table_names: set[str] = set()
    pattern = re.compile(r"\b(?:FROM|JOIN)\s+([`\"\[]?[\w.]+[`\"\]]?)", re.IGNORECASE)
    for match in pattern.finditer(query):
        raw_name = match.group(1).strip("`\"[]")
        if raw_name.startswith("("):
            continue
        table_names.add(raw_name.split(".")[-1].lower())
    return table_names


MCP_CONFIG = {
    "name": "sql_executor",
    "description": "执行 SQL 查询。用于查询业务数据、统计数据等。只支持 SELECT 查询，禁止执行危险操作。",
    "category": "database",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL查询语句。只支持 SELECT 语句。"
            },
            "db_uri": {
                "type": "string",
                "description": "数据库连接URI。可选，默认使用配置的数据库。"
            },
            "format": {
                "type": "string",
                "enum": ["json", "csv", "yaml", "md", "xlsx", "html"],
                "default": "md",
                "description": "输出格式"
            }
        },
        "required": ["query"]
    },
    "security_rules": {
        "forbidden_operations": ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"],
        "allowed_operations": ["SELECT"],
        "table_whitelist_env": "DB_ALLOWED_TABLES",
        "max_rows_env": "SQL_MAX_ROWS"
    },
    "examples": [
        {
            "input": {"query": "SELECT area_name, SUM(terminal_qty) FROM v_dm_sal_wolesale_terminal_dly WHERE period_td = '2024-08-01' GROUP BY area_name"},
            "description": "查询各区域8月终端量"
        }
    ]
}

register_mcp(MCP_CONFIG, sql_executor)
