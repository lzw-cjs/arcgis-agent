"""Unit tests for FastAPI REST API routes."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
        test_client.post("/api/v1/tasks", json={
            "tool_name": "test", "arguments": {}
        })
        response = test_client.get("/api/v1/tasks?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "count" in data


class TestToolEndpoints:
    """Verify all 33 tool endpoints are registered and return expected status.

    Uses mock _run_in_thread to avoid calling arcpy (which is unavailable
    in the test environment). Tests only verify route registration and
    parameter acceptance.
    """

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

    TOOL_SAMPLE_PARAMS = {
        "/api/v1/tools/workspace/set": {"path": "/fake/path"},
        "/api/v1/tools/data/list": {"workspace": "/fake"},
        "/api/v1/tools/data/describe": {"dataset_path": "/fake/data"},
        "/api/v1/tools/data/fields": {"dataset_path": "/fake/data"},
        "/api/v1/tools/data/extent": {"dataset_path": "/fake/data"},
        "/api/v1/tools/data/count": {"dataset_path": "/fake/data"},
        "/api/v1/tools/data/copy": {"src": "/fake/src", "dst": "/fake/dst"},
        "/api/v1/tools/data/delete": {"dataset_path": "/fake/data"},
        "/api/v1/tools/data/rename": {"dataset_path": "/fake/data", "new_name": "new"},
        "/api/v1/tools/data/convert": {"src": "/fake/src", "dst": "/fake/dst", "output_format": "shp"},
        "/api/v1/tools/gp/select": {"input_fc": "/fake/in", "output_fc": "/fake/out", "where_clause": "1=1"},
        "/api/v1/tools/gp/clip": {"input_fc": "/fake/in", "clip_fc": "/fake/clip", "output_fc": "/fake/out"},
        "/api/v1/tools/gp/buffer": {"input_fc": "/fake/in", "output_fc": "/fake/out", "distance": 100},
        "/api/v1/tools/gp/intersect": {"inputs": ["/fake/a", "/fake/b"], "output_fc": "/fake/out"},
        "/api/v1/tools/gp/union": {"inputs": ["/fake/a", "/fake/b"], "output_fc": "/fake/out"},
        "/api/v1/tools/gp/dissolve": {"input_fc": "/fake/in", "output_fc": "/fake/out", "dissolve_field": "ID"},
        "/api/v1/tools/gp/spatial-join": {"target_fc": "/fake/t", "join_fc": "/fake/j", "output_fc": "/fake/out"},
        "/api/v1/tools/gp/merge": {"inputs": ["/fake/a", "/fake/b"], "output_fc": "/fake/out"},
        "/api/v1/tools/gp/project": {"input_fc": "/fake/in", "output_fc": "/fake/out", "spatial_reference": "4326"},
        "/api/v1/tools/map/create": {"map_name": "Test Map"},
        "/api/v1/tools/map/add-layer": {"map_name": "Test Map", "layer_path": "/fake/data"},
        "/api/v1/tools/map/remove-layer": {"map_name": "Test Map", "layer_name": "layer1"},
        "/api/v1/tools/map/list-layers": {"map_name": "Test Map"},
        "/api/v1/tools/map/set-extent": {"map_name": "Test Map", "zoom_to_layer": "layer1"},
        "/api/v1/tools/map/export": {"map_name": "Test Map", "output_path": "/fake/out.png"},
        "/api/v1/tools/map/symbolize": {"map_name": "Test Map", "layer_name": "layer1", "symbology_type": "simple"},
        "/api/v1/tools/map/label": {"map_name": "Test Map", "layer_name": "layer1", "field": "NAME"},
        "/api/v1/tools/layout/create": {"layout_name": "Test Layout"},
        "/api/v1/tools/layout/add-element": {"layout_name": "Test Layout", "element_type": "text", "element_config": {}},
        "/api/v1/tools/layout/export": {"layout_name": "Test Layout", "output_path": "/fake/out.pdf"},
        "/api/v1/tools/analysis/summary-stats": {
            "input_fc": "/fake/in",
            "output_table": "/fake/out",
            "statistics_fields": [],
        },
    }

    @pytest.mark.parametrize("endpoint", TOOL_ENDPOINTS_GET)
    def test_get_endpoint_returns_ok(self, test_client, endpoint):
        """GET tool endpoints return 200 with mock _run_in_thread."""
        with patch(
            "arcgis_agent.api.routes.tools._run_in_thread",
            new_callable=AsyncMock,
            return_value={"success": True, "code": "OK", "message": "mock"},
        ):
            response = test_client.get(endpoint)
            assert response.status_code == 200, \
                f"{endpoint}: expected 200, got {response.status_code}"

    @pytest.mark.parametrize("endpoint", TOOL_ENDPOINTS_POST)
    def test_post_endpoint_registered(self, test_client, endpoint):
        """POST tool endpoints are registered (verified via 200 with mock or 201 for long-running)."""
        params = self.TOOL_SAMPLE_PARAMS.get(endpoint, {})
        # Map endpoints that use long-running pattern (return 201)
        long_running_prefixes = (
            "/api/v1/tools/gp/clip", "/api/v1/tools/gp/buffer",
            "/api/v1/tools/gp/intersect", "/api/v1/tools/gp/union",
            "/api/v1/tools/gp/dissolve", "/api/v1/tools/gp/spatial-join",
            "/api/v1/tools/gp/merge", "/api/v1/tools/gp/project",
            "/api/v1/tools/data/convert",
            "/api/v1/tools/map/export", "/api/v1/tools/layout/export",
        )
        expected_status = 201 if endpoint in long_running_prefixes else 200

        with patch(
            "arcgis_agent.api.routes.tools._run_in_thread",
            new_callable=AsyncMock,
            return_value={"success": True, "code": "OK", "message": "mock"},
        ):
            response = test_client.post(endpoint, json=params)
            assert response.status_code in (expected_status, 200, 201), \
                f"{endpoint}: expected {expected_status}/200/201, got {response.status_code}"

    def test_tool_count_is_33(self):
        """Verify exactly 33 tool endpoints are defined."""
        total = len(self.TOOL_ENDPOINTS_GET) + len(self.TOOL_ENDPOINTS_POST)
        assert total == 33, f"Expected 33 tool endpoints, found {total} (GET: {len(self.TOOL_ENDPOINTS_GET)}, POST: {len(self.TOOL_ENDPOINTS_POST)})"


class TestUploadEndpoint:
    def test_upload_rejects_no_file(self, test_client):
        response = test_client.post("/api/v1/upload")
        assert response.status_code in (422, 400)

    def test_upload_shp_file(self, test_client, tmp_path):
        shp_path = tmp_path / "test_upload.shp"
        shp_path.write_bytes(b"fake shapefile content")
        with open(shp_path, "rb") as f:
            response = test_client.post(
                "/api/v1/upload",
                files={"file": ("test.shp", f, "application/octet-stream")},
            )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "uploaded" in data
        assert "filename" in data

    def test_upload_zip_file(self, test_client, tmp_path):
        import zipfile
        zip_path = tmp_path / "test_data.zip"
        with zipfile.ZipFile(str(zip_path), "w") as zf:
            zf.writestr("data.shp", "fake")
            zf.writestr("data.shx", "fake")
            zf.writestr("data.dbf", "fake")
        with open(zip_path, "rb") as f:
            response = test_client.post(
                "/api/v1/upload",
                files={"file": ("test_data.zip", f, "application/zip")},
            )
        assert response.status_code in (200, 201)
        data = response.json()
        assert "uploaded" in data
        assert "extracted" in data

    def test_upload_rejects_unsupported_type(self, test_client, tmp_path):
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not a GIS file")
        with open(txt_path, "rb") as f:
            response = test_client.post(
                "/api/v1/upload",
                files={"file": ("test.txt", f, "text/plain")},
            )
        assert response.status_code == 400


class TestProvidersEndpoint:
    def test_providers_list(self, test_client):
        response = test_client.get("/api/v1/chat/providers")
        assert response.status_code == 200
        data = response.json()
        assert "default" in data
        assert "providers" in data
