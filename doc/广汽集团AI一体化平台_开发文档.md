# 广汽集团 AI 一体化平台开发文档

> 文档类型：详细开发文档  
> 文档状态：V2.0  
> 更新时间：2026-07-04  
> 对应产品文档：`doc/广汽集团AI一体化平台_PRD.md`

## 1. 文档目的

本文档用于记录当前仓库中“广汽集团 AI 一体化平台”原型的真实开发状态，并把后续开发拆成可持续勾选的待办项。

这份文档有两个用途：

- 作为当前实现的技术基线说明
- 作为后续持续开发的执行清单，做完一项就直接打勾

## 2. 当前技术基线

### 2.1 后端

- `api_server.py`：FastAPI 接口、SSE 流式输出、mock 管理端 API
- `chat_repository.py`：会话与消息持久化
- `permission_repository.py`：权限、组织、角色相关数据访问
- `registry_repository.py`：Skill / MCP / 任务注册与管理数据访问
- `skills/`：Skill 实现
- `mcps/`：MCP 实现

### 2.2 前端

- 技术栈：React 18 + TypeScript + Vite
- 入口：`web_frontend/src/App.tsx`
- 路由：`web_frontend/src/useWorkspaceRoute.ts`
- 壳层：`web_frontend/src/components/AppShell.tsx`
- 管理端原型数据：`web_frontend/src/managementData.ts`
- 公共管理组件：`web_frontend/src/components/ManagementUi.tsx`

## 3. 当前已落地的信息架构

### 3.1 一级导航

- `AI 助手`
- `能力中心`
- `平台治理`

### 3.2 平台治理当前一级入口

- `/admin`：工作台
- `/admin/assets`：统一目录
- `/admin/pipeline`：发布流水线
- `/admin/operations-center`：运行与权限

### 3.3 兼容保留路由

以下旧路由仍保留，用于兼容原型和测试：

- `/admin/permissions`
- `/admin/reviews`
- `/admin/operations`
- `/admin/releases`
- `/admin/skills`
- `/admin/mcps`

## 4. 当前已完成实现

### 4.1 已完成功能

- [x] 全局导航完成平台化命名，替换原始“系统管理 / Skill 商店”语义
- [x] 管理端一级入口重构为 `工作台 / 统一目录 / 发布流水线 / 运行与权限`
- [x] `Skill` 与 `MCP` 统一抽象为能力资产模型
- [x] 新增统一目录页，支持按类型、阶段、关键词筛选能力资产
- [x] 管理端工作台改造成“我的待处理事项”入口
- [x] 发布页降级为跨对象总览，不再承担主操作
- [x] 权限页降级为发布前治理配置辅助区
- [x] Skill 详情页完成单页推进骨架：测试 → 提审 → 发布
- [x] MCP 详情页完成单页推进骨架：测试 → 提审 → 发布
- [x] Skill / MCP 详情页共享 `LifecycleOverviewPanel` 公共阶段骨架组件
- [x] 统一目录按待处理优先级排序，优先展示阻塞、测试中、待提审对象
- [x] 工作台“继续处理”已改为解析真实对象，不再直接拼接裸任务标识
- [x] mock 数据已补齐关键待处理对象：`海外政策追踪`、`渠道库存诊断`、`库存快照 MCP`
- [x] 前端契约测试已覆盖统一目录、单详情页流程、阶段骨架组件
- [x] 前端生产构建通过

### 4.2 当前核心代码位置

- 工作台：`web_frontend/src/pages/AdminWorkbenchPage.tsx`
- 统一目录：`web_frontend/src/pages/AssetDirectoryPage.tsx`
- 发布流水线：`web_frontend/src/pages/AdminReleasePage.tsx`
- 运行与权限：`web_frontend/src/pages/AdminReviewPage.tsx`
- Skill 详情：`web_frontend/src/pages/SkillDetailPage.tsx`
- MCP 详情：`web_frontend/src/pages/McpDetailPage.tsx`
- 公共阶段骨架：`web_frontend/src/components/ManagementUi.tsx`
- 统一资产模型与 mock 数据：`web_frontend/src/managementData.ts`

## 5. 当前仍存在的已知问题

- 管理端已接入统一资产 API，但当前后端仍以 mock / 原型数据为主，不是真实业务生产数据
- 工作台、统一目录与详情页已复用统一生命周期状态工具，但仍基于原型级任务/资产映射
- 发布流水线和运行与权限仍保留较多旧原型字段与旧运营视角
- 前端打包仍有 `echarts` vendor chunk 过大的告警
- 浏览器演示依赖 mock API 启动；仅跑前端 preview 时管理页无法完成真实登录

## 6. 后续开发待办清单

下面清单按“推荐开发顺序”组织。后续开发时以这里为准，完成一项就打勾。

### 6.1 P0：统一状态与数据入口

- [x] 统一目录与单详情页主流程重构
- [x] 工作台使用真实对象解析跳转，而不是裸任务名拼路由
- [x] 将 Skill/MCP 详情页的阶段逻辑抽到统一状态工具
  - 目标文件：`web_frontend/src/managementData.ts` 或新增 `web_frontend/src/adminLifecycle.ts`
  - 需要统一：
    - `ReleaseStatus -> LifecycleStage` 映射
    - 当前阶段动作文案
    - 风险摘要与阶段焦点配置
- [x] 将工作台、统一目录、详情页全部改为复用同一套生命周期状态工具
- [x] 接入真实统一资产 API
  - 后端新增统一资产接口
  - 前端减少 `buildUnifiedAssets(...)` 的前端推导比例
- [x] 为统一资产增加稳定字段
  - `asset_id`
  - `asset_type`
  - `current_stage`
  - `risk_level`
  - `owner`
  - `dependency_status`
  - `action_url`

### 6.2 P0：管理端真实可用性

- [x] 启动前端 preview 时自动提示 mock API 依赖
- [x] 在登录页增加环境状态提示
  - mock API 是否可用
  - 当前是否为 mock 演示模式
- [x] 为登录失败增加更清晰的错误分类
  - 账号密码错误
  - 后端不可用
  - 权限不足
- [x] 将“平台管理员 / 销售员工 / AI 开发者”演示账号逻辑与后端 mock 数据一一对齐
- [x] 增加管理端页面基础 smoke test
  - 登录
  - 打开工作台
  - 打开统一目录
  - 打开 Skill 详情
  - 打开 MCP 详情

### 6.3 P1：统一目录完善

- [x] 为统一目录补充更多筛选器
  - 风险等级
  - 负责人
  - 是否被依赖
  - 是否待处理
- [x] 给统一目录补充分组视图
  - 按阶段分组
  - 按类型分组
  - 按风险分组
- [x] 为统一目录增加“仅看我的待处理”开关
- [x] 为统一目录增加“最近失败原因”高亮样式优化
- [x] 为统一目录增加空状态与无结果状态
- [x] 为统一目录补充分页或虚拟列表能力，避免未来数据量大时卡顿

### 6.4 P1：工作台完善

- [x] 将工作台的任务面板与统一资产状态彻底对齐
- [x] 移除工作台中仍偏“平台概览”的统计项
- [x] 增加“最近我操作过的对象”区块
- [x] 增加“审核退回待补充”专门分组
- [x] 增加“依赖解锁后恢复测试”的可视反馈
- [x] 工作台时间线改为可跳转至对象详情而不只是选中抽屉

### 6.5 P1：Skill / MCP 详情页深化

- [x] Skill/MCP 详情页的阶段骨架组件共用
- [x] 把 Skill/MCP 详情页的摘要卡、阶段焦点卡再继续组件化
- [x] 统一 Skill 与 MCP 页面的“当前阶段主操作”交互密度
- [x] 将详情页中的测试区与最近记录区拆成可复用子组件
- [x] 为 Skill 详情页增加真实的“提审资料完整性检查” mock
- [x] 为 MCP 详情页增加真实的“Schema 变更差异” mock
- [x] 让详情页中的“发布前治理配置”跳转到运行与权限页的对应位置
- [x] 为阻塞态详情页提供专门的解除阻塞引导

### 6.6 P1：发布流水线与运行与权限收尾

- [x] 将发布流水线中的卡片点击统一跳回对象详情主操作
- [x] 将发布流水线中的数据模型切换到统一资产视角
- [x] 保留跨对象总览，但减少旧运营型表述
- [x] 将运行与权限页拆成更清晰的四个视图
  - 组织树
  - 角色模板
  - 账号覆盖
  - 审计中心
- [x] 为运行与权限页补充从对象详情反向进入的上下文信息
  - 当前对象
  - 风险等级
  - 推荐配置动作

### 6.7 P2：前后端接口收敛

- [x] 后端补统一资产查询接口
- [x] 后端补统一任务查询接口
- [x] 后端补对象详情接口
  - [x] Skill 详情
  - [x] MCP 详情
  - 未来可合并为统一详情接口
- [x] 后端补测试、提审、发布动作接口
- [ ] 将前端 `hydratePlatformPrototypeData()` 迁移为真实接口驱动
- [ ] 将前端 mock 创建 Skill / MCP 的逻辑改为后端真实返回统一对象结构

### 6.8 P2：测试与质量

- [x] 前端契约测试覆盖新 IA 与统一目录
- [x] 为统一生命周期工具补单元测试
- [x] 为工作台路由解析补单元测试
- [x] 为统一目录排序补单元测试
- [x] 增加后端 mock API 的统一资产接口测试
- [ ] 增加浏览器级回归测试
- [x] 将构建告警与 chunk 体积纳入定期检查项

### 6.9 P2：性能与工程化

- [x] 拆分 `echarts` 相关大包，降低首屏 chunk
- [ ] 进一步梳理 `App.tsx`，减少管理端路由装配复杂度
- [ ] 将管理端页面配置抽成独立模块，减少 `App.tsx` 条件分支
- [ ] 清理旧原型残留命名
  - 例如旧的 `平台总览 / 平台运营 / Skill 编排 / MCP 治理` 文案兼容注释
- [ ] 为管理端增加更稳定的类型定义文件，减少页面内联类型推导

## 7. 推荐后续开发顺序

建议按以下顺序推进，而不是并行散改：

1. 统一生命周期状态工具
2. 统一资产真实 API
3. 工作台 / 统一目录 / 详情页全面切到真实统一资产数据
4. 发布流水线与运行与权限页收尾
5. 前端构建与包体积优化
6. 浏览器级自动化回归

## 8. 每次继续开发前的最小检查

后续继续开发前，先完成以下检查：

- [ ] `git status` 确认本次要修改的文件范围
- [ ] 明确本次只推进文档清单中的一个或一组相关事项
- [ ] 先补或更新对应测试
- [ ] 开发完成后执行：
  - [ ] `pytest tests/test_web_frontend_contract.py`
  - [ ] `node ./node_modules/typescript/bin/tsc -b`
  - [ ] `node ./node_modules/vite/bin/vite.js build`
- [ ] 若改动管理端交互，至少再做一次浏览器手工核验

## 9. 本次状态结论

当前仓库已经从“旧多入口治理原型”切换到“能力开发者优先”的主流程原型，但还没有完成真实统一资产接口、统一生命周期工具和浏览器自动化回归。

本轮已补充的最小可用性改进：

- [x] 登录页显示后端环境状态与 mock 依赖提示
- [x] 登录失败区分为账号密码错误 / 后端不可用 / 权限不足
- [x] 新增 `/api/admin/tasks` 统一任务查询接口，返回资产对齐字段与详情跳转地址
- [x] 新增 `/api/admin/assets/{asset_id}` 对象详情接口，统一返回资产、详情、关联任务与活动记录
- [x] 新增 `/api/admin/assets/{asset_id}/test|submit|publish` 统一资产动作接口
- [x] 新增 `web_frontend` 生命周期工具单元测试，覆盖阶段映射、任务归属、指标与排序
- [x] 将工作台任务/活动路由解析抽成可测工具，并补单元测试
- [x] 为统一目录排序补充自定义输入单元测试，覆盖阶段、类型与中文名称排序
- [x] 将 ECharts 改为本地 runtime 懒加载与按需模块注册，构建最大 JS chunk 降至 500 kB 以下
- [x] 新增 `web_frontend` bundle 体积检查脚本，定期拦截超过 500 kB 的 JS chunk
- [x] 演示账号列表与后端 mock 数据对齐
- [x] 增加管理端基础 smoke test

本轮验证命令：

- [x] `python3 -m pytest tests/test_api_server.py tests/test_web_frontend_contract.py tests/test_admin_smoke.py -q`
- [x] `cd web_frontend && node ./node_modules/typescript/bin/tsc src/managementData.ts --target ES2022 --module ES2022 --moduleResolution Bundler --outDir .tmp/management-data-test --skipLibCheck && node --test tests/managementData.test.mjs`
- [x] `cd web_frontend && node scripts/checkBundleSize.mjs`
- [x] `cd web_frontend && node ./node_modules/typescript/bin/tsc -b`
- [x] `cd web_frontend && node ./node_modules/vite/bin/vite.js build`

因此，当前阶段应视为：

- 信息架构已完成第一阶段重构
- 原型演示已可用
- 工程化和真实数据接入仍在待完成清单内
