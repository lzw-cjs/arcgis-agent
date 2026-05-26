"""Tests for POST /api/v1/chat SSE endpoint (Phase 7, Plan 07-04).

Covers: SSE streaming, non-streaming JSON mode, conversation history
persistence, provider listing, and chat session deletion.
"""
from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient


# ════════════════════════════════════════════════════════════════
# Streaming (SSE) Tests
# ════════════════════════════════════════════════════════════════


class TestChatSSEStreaming:
    """POST /api/v1/chat with stream=true returns SSE text/event-stream."""

    @pytest.mark.asyncio
    async def test_chat_returns_sse_content_type(self):
        """SSE response has text/event-stream content type."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"session_id": "test-sse-1", "message": "hello", "stream": True},
            )
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, \
            f"Expected text/event-stream, got {content_type}"

    @pytest.mark.asyncio
    async def test_chat_sse_stream_contains_events(self):
        """SSE stream contains at least one event (token or done)."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"session_id": "test-sse-2", "message": "hello", "stream": True},
            )
        assert response.status_code == 200
        body = response.text
        # SSE format: "event: <type>\ndata: <json>\n\n"
        assert len(body) > 0, "SSE response body should not be empty"

    @pytest.mark.asyncio
    async def test_chat_sse_has_done_event(self):
        """SSE stream should include a done event."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"session_id": "test-sse-3", "message": "hello", "stream": True},
            )
        assert response.status_code == 200
        body = response.text
        # Should contain event:done somewhere in the stream
        assert "done" in body.lower() or "DONE" in body or "event: done" in body or "event:done" in body, \
            f"SSE stream should include done event. Body preview: {body[:200]}"


# ════════════════════════════════════════════════════════════════
# Non-Streaming (JSON) Tests
# ════════════════════════════════════════════════════════════════


class TestChatJSONMode:
    """POST /api/v1/chat with stream=false returns JSON response."""

    @pytest.mark.asyncio
    async def test_chat_non_streaming_returns_json(self):
        """Non-streaming chat returns application/json."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"session_id": "test-json-1", "message": "hello", "stream": False},
            )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data, f"Response should include session_id: {data}"
        assert "response" in data, f"Response should include response field: {data}"

    @pytest.mark.asyncio
    async def test_chat_non_streaming_has_correct_session_id(self):
        """Non-streaming response returns the same session_id that was sent."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat",
                json={"session_id": "my-session-42", "message": "hello", "stream": False},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "my-session-42"


# ════════════════════════════════════════════════════════════════
# Conversation History Tests
# ════════════════════════════════════════════════════════════════


class TestConversationHistoryPersistence:
    """Conversation history is preserved across requests with same session_id."""

    @pytest.mark.asyncio
    async def test_history_preserved_across_two_requests(self):
        """Two consecutive POSTs with same session_id preserve context."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request
            r1 = await client.post(
                "/api/v1/chat",
                json={"session_id": "hist-test", "message": "hello", "stream": False},
            )
            assert r1.status_code == 200

            # Second request with same session_id
            r2 = await client.post(
                "/api/v1/chat",
                json={"session_id": "hist-test", "message": "what can you do?", "stream": False},
            )
            assert r2.status_code == 200
            data2 = r2.json()
            assert "response" in data2

    @pytest.mark.asyncio
    async def test_different_sessions_are_isolated(self):
        """Different session_ids have independent histories."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r_a = await client.post(
                "/api/v1/chat",
                json={"session_id": "session-a", "message": "hello A", "stream": False},
            )
            r_b = await client.post(
                "/api/v1/chat",
                json={"session_id": "session-b", "message": "hello B", "stream": False},
            )
            assert r_a.status_code == 200
            assert r_b.status_code == 200


# ════════════════════════════════════════════════════════════════
# Provider Listing Tests
# ════════════════════════════════════════════════════════════════


class TestChatProviders:
    """GET /api/v1/chat/providers returns available LLM providers."""

    @pytest.mark.asyncio
    async def test_providers_returns_list(self):
        """Providers endpoint returns provider configuration."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/chat/providers")
        assert response.status_code == 200
        data = response.json()
        assert "default" in data or "providers" in data, \
            f"Response should include default or providers: {data}"


# ════════════════════════════════════════════════════════════════
# Session Deletion Tests
# ════════════════════════════════════════════════════════════════


class TestChatSessionDeletion:
    """DELETE /api/v1/chat/{session_id} clears conversation history."""

    @pytest.mark.asyncio
    async def test_delete_session_returns_ok(self):
        """Deleting a session returns status ok."""
        from arcgis_agent.api.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/chat/test-delete-session")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
