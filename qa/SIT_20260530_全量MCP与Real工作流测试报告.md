# SIT 测试报告：全量 MCP 与 Real 工作流

## 1. 基本信息

| 项目 | 内容 |
|---|---|
| 测试日期 | 2026-05-30 |
| 测试对象 | Cot Research ChatBI PoC |
| 测试范围 | 自动化测试、MCP 健康检查、real MCP 调用、real 端到端 workflow、Streamlit 启动烟测 |
| 测试环境 | macOS 本地环境，Python 3.9.6 |
| 敏感信息策略 | 不在报告中记录 API Key、密码、SSH 密码 |

## 2. 测试结论

| 结论项 | 状态 | 说明 |
|---|---|---|
| 自动化测试 | PASS | `21 passed, 1 warning` |
| MCP mock 健康检查 | PASS | 7 个 MCP 均 OK |
| MCP real-missing-config 优雅失败 | PASS | 关键外部 MCP 均返回 `ConfigurationError` |
| MCP real 健康检查 | PASS | LLM、N2SQL、SQL、知识检索、Tavily、时间、文本分析均 OK |
| Real 数据查询 workflow | PASS | 完整生成表格、分析和口径说明 |
| Real 同环比 workflow | PASS_WITH_DATA_ISSUE | 流程成功，但业务数据为空值 |
| Real 闲聊 workflow | PASS | 模型回答成功 |
| Streamlit 启动烟测 | PASS | HTTP 200 |

整体结论：系统已具备进入 UAT 的技术条件，但需要在 UAT 前补充 Dify 远程知识库真实配置，并确认同环比数据口径。

## 3. 测试命令与结果

### 3.1 自动化测试

```bash
python3 -m pytest -q
```

结果：

```text
21 passed, 1 warning in 0.12s
```

### 3.2 MCP mock 与缺配置测试

```bash
python3 scripts/check_mcps.py
```

结果：

```text
MCP health check: mock
llm                 OK
n2sql               OK
sql_executor        OK
knowledge_retrieval OK
web_search          OK
time                OK
text_analysis       OK

MCP health check: real-missing-config
llm                 OK graceful failure: ConfigurationError
n2sql               OK graceful failure: ConfigurationError
sql_executor        OK graceful failure: ConfigurationError
web_search          OK graceful failure: ConfigurationError

Result: PASS
```

### 3.3 MCP real 测试

```bash
python3 scripts/check_mcps.py --mode real
```

结果：

```text
MCP health check: real
llm                 OK
n2sql               OK
sql_executor        OK
knowledge_retrieval OK
web_search          OK
time                OK
text_analysis       OK

Result: PASS
```

## 4. Real Workflow 用例

### TC-E2E-01 数据查询

| 字段 | 内容 |
|---|---|
| 输入 | `2023年6月中东公司的销量（包括批发量和终端量）是多少？` |
| 路由 Skill | `data_query` |
| 执行节点 | intent_recognition → knowledge_retrieval → n2sql_generation → sql_execution → data_interpretation → data_scope_explanation |
| 结果 | PASS |

输出摘要：

```text
批发量：2160
终端量：2311
最终回答包含数据表格、业务分析与统计口径说明。
```

### TC-E2E-02 同环比分析

| 字段 | 内容 |
|---|---|
| 输入 | `本月终端量同比去年怎么样？` |
| 路由 Skill | `yoy_yoy_analysis` |
| 执行节点 | yoy_knowledge_retrieval → yoy_n2sql → sql_execution → yoy_analysis |
| 结果 | PASS_WITH_DATA_ISSUE |

输出摘要：

```text
本月终端量：None
去年同期终端量：None
同比变化率：None
```

说明：技术链路成功，业务数据为空。该项不是程序崩溃，但需要 UAT 阶段确认“本月”解释、表数据覆盖范围和同比 SQL 口径。

### TC-E2E-03 闲聊

| 字段 | 内容 |
|---|---|
| 输入 | `汽车保养一般多少公里做一次？` |
| 路由 Skill | `chat` |
| 执行节点 | chat_response |
| 结果 | PASS |

输出摘要：模型正常返回汽车保养周期建议。

## 5. Streamlit 启动烟测

启动命令：

```bash
python3 -m streamlit run streamlit_langgraph.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

探针结果：

```text
GET http://localhost:8501
HTTP 200
```

结论：前端服务可启动，可进入 UAT 页面验收。

## 6. 发现的问题

| 编号 | 问题 | 严重度 | 状态 | 处理建议 |
|---|---|---|---|---|
| SIT-01 | Dify 远程知识库未真实验证，当前 `DIFY_BASE_URL` 仍为占位 host 且 `DIFY_ENABLED=false` | P1 | OPEN | 填入真实 Dify host，开启后补测 `knowledge_retrieval` |
| SIT-02 | 同环比 workflow 结果为空值 | P1 | OPEN | 明确测试月份和业务口径，补固定日期同环比用例 |
| SIT-03 | 前端视觉体验不佳 | P1 | OPEN | 下一阶段进行前端样式重构 |
| SIT-04 | Python/urllib3 LibreSSL warning | P3 | OPEN | 可在后续独立虚拟环境中处理 |

## 7. 修复记录

| 修复项 | 说明 |
|---|---|
| SSH 隧道启用 | `.env` 中打开 `SSH_ENABLED=true`，DB real 查询通过 |
| Tavily MCP 启用 | `.env` 中打开 `WEB_MCP_ENABLED=true`，Tavily real 查询通过 |
| `sshtunnel` 依赖 | 安装 `sshtunnel>=0.4.0` |
| Paramiko 兼容 | `requirements.txt` 固化 `paramiko<4` |
| httpx 代理参数兼容 | `web_search_mcp.py` 调整为无代理时不传 proxy 参数，有代理时用 `httpx.Client(proxy=...)` |

## 8. UAT 准入建议

建议进入 UAT，但带两个前置提醒：

1. Dify 远程知识库需要补真实 host 后复测。
2. 同环比 UAT 用例应使用明确年月，避免“本月”在数据表无覆盖时返回空值。
