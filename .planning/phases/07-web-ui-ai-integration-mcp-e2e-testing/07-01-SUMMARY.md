---
phase: 07
plan: 07-01
subsystem: api
tags: [fastapi, pydantic, middleware, schemas, tdd]
requires: []
provides: [FastAPI app skeleton, REST health endpoint, Swagger UI, arcpy thread safety, SSE schemas]
affects: [07-02, 07-03, 07-04]
tech-stack:
  added: [fastapi>=0.135, uvicorn>=0.46, python-multipart>=0.0.20, sse-starlette>=3.3]
  patterns: [asyncio.to_thread + threading.Lock, OrderedDict LRU, ASGI middleware, Pydantic v2 schemas]
key-files:
  created:
    - src/arcgis_agent/api/__init__.py
    - src/arcgis_agent/api/main.py
    - src/arcgis_agent/api/dependencies.py
    - src/arcgis_agent/api/middleware.py
    - src/arcgis_agent/api/schemas/__init__.py
    - src/arcgis_agent/api/schemas/chat.py
    - src/arcgis_agent/api/schemas/tasks.py
    - src/arcgis_agent/api/schemas/events.py
    - tests/unit/test_api_core.py
    - tests/unit/test_api_schemas.py
  modified:
    - pyproject.toml
decisions:
  - "_run_in_thread() 使用独立 _ARC_LOCK (threading.Lock)，与 mcp_server.py 模式相同但各自持锁，因为 API 和 MCP Server 通常运行在不同进程"
  - "ConversationStore 使用 OrderedDict + threading.Lock 实现 LRU 淘汰的线程安全内存存储"
  - "metrics_middleware 使用原生 ASGI 中间件（app.middleware('http')）而非 BaseHTTPMiddleware，以兼容 Starlette/FastAPI 的中间件栈"
  - "CORS 仅允许 localhost:5173（Vite dev server），符合 D-02 localhost-only 限制"
duration: ~25 min
completed: "2026-05-26"
---

# Phase 7 Plan 1: FastAPI App Skeleton Summary

FastAPI 应用骨架实现：app 工厂函数 create_app()、_run_in_thread() arcpy 线程安全包装器、ConversationStore 内存对话历史、metrics_middleware 请求指标日志、Pydantic v2 请求/响应 Schema（ChatRequest、TaskCreate、SSE Events）、pyproject.toml 依赖更新。

## Execution

2 tasks, 4 commits (TDD RED/GREEN per task), 39 tests pass.

### Task 1: FastAPI app factory + _run_in_thread() + DI + middleware

**Files created:** `src/arcgis_agent/api/__init__.py`, `main.py`, `dependencies.py`, `middleware.py`

**What was built:**
- `_run_in_thread(fn, *args, **kwargs)` — 通过 `asyncio.to_thread()` + `threading.Lock` 在后台线程串行化执行 arcpy 调用，自动将 Result 实例序列化为 dict，异常时返回 `Result.from_exception(exc).model_dump()`
- `ConversationStore` — 线程安全的内存对话历史存储，基于 `OrderedDict` + `threading.Lock`，LRU 淘汰策略，支持 get/update/delete 操作
- `get_conversation_store()` — 全局单例 lazy init
- `create_app()` — FastAPI 工厂函数，配置 CORS（localhost:5173）、metrics_middleware、lifespan（startup/shutdown ConversationStore）、health 路由（`GET /api/v1/health`）
- `metrics_middleware` — 记录每个请求的 path/method/status/duration_ms，>=500 记录 error，>5s 记录 warning

### Task 2: Pydantic schemas + pyproject.toml 更新

**Files created:** `src/arcgis_agent/api/schemas/__init__.py`, `chat.py`, `tasks.py`, `events.py`

**File modified:** `pyproject.toml`

**What was built:**
- `ChatRequest` — session_id（必填）、message（必填）、stream（默认 true）
- `ToolCallEvent` — SSE 工具调用事件（event + data）
- `TaskStatus` — 枚举：PENDING/RUNNING/COMPLETED/FAILED
- `TaskCreate` — tool_name（必填）、arguments（默认 {}）
- `TaskResult` — 完整任务执行状态，含 progress（0-100 约束）
- `ProgressEvent` / `TokenEvent` / `ErrorEvent` — SSE 流式事件模型
- `pyproject.toml`: 添加 fastapi>=0.135, uvicorn>=0.46, python-multipart>=0.0.20, sse-starlette>=3.3 依赖；添加 arcgis-agent-web 入口点

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pyproject.toml path resolution in test_api_schemas.py**
- **Found during:** Task 2 RED phase
- **Issue:** TestPyprojectToml fixture used `.parent.parent.parent.parent` (4 levels up) which resolved to `worktrees/` directory instead of worktree root
- **Fix:** Changed to `.parent.parent.parent` (3 levels up from `tests/unit/` to project root)
- **Files modified:** `tests/unit/test_api_schemas.py`
- **Commit:** Included in `26645e2` (RED commit for Task 2)

**2. [Rule 1 - Bug] Fixed middleware registration in main.py**
- **Found during:** Task 1 GREEN phase
- **Issue:** Used `app.add_middleware(type(metrics_middleware), dispatch=metrics_middleware)` which is incorrect for function-based middleware
- **Fix:** Changed to `app.middleware("http")(metrics_middleware)` — standard FastAPI/Starlette pattern for raw ASGI middleware
- **Files modified:** `src/arcgis_agent/api/main.py`
- **Commit:** Included in `96e47f8` (GREEN commit for Task 1)

## Verification Results

```
39 passed in 1.48s
- 16 tests: Task 1 (core infrastructure)
- 23 tests: Task 2 (schemas + pyproject.toml)
```

### Acceptance Criteria Met

| Criteria | Status |
|----------|--------|
| `grep "uvicorn.run" main.py` >= 1 | PASS (1) |
| `grep "threading.Lock" dependencies.py` >= 1 | PASS (3) |
| `grep "asyncio.to_thread" dependencies.py` >= 1 | PASS (3) |
| `grep "CORSMiddleware" main.py` >= 1 | PASS (2) |
| App routes count >= 1 | PASS (4) |
| `grep "class ChatRequest" chat.py` >= 1 | PASS (1) |
| `grep "class TaskStatus" tasks.py` >= 1 | PASS (1) |
| `grep "class ProgressEvent" events.py` >= 1 | PASS (1) |
| `grep "arcgis-agent-web" pyproject.toml` >= 1 | PASS (1) |
| `grep "python-multipart" pyproject.toml` >= 1 | PASS (1) |
| `grep "sse-starlette" pyproject.toml` >= 1 | PASS (1) |
| All schemas importable | PASS |

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `d3696b4` | test(07-01) | RED: failing tests for FastAPI app factory + _run_in_thread + DI + middleware |
| `96e47f8` | feat(07-01) | GREEN: implement FastAPI app factory + _run_in_thread + DI + middleware |
| `26645e2` | test(07-01) | RED: failing tests for Pydantic schemas + pyproject.toml updates |
| `17cccbe` | feat(07-01) | GREEN: implement Pydantic schemas + pyproject.toml updates |

## Threat Flags

（无 — 新增的 FastAPI 端口和网络端点已在 plan threat_model 中记录并缓解）

## Self-Check

All files verified present and commits confirmed.
