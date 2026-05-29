# Real 模式对接与 SSH 隧道数据库连接实现报告

为了配合您填入的真实 DeepSeek API Key 以及 StarRocks 数据库的 SSH 堡垒机通道，系统已成功完成了底层网络与连接协议的重构。目前，**所有 6 个核心 MCP 工具在 Real 模式下的真实连接测试已全部成功通过。**

---

## 1. 变更清单与技术实现

### 1.1 智能解析 `.env` 中的非标准 SSH 配置
在 [app_config.py](file:///d:/%E5%B7%A5%E4%BD%9C/%E5%A4%A7%E6%A8%A1%E5%9E%8B%E5%BA%94%E7%94%A8%E5%AD%A6%E4%B9%A0/Cot_research/app_config.py) 中，系统实现了一个极其强壮的混合解析器，支持同时解析标准环境变量和您在 `.env` 中添加的中文非标准 SSH 凭据：
* **目标文本格式**：
  ```
  本地连SR的ssh配置
  10.30.8.37：9081
  账号：model
  密码：^Dskj@Model1
  ```
* **实现逻辑**：利用正则表达式对 `.env` 进行全文扫描，提取 IP 和端口（支持中文冒号 `：` 与英文冒号 `:`），并提取“账号”和“密码”字样后的有效字符，封装为 `SSHConfig`。同时，依然保持对标准 `SSH_HOST`、`SSH_PORT`、`SSH_USER`、`SSH_PASSWORD` 环境变量的兼容。

### 1.2 编程式动态数据库 SSH 隧道
在 [sql_executor_mcp.py](file:///d:/%E5%B7%A5%E4%BD%9C/%E5%A4%A7%E6%A8%A1%E5%9E%8B%E5%BA%94%E7%94%A8%E5%AD%A6%E4%B9%A0/Cot_research/mcps/sql_executor_mcp.py) 中，为避免用户手动维护外部 SSH 隧道的繁琐步骤，我们将隧道建立完全自动化、编程式集成：
* 每次调用 `sql_executor` 查询数据库时，如果检测到 `config.ssh.enabled` 为真，则使用 `sshtunnel.SSHTunnelForwarder` 动态建立一个从本地随机空闲端口映射到目标数据库 `10.30.16.21:6033` 的安全 SSH 通道。
* 数据库驱动（`pymysql`）随后通过 `127.0.0.1:{local_port}` 进行超高速连接，数据读取完毕后，在 `finally` 块中**严格断开数据库连接并安全停用 SSH 隧道**，避免连接挂起和端口冲突。

### 1.3 LLM 模型名称动态解析与修正
在测试中我们发现，`llm_mcp.py` 的默认 `model` 参数为 `"DeepSeek-V3.1"`。由于官方 DeepSeek 接口不支持此占位名称（报错 400 Bad Request），我们对 [llm_mcp.py](file:///d:/%E5%B7%A5%E4%BD%9C/%E5%A4%A7%E6%A8%A1%E5%9E%8B%E5%BA%94%E7%94%A8%E5%AD%A6%E4%B9%A0/Cot_research/mcps/llm_mcp.py) 的模型解析机制进行了修正：
* 动态判断 `model` 入参，若属于默认值 `"DeepSeek-V3.1"` 或是空值，则自动退化为读取环境变量中配置的实际模型（默认 `deepseek-chat`）。这使得 DeepSeek 官方 API 调用完全畅通。

---

## 2. 验证与测试结果

### 2.1 自动化测试通过 (pytest)
我们在本地运行了自动化测试套件，**14 个用例全部以 100% 成功率通过：**
```powershell
pytest
# ============================= 14 passed in 0.34s ==============================
```

### 2.2 核心 MCP Real 模式健康检查 (100% PASS)
我们通过 `python scripts/check_mcps.py --mode real` 进行了真实接口联调，在加载您的真实 Key 以及数据库 SSH 隧道后，**6 大工具全部连通：**
```powershell
python scripts/check_mcps.py --mode real

MCP health check: real
------------------------------------------------------------------------
MCP                      STATUS   DETAILS
------------------------------------------------------------------------
llm                      OK       ok
n2sql                    OK       ok
sql_executor             OK       ok
knowledge_retrieval      OK       ok
time                     OK       ok
text_analysis            OK       ok

Result: PASS
```

这代表着我们的**大语言模型接口调用**、**自然语言转 SQL (N2SQL) 生成**、以及**通过安全 SSH 隧道连接并成功查询 StarRocks 真实数据库**的全套底层数据通路完全打通！

---

## 3. Dify 知识库深度集成与 `.env` 占位符设计

根据您在 `doc/DIFY_知识库_API集成文档.md` 中指明的 Dify 数据库及 "国际问答对-V3" 高质量 SQL 问答对知识库（Dataset ID: `ffa84ba6-4ec9-44a0-8f6d-594b27f7a829`），系统已完成以下优化：

1. **`.env` 与 `.env.example` 占位符规范**
   - **`.env.example` 全量更新**：新增了 SSH 堡垒机参数与 Dify 知识库检索 API 全量占位字段，方便任何人在初始化项目时一目了然需要填写哪些信息。
   - **`.env` 结构整理**：增加了详细的配置注释，并留出了清晰的自定义 Dify 知识库检索 API 备用空位（如 `DIFY_API_KEY_CUSTOM` 等），同时默认直接挂载您文档中指定的 **SQL 问答对知识库 (国际问答对-V3)**。

2. **Dify 知识库 API 检索验证**
   - 编写并运行了测试脚本 `scratch/test_dify.py`，模拟真实业务查询。
   - **实测结果**：检索服务通过安全 SSH 隧道建立与 Dify 私有局域网主机 `10.30.11.215:9879` 的通信，极速拉取并成功召回了匹配的 SQL 问答对片段。
   - 在 `check_mcps.py --mode real` 验证中，`knowledge_retrieval` 模块完美运行。这表明无论表结构推理、同环比口径，还是特定的复杂业务 SQL，都将享受到 Dify 高质量问答对检索的有力加持。

