# Phase 7: Web UI, AI Integration & MCP E2E Testing - Research

**Researched:** 2026-05-26
**Domain:** Full-stack GIS conversational assistant (FastAPI REST API, LangChain AI, React Web UI, MCP E2E Testing)
**Confidence:** HIGH

## Summary

Phase 7 在已完成 31 个 MCP 工具、5 个 Service、3 个 Adapter 接口的基础上，构建四个交付物：FastAPI REST API（将 MCP 工具暴露为 HTTP endpoint）、LangChain AI 集成（聊天+工具调用代理循环）、React 前端（聊天界面+ArcGIS 地图嵌入）、MCP E2E 测试（自动化+手动清单）。

所有外部依赖已安装或可立即安装。FastAPI 0.135.1、Uvicorn 0.46.0、langchain-core 1.3.2、langchain-openai 1.2.1、pytest 9.0.3 均在 arcgis-agent conda 环境中可用。Node.js v24.14.0 + npm 11.9.0 在系统 PATH 中可用。MCP ClientSession 可从 conda 环境导入。

**Primary recommendation:** 已有 Service 层、Result 模型、Adapter 模式、线程安全锁均已完备，Phase 7 是纯粹的"适配和连接"工作。REST API 创建一个薄的路由层直接调用 Service；AI 层创建一个 ILLMProvider Adapter 包装 ChatOpenAI；前端创建一个纯展示层调用 REST。四个交付物按 REST API -> AI -> 前端 -> E2E 测试的顺序依次构建，每个交付物都可独立验证。

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| REST endpoint 定义 (31 tools) | API / Backend | — | FastAPI 路由层直接调用 Service，不涉及前端 |
| arcpy 线程安全串行化 | API / Backend | — | threading.Lock 在 API 层复用，与服务无关 |
| 任务存储 (task_id + 轮询) | API / Backend | Database / Storage | 内存队列 + SQLite，在 FastAPI 进程内管理 |
| 聊天代理循环 (LLM + Tool Call) | API / Backend | — | ChatService 编排工具选择+执行+回复全流程 |
| LLM Provider 适配 (OpenAI compatible) | API / Backend | — | ILLMProvider Adapter 封装外部 API 调用 |
| 前端聊天 UI 渲染 | Browser / Client | — | React 纯展示层，所有业务逻辑在后端 |
| 前端 ArcGIS 地图嵌入 | Browser / Client | — | ArcGIS Maps SDK 客户端加载，API Key 前端使用 |
| 前端状态管理 (Zustand) | Browser / Client | — | 仅管理会话 UI 状态，不持久化 |
| MCP E2E 测试 | API / Backend | — | pytest 通过 stdio ClientSession 连接 MCP Server |
| Vite 开发代理 | Frontend Server | — | Vite proxy 将 /api/* 转发到 FastAPI:8000 |

## User Constraints (from CONTEXT.md)

### Locked Decisions (31 items)

**REST API 设计 (D-01 to D-15):**
- D-01: FastAPI 框架，自动 OpenAPI/Swagger + Pydantic 集成
- D-02: localhost only (127.0.0.1)，无需认证
- D-03: MCP 保持 stdio 传输，前端只用 REST，两套独立
- D-04: API 覆盖全部 31 个 MCP 工具
- D-05: 复用 threading.Lock 串行化 arcpy 调用
- D-06: 错误格式沿用 Result 模型 (success/code/message/data)
- D-07: Vite proxy, /api/* 转发到 FastAPI:8000
- D-08: API 嵌入 src/arcgis_agent/api/，复用 models/services
- D-09: 长时操作 POST 返回 task_id，前端轮询 GET /api/v1/tasks/{id}
- D-10: 任务存储 = 内存队列 + SQLite
- D-11: API 前缀 = /api/v1/
- D-12: 支持文件上传 (.shp, .zip, .gdb)
- D-13: 实时进度通过 SSE 推送
- D-14: Swagger UI 保持开启 (/docs)
- D-15: 统一 .bat 启动脚本

**前端技术栈 (D-16 to D-22):**
- D-16: Vite + React Router (SPA)
- D-17: ArcGIS Maps SDK API Key 认证
- D-18: 单面板聊天式布局
- D-19: 内嵌可折叠地图面板
- D-20: Ant Design 组件库
- D-21: 前端目录 = web/
- D-22: Zustand 状态管理

**AI 集成 (D-23 to D-27):**
- D-23: 多模型支持，首期优先国内模型（通义千问/DeepSeek）
- D-24: ILLMProvider Adapter 接口，遵循现有 ABC 模式
- D-25: LLM 通过后端代理 (/api/v1/chat)，API Key 在后端
- D-26: 国内模型通过 OpenAI 兼容 API 对接
- D-27: 模板化建议（操作后触发预设建议）

**MCP E2E 测试 (D-28 to D-31):**
- D-28: pytest + mcp SDK ClientSession，stdio 连接
- D-29: 覆盖全部 31 个 MCP 工具
- D-30: 手动测试清单 (Markdown) + 报告模板
- D-31: 复用现有 fixture (tests/conftest.py)

### Claude's Discretion
- FastAPI 路由和 endpoint 具体设计
- ILLMProvider 接口方法签名和 Adapter 实现细节
- 前端 React 组件树、路由表、Zustand store 结构
- 模板化建议的具体触发规则和建议内容
- E2E 测试用例具体编写
- API Key / 模型配置文件的存放和加载方式

### Deferred Ideas (OUT OF SCOPE)
无 — 讨论保持在阶段范围内

## Phase Requirements

Phase 7 无 v1 REQUIREMENTS.md 映射（Phase 7 在 CONEXT.md 的 31 项决策中定义）。下表列出每个决策如何被研究支持：

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01~D-15 | REST API 设计 | FastAPI 0.135.1 installed; uvicorn 0.46.0 installed; sse-starlette 3.3.4 installed; SQLite 3.46.1 available; 现有 _ARC_LOCK 模式可直接复用 |
| D-16~D-22 | 前端技术栈 | Node.js v24.14.0 + npm 11.9.0 available; Vite 8.0.14, React 19.2.6, Ant Design 6.4.3, Zustand 5.0.13, @arcgis/map-components-react 5.0.19 all available via npm |
| D-23~D-27 | AI 集成 | langchain-core 1.3.2 + langchain-openai 1.2.1 installed; ILLMProvider ABC 遵循 adapters/base.py 现有模式; ChatService 遵循 services/base.py DI 模式 |
| D-28~D-31 | MCP E2E 测试 | pytest 9.0.3 installed; mcp ClientSession available; 现有 e2e 测试 pattern (tests/e2e/test_e2e_english_path.py) 可复用 |

## Standard Stack

### Core (Python Backend)

| Library | Version (Installed) | Latest | Purpose | Why Standard |
|---------|---------------------|--------|---------|--------------|
| FastAPI | 0.135.1 | 0.136.3 | REST API framework | Pydantic v2 集成，自动 OpenAPI/Swagger [VERIFIED: pip list] |
| Uvicorn | 0.46.0 | — | ASGI server | FastAPI 官方推荐 [VERIFIED: pip list] |
| langchain-core | 1.3.2 | 1.4.0 | LLM primitives (messages, tools) | 项目 AI-SPEC 指定，ChatOpenAI + BaseTool + BaseMessage [VERIFIED: pip list] |
| langchain-openai | 1.2.1 | 1.2.2 | OpenAI-compatible LLM client | 适配通义千问/DeepSeek/OpenAI 所有兼容 API [VERIFIED: pip list] |
| sse-starlette | 3.3.4 | — | Server-Sent Events (D-13) | FastAPI SSE 标准方案 [VERIFIED: pip list] |
| mcp | 1.27.1 | — | MCP ClientSession for E2E tests | D-28 指定 [VERIFIED: pip list] |

### Core (Frontend)

| Library | Latest Version | Purpose | Why Standard |
|---------|---------------|---------|--------------|
| React | 19.2.6 | UI framework | D-16 指定 [VERIFIED: npm view] |
| Vite | 8.0.14 | Build tool + dev proxy | D-16 指定，内置 proxy 支持 D-07 [VERIFIED: npm view] |
| Ant Design | 6.4.3 | UI component library (D-20) | 中文文档完善，组件丰富 [VERIFIED: npm view] |
| Zustand | 5.0.13 | State management (D-22) | 轻量，TypeScript 友好 [VERIFIED: npm view] |
| @arcgis/map-components-react | 5.0.19 | ArcGIS Map component | D-17 指定，ArcGIS Maps SDK 官方 React 封装 [VERIFIED: npm view] |
| react-router-dom | — | SPA routing (D-16) | React Router v7/v6 配套 [CITED: reactrouter.com] |

### Supporting

| Library | Purpose | When to Use |
|---------|---------|-------------|
| aiohttp 3.13.3 | HTTP client (替代 httpx 在测试中) | Async HTTP 调用测试 [VERIFIED: pip list] |
| httpx 0.28.1 | HTTP client | REST API E2E 测试 [VERIFIED: pip list] |
| SQLite (stdlib) | 任务持久化 (D-10) | 任务存储，无需额外 pip install [VERIFIED: sqlite3 3.46.1] |
| python-multipart | 文件上传 (D-12) | FastAPI UploadFile 后端依赖 [ASSUMED: must add to pyproject.toml] |
| aiosqlite 0.21.0 | Async SQLite wrapper | 任务存储的异步访问 [VERIFIED: pip list] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Flask + flask-openapi | FastAPI 的 Pydantic v2 集成和异步支持优于 Flask；项目已安装 FastAPI |
| langchain-core | 直接用 openai SDK | openai SDK 需要更多手写样板（工具 schema、消息管理）。langchain-core 提供 BaseTool、消息原语、trim_messages 等开箱即用 |
| Ant Design | Material UI (MUI) | Ant Design 中文文档更完善，适合国内用户群体 (D-23) |
| Zustand | Redux Toolkit | Zustand 更轻量，项目状态简单不需要 Redux 的中间件生态 |
| @arcgis/map-components-react | @arcgis/core (vanilla JS) | map-components 提供 React 原生组件封装，减少样板代码 |

**Installation (Python side, additions to pyproject.toml):**
```bash
pip install "sse-starlette>=3.3" "python-multipart>=0.0.20" "aiosqlite>=0.21"
```
langchain-core、langchain-openai、fastapi、uvicorn 已安装，无需重新安装。

**Installation (Frontend side):**
```bash
cd web
npm create vite@latest . -- --template react-ts  # 或手动创建
npm install react-router-dom antd zustand @arcgis/map-components-react
```

**Version verification results (2026-05-26):**
- FastAPI: 0.135.1 installed (0.136.3 latest) — minor patch gap, no breaking changes in CHANGELOG [VERIFIED: pip index]
- langchain-core: 1.3.2 installed (1.4.0 latest) — 0.1.8 minor versions behind, significant new features in 1.4.0 may require testing [VERIFIED: AI-SPEC]
- langchain-openai: 1.2.1 installed (1.2.2 latest) — safe [VERIFIED: AI-SPEC]
- React: 19.2.6 latest — stable [VERIFIED: npm view]
- Vite: 8.0.14 latest — stable [VERIFIED: npm view]
- Ant Design: 6.4.3 latest — stable [VERIFIED: npm view]

## Architecture Patterns

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        BROWSER (localhost:5173)                       │
│                                                                       │
│  ┌─────────────────────────┐    ┌──────────────────────────────┐     │
│  │    ChatPanel.tsx        │    │    MapPanel.tsx               │     │
│  │  ┌───────────────────┐  │    │  ┌────────────────────────┐   │     │
│  │  │ MessageBubble[]   │  │    │  │ @arcgis/map-components │   │     │
│  │  │ (Markdown render) │  │    │  │ (API Key from frontend)│   │     │
│  │  └───────────────────┘  │    │  └────────────────────────┘   │     │
│  │  Zustand chatStore       │    │  Collapsible, toggled by AI   │     │
│  └───────────┬─────────────┘    └──────────────────────────────┘     │
│              │ fetch()                                                │
└──────────────┼───────────────────────────────────────────────────────┘
               │ /api/v1/*
               │ (Vite proxy → localhost:8000)
┌──────────────┼───────────────────────────────────────────────────────┐
│              ▼              FASTAPI (localhost:8000)                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  REST Routes: /api/v1/                                        │    │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │    │
│  │  │ tools.py          │  │ chat.py           │  │ tasks.py    │  │    │
│  │  │ GET /tools        │  │ POST /chat        │  │ GET /tasks/ │  │    │
│  │  │ POST /workspace/* │  │ (SSE stream)      │  │ {id}        │  │    │
│  │  │ POST /data/*      │  │ ┌──────────────┐  │  │ (polling)   │  │    │
│  │  │ POST /gp/*        │  │ │ChatService    │  │  └────────────┘  │    │
│  │  │ POST /map/*       │  │ │ ┌──────────┐  │  │                  │    │
│  │  │ POST /layout/*    │  │ │ │Agent Loop│  │  │  TaskStore       │    │
│  │  │ POST /analysis/*  │  │ │ │┌───────┐ │  │  │  (mem+sqlite)    │    │
│  │  │ POST /upload      │  │ │ ││LLM    │ │  │  │                  │    │
│  │  └──────────────────┘  │ │ ││Adapter│ │  │  │                  │    │
│  │                         │ │ ││(Chat  │ │  │  │                  │    │
│  │  _run_sync() wrapper    │ │ ││OpenAI)│ │  │  │                  │    │
│  │  (asyncio.to_thread +   │ │ │└───────┘ │  │  │                  │    │
│  │   threading.Lock)       │ │ │┌───────┐ │  │  │                  │    │
│  │                         │ │ ││Tool   │ │  │  │                  │    │
│  │  ┌────────────────────┐ │ │ ││Dispatch│ │  │  │                  │    │
│  │  │  Services (复用)    │ │ │ ││(31    │ │  │  │                  │    │
│  │  │  GeoProcessing     │◄├─┼─┤│tools) │ │  │  │                  │    │
│  │  │  MapProduction     │ │ │ │└───────┘ │  │  │                  │    │
│  │  │  DataManagement    │ │ │ └──────────┘  │  │                  │    │
│  │  │  LayoutService     │ │ │                │  │                  │    │
│  │  │  AnalysisService   │ │ │  ILLMProvider  │  │                  │    │
│  │  └────────┬───────────┘ │ │  (ABC)         │  │                  │    │
│  │           │             │ └────────────────┘  │                  │    │
│  │           │             └──────────────────────┘                  │    │
│  └───────────┼──────────────────────────────────────────────────────┘    │
│              │                                                           │
│  ┌───────────▼──────────────────────────────────────────────────────┐    │
│  │  Adapters: ArcPyGeoProcessor / ArcPyMapDocument / ArcPyDataAccessor│   │
│  │  (lazy import arcpy, COM object serialization)                     │   │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────┐
│  MCP Server (stdio, 独立进程)                                          │
│  mcp_server.py — 31 tools — arcgis-agent-mcp 入口点                    │
│  (Phase 7 不修改，仅新增 E2E 测试)                                      │
└──────────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────┐
│  External LLM APIs (https)                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│  │ DashScope (Qwen) │  │ DeepSeek API     │  │ OpenAI API       │       │
│  │ qwen-plus        │  │ deepseek-chat   │  │ gpt-4o          │       │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
arcgis-agent/
├── src/arcgis_agent/
│   ├── adapters/
│   │   ├── base.py              # 现有: IGeoProcessor, IMapDocument, IDataAccessor, ILayoutDocument
│   │   ├── llm.py               # NEW: OpenAICompatibleProvider (wraps ChatOpenAI)
│   │   └── mock_llm.py          # NEW: MockLLMProvider for tests
│   ├── api/                     # NEW: FastAPI REST layer
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory, lifespan, CORS, middleware
│   │   ├── dependencies.py      # DI: get_llm_provider(), get_chat_service(), get_task_store()
│   │   ├── middleware.py         # Metrics, request logging
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── tools.py         # 31 tool endpoints (workspace, data, gp, map, layout, analysis)
│   │   │   ├── chat.py          # POST /api/v1/chat (SSE stream + agent loop)
│   │   │   ├── tasks.py         # GET /api/v1/tasks/{id} (long operation polling)
│   │   │   └── upload.py        # POST /api/v1/upload (文件上传)
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── chat.py          # ChatRequest, ChatResponse, ToolCallEvent
│   │       ├── tasks.py         # TaskCreate, TaskStatus, TaskResult
│   │       └── events.py        # SSE event models (ProgressEvent, TokenEvent, ErrorEvent)
│   ├── services/
│   │   ├── chat_service.py      # NEW: ChatService — orchestrates agent loop
│   │   ├── task_service.py      # NEW: TaskService — manages long-running operations
│   │   ├── base.py              # 现有
│   │   ├── geoprocessing.py     # 现有 (unchanged)
│   │   ├── map_service.py       # 现有 (unchanged)
│   │   ├── layout_service.py    # 现有 (unchanged)
│   │   ├── data_discovery.py    # 现有 (unchanged)
│   │   ├── data_management.py   # 现有 (unchanged)
│   │   ├── analysis_service.py  # 现有 (unchanged)
│   │   ├── workspace_service.py # 现有 (unchanged)
│   │   └── project_service.py   # 现有 (unchanged)
│   ├── models/
│   │   └── result.py            # 现有 (unchanged, REST API 复用)
│   ├── config.py                # 现有 + NEW: LLMConfig, LLMProviderConfig
│   ├── mcp_server.py            # 现有 (unchanged)
│   ├── observability.py         # NEW: OpenTelemetry + Phoenix tracing setup
│   └── ...
├── web/                         # NEW: React frontend (separate project)
│   ├── src/
│   │   ├── App.tsx              # Root: React Router + Ant Design ConfigProvider
│   │   ├── main.tsx             # Entry point
│   │   ├── stores/
│   │   │   └── chatStore.ts     # Zustand: messages, sessionId, loading, mapPanelOpen
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx    # Main chat UI: message list + input box
│   │   │   ├── MessageBubble.tsx # Single message: user/AI with Markdown + ToolCallCard
│   │   │   ├── MapPanel.tsx     # ArcGIS map, collapsible
│   │   │   ├── ToolCallCard.tsx # Inline tool execution display (name, args, result, status)
│   │   │   ├── InputBox.tsx     # Chat input with send/suggest buttons
│   │   │   └── SuggestionBar.tsx # Template suggestions (D-27) as quick-action buttons
│   │   ├── api/
│   │   │   └── chat.ts          # fetch() wrappers for /api/v1/chat, /tools, /tasks
│   │   └── types/
│   │       └── index.ts         # TypeScript types (Message, ToolCall, etc.)
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts           # proxy: { '/api': 'http://127.0.0.1:8000' }
├── tests/
│   ├── e2e/                     # NEW subdirectory
│   │   ├── test_mcp_tools.py    # 31 tool E2E tests via MCP ClientSession
│   │   ├── test_chat_loop.py    # AI agent loop integration tests
│   │   └── INTEGRATION_CHECKLIST.md  # D-30: Manual Claude Code test checklist
│   ├── unit/
│   │   ├── adapters/
│   │   │   └── test_llm_adapter.py   # NEW: ILLMProvider unit tests
│   │   ├── services/
│   │   │   ├── test_chat_service.py  # NEW: ChatService unit tests
│   │   │   └── test_task_service.py  # NEW: TaskService unit tests
│   │   └── api/
│   │       └── test_routes.py        # NEW: FastAPI route tests (TestClient)
│   └── conftest.py              # 现有 + NEW: llm fixtures
├── scripts/
│   └── start-web.bat            # NEW: D-15 统一启动脚本
├── promptfooconfig.yaml         # NEW: Promptfoo CI eval config
└── pyproject.toml               # 现有 + NEW: arcgis-agent-web entry point
```

### Pattern 1: REST Endpoint = Thin Wrapper Around Service + _run_sync()

**What:** 每个 MCP 工具对应一个 FastAPI endpoint，复用相同的 Service 层和 `_run_sync()` 串行化模式。

**When to use:** 所有 31 个工具 endpoint 均采用此模式。

**Example (from mcp_server.py, adapted for FastAPI):**
```python
# src/arcgis_agent/api/routes/tools.py
"""Tool endpoints: one route per MCP tool, reusing Services."""
from fastapi import APIRouter, HTTPException
from arcgis_agent.api.dependencies import _run_in_thread

router = APIRouter(prefix="/api/v1")

@router.post("/gp/buffer")
async def buffer_endpoint(
    input_fc: str,
    output_fc: str,
    distance: float,
    unit: str = "Meters",
):
    """Create buffer around features. Matches MCP tool gp_buffer."""
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().buffer(
            input_fc, output_fc, distance, unit=unit
        )
    result = await _run_in_thread(_execute)  # asyncio.to_thread + _ARC_LOCK
    if not result.success:
        raise HTTPException(status_code=422, detail=result.model_dump())
    return result.model_dump()
```

### Pattern 2: Agent Loop (HumanMessage -> LLM -> ToolCalls -> Execute -> ToolMessage -> Repeat)

**What:** ChatService 编排完整的聊天-工具调用-响应循环，上游由 FastAPI chat endpoint 调用，下游通过 ILLMProvider 调用 LLM API。

**When to use:** POST /api/v1/chat，每条用户消息一次。

**Pattern (from AI-SPEC.md Section 3.3, adapted for existing Service layer):**
```python
# src/arcgis_agent/services/chat_service.py
class ChatService:
    def __init__(self, llm_provider: ILLMProvider, task_store: TaskStore):
        self._provider = llm_provider
        self._tasks = task_store
        self._tools = self._build_tools()  # Wrap existing Services as LangChain tools

    async def chat(self, session_id: str, user_input: str) -> AsyncGenerator:
        """Execute one turn of the chat-tool-response loop. Yields SSE events."""
        history = self._store.get(session_id)
        # ... agent loop (see AI-SPEC.md Section 4b.2 for full async pattern)
```

### Pattern 3: ILLMProvider ABC + Production + Mock (existing Adapter pattern)

**What:** ILLMProvider 定义为 ABC，生产实现包装 ChatOpenAI，Mock 实现用于测试。与 IGeoProcessor/IMapDocument/IDataAccessor 模式完全一致。

**When to use:** 所有 LLM 调用通过此 Adapter，前端和后端都不直接调用 LLM API。

**Example:**
```python
# src/arcgis_agent/adapters/base.py — NEW ABC
class ILLMProvider(ABC):
    @abstractmethod
    def chat(self, user_message: str, history: list | None = None) -> AIMessage: ...
    @abstractmethod
    def chat_with_tools(self, user_message: str, history: list | None = None,
                        max_iterations: int = 5) -> tuple[AIMessage, list[dict]]: ...
```

### Pattern 4: SSE Progress Streaming for AI Chat

**What:** 聊天响应通过 Server-Sent Events 流式推送到前端，包含 token 级文本流、工具执行事件、进度更新。

**When to use:** 所有聊天请求（POST /api/v1/chat），前端通过 EventSource 或 fetch + ReadableStream 接收。

**Event types:**
- `token`: LLM 逐 token 文本输出
- `tool_start`: 工具开始执行（名1 + 参数）
- `tool_end`: 工具执行完成（名称 + 成功/失败 + 结果）
- `progress`: 长时操作进度更新（百分比 + 描述）
- `error`: 错误事件
- `done`: 流结束

### Anti-Patterns to Avoid

- **在 FastAPI 路由中直接 import arcpy:** 遵循 lazy import 模式，arcpy 仅在 `_run_in_thread()` 的 lambda 内导入
- **在 FastAPI 中使用 `asyncio.run()`:** FastAPI 已有事件循环，必须使用 `async def` + `await`，不可用 `asyncio.run()` 创建嵌套事件循环
- **同步 `def` 的 FastAPI endpoint 调用 CPU 密集型操作:** arcpy 操作必须通过 `asyncio.to_thread()` 或 `run_in_executor()` 包装
- **Streaming 初始 LLM 响应导致无法检查 tool_calls:** 先 `ainvoke()` 检查是否有 tool calls，执行完工具后，只对最终文本响应使用 `astream()`
- **忘记在 ToolMessage 中包含 `tool_call_id`:** 必须包含工具调用 ID，否则模型无法关联工具结果
- **在前端硬编码 ArcGIS API Key:** 通过环境变量或后端配置注入，不提交到 git

## Existing Code Analysis

### What Can Be Reused (No Changes Needed)

| Asset | Location | How It Is Reused |
|-------|----------|-----------------|
| 31 MCP 工具定义 | `src/arcgis_agent/mcp_server.py` | 每个工具的注释、参数签名、验证逻辑: REST endpoint 参考 |
| `_run_sync()` + `_ARC_LOCK` | `src/arcgis_agent/mcp_server.py` | REST API 直接复用相同的串行化模式 |
| `Result` 模型 | `src/arcgis_agent/models/result.py` | REST API 响应格式，D-06 指定 |
| `BaseService` + DI | `src/arcgis_agent/services/base.py` | ChatService 继承此模式注入 ILLMProvider |
| 所有 Service 类（8 个） | `src/arcgis_agent/services/` | REST API 路由直接调用 |
| Adapter ABCs（4 个） | `src/arcgis_agent/adapters/base.py` | ILLMProvider 添加到此文件 |
| `WorkspaceConfig` | `src/arcgis_agent/config.py` | 扩展存储 LLM 配置 |
| 现有 test fixtures | `tests/conftest.py` | E2E 测试复用 + 新增 LLM fixtures |

### What Needs Extension (Existing Files Modified)

| File | Change Required |
|------|----------------|
| `src/arcgis_agent/adapters/base.py` | 添加 `ILLMProvider` ABC (chat, chat_with_tools 方法) |
| `src/arcgis_agent/config.py` | 添加 `LLMProviderConfig` + `LLMConfig` dataclasses |
| `pyproject.toml` | 添加 `arcgis-agent-web` entry point, `sse-starlette`, `python-multipart` 依赖 |
| `tests/conftest.py` | 添加 `mock_llm`, `llm_config` fixtures |

### What Needs Creation (New Directories)

| New Directory/File | Purpose |
|--------------------|---------|
| `src/arcgis_agent/api/` | FastAPI 应用、路由、中间件、schemas |
| `src/arcgis_agent/adapters/llm.py` | OpenAICompatibleProvider 生产实现 |
| `src/arcgis_agent/adapters/mock_llm.py` | MockLLMProvider 测试实现 |
| `src/arcgis_agent/adapters/gis_tools.py` | 31 个 LangChain StructuredTool 包装 |
| `src/arcgis_agent/services/chat_service.py` | 聊天代理循环编排 |
| `src/arcgis_agent/services/task_service.py` | 长时操作任务存储和管理 |
| `src/arcgis_agent/observability.py` | OpenTelemetry + Phoenix 追踪 |
| `web/` | React 前端项目（独立 package.json） |
| `tests/e2e/test_mcp_tools.py` | MCP E2E 自动化测试 |
| `tests/e2e/INTEGRATION_CHECKLIST.md` | Claude Code 手动测试清单 |
| `tests/unit/adapters/test_llm_adapter.py` | ILLMProvider 单元测试 |
| `tests/unit/services/test_chat_service.py` | ChatService 单元测试 |
| `scripts/start-web.bat` | 统一启动脚本 |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM 工具调用循环 | 手写 OpenAI API 调用 + JSON 解析 | langchain-core `ChatOpenAI.bind_tools()` + `BaseTool` | LangChain 处理 Pydantic schema 生成、JSON Schema 转换、消息序列化。手写需要 300+ 行解析和验证代码 |
| SSE 流式响应 | 手写 `text/event-stream` 格式化和帧协议 | `sse-starlette` (Server-Sent Events) | SSE 有帧格式要求（`data:`, `event:`, reconnection），手写容易产生协议错误 |
| Token 计数和消息截断 | 手写 tiktoken 集成 | `langchain_core.messages.utils.trim_messages()` | trim_messages 已处理 token budget、消息边界、system message 保护、多模型 tokenizer |
| 任务队列和持久化 | 手写文件队列 + 文件系统任务存储 | 内存 `OrderedDict` + SQLite（stdlib sqlite3） | SQLite 提供事务性持久化和并发读，比文件系统方案可靠 |
| 长时操作轮询 | 手写轮询循环 + 重试逻辑 | FastAPI BackgroundTasks + SQLite task 表 + 简单 GET endpoint | 模式简单标准，无需 Celery/Redis |
| 前端 Markdown 渲染 | 手写 Markdown parser | `react-markdown` + `remark-gfm` | 完整 CommonMark + GFM 支持，内置 XSS 防护 [ASSUMED: 需在 web/ 安装] |
| arcpy 线程安全 | asyncio + 手动互斥 | 复用现有 `threading.Lock` + `asyncio.to_thread()` | 模式已存在且验证，D-05 指定复用 |

**Key insight:** 项目的核心价值是 GIS 工具调用编排，不是基础设施。LLM 消息管理、SSE 协议、Token 计数这些都是成熟的标准问题，有高质量的库解决。Phase 7 投入应在 ChatService 的工具选择逻辑、模板化建议、前端聊天 UX 上，而不是重造基础设施轮子。

## Runtime State Inventory

> Phase 7 是纯 greenfield 新增阶段（不涉及 rename/refactor/migration）。无运行时状态需要迁移。

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — 新增 SQLite task store，不涉及现有数据 | N/A |
| Live service config | None — 新增 LLM provider config (~/.arcgis-agent/llm_config.json)，不涉及现有配置 | N/A |
| OS-registered state | None | N/A |
| Secrets/env vars | None — 新增 `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 环境变量 | 用户手动设置或 .env 文件 |
| Build artifacts | None | N/A |

## Common Pitfalls

### Pitfall 1: arcpy COM 线程模型与 FastAPI async 事件循环冲突

**What goes wrong:** FastAPI 使用 asyncio 事件循环处理请求。arcpy 基于 COM，必须在 STA (Single-Threaded Apartment) 线程运行。如果在事件循环线程直接调用 arcpy，COM 初始化失败或静默损坏数据。

**Why it happens:** Windows COM 线程模型要求 arpy 调用在同一线程且已初始化 COM。asyncio 事件循环可能在不同线程间迁移回调。

**How to avoid:** 所有 arcpy 调用通过 `asyncio.to_thread()` 包装，并使用现有 `_ARC_LOCK` (threading.Lock) 确保互斥。此模式已在 MCP server 验证。FastAPI endpoint 使用 `async def` + `await _run_in_thread()`。绝不在事件循环线程直接调用 arcpy。

**Warning signs:** `CoInitialize` 错误、`HRESULT` 错误、间歇性 `AttributeError` on arcpy objects、数据损坏。

### Pitfall 2: ArcGIS Maps SDK for JavaScript 的 React 19 兼容性

**What goes wrong:** @arcgis/map-components-react 5.0.19 构建在 ArcGIS Maps SDK for JavaScript 上，该 SDK 可能不完全兼容 React 19 的新特性（如 concurrent rendering）。

**Why it happens:** ArcGIS Maps SDK 版本周期比 React 慢。React 19 于 2024 年 12 月发布，ArcGIS 组件可能仍以 React 18 为目标。

**How to avoid:** 在使用 @arcgis/map-components-react 的组件上使用 React 18 兼容模式渲染（如果遇到问题）。考虑使用 @arcgis/core (vanilla JS SDK) + 手写 React ref 封装作为 fallback。在 web/ 项目启动后立即验证地图组件是否正常渲染。

**Warning signs:** 地图组件加载后空白、`Warning: Component XYZ accessed React 18 APIs` 控制台警告、地图交互事件不触发。

### Pitfall 3: 完整 `langchain` 包的冗余依赖

**What goes wrong:** 当前环境中 `langchain` 1.2.16（meta-package）已安装，但 Phase 7 只使用 `langchain-core` + `langchain-openai`。如果在代码中不经意导入 `langchain.*` 子包，可能触发未安装的依赖（如 vector stores、document loaders）。

**Why it happens:** AI-SPEC.md 特意选择 `langchain-core` 而非 `langchain` meta-package，但环境中已有两者。

**How to avoid:** 代码中仅从 `langchain_core.*` 和 `langchain_openai.*` 导入。在 `pyproject.toml` 中显式指定 `langchain-core>=1.3,<2` 和 `langchain-openai>=1.2,<2` 作为直接依赖，不添加到 `langchain` meta-package。

**Warning signs:** ImportError for langchain.vectorstores、langchain.document_loaders 等模块。

### Pitfall 4: 聊天历史无限增长导致 token 预算超支

**What goes wrong:** 多步 GIS 工作流（如 select -> buffer -> clip -> export）每条消息累积 SystemMessage、HumanMessage、AIMessage、ToolMessage。10 轮对话可产生 15,000+ token，逼近 qwen-plus 的 131K 限制。更关键的是工具定义 31 个每次发送消耗 4,000 token。

**Why it happens:** 每次 chat 请求，整个历史 + 31 个工具 schema 都发送给 LLM。历史越长，每次请求成本越高。

**How to avoid:** 
1. 在每次请求前调用 `manage_context()`（使用 `trim_messages()` strategy="last"）保持上下文在 max_tokens 以内
2. 20+ 轮对话时注入摘要消息替代中间历史
3. 保留 SystemMessage（第一条消息），裁剪中间轮次，保留最近 5 轮
4. 短期（Phase 7）使用全部 31 个工具定义；后期考虑意图分类 + 动态工具注册

**Warning signs:** 单次 LLM 调用 input tokens > 50,000（成本显著上升）、模型响应开始遗漏早期指令、`context_length_exceeded` 错误。

### Pitfall 5: 中文路径在 LLM 生成的参数中导致 arcpy 崩溃

**What goes wrong:** arcpy.mp 在包含中文字符的路径上完全不可用（已知 bug）。如果 LLM 根据用户的中文输入生成了中文路径作为工具参数，arcpy 操作会崩溃。

**Why it happens:** 项目 memory 中已记录：arcpy.mp 在中文用户名系统不可用。此 bug 影响所有 Map 和 Layout 操作。

**How to avoid:** 
1. ChatService 的 pre-execution hook 检测路径参数中的非 ASCII 字符
2. 检测到时记录 WARNING 但不过滤（非 Map 操作可能正常）
3. 系统提示中包含规则："Output paths should use ASCII characters only. Use English directory names."
4. Map/Layout 相关 endpoint 在检测到中文路径时返回明确的错误消息

**Warning signs:** `OSError` from arcpy、`UnicodeEncodeError` when arcpy tries to create output、Map/Layout 操作静默失败。

## Code Examples

### REST API Endpoint Pattern (from existing mcp_server.py)

```python
# Source: src/arcgis_agent/mcp_server.py lines 37-57 (existing pattern, adapted for FastAPI)
# _run_sync() uses threading.Lock + lazy import + Result.model_dump()
# For FastAPI, the same pattern with asyncio.to_thread():
import asyncio
import threading
from functools import partial

_ARC_LOCK = threading.Lock()

async def _run_in_thread(fn, *args, **kwargs):
    """Execute a service call in a thread pool, under arcpy serialization lock."""
    def _sync():
        with _ARC_LOCK:
            from arcgis_agent.models.result import Result
            result = fn(*args, **kwargs)
            if isinstance(result, Result):
                return result.model_dump()
            return result
    return await asyncio.to_thread(_sync)
```

### ChatService Agent Loop (from AI-SPEC.md Section 4.2)

```python
# Source: AI-SPEC.md lines 598-680 (verified against langchain-openai 1.2.1 API)
# Core pattern: bind_tools() -> invoke() -> check tool_calls -> execute -> ToolMessage -> repeat
# Full implementation in AI-SPEC.md Section 4.2 "Core Pattern: ILLMProvider Adapter"
```

### Zustand Chat Store (Frontend)

```typescript
// web/src/stores/chatStore.ts
// Source: Zustand 5.0 docs [CITED: https://zustand.docs.pmnd.rs/]
import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  toolCalls?: ToolCall[];
  timestamp: number;
}

interface ChatState {
  messages: Message[];
  sessionId: string;
  loading: boolean;
  mapPanelOpen: boolean;
  addMessage: (msg: Message) => void;
  setLoading: (v: boolean) => void;
  toggleMapPanel: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: crypto.randomUUID(),
  loading: false,
  mapPanelOpen: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (v) => set({ loading: v }),
  toggleMapPanel: () => set((s) => ({ mapPanelOpen: !s.mapPanelOpen })),
}));
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OpenAI `max_tokens` parameter | `max_completion_tokens` | September 2024 | LangChain ChatOpenAI 仍接受 max_tokens（内部转换）。向前兼容应使用 max_completion_tokens |
| React 18 concurrent features | React 19 (released Dec 2024) | Dec 2024 | ArcGIS Maps SDK 兼容性待验证（见 Pitfall 2） |
| LangChain AgentExecutor (opinionated) | 手写 agent loop with langchain-core | AI-SPEC decision | Phase 7 手写循环，完整控制工具选择和执行 |
| sse-starlette `EventSourceResponse` | `sse-starlette` 3.3.4 | Current stable | FastAPI SSE 标准方案 |

**Deprecated/outdated:**
- `bind_tools(function_call=...)`: 旧版 OpenAI function_call API 已被 tool_calls 替代。始终使用 `bind_tools(tools)` 不带 function_call 参数。
- 手写 JSON Schema for tools: 使用 `@tool(args_schema=PydanticModel)`，LangChain 自动生成 JSON Schema。

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | python-multipart 作为文件上传依赖，当前环境未安装 | Standard Stack | 文件上传功能无法工作；需要在 conda 环境中 `pip install python-multipart` |
| A2 | react-markdown + remark-gfm 用于前端 Markdown 渲染 | Don't Hand-Roll | 需在 web/ 中额外 npm install；Ant Design 可能有内置 Markdown 组件可替代 |
| A3 | @arcgis/map-components-react 5.0.19 兼容 React 19 | Common Pitfalls | 需降级 React 到 18 或使用 @arcgis/core 手写封装（工作量增加 2-3 天） |
| A4 | Vite 8.x 的 proxy 配置语法未改变 | Architecture Patterns | Vite 从 5 到 8 有 breaking changes；proxy 语法需验证 [ASSUMED: based on Vite 5 docs, not 8] |
| A5 | sse-starlette 3.3.4 API 与 AI-SPEC.md 中的 EventSourceResponse 一致 | Code Examples | AI-SPEC 使用 sse-starlette EventSourceResponse，但当前版本 API 可能不同 [ASSUMED: 未对 3.3.4 验证] |

**If this table is empty:** N/A — 5 assumptions flagged for user confirmation.

## Open Questions

1. **ArcGIS Maps SDK API Key 的获取和管理方式**
   - What we know: D-17 指定 API Key 方案；用户需在 ArcGIS Developer 创建 key
   - What's unclear: API Key 放哪里（.env 在前端？config 在后端？）；前端如何加载（Vite 环境变量？）；是否需要 OAuth 2.0 作为备选
   - Recommendation: API Key 通过 Vite 环境变量 `VITE_ARCGIS_API_KEY` 注入前端；在后端 config 中不存储（前端直接使用）

2. **langchain-core 1.4.0 升级路径**
   - What we know: 当前安装 1.3.2，最新 1.4.0（0.1.8 版本差距）。AI-SPEC.md 指定 `>=1.3`
   - What's unclear: 1.4.0 是否有 breaking changes 影响 ChatOpenAI、BaseTool、或 trim_messages API
   - Recommendation: 锁定 `>=1.3,<2`（如 AI-SPEC 指定），在实现期间不急于升级到 1.4。如果 1.4 引入所需功能再升级

3. **React 19 + ArcGIS Maps SDK 兼容性**
   - What we know: React 19.2.6 是最新稳定版；@arcgis/map-components-react 5.0.19 发布时 React 19 尚未广泛采用
   - What's unclear: 地图组件在 React 19 strict mode + concurrent features 下是否正常工作
   - Recommendation: 前端项目初始化后立即验证地图渲染。如果失败，计划 B：使用 @arcgis/core (vanilla JS) + `useRef` + `useEffect` 手写地图封装

4. **SSE vs WebSocket 的最终选择**
   - What we know: D-13 指定 SSE 推送进度
   - What's unclear: SSE 是单向（server -> client），工具调用参数提交仍需要 POST 请求。是否需要双工通信（如取消长时操作）？
   - Recommendation: SSE 满足 Phase 7 需求。如果后期需要取消操作等双向功能，升级到 WebSocket

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (arcgis-agent conda env) | Backend runtime | ✓ | 3.11.10 | — |
| FastAPI | REST API | ✓ | 0.135.1 | — |
| Uvicorn | ASGI server | ✓ | 0.46.0 | — |
| langchain-core | AI agent loop | ✓ | 1.3.2 | — |
| langchain-openai | LLM client | ✓ | 1.2.1 | — |
| sse-starlette | SSE streaming | ✓ | 3.3.4 | — |
| mcp (ClientSession) | MCP E2E tests | ✓ | 1.27.1 | — |
| pytest | All tests | ✓ | 9.0.3 | — |
| sqlite3 | Task store | ✓ | 3.46.1 | — |
| Node.js | Frontend build | ✓ | v24.14.0 | — |
| npm | Frontend package manager | ✓ | 11.9.0 | — |
| python-multipart | File upload (D-12) | ✗ | — | pip install python-multipart |
| arize-phoenix | Tracing (optional) | ✗ | — | pip install arize-phoenix (optional, dev only) |
| opentelemetry-* | Instrumentation (optional) | ✗ | — | pip install opentelemetry-* (optional, dev only) |
| promptfoo | CI evals | ✗ | — | npm install -g promptfoo (optional, eval only) |

**Missing dependencies with no fallback:**
- python-multipart: FastAPI 文件上传的必需依赖。`pip install python-multipart` 即可，无版本冲突风险。

**Missing dependencies with fallback:**
- arize-phoenix + opentelemetry: 生产监控和追踪。可延后安装；追踪是 opt-in（环境变量 `ARCGIS_AGENT_TRACING=true`）。默认关闭时无性能开销。
- promptfoo: CI eval 工具。可延后到 Verify 阶段安装；eval 在开发期间手动运行即可。

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | none — uses pyproject.toml [tool.pytest.ini_options] or pytest.ini (to verify) |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ -x -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01~D-15 | REST API endpoints (31 tools) | unit | `pytest tests/unit/api/test_routes.py -x -q` | ❌ Wave 0 |
| D-23~D-27 | ILLMProvider adapter + ChatService | unit | `pytest tests/unit/adapters/test_llm_adapter.py tests/unit/services/test_chat_service.py -x -q` | ❌ Wave 0 |
| D-15 | TaskService (SQLite + memory) | unit | `pytest tests/unit/services/test_task_service.py -x -q` | ❌ Wave 0 |
| D-28~D-29 | MCP E2E (31 tools via ClientSession) | e2e | `pytest tests/e2e/test_mcp_tools.py -x -v` | ❌ Wave 0 |
| D-30 | Claude Code manual checklist | manual | N/A (manual — checklist in INTEGRATION_CHECKLIST.md) | ❌ Wave 0 |
| D-01~D-27 | Full chat loop integration | integration | `pytest tests/e2e/test_chat_loop.py -x -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/ -x -q`
- **Per wave merge:** `pytest tests/ -x -v`
- **Phase gate:** Full suite green + manual Claude Code checklist completed

### Wave 0 Gaps
- [ ] `tests/unit/api/test_routes.py` — REST endpoint 测试（TestClient）
- [ ] `tests/unit/adapters/test_llm_adapter.py` — ILLMProvider 单元测试（MockLLMProvider）
- [ ] `tests/unit/services/test_chat_service.py` — ChatService 单元测试（注入 MockLLMProvider）
- [ ] `tests/unit/services/test_task_service.py` — TaskService 单元测试（内存 + SQLite）
- [ ] `tests/e2e/test_mcp_tools.py` — MCP E2E 测试（31 个工具，MCP ClientSession）
- [ ] `tests/e2e/test_chat_loop.py` — 完整聊天循环集成测试
- [ ] `tests/e2e/INTEGRATION_CHECKLIST.md` — Claude Code 手动测试清单
- [ ] `tests/conftest.py` — 新增 `mock_llm`, `llm_config`, `test_client` fixtures
- [ ] pytest 配置（如果 pyproject.toml 中无 [tool.pytest.ini_options]）— 设置 asyncio_mode

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | D-02: localhost only, no auth layer needed |
| V3 Session Management | yes (partial) | session_id 用于对话历史隔离；不涉及登录会话 |
| V4 Access Control | no | localhost only, single user |
| V5 Input Validation | yes | FastAPI Pydantic models + Service layer validation (existing) |
| V6 Cryptography | no | 无加密需求（本地传输，不涉及敏感数据持久化） |
| V7 Error Handling | yes | Result 模型 + structured error codes (existing) + 不泄露 arcpy 内部错误 |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LLM API Key 在前端泄露 | Information Disclosure | D-25: API Key 仅在后端存储，所有 LLM 调用通过 /api/v1/chat 代理 |
| 提示注入（用户输入操控工具调用） | Elevation of Privilege | 系统提示设定规则 + 工具描述明确限制；LLM 判断是否应调用工具 |
| 路径遍历攻击（LLM 生成恶意路径） | Tampering | Service 层已有路径验证（exists() 检查），但需额外验证输出路径不在敏感目录 |
| 无限制的 API 调用消耗 credits | Denial of Service | MAX_TOOL_ITERATIONS=5 guardrail + max_tokens=2048 + 单用户 localhost 限制 |
| arcpy 许可证耗尽 | Denial of Service | 现有 try/finally + CheckInExtension 模式（Service 层已有） |

## Sources

### Primary (HIGH confidence)
- `pip list` output — 所有 installed package versions (FastAPI, langchain-core, langchain-openai, uvicorn, sse-starlette, mcp, pytest, aiosqlite) [VERIFIED: 2026-05-26]
- `npm view` output — 最新 npm package versions (React 19.2.6, Vite 8.0.14, Ant Design 6.4.3, Zustand 5.0.13, @arcgis/map-components-react 5.0.19) [VERIFIED: 2026-05-26]
- `pip index versions fastapi` — FastAPI 0.135.1 installed, 0.136.3 latest [VERIFIED: 2026-05-26]
- `sqlite3.sqlite_version` check — 3.46.1 in arcgis-agent conda env [VERIFIED: 2026-05-26]
- MCP ClientSession import check — available at `mcp.client.session.ClientSession` [VERIFIED: 2026-05-26]
- AI-SPEC.md — 完整的代码示例和 API 参考（langchain-core 1.3 + langchain-openai 1.2）[CITED: AI-SPEC.md Sections 3-7]
- CONTEXT.md — 31 项用户决策 [CITED: CONTEXT.md]
- src/arcgis_agent/mcp_server.py — 现有 31 个 MCP 工具定义、_run_sync() 模式、_ARC_LOCK [VERIFIED: 源代码]
- src/arcgis_agent/adapters/base.py — 现有 ABC 接口模式 [VERIFIED: 源代码]
- src/arcgis_agent/models/result.py — Result 模型（API 复用）[VERIFIED: 源代码]
- src/arcgis_agent/services/base.py — BaseService DI 模式 [VERIFIED: 源代码]
- pyproject.toml — 现有依赖和 entry points [VERIFIED: 源代码]

### Secondary (MEDIUM confidence)
- LangChain ChatOpenAI documentation — 通过 AI-SPEC.md Section 3 引用 [CITED: docs.langchain.com]
- Ant Design documentation — D-20 指定 [CITED: ant.design]
- Zustand documentation — D-22 指定 [CITED: zustand.docs.pmnd.rs]
- ArcGIS Maps SDK for JavaScript — D-17 指定 [CITED: developers.arcgis.com]
- FastAPI documentation — D-01 指定 [CITED: fastapi.tiangolo.com]

### Tertiary (LOW confidence)
- ArcGIS Maps SDK 与 React 19 兼容性 — 无官方文档确认 [ASSUMED]
- react-markdown 与 Ant Design 内置 Markdown 功能的选择 — 未对比验证 [ASSUMED]
- Vite 8.x proxy 配置语法 — 基于 Vite 5 文档假设 [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 所有包版本通过 pip list + npm view 验证
- Architecture: HIGH — 基于现有已验证的四层架构 + AI-SPEC.md 的 agent loop 模式
- Pitfalls: MEDIUM — arcpy COM 线程安全已知且已验证；React 19 兼容性未验证
- Environment availability: HIGH — 所有核心依赖已确认安装或可从 npm/pip 获取

**Research date:** 2026-05-26
**Valid until:** 2026-06-26 (30 days — stable stack, minor version bumps expected)

## Implementation Recommendations

### Recommended Build Order

Phase 7 的四个交付物有明确的依赖链。推荐按以下顺序构建：

**Wave 1: REST API Layer (backend foundation)**
1. `src/arcgis_agent/api/main.py` — FastAPI app factory + lifespan + CORS
2. `src/arcgis_agent/api/dependencies.py` — `_run_in_thread()` 包装器 + DI functions
3. `src/arcgis_agent/api/routes/tools.py` — 31 tool endpoints (直接映射 MCP 工具)
4. `src/arcgis_agent/api/routes/upload.py` — 文件上传 endpoint
5. `src/arcgis_agent/api/routes/tasks.py` — 任务轮询 endpoint
6. `src/arcgis_agent/services/task_service.py` — 长时操作任务存储
7. `pyproject.toml` — `arcgis-agent-web` entry point

**依赖:** 无（直接使用现有 Service 层）  
**验证:** `http://127.0.0.1:8000/docs` 显示 31+ endpoints  

**Wave 2: AI Integration (agent intelligence)**
8. `src/arcgis_agent/config.py` — LLMConfig + LLMProviderConfig
9. `src/arcgis_agent/adapters/base.py` — ILLMProvider ABC
10. `src/arcgis_agent/adapters/llm.py` — OpenAICompatibleProvider
11. `src/arcgis_agent/adapters/mock_llm.py` — MockLLMProvider
12. `src/arcgis_agent/adapters/gis_tools.py` — 31 LangChain StructuredTool wrappers
13. `src/arcgis_agent/services/chat_service.py` — ChatService (agent loop)
14. `src/arcgis_agent/api/routes/chat.py` — POST /api/v1/chat (SSE stream)

**依赖:** Wave 1 (需要 REST 框架)  
**验证:** curl POST /api/v1/chat 返回 AI 响应  

**Wave 3: React Frontend (UI presentation)**
15. `web/` — Vite + React + TypeScript project init
16. `web/src/api/chat.ts` — fetch() wrappers
17. `web/src/stores/chatStore.ts` — Zustand state
18. `web/src/components/` — ChatPanel, MessageBubble, MapPanel, InputBox, ToolCallCard
19. `web/src/App.tsx` — Router + Layout + ConfigProvider
20. `web/vite.config.ts` — proxy + ArcGIS API Key env var

**依赖:** Wave 1 + 2 (需要 REST API + chat endpoint)  
**验证:** `http://localhost:5173` 聊天界面正常显示  

**Wave 4: E2E Testing + Polish**
21. `tests/e2e/test_mcp_tools.py` — 31 MCP tool tests
22. `tests/e2e/INTEGRATION_CHECKLIST.md` — Claude Code manual tests
23. `tests/unit/adapters/test_llm_adapter.py` — ILLMProvider tests
24. `tests/unit/services/test_chat_service.py` — ChatService tests
25. `tests/unit/api/test_routes.py` — FastAPI TestClient tests
26. `scripts/start-web.bat` — 统一启动脚本
27. `src/arcgis_agent/observability.py` — Phoenix tracing (optional)

**依赖:** Wave 1-3 (需要完整系统)  
**验证:** 所有测试通过 + Claude Code 手动清单完成  

### Cross-Cutting Concerns (address throughout)

- **LLM Provider 配置管理:** Wave 2 中与 ILLMProvider 一起创建
- **Promptfoo eval 配置:** Wave 4 中设置（evaluation-focused）
- **错误日志和中文本地化:** Wave 1-3 中逐步添加
- **文档/README 更新:** 每个 wave 完成后更新

