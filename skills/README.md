# Skills 文件夹

## 概述

Skill 是业务能力单元，封装一个完整的业务流程。每个 Skill 包含：
- **名称和描述**: 标识 Skill 用途
- **MCP 工具列表**: Skill 调用的底层工具
- **流程定义**: Skill 的执行步骤
- **示例**: 展示 Skill 适用的场景

## 现有 Skills

### 1. data_query_skill.py - 数据查询 Skill
完整的数据分析流程：
```
意图识别 → 知识检索 → N2SQL → SQL生成 → SQL执行 → 数据解读 → 数据口径
```

### 2. chat_skill.py - 闲聊 Skill
处理非数据相关的日常对话

### 3. yoy_yoy_analysis_skill.py - 同环比分析 Skill
专门处理同比、环比相关的查询

## 添加新的 Skill

创建一个新的 Skill 文件，参考 `data_query_skill.py` 的结构：

```python
from skills import register_skill

SKILL_CONFIG = {
    "name": "your_skill_name",          # 唯一标识
    "description": "Skill 描述",         # 说明用途
    "category": "分类",                   # 业务分类
    "mcp_tools": ["mcp1", "mcp2"],     # 使用的 MCP 工具
    "output_type": "输出类型",
    "examples": [                        # 示例问题
        "示例1",
        "示例2"
    ],
    "flow": {
        "steps": [
            {
                "step": 1,
                "name": "step_name",
                "description": "步骤描述",
                "mcp": "mcp_name"
            }
        ]
    }
}

register_skill(SKILL_CONFIG)
```

## Skill 配置说明

| 字段 | 必填 | 说明 |
|------|------|------|
| name | 是 | Skill 唯一标识 |
| description | 是 | Skill 功能描述 |
| category | 否 | 业务分类 |
| mcp_tools | 是 | 使用的 MCP 工具名称列表 |
| output_type | 否 | 输出类型（表格/文本/数值等）|
| examples | 否 | 示例问题列表 |
| flow | 否 | 执行流程定义 |
