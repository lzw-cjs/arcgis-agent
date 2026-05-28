# Coding Conventions

**Analysis Date:** 2026-05-27

## Languages

**Primary:** Python 3.9+ (backend, CLI, API, services)
**Secondary:** TypeScript/React (frontend), SQL (SQLite task storage)

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g., `map_service.py`, `task_service.py`)
- TypeScript/React components: `PascalCase.tsx` (e.g., `ChatPanel.tsx`, `MessageBubble.tsx`)
- Test files: `test_<module>.py` or `<name>.test.ts`

**Functions:**
- Python: `snake_case` (e.g., `get_conversation_store()`, `_run_in_thread()`)
- TypeScript: `camelCase` (e.g., `sendMessage()`, `useChatStore()`)
- Private/internal: leading underscore (e.g., `_execute()`, `_sync()`)

**Variables:**
- Python: `snake_case` (e.g., `task_store`, `conversation_store`)
- TypeScript: `camelCase` (e.g., `sessionId`, `fullContent`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `MAX_TOOL_ITERATIONS`, `E2E_WORKSPACE`)

**Types:**
- Python: `PascalCase` (e.g., `BaseModel`, `Result`, `TaskStatus`)
- TypeScript: `PascalCase` interfaces (e.g., `Message`, `ToolCall`, `ChatState`)

**Classes:**
- Python: `PascalCase` (e.g., `BaseService`, `ConversationStore`, `TaskStore`)
- Abstract base classes: prefixed with `I` (e.g., `IGeoProcessor`, `IMapDocument`, `IDataAccessor`, `ILLMProvider`)

## Code Style

**Formatting:**
- No automated formatter enforced (no Black, Ruff, or Prettier config found)
- Manual style: 4-space indentation, ~100 char line length (observed)
- Trailing whitespace and blank lines used for visual separation

**Docstrings:**
- Google-style docstrings with type hints in signatures
- Module-level docstrings describe purpose and usage
- Class docstrings explain responsibility and usage patterns

**Type Hints:**
- Full type annotations throughout Python codebase
- `from __future__ import annotations` used for forward references
- Union syntax: `str | None` (Python 3.10+ style)

## Import Organization

**Python order (observed):**
1. Standard library (`import sys`, `import json`, `from pathlib import Path`)
2. Third-party (`from fastapi import APIRouter`, `from pydantic import BaseModel`)
3. Internal project (`from arcgis_agent.models.result import Result`)

**Path Aliases:**
- No path aliases configured; absolute imports from `arcgis_agent.*` used throughout
- Frontend uses relative imports with `../` paths (e.g., `import { useChatStore } from '../stores/chatStore'`)

## Error Handling

**Patterns:**
- Custom exception hierarchy in `arcgis_agent/exceptions.py`:
  - `AgentError` (base, code + exit_code)
  - `UserError` (exit code 1)
  - `SystemError_` (exit code 2)
  - `ArcGISError` (exit code 3)
- Services return `Result` objects (Pydantic model) instead of raising:
  ```python
  Result.ok(data={...}, message="...")
  Result.error(code="FILE_NOT_FOUND", message="...")
  Result.from_exception(exc)
  ```
- CLI maps exceptions to exit codes in `main()` (`src/arcgis_agent/cli.py`)

## Logging

**Framework:** Python standard `logging` module

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)`
- Configured via `setup_logging(verbose, quiet)` in `src/arcgis_agent/logging_config.py`
- Levels: DEBUG (verbose), WARNING (default), ERROR (quiet)
- Format: `"[%(levelname)s] %(name)s: %(message)s"`

## Comments

**When to Comment:**
- Section dividers with Unicode box-drawing characters: `# ── Section Name ──`
- Inline comments for arcpy thread-safety concerns
- Chinese comments in API routes for bilingual documentation

**Docstring style:**
- Triple-quoted, descriptive
- Include usage examples where non-obvious

## Function Design

**Size:** Functions are typically 10-40 lines; services methods ~20-60 lines

**Parameters:**
- Use keyword arguments for optional params
- Type hints on all parameters

**Return Values:**
- Services return `Result` objects consistently
- API routes return dicts or FastAPI response objects

## Module Design

**Exports:**
- No explicit `__all__` declarations found
- Public API determined by what's imported

**Barrel Files:**
- `__init__.py` used for package-level exports (e.g., `src/arcgis_agent/__init__.py` exposes `__version__`)
- `api/schemas/__init__.py` aggregates schema exports

## Architecture Patterns

**Adapter Pattern:**
- Abstract interfaces in `src/arcgis_agent/adapters/base.py`
- Mock implementations in `src/arcgis_agent/adapters/mock_adapter.py`
- ArcPy implementations in `src/arcgis_agent/adapters/arcpy_adapter.py`
- Production vs test adapters injected via `BaseService.__init__()`

**Singleton Pattern:**
- `get_conversation_store()` returns lazy-init singleton
- `get_task_store()` returns lazy-init singleton
- `get_chat_service()` returns lazy-init singleton

**Factory Pattern:**
- `create_app()` in `src/arcgis_agent/api/main.py` returns configured FastAPI instance

**Result Object Pattern:**
- All service methods return `Result` (Pydantic model) instead of raising exceptions
- Enables consistent JSON serialization and error propagation

## Anti-Patterns

### Global Mutable State

**What happens:** Module-level singletons (`_conversation_store`, `_task_store`, `_chat_service`) are mutated at runtime.
**Why it's wrong:** Makes testing harder and can cause state leakage between tests.
**Do this instead:** Use dependency injection or context managers. The codebase already supports DI via `BaseService` constructor injection.

### Lazy Imports Inside Functions

**What happens:** Some modules do lazy imports inside function bodies (e.g., `from arcgis_agent.services.map_service import MapService` inside route handlers).
**Why it's wrong:** Defers import errors to runtime, makes static analysis harder.
**Do this instead:** Import at module top level unless circular dependency requires lazy import.

### Hardcoded Chinese Strings in API

**What happens:** API route docstrings and OpenAPI tags contain Chinese text mixed with English code.
**Why it's wrong:** Can cause encoding issues in some environments, harder for non-Chinese speakers to maintain.
**Do this instead:** Use i18n framework for localization, keep code in English.

## Cross-Cutting Concerns

**Thread Safety:**
- `_ARC_LOCK = threading.Lock()` serializes all arcpy COM calls
- `asyncio.to_thread()` offloads blocking calls from event loop
- `ConversationStore` uses `threading.Lock()` for in-memory state
- `TaskStore` uses `threading.local()` for SQLite connection per thread

**Configuration:**
- Environment variables for LLM provider keys (`DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`)
- `~/.arcgis-agent/config.json` for workspace persistence
- No `.env` file usage detected

---

*Convention analysis: 2026-05-27*
