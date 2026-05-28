<!-- refreshed: 2026-05-27 -->
# Architecture

**Analysis Date:** 2026-05-27

## System Overview

ArcGIS Agent is a multi-interface AI-powered GIS automation platform. It exposes ArcGIS Pro functionality through three primary interfaces: a Click-based CLI, an MCP (Model Context Protocol) server, and a FastAPI REST web API with a React frontend. All interfaces converge on the same service layer, which delegates to arcpy via an adapter pattern for testability.

```text
+---------------------------------------------------------------+
|                        User Interfaces                         |
|  +----------------+  +----------------+  +-------------------+  |
|  | CLI (Click)    |  | MCP Server     |  | Web UI (React)   |  |
|  | `cli.py`       |  | `mcp_server.py`|  | `web/src/`       |  |
|  +-------+--------+  +-------+--------+  +--------+----------+  |
|          |                  |                     |             |
|          |                  |                     | SSE/REST    |
|          v                  v                     v             |
+---------------------------------------------------------------+
|                        Service Layer                           |
|  `services/` - Workspace, Project, Data, Geo, Map, Layout     |
|  `chat_service.py` - LLM agent loop with tool calling         |
+---------------------------------------------------------------+
|                        Adapter Layer                           |
|  `adapters/arcpy_adapter.py` - Real arcpy implementations     |
|  `adapters/mock_adapter.py`  - Mock implementations for tests |
|  `adapters/llm.py`           - OpenAI-compatible LLM provider |
|  `adapters/gis_tools.py`     - LangChain tool definitions     |
+---------------------------------------------------------------+
|                        External Systems                        |
|  ArcGIS Pro (arcpy)  |  LLM APIs (Qwen/DeepSeek/OpenAI)      |
+---------------------------------------------------------------+
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| CLI | Click command group with plugin discovery via entry points | `src/arcgis_agent/cli.py` |
| MCP Server | FastMCP server exposing all GIS tools as MCP tools over stdio | `src/arcgis_agent/mcp_server.py` |
| FastAPI App | REST API with CORS, middleware, lifespan, route registration | `src/arcgis_agent/api/main.py` |
| Chat Service | LLM agent loop: message -> LLM -> tool detection -> execution -> SSE | `src/arcgis_agent/services/chat_service.py` |
| Geo Service | Buffer, clip, intersect, union, dissolve, spatial join, merge, project, select | `src/arcgis_agent/services/geoprocessing.py` |
| Map Service | Create map, add/remove layers, symbolize, label, export | `src/arcgis_agent/services/map_service.py` |
| Layout Service | Create layout, add elements (text, legend, scale-bar, etc.), export | `src/arcgis_agent/services/layout_service.py` |
| Data Discovery | List, describe, get fields/extent/count of datasets | `src/arcgis_agent/services/data_discovery.py` |
| Data Management | Copy, delete, rename, convert datasets | `src/arcgis_agent/services/data_management.py` |
| Task Service | SQLite-backed async task tracking with thread-safe CRUD | `src/arcgis_agent/services/task_service.py` |
| arcpy Adapter | Real arcpy implementations of IGeoProcessor, IMapDocument, etc. | `src/arcgis_agent/adapters/arcpy_adapter.py` |
| LLM Adapter | OpenAI-compatible provider using langchain-openai ChatOpenAI | `src/arcgis_agent/adapters/llm.py` |
| GIS Tools | 33 LangChain StructuredTool definitions wrapping services | `src/arcgis_agent/adapters/gis_tools.py` |
| React Frontend | Chat UI with SSE streaming, tool call visualization, map panel | `web/src/` |

## Pattern Overview

**Overall:** Layered Architecture with Adapter Pattern, Repository Pattern, and Agent Loop

**Key Characteristics:**
- **Adapter Pattern:** All arcpy calls go through ABC interfaces (`IGeoProcessor`, `IMapDocument`, etc.), allowing mock injection for testing
- **Service Layer:** Business logic is centralized in `services/` classes that accept adapter injection
- **Result Pattern:** All operations return a standardized `Result` model (success/code/message/data)
- **Thread Safety:** arcpy is COM-based and NOT thread-safe; all calls are serialized via `threading.Lock` + `asyncio.to_thread()`
- **Plugin Architecture:** CLI commands are registered via `importlib.metadata` entry points
- **Agent Loop:** Chat service implements a ReAct-style loop: LLM -> tool calls -> execution -> result feedback

## Layers

### Presentation Layer (CLI / MCP / Web)

**Purpose:** User-facing interfaces
**Location:** `src/arcgis_agent/cli.py`, `src/arcgis_agent/mcp_server.py`, `src/arcgis_agent/api/`, `web/src/`
**Contains:** Click commands, FastMCP tool decorators, FastAPI routers, React components
**Depends on:** Service layer
**Used by:** End users, AI agents (via MCP), web browsers

### Service Layer

**Purpose:** Business logic and orchestration
**Location:** `src/arcgis_agent/services/`
**Contains:** Service classes (GeoprocessingService, MapService, ChatService, etc.)
**Depends on:** Adapter layer (via BaseService DI)
**Used by:** Presentation layer, GIS tools

### Adapter Layer

**Purpose:** Abstract external dependencies (arcpy, LLM APIs)
**Location:** `src/arcgis_agent/adapters/`
**Contains:** ABC interfaces, arcpy implementations, mock implementations, LLM provider, LangChain tools
**Depends on:** arcpy (lazy import), langchain-openai
**Used by:** Service layer

### Data/External Layer

**Purpose:** Persistent storage and external APIs
**Location:** ArcGIS Pro projects, SQLite (`tasks.db`), LLM provider APIs
**Contains:** `.aprx` files, feature classes, task database, conversation history
**Depends on:** N/A (external)
**Used by:** Adapter layer, Service layer

## Data Flow

### Primary Request Path (Web API)

1. **Request** arrives at FastAPI router (`src/arcgis_agent/api/routes/tools.py:42`)
2. **Route handler** validates input and calls `_run_in_thread()` (`src/arcgis_agent/api/dependencies.py:89`)
3. **Thread pool** executes the service method under `_ARC_LOCK` (`src/arcgis_agent/api/dependencies.py:102`)
4. **Service** performs business logic and delegates to adapter (`src/arcgis_agent/services/base.py:25`)
5. **Adapter** calls arcpy operations (`src/arcgis_agent/adapters/arcpy_adapter.py`)
6. **Result** propagates back as JSON via the standardized `Result` model

### Chat/Agent Flow

1. **POST /api/v1/chat** receives user message (`src/arcgis_agent/api/routes/chat.py:62`)
2. **ChatService** loads conversation history from `ConversationStore` (`src/arcgis_agent/services/chat_service.py:104`)
3. **Context management** trims messages if too long (`chat_service.py:109`)
4. **Agent loop** runs via `asyncio.to_thread()` for arcpy safety (`chat_service.py:119`)
5. **LLM provider** invokes model with tools bound (`src/arcgis_agent/adapters/llm.py:137`)
6. **Tool calls** are dispatched to `gis_tools.py` StructuredTools (`src/arcgis_agent/adapters/gis_tools.py`)
7. **Tools** call service layer methods which delegate to arcpy adapters
8. **Results** feed back to LLM for final response
9. **SSE events** stream tokens, tool_start/tool_end, suggestions, done to frontend (`chat.py:99`)

### MCP Tool Flow

1. AI client calls MCP tool over stdio
2. **mcp_server.py** receives the call (`src/arcgis_agent/mcp_server.py:37`)
3. **`_run_sync()`** acquires `_ARC_LOCK` and executes the service method
4. **Result** is returned as a dict (success/code/message/data)
5. MCP client inspects the result

## Key Abstractions

**BaseService:**
- Purpose: Dependency injection container for adapters
- File: `src/arcgis_agent/services/base.py`
- Pattern: Constructor injection with lazy fallback to real adapters

**Result Model:**
- Purpose: Standardized output for all operations
- File: `src/arcgis_agent/models/result.py`
- Pattern: Pydantic BaseModel with factory methods `ok()`, `error()`, `from_exception()`

**Adapter ABCs (IGeoProcessor, IMapDocument, etc.):**
- Purpose: Isolate arcpy for testability
- File: `src/arcgis_agent/adapters/base.py`
- Pattern: Abstract Base Classes with full method signatures

**ConversationStore:**
- Purpose: Thread-safe in-memory chat history with LRU eviction
- File: `src/arcgis_agent/api/dependencies.py:27`
- Pattern: OrderedDict + threading.Lock, max 100 sessions

**TaskStore:**
- Purpose: Persistent async task tracking
- File: `src/arcgis_agent/services/task_service.py`
- Pattern: SQLite with thread-local connections

## Entry Points

**CLI:**
- Location: `src/arcgis_agent/cli.py:36`
- Triggers: `arcgis-agent` command
- Responsibilities: Plugin loading, exit code mapping, UTF-8 reconfiguration

**MCP Server:**
- Location: `src/arcgis_agent/mcp_server.py:596`
- Triggers: `arcgis-agent-mcp` command
- Responsibilities: FastMCP server, stdio transport, signal handling

**Web API:**
- Location: `src/arcgis_agent/api/main.py:126`
- Triggers: `arcgis-agent-web` command or `uvicorn`
- Responsibilities: FastAPI app creation, route registration, lifespan management

**Frontend:**
- Location: `web/src/main.tsx`
- Triggers: `vite` dev server or built static files
- Responsibilities: React app rendering, BrowserRouter

## Architectural Constraints

- **Threading:** arcpy is COM-based and single-threaded. All arcpy calls MUST go through `_ARC_LOCK` (`threading.Lock`) and `asyncio.to_thread()` for async contexts.
- **Global state:** `_conversation_store` (lazy singleton), `_ARC_LOCK` (module-level lock), `_chat_service` and `_llm_config` (lazy singletons in chat routes).
- **Lazy imports:** arcpy is imported inside constructors, not at module level, to allow test imports without ArcGIS Pro installed.
- **Chinese path bug:** arcpy.mp operations fail on systems with Chinese usernames. The codebase logs warnings but does not block execution.
- **No circular imports:** Services import adapters; adapters do not import services. Tools import services directly inside function bodies.

## Anti-Patterns

### Direct arcpy Calls in Services

**What happens:** Services could directly call arcpy methods instead of going through adapters.
**Why it's wrong:** Makes testing impossible without ArcGIS Pro installed. Violates the adapter pattern purpose.
**Do this instead:** Always access arcpy via `self._gp`, `self._map`, `self._data`, `self._layout` injected through `BaseService` (`src/arcgis_agent/services/base.py`).

### Synchronous arcpy in Async Context Without Threading

**What happens:** Calling arcpy directly from FastAPI handlers blocks the event loop.
**Why it's wrong:** Freezes the entire API server for the duration of the geoprocessing operation.
**Do this instead:** Always wrap arcpy calls in `_run_in_thread()` (`src/arcgis_agent/api/dependencies.py:89`) or `asyncio.to_thread()` (`src/arcgis_agent/services/chat_service.py:119`).

### Exposing API Keys to Frontend

**What happens:** LLM API keys could be sent to the browser.
**Why it's wrong:** Security risk; keys should remain server-side only.
**Do this instead:** API keys are loaded from environment variables on the backend only (`src/arcgis_agent/config.py`). The `/chat/providers` endpoint returns only configuration status, never key values.

## Error Handling

**Strategy:** Hierarchical exception classes with standardized Result output

**Patterns:**
- All service methods catch exceptions and return `Result.from_exception(e)`
- arcpy errors are wrapped in `ArcGISError` with `arcpy_messages` field
- FastAPI routes return JSON with the Result dict structure
- SSE streams include `error` events with code and message

**Exit Codes (CLI):**
- 0 = success
- 1 = user error (UserError)
- 2 = system error (SystemError_)
- 3 = ArcGIS error (ArcGISError)

## Cross-Cutting Concerns

**Logging:** Python `logging` module with structured config (`src/arcgis_agent/logging_config.py`). Metrics middleware logs every request with path, method, status, duration.

**Validation:** Pydantic models for API request/response schemas (`src/arcgis_agent/api/schemas/`). Service-level input validation before touching arcpy.

**Authentication:** No built-in auth. LLM API keys are server-side only. CORS allows `localhost:5173` for Vite dev server.

**Configuration:** Environment variables for LLM providers (`DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`). Workspace config persisted to `~/.arcgis-agent/config.json`.

---

*Architecture analysis: 2026-05-27*
