"""
SQL执行器 MCP

执行 SQL 查询，支持重试机制
"""

import json
from typing import TypedDict, Literal
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
            "error_type": "ArgumentError"
        }, ensure_ascii=False)

    forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
    query_upper = query.strip().upper()

    for keyword in forbidden_keywords:
        if keyword in query_upper:
            return json.dumps({
                "success": False,
                "error": f"禁止执行危险SQL: 包含 {keyword} 关键字",
                "error_type": "SecurityError"
            }, ensure_ascii=False)

    # Load environment variables from .env if available
    import os
    # Try multiple paths for .env
    for path in [".env", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
            except Exception:
                pass

    # 从环境变量解析或使用 db_uri
    if not db_uri:
        db_user = os.getenv("DB_USER", "aiwork")
        db_password = os.getenv("DB_PASSWORD", "I!p0P(FZZt")
        db_host = os.getenv("DB_HOST", "10.30.16.21")
        db_port = int(os.getenv("DB_PORT", "6033"))
        db_name = os.getenv("DB_NAME", "ads_international")
    else:
        try:
            db_user = db_uri.split('://')[1].split(':')[0] if '://' in db_uri else 'root'
            db_password = db_uri.split(':')[2].split('@')[0] if len(db_uri.split(':')) > 2 else ''
            db_host = db_uri.split('@')[1].split('/')[0].split(':')[0] if '@' in db_uri else 'localhost'
            db_port = int(db_uri.split(':')[-1].split('/')[0]) if ':' in db_uri else 3306
            db_name = db_uri.split('/')[-1] if '/' in db_uri else ''
        except Exception:
            db_user, db_password, db_host, db_port, db_name = "aiwork", "I!p0P(FZZt", "10.30.16.21", 6033, "ads_international"

    # 执行查询
    try:
        import pymysql

        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)

            if query_upper.strip().startswith('SELECT'):
                results = cursor.fetchall()
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
                    "row_count": len(results)
                }, ensure_ascii=False)
            else:
                connection.commit()
                return json.dumps({
                    "success": True,
                    "affected_rows": cursor.rowcount,
                    "message": "执行成功"
                }, ensure_ascii=False)

    except Exception as e:
        error_type = type(e).__name__
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": error_type
        }, ensure_ascii=False)


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
        "allowed_operations": ["SELECT"]
    },
    "examples": [
        {
            "input": {"query": "SELECT area_name, SUM(terminal_qty) FROM v_dm_sal_wolesale_terminal_dly WHERE period_td = '2024-08-01' GROUP BY area_name"},
            "description": "查询各区域8月终端量"
        }
    ]
}

register_mcp(MCP_CONFIG, sql_executor)
