"""Unit tests for FastAPI REST API routes."""
from __future__ import annotations

import pytest


class TestHealthCheck:
    def test_health_returns_ok(self, test_client):
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestChatEndpoint:
    def test_chat_non_stream_returns_json(self, test_client):
        """POST /api/v1/chat with stream=false returns JSON (MockLLM)."""
        response = test_client.post("/api/v1/chat", json={
            "session_id": "test-001",
            "message": "hello",
            "stream": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "response" in data
        # With MockLLMProvider, should get a mock response text
        assert len(data["response"]) > 0

    def test_chat_stream_returns_sse(self, test_client):
        """POST /api/v1/chat with stream=true returns SSE."""
        response = test_client.post("/api/v1/chat", json={
            "session_id": "test-002",
            "message": "hello",
            "stream": True,
        })
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_chat_with_empty_message(self, test_client):
        response = test_client.post("/api/v1/chat", json={
            "session_id": "test-003",
            "message": "",
            "stream": False,
        })
        # Accept empty message (LLM will handle)
        assert response.status_code == 200


class TestTasksEndpoint:
    def test_create_task(self, test_client):
        response = test_client.post("/api/v1/tasks", json={
            "tool_name": "gp_buffer",
            "arguments": {"input_fc": "roads", "distance": 100},
        })
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_get_task_not_found(self, test_client):
        response = test_client.get("/api/v1/tasks/nonexistent-id")
        assert response.status_code == 404

    def test_list_tasks(self, test_client):
        # Create a task first
        test_client.post("/api/v1/tasks", json={
            "tool_name": "test", "arguments": {}
        })
        response = test_client.get("/api/v1/tasks?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "count" in data


class TestToolEndpoints:
    """Verify all tool endpoints are registered and return expected status."""

    TOOL_ENDPOINTS_GET = [
        "/api/v1/tools/workspace/get",
        "/api/v1/tools/project/info",
    ]

    TOOL_ENDPOINTS_POST = [
        "/api/v1/tools/workspace/set",
        "/api/v1/tools/data/list",
        "/api/v1/tools/data/describe",
        "/api/v1/tools/data/fields",
        "/api/v1/tools/data/extent",
        "/api/v1/tools/data/count",
        "/api/v1/tools/data/copy",
        "/api/v1/tools/data/delete",
        "/api/v1/tools/data/rename",
        "/api/v1/tools/data/convert",
        "/api/v1/tools/gp/select",
        "/api/v1/tools/gp/clip",
        "/api/v1/tools/gp/buffer",
        "/api/v1/tools/gp/intersect",
        "/api/v1/tools/gp/union",
        "/api/v1/tools/gp/dissolve",
        "/api/v1/tools/gp/spatial-join",
        "/api/v1/tools/gp/merge",
        "/api/v1/tools/gp/project",
        "/api/v1/tools/map/create",
        "/api/v1/tools/map/add-layer",
        "/api/v1/tools/map/remove-layer",
        "/api/v1/tools/map/list-layers",
        "/api/v1/tools/map/set-extent",
        "/api/v1/tools/map/export",
        "/api/v1/tools/map/symbolize",
        "/api/v1/tools/map/label",
        "/api/v1/tools/layout/create",
        "/api/v1/tools/layout/add-element",
        "/api/v1/tools/layout/export",
        "/api/v1/tools/analysis/summary-stats",
    ]

    @pytest.mark.parametrize("endpoint", TOOL_ENDPOINTS_GET)
    def test_get_endpoint_exists(self, test_client, endpoint):
        """GET tool endpoints return 200 or 405 (method depends on tool)."""
        response = test_client.get(endpoint)
        # 200 or 405 (Method Not Allowed for POST-only) both OK for registration check
        assert response.status_code in (200, 405, 422), \
            f"{endpoint}: expected 200/405/422, got {response.status_code}"

    @pytest.mark.parametrize("endpoint", TOOL_ENDPOINTS_POST)
    def test_post_endpoint_accepts_json(self, test_client, endpoint):
        """POST tool endpoints accept JSON body."""
        response = test_client.post(endpoint, json={})
        # 422 = validation error (expected since we sent empty body), 200 = success
        assert response.status_code in (200, 422), \
            f"{endpoint}: expected 200 or 422, got {response.status_code}"


class TestUploadEndpoint:
    def test_upload_rejects_no_file(self, test_client):
        response = test_client.post("/api/v1/upload")
        assert response.status_code in (422, 400)

    def test_upload_shp_file(self, test_client):
        response = test_client.post(
            "/api/v1/upload",
            files={"file": ("test.shp", b"fake shapefile content", "application/octet-stream")},
        )
        assert response.status_code in (200, 201)


class TestProvidersEndpoint:
    def test_providers_list(self, test_client):
        response = test_client.get("/api/v1/chat/providers")
        assert response.status_code == 200
        data = response.json()
        assert "default" in data
        assert "providers" in data
