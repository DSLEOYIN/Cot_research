# 行业标准级 MCP 工具与 Skill 规范定义手册

为了实现您的愿景——**“在互联网上看到任何优秀的 Skill 或 MCP 工具，都可以直接零缝隙配置进来并供大模型决策使用”**，本系统采用了**完全对接 Anthropic 官方 Model Context Protocol (MCP) 规范**的工具标准，并结合了**声明式工作流 DSL（如 Dify、LangFlow）**，为 Skill 制定了一套高度通用的声明格式。

本手册为您定义了 **MCP Tool** 与 **Skill** 的**行业官方标准 Schema 契约**，并提供了标准的配置模板与集成注册机制。

---

# 一、 MCP Tool (工具层) 行业标准规范

根据 Anthropic 官方 MCP 规范，一个 Tool 的定义必须严格遵循其 JSON 契约。其核心要点是：参数定义必须为标准的 **JSON Schema (Draft-07 或 2020-12)**，且属性键名为 **`inputSchema` (驼峰命名)**。

### 1. 官方标准 MCP Tool JSON 声明格式
如果您在网上下载或购买了标准的 MCP 插件，其元数据格式通常如下所示：
```json
{
  "name": "fetch_market_news",
  "description": "获取特定行业或竞品的最新市场新闻与动态。适用于收集竞品分析素材。",
  "inputSchema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "industry": {
        "type": "string",
        "description": "目标行业名称，例如 'automotive', 'semiconductor'"
      },
      "competitors": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "需要关注的竞品公司列表，例如 ['tesla', 'byd']"
      },
      "limit": {
        "type": "integer",
        "default": 5,
        "description": "返回的新闻条数限制"
      }
    },
    "required": ["industry"]
  }
}
```

### 2. 标准 Python 模块编写模板 (`mcps/market_news_mcp.py`)
在系统中导入一个全新的工具，只需在 `mcps/` 目录下创建一个新的 Python 文件并实现如下逻辑：

```python
# mcps/market_news_mcp.py
import json
from typing import List, Optional
from mcps import register_mcp

# 1. 编写原子工具函数
def fetch_market_news(industry: str, competitors: Optional[List[str]] = None, limit: int = 5) -> str:
    """
    获取特定行业或竞品的最新市场新闻与动态。适用于收集竞品分析素材。
    
    Args:
        industry: 目标行业名称
        competitors: 关注的竞品列表
        limit: 返回新闻限制条数
    """
    try:
        # 这里编写您的业务逻辑（例如调用第三方 REST API，或执行本地脚本）
        mock_data = {
            "success": True,
            "news": [
                {"title": f"{industry} 行业新趋势", "source": "Reuters", "content": "数据摘要..."},
            ]
        }
        return json.dumps(mock_data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# 2. 注册配置 - 严格对接 MCP 官方规范 (inputSchema)
MCP_CONFIG = {
    "name": "fetch_market_news",
    "description": "获取特定行业或竞品的最新市场新闻与动态。适用于收集竞品分析素材。",
    "category": "retrieval",
    "inputSchema": {
        "type": "object",
        "properties": {
            "industry": {
                "type": "string",
                "description": "目标行业名称，例如 'automotive'"
            },
            "competitors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "关注的竞品列表，可选"
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "description": "返回新闻条数限制"
            }
        },
        "required": ["industry"]
    }
}

# 3. 动态加载注册
register_mcp(MCP_CONFIG, fetch_market_news)
```

最后在 `mcps/__init__.py` 的底部添加一行导入语句：
```python
from . import market_news_mcp
```
**系统检测到后会在 Streamlit 侧边栏和编排层中自动热插拔载入该工具。**

---

# 二、 Skill (能力编排层) 行业标准规范

由于 Anthropic MCP 协议本身只定义了底层的原子 `Tools`，没有定义复合的工作流编排。
为了让您在互联网上发现的复杂业务流（比如“数据分析 SOP”、“同环比诊断”）能以标准化的格式配置进来，系统采用双大括号 `{{ }}` 语法（类似 Jinja2 或 Dify 变量槽）在步骤间传递数据：

### 1. 标准 Skill 声明格式模板 (`skills/data_query_skill.py`)
在系统中导入一个全新的 Skill 工作流，只需在 `skills/` 目录下创建一个新的 Python 文件并配置声明式 DSL 流：

```python
# skills/data_query_skill.py
from skills import register_skill

SKILL_CONFIG = {
    "name": "data_query",
    "description": "数据查询与分析技能。当用户询问销量、库存、订单、达成率、排产等业务数据时使用。",
    "category": "数据分析",
    "mcpTools": [
        "llm",                  # 意图识别、数据解读、数据口径
        "knowledge_retrieval",   # 知识检索
        "sql_executor",         # SQL执行
        "n2sql",                # 自然语言转SQL
    ],
    "output_type": "表格/数值/分析报告",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的自然语言查询"
            }
        },
        "required": ["query"]
    },
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "intent_recognition",
                "description": "意图识别 - 判断是否数据查询",
                "mcp": "llm",
                "arguments": {
                    "prompt": "{{input.query}}",
                    "prompt_type": "intent_classification"
                }
            },
            {
                "step": 2,
                "name": "knowledge_retrieval",
                "description": "知识检索 - 检索表结构和字段标准",
                "mcp": "knowledge_retrieval",
                "arguments": {
                    "query": "{{input.query}}",
                    "dataset_ids": ["字段标准查询名检索", "表用途说明"] # 自动局限于指定数据集
                }
            },
            {
                "step": 3,
                "name": "n2sql_generation",
                "description": "N2SQL生成 - 根据检索结果与表结构生成SQL",
                "mcp": "n2sql",
                "arguments": {
                    "query": "{{input.query}}",
                    "table_info": "{{steps.knowledge_retrieval.output}}" # 管道传参，自动保留字典类型
                }
            },
            {
                "step": 4,
                "name": "sql_execution",
                "description": "SQL执行 - 安全查询数据库",
                "mcp": "sql_executor",
                "arguments": {
                    "query": "{{steps.n2sql_generation.output.sql}}",
                    "format": "md"
                }
            },
            {
                "step": 5,
                "name": "data_interpretation",
                "description": "数据解读 - LLM分析查询结果",
                "mcp": "llm",
                "arguments": {
                    "prompt": "用户输入：{{input.query}}\n数据结果：{{steps.sql_execution.output.data}}\nSQL：{{steps.n2sql_generation.output.sql}}",
                    "prompt_type": "data_analysis"
                }
            }
        ]
    }
}

register_skill(SKILL_CONFIG)
```

最后在 `skills/__init__.py` 的底部添加一行导入语句：
```python
from . import data_query_skill
```
**系统会在运行状态下，通过 `langgraph_cot.py` 双层决策引擎，自动路由和顺序执行该 SOP 管道！**

---

# 三、 总结：如何将“外网优秀工具”快速配置进来？

1. **导入一个工具 Python 脚本**：
   * 在 `mcps/` 创建 `tool_mcp.py`。
   * 编写执行函数并包裹在 `register_mcp(MCP_CONFIG, func)` 中。
   * 严格声明驼峰命名的 `inputSchema` JSON Schema。
   * 在 `mcps/__init__.py` 导入该文件。
   
2. **导入一个流程工作流 (SOP)**：
   * 在 `skills/` 创建 `workflow_skill.py`。
   * 配置标准的 `SKILL_CONFIG` 及 `steps` 管道，在变量插值中利用 `{{input.query}}` 和 `{{steps.step_name.output.field}}` 打通传参。
   * 在 `skills/__init__.py` 导入该文件。
