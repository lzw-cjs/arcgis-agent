"""Tests for FastAPI app factory, _run_in_thread, DI, and middleware.

Task 1: Core infrastructure (07-01)
"""
from __future__ import annotations

import asyncio
import threading
import time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


# ── Tests: _run_in_thread() ──────────────────────────────────────


class TestRunInThread:
    """_run_in_thread() executes functions via asyncio.to_thread() + threading.Lock."""

    @pytest.mark.asyncio
    async def test_runs_sync_function_and_returns_result(self):
        """A simple sync function should return its value via _run_in_thread."""
        from arcgis_agent.api.dependencies import _run_in_thread

        def add(a: int, b: int) -> int:
            return a + b

        result = await _run_in_thread(add, 2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_returns_result_model_dump_when_result_instance(self):
        """When the function returns a Result, _run_in_thread returns model_dump()."""
        from arcgis_agent.api.dependencies import _run_in_thread
        from arcgis_agent.models.result import Result

        def make_ok():
            return Result.ok(data={"key": "value"})

        result = await _run_in_thread(make_ok)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_catches_exceptions_as_result_error(self):
        """Exceptions inside the function should be caught and returned as Result error dict."""
        from arcgis_agent.api.dependencies import _run_in_thread

        def raise_err():
            raise ValueError("test error")

        result = await _run_in_thread(raise_err)
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "test error" in result.get("message", "")


# ── Tests: ConversationStore ─────────────────────────────────────


class TestConversationStore:
    """ConversationStore provides thread-safe in-memory chat history."""

    def test_get_returns_empty_list_for_new_session(self):
        """get() returns [] for a session_id that has no messages."""
        from arcgis_agent.api.dependencies import ConversationStore

        store = ConversationStore(max_sessions=5)
        assert store.get("nonexistent") == []

    def test_update_and_get_preserves_order(self):
        """update() stores messages, get() returns them in insertion order."""
        from arcgis_agent.api.dependencies import ConversationStore

        store = ConversationStore(max_sessions=5)
        msg1 = {"role": "user", "content": "hello"}
        msg2 = {"role": "assistant", "content": "hi there"}

        store.update("s1", [msg1, msg2])  # type: ignore[arg-type]
        result = store.get("s1")
        assert len(result) == 2
        assert result[0] == msg1
        assert result[1] == msg2

    def test_delete_removes_session(self):
        """delete() removes a session and its messages."""
        from arcgis_agent.api.dependencies import ConversationStore

        store = ConversationStore(max_sessions=5)
        store.update("s1", [{"role": "user", "content": "x"}])  # type: ignore[arg-type]
        store.delete("s1")
        assert store.get("s1") == []

    def test_lru_eviction_when_max_sessions_reached(self):
        """When max_sessions is reached, oldest session is evicted (LRU)."""
        from arcgis_agent.api.dependencies import ConversationStore

        store = ConversationStore(max_sessions=3)
        store.update("a", [{"role": "user", "content": "a"}])  # type: ignore[arg-type]
        store.update("b", [{"role": "user", "content": "b"}])  # type: ignore[arg-type]
        store.update("c", [{"role": "user", "content": "c"}])  # type: ignore[arg-type]
        # Insert 4th, should evict "a" (oldest)
        store.update("d", [{"role": "user", "content": "d"}])  # type: ignore[arg-type]
        assert store.get("a") == []  # evicted
        assert store.get("b") != []
        assert store.get("c") != []
        assert store.get("d") != []

    def test_update_moves_session_to_end(self):
        """update() on an existing session moves it to most-recently-used."""
        from arcgis_agent.api.dependencies import ConversationStore

        store = ConversationStore(max_sessions=3)
        store.update("a", [{"role": "user", "content": "a"}])  # type: ignore[arg-type]
        store.update("b", [{"role": "user", "content": "b"}])  # type: ignore[arg-type]
        store.update("c", [{"role": "user", "content": "c"}])  # type: ignore[arg-type]
        # Touch "a" to make it recently used
        store.update("a", [{"role": "user", "content": "a2"}])  # type: ignore[arg-type]
        # Insert 4th, should evict "b" (now the oldest)
        store.update("d", [{"role": "user", "content": "d"}])  # type: ignore[arg-type]
        assert store.get("a") != []  # still there (was touched)
        assert store.get("b") == []  # evicted
        assert store.get("c") != []
        assert store.get("d") != []


# ── Tests: get_conversation_store ────────────────────────────────


class TestGetConversationStore:
    """get_conversation_store() provides a lazy-init singleton."""

    def test_returns_same_instance_on_multiple_calls(self):
        """Multiple calls return the same singleton instance."""
        from arcgis_agent.api.dependencies import get_conversation_store

        s1 = get_conversation_store()
        s2 = get_conversation_store()
        assert s1 is s2


# ── Tests: create_app() ──────────────────────────────────────────


class TestCreateApp:
    """create_app() returns a configured FastAPI instance."""

    def test_returns_fastapi_instance(self):
        """create_app() returns a FastAPI app."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        assert isinstance(app, FastAPI)

    def test_has_health_route(self):
        """The app includes a GET /api/v1/health route."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        route_paths = [r.path for r in app.routes]
        assert "/api/v1/health" in route_paths

    def test_app_title_and_version(self):
        """The app has the correct title and version."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        assert app.title == "arcgis-agent REST API"
        assert app.version == "0.1.0"


# ── Tests: Health endpoint ───────────────────────────────────────


class TestHealthEndpoint:
    """GET /api/v1/health returns service status."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        """Health endpoint returns {"status": "ok"}."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


# ── Tests: Swagger UI ────────────────────────────────────────────


class TestDocsEndpoint:
    """GET /docs serves the Swagger UI."""

    @pytest.mark.asyncio
    async def test_docs_returns_200(self):
        """Swagger UI endpoint returns 200."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


# ── Tests: metrics_middleware ────────────────────────────────────


class TestMetricsMiddleware:
    """metrics_middleware logs request metrics (path, method, status, duration)."""

    @pytest.mark.asyncio
    async def test_middleware_logs_on_request(self):
        """The middleware should process requests without errors (functional check)."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")
        # Middleware should have logged without crashing
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_404(self):
        """Middleware should handle 404 responses without crashing."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/nonexistent")
        # Just verify middleware didn't crash
        assert response.status_code == 404
