# MCPs 文件夹

## 概述

MCP (Model Context Protocol) 是底层工具执行单元。每个 MCP 封装一个具体的可执行能力。

## 现有 MCPs

| MCP 名称 | 文件 | 功能 |
|----------|------|------|
| sql_executor | sql_executor_mcp.py | 执行 SQL 查询 |
| knowledge_retrieval | knowledge_retrieval_mcp.py | 向量数据库知识检索 |
| llm | llm_mcp.py | 调用大语言模型 |
| time | time_mcp.py | 获取当前时间 |
| text_analysis | text_analysis_mcp.py | 文本分析（摘要/情感/关键词）|
| n2sql | n2sql_mcp.py | 自然语言转 SQL |
| web_search | web_search_mcp.py | 联网检索（Tavily） |

## 添加新的 MCP

创建一个新的 MCP 文件，参考 `sql_executor_mcp.py` 的结构：

```python
import json
from mcps import register_mcp

def your_mcp_function(
    param1: str,
    param2: int = 10
) -> str:
    """
    MCP 函数说明

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        JSON 格式的执行结果
    """
    try:
        # 执行逻辑
        result = {"success": True, "data": "..."}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


MCP_CONFIG = {
    "name": "your_mcp_name",           # MCP 唯一标识
    "description": "MCP 功能描述",       # 说明用途
    "category": "分类",                  # 工具分类（database/ai/nlp等）
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "参数1说明"
            },
            "param2": {
                "type": "integer",
                "default": 10,
                "description": "参数2说明"
            }
        },
        "required": ["param1"]
    },
    "examples": [
        {
            "input": {"param1": "value1", "param2": 5},
            "description": "示例说明"
        }
    ]
}

register_mcp(MCP_CONFIG)
```

## MCP 配置说明

| 字段 | 必填 | 说明 |
|------|------|------|
| name | 是 | MCP 唯一标识 |
| description | 是 | MCP 功能描述 |
| category | 否 | 分类（database/ai/nlp/retrieval/utility）|
| input_schema | 是 | 输入参数 JSON Schema |
| examples | 否 | 使用示例 |

## 输入 Schema 示例

```python
"input_schema": {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "查询语句"
        },
        "limit": {
            "type": "integer",
            "default": 10,
            "description": "返回数量限制"
        },
        "format": {
            "type": "string",
            "enum": ["json", "xml", "csv"],
            "default": "json"
        }
    },
    "required": ["query"]
}
```

## 返回格式规范

MCP 函数应返回 JSON 格式的字符串：

```python
# 成功时
json.dumps({
    "success": True,
    "data": {...},      # 业务数据
    "extra": "额外信息"  # 可选
}, ensure_ascii=False)

# 失败时
json.dumps({
    "success": False,
    "error": "错误信息",
    "error_type": "ErrorType"  # 可选
}, ensure_ascii=False)
```
