# External Integrations

**Analysis Date:** 2026-05-27

## APIs & External Services

**LLM Providers (OpenAI-compatible APIs):**
- **Qwen (通义千问)** - Primary/default provider
  - Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - Auth: `DASHSCOPE_API_KEY` env var
  - Model: `qwen-plus` (configurable via `QWEN_MODEL`)
  - Client: LangChain `ChatOpenAI` with custom `base_url`
  - Code: `src/arcgis_agent/config.py:56-65`

- **DeepSeek**
  - Endpoint: `https://api.deepseek.com/v1`
  - Auth: `DEEPSEEK_API_KEY` env var
  - Model: `deepseek-chat` (configurable via `DEEPSEEK_MODEL`)
  - Code: `src/arcgis_agent/config.py:66-74`

- **OpenAI**
  - Endpoint: `https://api.openai.com/v1`
  - Auth: `OPENAI_API_KEY` env var
  - Model: `gpt-4o` (configurable via `OPENAI_MODEL`)
  - Code: `src/arcgis_agent/config.py:75-84`

**ArcGIS / arcpy:**
- **ESRI ArcPy** - Core geoprocessing engine (COM-based)
  - Channel: ESRI Conda (`environment.yml`)
  - Thread-safety: Serialized via `threading.Lock` (`_ARC_LOCK`)
  - Known issue: Chinese path encoding bugs on Windows
  - Code: `src/arcgis_agent/adapters/arcpy_adapter.py`

**ArcGIS Map Components (Frontend):**
- **@arcgis/map-components-react** ^5.0.0
  - React wrapper for ArcGIS JavaScript API map components
  - Used in: `web/src/components/MapPanel.tsx`

## Data Storage

**Databases:**
- **SQLite** - Task persistence
  - Path: `~/.arcgis-agent/tasks.db`
  - Schema: tasks table (task_id, tool_name, status, arguments, result, error, progress, timestamps)
  - Code: `src/arcgis_agent/services/task_service.py`

**File Storage:**
- Local filesystem - Workspace data, uploaded files
- Upload directory: `~/.arcgis-agent/uploads/`
- Supported formats: .shp, .shx, .dbf, .prj, .cpg, .zip, .gdb
- Code: `src/arcgis_agent/api/routes/upload.py`

**Caching:**
- In-memory LRU - ConversationStore (`src/arcgis_agent/api/dependencies.py`)
  - Max 100 sessions, LRU eviction
  - Thread-safe with `threading.Lock`

## Authentication & Identity

**Auth Provider:** None (custom API key-based)
- LLM API keys stored in environment variables only
- No user authentication system
- API keys never exposed to frontend (backend-only)
- CORS: Allowed origin `http://localhost:5173` (dev server)

## Monitoring & Observability

**Error Tracking:**
- Python logging module with structured logging
- Metrics middleware logs request duration, status code
- Slow requests (>5s) and server errors (>=500) logged at warning/error
- Code: `src/arcgis_agent/api/middleware.py`

**Logs:**
- Console logging (stdout/stderr)
- UTF-8 forced on Windows to prevent GBK encoding crashes
- Log levels: DEBUG (verbose), INFO (default), WARNING, ERROR

## CI/CD & Deployment

**Hosting:** Local development only
- Backend: `127.0.0.1:8000` (Uvicorn)
- Frontend dev server: `localhost:5173` (Vite)
- No containerization (Dockerfile not detected)
- No CI/CD pipeline detected

**Build Process:**
- Python: `pip install .` (non-editable install required for Chinese usernames)
- Frontend: `npm run build` (tsc + vite build)

## Environment Configuration

**Required env vars:**
- `DASHSCOPE_API_KEY` - Qwen LLM API key
- `DEEPSEEK_API_KEY` - DeepSeek LLM API key
- `OPENAI_API_KEY` - OpenAI API key
- `LLM_DEFAULT_PROVIDER` - Default LLM provider (default: "qwen")
- `QWEN_MODEL`, `DEEPSEEK_MODEL`, `OPENAI_MODEL` - Model IDs
- `QWEN_BASE_URL`, `DEEPSEEK_BASE_URL`, `OPENAI_BASE_URL` - Custom endpoints URLs

**Secrets location:**
- Environment variables only
- Never committed to source code
- Never exposed to frontend

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

## MCP (Model Context Protocol)

**MCP Server:**
- Transport: stdio
- Entry point: `arcgis-agent-mcp` (pyproject.toml)
- Exposes all 33 GIS tools as MCP tools
- Thread-safe via `_ARC_LOCK` serialization
- Code: `src/arcgis_agent/mcp_server.py`

## API Endpoints Summary

**Chat:**
- `POST /api/v1/chat` - Chat with LLM (SSE streaming or JSON)
- `DELETE /api/v1/chat/{session_id}` - Clear conversation
- `GET /api/v1/chat/providers` - List available LLM providers

**Tools (33 GIS operations):**
- Workspace: `POST /workspace/set`, `GET /workspace/get`
- Project: `GET /project/info`
- Data Discovery: `POST /data/list`, `POST /data/describe`, `POST /data/fields`, `POST /data/extent`, `POST /data/count`
- Data Management: `POST /data/copy`, `POST /data/delete`, `POST /data/rename`, `POST /data/convert`
- Geoprocessing: `POST /gp/select`, `POST /gp/clip`, `POST /gp/buffer`, `POST /gp/intersect`, `POST /gp/union`, `POST /gp/dissolve`, `POST /gp/spatial-join`, `POST /gp/merge`, `POST /gp/project`
- Analysis: `POST /analysis/summary-stats`
- Map: `POST /map/create`, `POST /map/add-layer`, `POST /map/remove-layer`, `POST /map/list-layers`, `POST /map/set-extent`, `POST /map/export`, `POST /map/symbolize`, `POST /map/label`
- Layout: `POST /layout/create`, `POST /layout/add-element`, `POST /layout/export`

**Tasks:**
- `POST /api/v1/tasks` - Create async task
- `GET /api/v1/tasks/{task_id}` - Get task status/result
- `GET /api/v1/tasks` - List recent tasks

**Upload:**
- `POST /api/v1/upload` - Upload GIS files

**Health:**
- `GET /api/v1/health` - Health check

## SSE (Server-Sent Events)

**Event types:**
- `token` - LLM text chunk
- `tool_start` - Tool execution begins
- `tool_end` - Tool execution completes
- `suggestions` - Follow-up suggestions
- `done` - Stream ends
- `error` - Error occurred

**Implementation:** `sse-starlette` library
**Code:** `src/arcgis_agent/api/routes/chat.py`

---

*Integration audit: 2026-05-27*
