# Phase 7: Web UI, AI Integration & MCP E2E Testing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 07-web-ui-ai-integration-mcp-e2e-testing
**Areas discussed:** 前后端通信方式, 前端技术栈, AI 集成, MCP E2E 测试

---

## 前后端通信方式

| Option | Description | Selected |
|--------|-------------|----------|
| FastAPI | 现代异步框架，自动 OpenAPI/Swagger 文档，Pydantic 集成 | ✓ |
| Flask | 轻量同步框架，简单直接但需手动文档 | |

| Option | Description | Selected |
|--------|-------------|----------|
| localhost only | API 只监听 127.0.0.1，仅本机前端可访问 | ✓ |
| 局域网可访问 | 监听 0.0.0.0，团队可访问，需认证层 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 保留 stdio，前端只用 REST | MCP 保持现有 stdio 模式不变 | ✓ |
| 改为 SSE/HTTP 双模式 | MCP 同时支持 stdio 和 SSE | |

| Option | Description | Selected |
|--------|-------------|----------|
| 全部暴露 | 所有 31 个工具都有对应 REST endpoint | ✓ |
| 核心子集 | 只暴露前端需要的部分 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 复用 threading.Lock 串行化 | 所有 arcpy 调用通过同一 Lock 串行执行 | ✓ |
| 进程池隔离 | 每个请求 fork 子进程跑 arcpy | |

| Option | Description | Selected |
|--------|-------------|----------|
| 沿用 Result 模型 | 与 CLI/MCP 一致的 success/code/message/data | ✓ |
| RFC 7807 Problem Detail | 标准 HTTP 错误格式 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Vite proxy | Vite 开发服务器代理 /api/* 到 FastAPI | ✓ |
| CORS 直连 | FastAPI 开启 CORS，前端直连 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 嵌入现有包 | src/arcgis_agent/api/ 目录，复用 models 和 services | ✓ |
| 独立 Python 包 | 单独的 web/ 目录，独立 pyproject.toml | |

| Option | Description | Selected |
|--------|-------------|----------|
| 异步任务 + 轮询 | POST 返回 task_id，前端轮询 GET /tasks/{id} | ✓ |
| 同步等待 | 请求保持连接直到操作完成 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 内存 + SQLite | 内存队列 + SQLite 持久化任务状态 | ✓ |
| Redis + Celery | 专业任务队列，依赖 Redis | |

| Option | Description | Selected |
|--------|-------------|----------|
| /api/v1/ | 标准 REST 版本前缀 | ✓ |
| /api/ 无版本 | 简单，内部工具无需版本控制 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 支持上传 | 前端可拖拽上传 shp/zip，后端接收 | ✓ |
| 不上传，仅浏览本地路径 | 前端提供文件浏览器选本地路径 | |

| Option | Description | Selected |
|--------|-------------|----------|
| SSE 推送 | FastAPI SSE，前端 EventSource 监听进度 | ✓ |
| 仅轮询任务状态 | 前端定时 GET，不显示实时百分比 | |
| WebSocket | 双向实时通信 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 开启 Swagger UI | /docs 提供交互式 API 文档 | ✓ |
| 仅生产禁用 | 开发环境开启，生产环境关闭 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 统一启动脚本 | 一个 .bat 同时启动 FastAPI + Vite | ✓ |
| 分别启动 | 两个终端窗口分别启动 | |

---

## 前端技术栈

| Option | Description | Selected |
|--------|-------------|----------|
| Vite + React Router | 最快构建工具 + SPA 路由 | ✓ |
| Next.js | 全栈框架，但 API 已是 Python | |

| Option | Description | Selected |
|--------|-------------|----------|
| API Key | ArcGIS Developer 创建免费 API Key | ✓ |
| OAuth 2.0 登录 | 用户用 ArcGIS 账号登录 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 单面板聊天式 | AI 聊天为主界面 | ✓ |
| 经典三面板布局 | 数据列表/地图/工具面板 | |
| 可切换双模式 | 聊天和 GIS 视图可切换 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 聊天内嵌地图面板 | 可折叠地图视图，点击展开 | ✓ |
| 独立地图页面 | 跳转到独立页面全屏查看 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ant Design | 国内最流行 React 组件库，中文完善 | ✓ |
| Material UI | Google Material Design | |
| Tailwind CSS + Headless UI | 原子化 CSS，高度定制 | |

| Option | Description | Selected |
|--------|-------------|----------|
| web/ 目录 | 前端放在项目根目录 web/，与 src/ 并列 | ✓ |
| 独立 Git 仓库 | 前端单独 repo | |

| Option | Description | Selected |
|--------|-------------|----------|
| Zustand | 轻量级状态管理，API 简洁 | ✓ |
| Redux Toolkit | 功能完整但偏重 | |
| React Context + useReducer | 无需额外依赖 | |

---

## AI 集成

| Option | Description | Selected |
|--------|-------------|----------|
| 国内模型优先 | 通义千问/DeepSeek 等，中文理解强 | ✓ |
| Claude API | MCP 原生支持 | (后续) |
| OpenAI | Function Calling 成熟 | (后续) |

| Option | Description | Selected |
|--------|-------------|----------|
| 统一 LLM Adapter 接口 | 抽象 ILLMProvider，与现有模式一致 | ✓ |
| LiteLLM 代理 | 统一多个提供商 API | |
| 直接调用各 SDK | 前端分别对接 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 后端代理 | FastAPI /api/v1/chat 代理 LLM 调用 | ✓ |
| 前端直调 | 前端直接调用 SDK | |

| Option | Description | Selected |
|--------|-------------|----------|
| OpenAI 兼容 API | 国内多数模型提供 /v1/chat/completions | ✓ |
| 各模型原生 SDK | 每个模型单独对接 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 模板化建议 | 根据操作类型触发预设建议 | ✓ |
| 系统 Prompt 注入 | LLM 预置分析洞察规则 | |
| 独立分析 Agent | 额外 Agent 循环分析 | |

---

## MCP E2E 测试

| Option | Description | Selected |
|--------|-------------|----------|
| pytest + mcp SDK ClientSession | 连接 stdio MCP Server，标准测试框架 | ✓ |
| 独立 Python 脚本 | 无测试报告/覆盖率 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 全部 31 个工具 | 每个 MCP 工具至少一个 E2E 用例 | ✓ |
| 按类别抽样 | 每类抽 2-3 个代表工具 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 手动测试清单 + 报告模板 | Markdown 场景清单，手动执行记录 | ✓ |
| 自动化 Claude Code 调用 | Bash 脚本模拟，不可靠 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 复用现有 fixture | tests/conftest.py 已有 test_data | ✓ |
| 独立测试数据集 | 独立的 .gdb 文件 | |

---

## Claude's Discretion

- FastAPI 路由和 endpoint 的具体设计（URL 命名、参数映射）
- ILLMProvider 接口方法签名和各模型 Adapter 实现
- 前端 React 组件树、路由表、Zustand store 结构
- 模板化建议的具体触发规则和建议内容
- E2E 测试用例的具体编写
- API Key / 模型配置文件的存放和加载方式

## Deferred Ideas

无
