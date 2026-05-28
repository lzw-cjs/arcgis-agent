# Codebase Structure

**Analysis Date:** 2026-05-27

## Directory Layout

```
arcgis-agent/
├── src/                          # Python backend source code
│   └── arcgis_agent/
│       ├── __init__.py           # Package version
│       ├── __main__.py           # python -m arcgis_agent entry
│       ├── cli.py                # Click CLI entry point
│       ├── mcp_server.py         # MCP server (FastMCP stdio)
│       ├── config.py             # LLM provider & workspace config
│       ├── exceptions.py         # Exception hierarchy (AgentError, UserError, etc.)
│       ├── logging_config.py     # Logging setup
│       ├── plugins.py            # Entry-point plugin loader
│       ├── env_check.py          # Environment validation
│       ├── api/                  # FastAPI REST API
│       │   ├── main.py           # App factory, lifespan, route registration
│       │   ├── dependencies.py   # DI, ConversationStore, _run_in_thread
│       │   ├── middleware.py     # Request metrics middleware
│       │   ├── routes/           # API route modules
│       │   │   ├── __init__.py
│       │   │   ├── chat.py       # POST /chat, DELETE /chat/{id}, GET /chat/providers
│       │   │   ├── tools.py      # 33 GIS tool REST endpoints
│       │   │   ├── tasks.py      # Async task CRUD
│       │   │   └── upload.py     # File upload (.shp, .zip, .gdb)
│       │   └── schemas/          # Pydantic request/response schemas
│       │       ├── __init__.py
│       │       ├── chat.py       # ChatRequest, ToolCallEvent
│       │       ├── tasks.py      # TaskCreate, TaskResult, TaskStatus
│       │       └── events.py     # ProgressEvent, TokenEvent, ErrorEvent
│       ├── services/             # Business logic services
│       │   ├── __init__.py
│       │   ├── base.py           # BaseService (adapter DI)
│       │   ├── chat_service.py   # LLM agent loop, SSE streaming
│       │   ├── geoprocessing.py  # Buffer, clip, intersect, union, etc.
│       │   ├── map_service.py    # Create map, layers, symbolize, export
│       │   ├── layout_service.py # Layouts, elements, export
│       │   ├── data_discovery.py # List, describe, fields, extent, count
│       │   ├── data_management.py # Copy, delete, rename, convert
│       │   ├── analysis_service.py # Summary statistics
│       │   ├── project_service.py  # Project info
│       │   ├── workspace_service.py # Workspace get/set
│       │   └── task_service.py    # SQLite task store
│       ├── adapters/             # External dependency adapters
│       │   ├── __init__.py
│       │   ├── base.py           # ABC interfaces (IGeoProcessor, IMapDocument, etc.)
│       │   ├── arcpy_adapter.py  # Real arcpy implementations
│       │   ├── mock_adapter.py   # Mock implementations for testing
│       │   ├── llm.py            # OpenAI-compatible LLM provider
│       │   ├── mock_llm.py       # Mock LLM provider for dev
│       │   └── gis_tools.py      # 33 LangChain StructuredTool definitions
│       ├── commands/             # CLI command plugins (Click)
│       │   ├── __init__.py
│       │   ├── workspace.py      # workspace set/get
│       │   ├── project.py        # project info
│       │   ├── data.py           # data list/describe
│       │   ├── geoprocessing.py  # buffer, clip, intersect, etc.
│       │   ├── analysis.py       # summary statistics
│       │   ├── map.py            # map create, add-layer, export, etc.
       │   └── layout.py         # layout create, add-element, export
│       └── models/
│           ├── __init__.py
│           └── result.py         # Standardized Result Pydantic model
├── web/                          # React frontend (Vite + TypeScript)
│   ├── package.json              # React 19, Ant Design, Zustand, ArcGIS Map Components
│   ├── vite.config.ts           # Vite config with API proxy
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx              # React entry point (BrowserRouter)
│       ├── App.tsx               # Root layout (Header + ChatPanel + MapPanel)
│       ├── vite-env.d.ts
│       ├── api/
│       │   └── chat.ts           # SSE chat client, fetch helpers
│       ├── components/
│       │   ├── ChatPanel.tsx     # Main chat interface
│       │   ├── InputBox.tsx      # Message input component
│       │   ├── MessageBubble.tsx # Chat message display
│       │   ├── ToolCallCard.tsx  # Tool execution visualization
│       │   ├── SuggestionBar.tsx # Post-tool suggestion chips
│       │   └── MapPanel.tsx      # ArcGIS map viewer panel
│       ├── stores/
│       │   └── chatStore.ts      # Zustand chat state management
│       └── types/
│           └── index.ts          # TypeScript interfaces (Message, ToolCall, SSEEvent)
├── tests/                        # Test suite
│   ├── conftest.py               # Shared fixtures (mock adapters, test client)
│   ├── unit/                     # Unit tests
│   │   ├── adapters/             # Adapter tests
│   │   ├── api/                  # API route tests
│   │   ├── services/             # Service tests
│   │   └── test_*.py             # Module-specific unit tests
│   └── e2e/                      # End-to-end tests
│       ├── test_chat_loop.py
│       ├── test_mcp_tools.py
│       └── test_e2e_english_path.py
├── scripts/                      # Utility scripts
├── .planning/                    # Project planning docs
│   └── codebase/                 # Codebase analysis documents
├── pyproject.toml                # Python project config, dependencies, entry points
├── environment.yml               # Conda environment spec
├── README.md                     # Project documentation (Chinese)
└── arcgis-agent.bat              # Windows wrapper script
```

## Directory Purposes

**`src/arcgis_agent/`:"**
- Purpose: Core Python backend
- Contains: All business logic, adapters, API, CLI, MCP server
- Key files: `cli.py`, `mcp_server.py`, `api/main.py`, `config.py`

**`src/arcgis_agent/api/`:"**
- Purpose: FastAPI REST API
- Contains: Route handlers, schemas, dependencies, middleware
- Key files: `main.py` (app factory), `routes/tools.py` (33 endpoints), `routes/chat.py` (SSE streaming)

**`src/arcgis_agent/services/`:"**
- Purpose: Business logic layer
- Contains: Service classes that orchestrate operations and validate inputs
- Key files: `base.py` (DI), `chat_service.py` (agent loop), `geoprocessing.py`, `map_service.py`

**`src/arcgis_agent/adapters/`:"**
- Purpose: Abstract external dependencies
- Contains: ABC interfaces, real arcpy implementations, mocks, LLM provider, LangChain tools
- Key files: `base.py` (ABCs), `arcpy_adapter.py` (real arcpy), `gis_tools.py` (33 tools)

**`src/arcgis_agent/commands/`:"**
- Purpose: CLI command plugins registered via entry points
- Contains: Click command definitions for each domain
- Key files: `geoprocessing.py`, `map.py`, `layout.py`, etc.

**`web/src/`:"**
- Purpose: React frontend
- Contains: Components, API clients, state management, types
- Key files: `App.tsx`, `components/ChatPanel.tsx`, `stores/chatStore.ts`

**`tests/`:"**
- Purpose: Test suite
- Contains: Unit tests (adapters, API, services) and e2e tests
- Key files: `conftest.py` (fixtures), `e2e/test_chat_loop.py`

## Key File Locations

**Entry Points:**
- `src/arcgis_agent/cli.py:36` - CLI main()
- `src/arcgis_agent/mcp_server.py:596` - MCP server main()
- `src/arcgis_agent/api/main.py:126` - Web API main()
- `web/src/main.tsx` - React frontend entry

**Configuration:**
- `pyproject.toml` - Python deps, entry points, build config
- `src/arcgis_agent/config.py` - LLM providers, workspace config
- `web/vite.config.ts` - Vite dev server, API proxy
- `web/package.json` - Frontend dependencies

**Core Logic:**
- `src/arcgis_agent/services/base.py` - BaseService with adapter DI
- `src/arcgis_agent/adapters/base.py` - ABC interfaces
- `src/arcgis_agent/models/result.py` - Standardized Result model

**Testing:**
- `tests/conftest.py` - Shared fixtures (mock adapters, test client)
- `tests/unit/` - Unit tests organized by component
- `tests/e2e/` - End-to-end tests

## Naming Conventions

**Files:**
- Service files: `{domain}_service.py` (e.g., `map_service.py`)
- Adapter files: `{technology}_adapter.py` (e.g., `arcpy_adapter.py`)
- Command files: `{domain}.py` (e.g., `geoprocessing.py`)
- Test files: `test_{module}.py` (e.g., `test_map_service.py`)

**Directories:**
- Singular nouns for domain packages: `services/`, `adapters/`, `commands/`
- Plural for collections: `routes/`, `schemas/`, `components/`

## Where to Add New Code

**New GIS Tool:**
- Tool definition: `src/arcgis_agent/adapters/gis_tools.py` (add StructuredTool)
- Service method: `src/arcgis_agent/services/{domain}_service.py`
- MCP tool: `src/arcgis_agent/mcp_server.py` (add `@mcp.tool()`)
- API route: `src/arcgis_agent/api/routes/tools.py` (add endpoint)
- CLI command: `src/arcgis_agent/commands/{domain}.py`

**New Service:**
- Implementation: `src/arcgis_agent/services/{name}_service.py`
- Inherit from `BaseService` for adapter injection
- Tests: `tests/unit/services/test_{name}_service.py`

**New API Endpoint:**
- Route: `src/arcgis_agent/api/routes/{name}.py`
- Schema: `src/arcgis_agent/api/schemas/{name}.py`
- Register in `src/arcgis_agent/api/main.py`

**New Frontend Component:**
- Component: `web/src/components/{ComponentName}.tsx`
- Types: `web/src/types/index.ts` (if new interfaces needed)
- API: `web/src/api/chat.ts` (if new endpoints)

**New Adapter:**
- Interface: `src/arcgis_agent/adapters/base.py` (add ABC)
- Implementation: `src/arcgis_agent/adapters/{name}_adapter.py`
- Mock: `src/arcgis_agent/adapters/mock_adapter.py`
- Wire into `BaseService`: `src/arcgis_agent/services/base.py`

## Special Directories

**`.planning/`:"**
- Purpose: Project planning documents and codebase analysis
- Generated: No (manually maintained)
- Committed: Yes

**`src/arcgis_agent.egg-info/`:"**
- Purpose: setuptools package metadata
- Generated: Yes (by `pip install`)
- Committed: No (in `.gitignore`)

**`web/dist/`:"**
- Purpose: Vite production build output
- Generated: Yes (by `vite build`)
- Committed: No (in `.gitignore`)

**`build/`:"**
- Purpose: Python build artifacts
- Generated: Yes (by `python -m build`)
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2026-05-27*
