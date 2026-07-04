# 广汽集团 AI 一体化平台原型

一个基于统一 AI 门户、Skill 编排和 MCP 原子能力底座的集团 AI 一体化平台原型。当前开发基线优先保证四件事：

- 可以在无 API Key、无数据库的环境中使用 mock 模式完整演示。
- 前端信息架构覆盖 AI 助手、能力中心、平台治理三类工作区。
- 后端提供能力、组织权限、Skill/MCP 治理和运营指标的第一阶段 mock API。
- 真实凭据不写入源码，统一通过 `.env` 读取。
- 关键 MCP 失败时 workflow 立即中断，并返回清晰错误。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Mock 演示

mock 模式是默认模式，不需要 API Key 或数据库。

```powershell
$env:APP_MODE = "mock"
streamlit run streamlit_langgraph.py
```

Web 入口可通过 FastAPI + Vite 启动：

```powershell
$env:APP_MODE = "mock"
uvicorn api_server:app --host 127.0.0.1 --port 8001 --reload
```

```powershell
cd web_frontend
npm install
npm run dev
```

启动后可尝试：

- 本月中东公司销量多少？
- 本月终端量同比去年怎么样？
- 汽车保养一般多少公里做一次？

平台治理 mock API 可直接验证：

```powershell
curl http://127.0.0.1:8001/api/capabilities/data_query
curl http://127.0.0.1:8001/api/organizations/gac-international/permissions
curl http://127.0.0.1:8001/api/admin/metrics/overview
```

## Real 模式

复制 `.env.example` 为 `.env`，补齐模型和数据库配置：

```powershell
Copy-Item .env.example .env
```

关键配置：

```ini
APP_MODE=real
DEEPSEEK_API_KEY=
MODEL_BASE_URL=https://api.deepseek.com/chat/completions
MODEL_NAME=deepseek-chat
DB_HOST=
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=
DB_ALLOWED_TABLES=v_dm_sal_wolesale_terminal_dly,v_dm_sal_stock_dly,v_dm_sal_sc_order_dly,v_dm_sal_scheduling_dly
SQL_MAX_ROWS=500
DB_CONNECT_TIMEOUT=5
DB_READ_TIMEOUT=30
DB_WRITE_TIMEOUT=30
```

然后启动：

```powershell
streamlit run streamlit_langgraph.py
```

## 命令行验证

```powershell
$env:APP_MODE = "mock"
python -c "from langgraph_cot import run_agent; import json; print(json.dumps(run_agent('本月中东公司销量多少？'), ensure_ascii=False, default=str))"
```

## MCP 健康检查

一键检查所有 MCP 的 mock 可调用性，以及 real 模式缺配置时关键 MCP 是否能清晰失败：

```powershell
python scripts/check_mcps.py
```

只跑 mock：

```powershell
python scripts/check_mcps.py --mode mock
```

只跑 real 缺配置检查：

```powershell
python scripts/check_mcps.py --mode real-missing-config
```

真实 MCP 测试需要先配置 `.env`，然后手动运行：

```powershell
python scripts/check_mcps.py --mode real
```

如果缺少 API Key 或数据库配置，脚本会列出缺失项，不会发起真实外部调用。

## 自动化测试

```powershell
pytest -q
```

当前测试覆盖：

- 平台能力、组织权限、Skill/MCP 治理和运营指标 mock API
- MCP 标准返回契约
- mock 模式三条端到端链路
- real 模式缺配置时的 workflow 中断
- SQL 危险语句和非 SELECT 拦截

## 项目结构

- `langgraph_cot.py`: Skill 路由与 SOP workflow 执行器。
- `api_server.py`: 统一 AI 门户与平台治理原型使用的 FastAPI API 与 SSE 入口。
- `chat_repository.py`: SQLite 会话、消息、思考步骤持久化。
- `web_frontend/`: React 平台前端工程，包含 AI 助手、能力中心和平台治理工作区。
- `app_config.py`: 统一配置读取入口。
- `scripts/check_mcps.py`: MCP 健康检查脚本。
- `skills/`: 业务 SOP 层。
- `mcps/`: 原子工具层。
- `streamlit_langgraph.py`: 可视化调试界面。
- `doc/后续开发计划_codex_20260522.md`: 后续开发排期与跟踪文档。
