# 技术栈

**分析日期：** 2026-05-27

## 编程语言

**主要语言：**
- Python 3.11 - 后端 API、CLI、MCP 服务器、ArcGIS 自动化服务
- TypeScript ~5.7 - React 前端（位于 `web/` 目录的 Vite 项目）

**次要语言：**
- HTML/CSS - 前端 UI（通过 React/JSX）
- JSON - 配置、API 模式定义、任务存储

## 运行时环境

**后端环境：**
- Python 3.11（Conda 环境，`environment.yml`）
- ArcPy（ESRI Conda 频道）- 基于 COM 的 ArcGIS Pro 地理处理

**前端环境：**
- Node.js（通过 Vite 开发服务器）
- 浏览器目标：ES2020、DOM、DOM.Iterable

**包管理器：**
- pip（Python）- 通过 `pyproject.toml`
- npm（Node.js）- `web/package.json`
- 锁定文件：`web/package-lock.json` 已存在

## 框架

**后端核心：**
- FastAPI >=0.135 - REST API 框架（`src/arcgis_agent/api/main.py`）
- Uvicorn >=0.46 - ASGI 服务器（`src/arcgis_agent/api/main.py:130`）
- Pydantic >=2.11 - 数据验证与序列化
- LangChain Core >=0.3.0 - LLM 代理框架、消息类型
- LangChain OpenAI >=0.3.0 - 兼容 OpenAI 的 LLM 客户端
- Click >=8.1 - CLI 框架（`src/arcgis_agent/cli.py`）
- MCP >=1.0 - 模型上下文协议服务器（`src/arcgis_agent/mcp_server.py`）

**前端核心：**
- React ^19.2.0 - UI 框架
- React DOM ^19.2.0 - DOM 渲染
- React Router DOM ^7.0.0 - 客户端路由
- Ant Design ^6.4.0 - UI 组件库（中文本地化）
- @ant-design/icons ^6.0.0 - 图标集
- Zustand ^5.0.0 - 状态管理（`web/src/stores/chatStore.ts`）
- @arcgis/map-components-react ^5.0.0 - ArcGIS 地图组件
- react-markdown ^9.0.0 - 聊天中的 Markdown 渲染
- remark-gfm ^4.0.0 - GitHub 风格 Markdown 支持

**构建/开发：**
- Vite ^8.0.0 - 前端构建工具和开发服务器（`web/vite.config.ts`）
- @vitejs/plugin-react ^6.0.0 - Vite 的 React 支持
- TypeScript ~5.7.0 - 类型检查
- @rolldown/plugin-babel ^0.2.0 - Babel 插件（基于 Rollup）

## 关键依赖

**后端关键依赖：**
- `fastapi` >=0.135 - 支持自动生成 OpenAPI 文档的 REST API
- `uvicorn` >=0.46 - ASGI 服务器
- `pydantic` >=2.11 - 模式验证（FastAPI 模型、Result 模型）
- `langchain-core` >=0.3.0 - LLM 消息类型、工具抽象
- `langchain-openai` >=0.3.0 - 用于通义千问/DeepSeek/OpenAI 的 ChatOpenAI 客户端
- `sse-starlette` >=3.3 - SSE 流式响应（`src/arcgis_agent/api/routes/chat.py`）
- `python-multipart` >=0.0.20 - 文件上传处理
- `mcp` >=1.0 - 用于 AI 代理工具暴露的 FastMCP 服务器
- `click` >=8.1 - CLI 命令框架
- `rich` - 终端输出格式化

**前端关键依赖：**
- `react` ^19.2.0 / `react-dom` ^19.2.0 - UI 框架
- `antd` ^6.4.0 - 组件库（中文本地化 `zh_CN`）
- `zustand` ^5.0.0 - 轻量级状态管理
- `@arcgis/map-components-react` ^5.0.0 - ArcGIS 地图集成
- `react-markdown` ^9.0.0 + `remark-gfm` ^4.0.0 - Markdown 渲染

**基础设施：**
- SQLite3（标准库）- 任务持久化（`src/arcgis_agent/services/task_service.py`）
- threading.Lock - arcpy 序列化（COM 线程安全）
- asyncio - FastAPI 异步处理程序、SSE 流式传输

## 配置

**环境变量：**
- LLM 提供商的环境变量：
  - `DASHSCOPE_API_KEY` / `QWEN_MODEL` / `QWEN_BASE_URL`
  - `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL`
  - `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL`
  - `LLM_DEFAULT_PROVIDER` - 默认提供商选择
- 工作空间配置：`~/.arcgis-agent/config.json`
- 任务数据库：`~/.arcgis-agent/tasks.db`

**构建：**
- `pyproject.toml` - Python 包定义、依赖、入口点
- `web/package.json` - Node.js 依赖
- `web/vite.config.ts` - Vite 配置（端口 5173，代理到 :8000）
- `web/tsconfig.json` - TypeScript 配置（ES2020，bundler 解析）
- `environment.yml` - Conda 环境（Python 3.11、arcpy、numpy、pandas）

## 平台要求

**开发环境：**
- 已安装 ArcGIS Pro 的 Windows（arcpy 依赖）
- 可访问 esri 频道的 Conda
- 用于前端开发的 Node.js
- 至少一个 LLM 提供商的 API 密钥

**生产环境：**
- 相同的 Windows + ArcGIS Pro 环境（arcpy 仅支持 Windows）
- 后端运行在 `127.0.0.1:8000`
- 前端开发服务器在 `localhost:5173`（将 `/api` 代理到后端）

## 测试

**前端：**
- Vitest ^3.0.0 - 测试运行器（`npm run test`）
- 测试：`web/src/__tests__/*.test.ts`
  - `chatApi.test.ts` - SSE API 客户端测试
  - `chatStore.test.ts` - Zustand 存储测试
  - `types.test.ts` - TypeScript 类型测试

**后端：**
- pytest（由项目结构推断，未找到显式配置）
- 248/358 测试通过（根据项目记忆）

## CLI 入口点

- `arcgis-agent` - 主 CLI（`src/arcgis_agent/cli.py:main`）
- `arcgis-agent-mcp` - MCP 服务器（`src/arcgis_agent/mcp_server.py:main`）
- `arcgis-agent-web` - Web API 服务器（`src/arcgis_agent/api/main.py:main`）

---

*技术栈分析：2026-05-27*
