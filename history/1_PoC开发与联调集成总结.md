# ChatBI 双层决策系统 PoC 全流程开发与集成总结

本项目是一个基于 **Skill (声明式业务 SOP) + MCP (原子工具协议)** 双层架构的 ChatBI 概念验证系统（PoC）。它使用 LangGraph 作为核心双层引擎，实现了“意图选择（Skill 路由） -> 顺序管道执行（SOP 驱动） -> 原子工具（MCP 契约）”的高内聚解耦设计。

本报告对整个 PoC 系统开发、网络联调、SIT 测试及配置外置化工作进行了全面、事实性的复盘总结。

---

## 1. 核心工作与技术突破总结

### 1.1 堡垒机 SSH 隧道自动建立与安全生命周期管理
* **物理挑战**：StarRocks 分析库（`10.30.16.21:6033`）以及 Dify 知识库检索服务（`10.30.11.215:9879`）均位于专有局域网私有网段内，外部必须通过堡垒机（`10.30.8.37:9081`）进行代理中转。
* **技术实现**：
  - 在 [`sql_executor_mcp.py`](file:///d:/工作/大模型应用学习/Cot_research/mcps/sql_executor_mcp.py) 与 [`knowledge_retrieval_mcp.py`](file:///d:/工作/大模型应用学习/Cot_research/mcps/knowledge_retrieval_mcp.py) 中，系统集成了 `SSHTunnelForwarder`。
  - **自动路由与解耦**：当检测到 `config.ssh.enabled` 为真时，系统会自动在本地随机空闲端口上建立一个到目标堡垒机的 SSH 安全隧道，使客户端能够直接通过 `127.0.0.1:{local_port}` 与私网主机通信。
  - **严密生命周期护栏**：使用了 `finally` 块，确保不论数据库执行是成功还是抛出异常，**连接句柄与 SSH 隧道端口都会被 100% 安全关闭**，完全杜绝了端口悬挂与数据库连接溢出的隐患。

### 1.2 外部 Dify 知识检索的深度整合
* **检索对接**：在 [`knowledge_retrieval_mcp.py`](file:///d:/工作/大模型应用学习/Cot_research/mcps/knowledge_retrieval_mcp.py) 中，根据您提供的 `doc/DIFY_知识库_API集成文档.md`，深度集成了 Dify retrieve 检索 API。
* **业务逻辑对接**：
  - 检索载入时默认直接指向 **“SQL 问答对知识库（国际问答对-V3）”**（Dataset ID: `ffa84ba6-4ec9-44a0-8f6d-594b27f7a829`）。
  - 设置检索策略为混合检索（`hybrid_search`）并激活 SiliconFlow 支持的外接 **Rerank 大模型重排机制**（模型：`bce-reranker-base_v1`），确保检索相似度的绝对精准。
  - **高可用降级机制**：若 Dify 局域网服务响应超时或出现网络抖动，系统会自动、平滑地降级为本地规则的关键词内存过滤，保障整体 ChatBI 对话流程不断裂。

### 1.3 LLM 默认模型占位名称自适应解析与修正
* **接口保护**：在 [`llm_mcp.py`](file:///d:/工作/大模型应用学习/Cot_research/mcps/llm_mcp.py) 中，针对默认 `model` 参数为 `"DeepSeek-V3.1"` 会导致官方 API 报错 400 Bad Request 的问题，设计了智能退化策略。
* **技术实现**：如果检测到调用模型为空或为默认占位符，会自动提取配置中的 `deepseek-chat` 或环境变量中所定义的真实模型，使得官方 DeepSeek API 的调用全链路畅通。

### 1.4 对齐用户意图的最终答案结构化编译
* **原痛点**：在多步 SOP 执行中，SOP 步骤 6（数据口径说明）的输出常有覆盖步骤 5（数据深度分析）的问题，且输出排版无序。
* **技术实现**：
  - 在 [`langgraph_cot.py`](file:///d:/工作/大模型应用学习/Cot_research/langgraph_cot.py) 的 `step2_run_workflow` 节点中，为 `data_query` 和 `yoy_yoy_analysis` 两个业务 Skill 编写了专用的答案结构化编译器。
  - 强力编排输出格式，保证最终呈现给用户的业务回复完全对齐期望：
    1. **📊 数据查询结果**（Markdown 表格，置于首位提供最直观结果）
    2. **💡 业务分析与解读**（DeepSeek 大模型基于真实数据的商业分析）
    3. **🛡️ 数据统计口径说明**（以 Blockquote 块引用作为注脚，整洁优雅）

### 1.5 stream_langgraph 前端图表自动绘制
* **无侵入可视化**：在 [`streamlit_langgraph.py`](file:///d:/工作/大模型应用学习/Cot_research/streamlit_langgraph.py) 中，设计了无侵入的 Markdown 表格提取与数据可视化组件 `render_markdown_table_chart`。
* **技术实现**：系统会自动扫描最终文本输出及中间步骤数据，当识别到含有 `|` 组成的 Markdown 数据表时，自动使用 `Pandas` 对其进行表格行切分，并将数据自适应转换为浮点数，在 Streamlit 页面上渲染出极其美观、可交互的柱状图（`st.bar_chart`），真正实现一键 ChatBI 的可视化展示。

---

## 2. 交付文件拓扑结构与位置说明

按照您的指示，所有回顾、设计与集成总结报告，以及系统集成测试（SIT）报告均已安全归档至项目的物理目录中，具体文件位置如下：

### 2.1 `history/` 目录（全流程开发总结与架构设计）
* **[history/work_summary.md](file:///d:/工作/大模型应用学习/Cot_research/history/work_summary.md)**:
  - *当前文件*。汇总记录 PoC 阶段在堡垒机隧道连接、Dify 检索集成、LLM 校验、数据对齐排版及自动图表绘制方面的核心突破。
* **[history/project_review_and_roadmap.md](file:///d:/工作/大模型应用学习/Cot_research/history/project_review_and_roadmap.md)**:
  - *项目回顾与路线图*。全面梳理 Skill + MCP 的双层解耦架构设计，分析已实现的 M1~M4 五大基线里程碑，并为未来的 SQL 自动纠错与 YAML 描述文件外置化划定技术路径。
* **[history/walkthrough.md](file:///d:/工作/大模型应用学习/Cot_research/history/walkthrough.md)**:
  - *开发演练报告*。详细记录 app_config.py 强壮解析、数据库/Dify 隧道管理及模型解析代码级的微观演练细节。

### 2.2 `qa/` 目录（系统集成测试 SIT 报告）
* **[qa/sit_report.md](file:///d:/工作/大模型应用学习/Cot_research/qa/sit_report.md)**:
  - *系统集成测试报告*。记录在 **`real` 真实模式** 下，通过 SSH 通道，使用真实 DeepSeek 秘钥与真实 StarRocks 数据库联调通过的 3 大测试用例执行轨迹：
    - **TC-01** (销量查询，成功获取 2023 年 6 月中东公司批发量 2160、终端量 2311，并给出了优秀的商业分析和口径对齐)
    - **TC-02** (同环比计算，成功处理了分母为零的边缘场景，展现出优异的数据防御能力)
    - **TC-03** (对话闲聊，提供了详实的车辆保养指南)
  - 报告中完整包含了三层架构 CoT（意图路由 -> SOP 管道执行 -> 工具执行明细）的详细痕迹。

---

## 3. 后续展望

系统目前已具备优异的生产环境级连通性。后续可在当前基线之上，平滑地开展以下迭代：
1. **自动纠错环路（SQL Auto-Correction）**：当 StarRocks 执行发生语法错误时，捕获异常并反馈给 LLM，重试 1-2 次，增强系统鲁棒性。
2. **元数据外置（Metadata Externalization）**：将表结构及字段中英文定义迁移至统一的 `config/metadata.yml` 文件中，免除代码修改。
