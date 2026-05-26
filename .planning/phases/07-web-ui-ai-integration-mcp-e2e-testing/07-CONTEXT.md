# Phase 7: Web UI, AI Integration & MCP E2E Testing - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

在已有 CLI + MCP Server（31 个工具）之上，构建三个独立交付物：

1. **FastAPI REST API** — 将 31 个 MCP 工具对应暴露为 HTTP endpoint，前端通过 REST 调用
2. **React Web UI** — 单面板聊天式界面，内嵌 ArcGIS 地图，AI 驱动的 GIS 操作体验
3. **MCP E2E 测试** — pytest 自动化测试 + Claude Code 手动集成测试清单

前端与 CLI/MCP 解耦，独立部署。MCP 保持 stdio 模式不变（供 Claude Code 使用），前端仅通过 REST 调用。
</domain>

<decisions>
## Implementation Decisions

### REST API 设计
- **D-01:** 框架 = FastAPI，利用自动 OpenAPI/Swagger 文档和 Pydantic 集成
- **D-02:** 监听策略 = localhost only (127.0.0.1)，仅本机前端可访问，无需认证层
- **D-03:** MCP 保持 stdio 传输，前端只用 REST，两套独立互不干扰
- **D-04:** API 覆盖全部 31 个 MCP 工具，每个工具对应 REST endpoint
- **D-05:** arcpy 线程安全：复用 MCP 的 threading.Lock 串行化所有 arcpy 调用
- **D-06:** 错误格式沿用 Result 模型（success/code/message/data），与 CLI/MCP 一致
- **D-07:** 开发代理 = Vite proxy，/api/* 转发到 FastAPI:8000
- **D-08:** API 模块嵌入现有包 `src/arcgis_agent/api/`，复用 models 和 services
- **D-09:** 长时操作（buffer、export 等）：POST 返回 task_id，前端轮询 GET /api/v1/tasks/{id}
- **D-10:** 任务存储 = 内存队列 + SQLite 持久化，无需额外依赖
- **D-11:** API 路径前缀 = /api/v1/，后续不兼容变更新增 /api/v2/
- **D-12:** 支持文件上传（.shp, .zip, .gdb），后端接收保存到工作区
- **D-13:** 实时进度通过 SSE（Server-Sent Events）推送给前端
- **D-14:** Swagger UI 保持开启（/docs），开发和生产均可用
- **D-15:** 统一 .bat 启动脚本，同时启动 FastAPI（后台）+ Vite（前台）

### 前端技术栈
- **D-16:** 构建工具 = Vite + React Router (SPA 路由)
- **D-17:** ArcGIS Maps SDK 认证 = API Key（在 ArcGIS Developer 创建）
- **D-18:** 布局 = 单面板聊天式，AI 对话为主界面
- **D-19:** 地图嵌入 = 聊天内嵌可折叠地图面板，AI 回复中地图链接点击展开
- **D-20:** UI 组件库 = Ant Design，中文文档完善，组件丰富
- **D-21:** 前端项目目录 = web/（项目根目录下，与 src/ 并列）
- **D-22:** 状态管理 = Zustand，轻量简洁，TypeScript 友好

### AI 集成
- **D-23:** 多模型支持，首期优先国内模型（通义千问/DeepSeek 等）
- **D-24:** LLM 架构 = 统一 ILLMProvider Adapter 接口（chat + tool_call），与项目现有 Adapter 模式一致
- **D-25:** LLM 调用通过后端代理（FastAPI /api/v1/chat），API Key 安全保存在后端
- **D-26:** 国内模型通过 OpenAI 兼容 API（/v1/chat/completions）对接，一个 Adapter 适配多数
- **D-27:** 智能分析建议 = 模板化建议（根据操作类型触发预设建议，如 buffer 后提示"是否叠加分析？"）

### MCP E2E 测试
- **D-28:** 测试框架 = pytest + mcp SDK ClientSession，连接 stdio MCP Server
- **D-29:** 覆盖全部 31 个 MCP 工具，每个工具至少一个 E2E 用例
- **D-30:** Claude Code 集成测试 = 手动测试清单（Markdown）+ 报告模板（"说什么 → 期望什么"）
- **D-31:** 测试数据复用现有 fixture（tests/conftest.py 的 test_data）

### Claude's Discretion
- FastAPI 路由和 endpoint 的具体设计（URL 命名、参数映射）
- ILLMProvider 接口方法签名和各模型 Adapter 实现细节
- 前端 React 组件树、路由表、Zustand store 结构
- 模板化建议的具体触发规则和建议内容
- E2E 测试用例的具体编写
- API Key / 模型配置文件的存放和加载方式
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 项目架构与需求
- `.planning/PROJECT.md` — 四层架构定义、插件设计、约束条件
- `.planning/REQUIREMENTS.md` — 全部 v1 需求定义
- `.planning/ROADMAP.md` — Phase 7 目标、交付物、依赖关系
- `.planning/STATE.md` — 项目当前状态和已知阻塞

### 已有后端实现（直接扩展）
- `src/arcgis_agent/mcp_server.py` — 31 个 MCP 工具定义和 _run_sync() 模式
- `src/arcgis_agent/adapters/base.py` — Adapter 接口模式（ILLMProvider 参考此模式）
- `src/arcgis_agent/models/result.py` — Result 模型（REST API 复用）
- `src/arcgis_agent/services/` — 所有 Service 层（REST API 直接调用）
- `pyproject.toml` — entry points 和依赖配置

### Phase 3-5 决策（继承模式）
- `.planning/phases/04-map-production/04-CONTEXT.md` — 四层架构模式、错误码规范
- `.planning/phases/03-geoprocessing/03-CONTEXT.md` — Adapter 模式、测试隔离策略

### 外部参考
- ArcGIS Maps SDK for JavaScript — 地图组件和 API Key 配置
- Ant Design — React 组件库文档
- FastMCP / MCP SDK — ClientSession 用于 E2E 测试
- OpenAI 兼容 API 规范 — 国内模型对接标准
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mcp_server.py` 的 31 个 `@mcp.tool()` 定义：可直接映射为 REST endpoint
- `_run_sync()` + `_ARC_LOCK`：REST API 直接复用串行化模式
- `Result` 模型：REST API 响应格式与 CLI/MCP 一致
- `BaseService` 依赖注入：ILLMProvider 注入到 ChatService
- `WorkspaceConfig`：工作空间管理复用

### Established Patterns
- Adapter 接口 + ArcPy 实现 + Mock 实现的三层模式（ILLMProvider 同样）
- lazy import arcpy（构造函数内导入，非模块级）
- 错误码格式：统一前缀 + 语义化后缀
- 测试用 Mock Adapter，不需要真实依赖
- Click + entry_points 插件注册（前端不涉及，REST 单独启动）

### Integration Points
- `src/arcgis_agent/api/` — 新建目录，存放 FastAPI 路由和中间件
- `web/` — 新建目录，独立的前端项目
- `tests/e2e/` — 新建目录，MCP E2E 测试
- `pyproject.toml` — 新增 `arcgis-agent-web` entry point
- 现有 Service 层无需修改，REST API 直接调用
</code_context>

<specifics>
## Specific Ideas

- REST API 启动命令：`arcgis-agent-web` 或 `python -m arcgis_agent.api`
- 聊天 API 流程：用户消息 → POST /api/v1/chat → LLM Adapter → Tool Call 识别 → 执行 GIS 操作 → SSE 推送进度 → 返回结果
- 模板化建议示例：buffer 完成后 → "是否需要对这个缓冲区做叠加分析？"；导出地图后 → "是否需要调整符号化？"
- 前端聊天界面参考 ChatGPT/Claude 风格的消息气泡 + Markdown 渲染
- ArcGIS Map 组件使用 `@arcgis/map-components-react`
</specifics>

<deferred>
## Deferred Ideas

无 — 讨论保持在阶段范围内

</deferred>

---

*Phase: 07-Web-UI-AI-Integration-MCP-E2E-Testing*
*Context gathered: 2026-05-26*
