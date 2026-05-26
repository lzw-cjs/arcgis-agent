"""Tests for Pydantic schemas (chat/tasks/events) and pyproject.toml.

Task 2: Schemas + pyproject.toml update (07-01)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError


# ── Tests: ChatRequest ──────────────────────────────────────────


class TestChatRequest:
    """ChatRequest validates session_id, message, and stream fields."""

    def test_valid_request(self):
        """Valid ChatRequest with required fields should pass."""
        from arcgis_agent.api.schemas.chat import ChatRequest

        req = ChatRequest(session_id="abc-123", message="hello")
        assert req.session_id == "abc-123"
        assert req.message == "hello"
        assert req.stream is True  # default

    def test_session_id_is_required(self):
        """session_id must be provided."""
        from arcgis_agent.api.schemas.chat import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(message="hello")  # type: ignore[call-arg]

    def test_message_is_required(self):
        """message must be provided."""
        from arcgis_agent.api.schemas.chat import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(session_id="abc")  # type: ignore[call-arg]

    def test_stream_defaults_to_true(self):
        """stream field defaults to True when not specified."""
        from arcgis_agent.api.schemas.chat import ChatRequest

        req = ChatRequest(session_id="abc", message="hello")
        assert req.stream is True

    def test_stream_can_be_set_to_false(self):
        """stream field can be explicitly set to False."""
        from arcgis_agent.api.schemas.chat import ChatRequest

        req = ChatRequest(session_id="abc", message="hello", stream=False)
        assert req.stream is False


# ── Tests: ToolCallEvent ────────────────────────────────────────


class TestToolCallEvent:
    """ToolCallEvent carries tool call event type and data."""

    def test_tool_call_event_fields(self):
        """ToolCallEvent has event and data fields."""
        from arcgis_agent.api.schemas.chat import ToolCallEvent

        evt = ToolCallEvent(event="tool_start", data={"tool": "buffer"})
        assert evt.event == "tool_start"
        assert evt.data == {"tool": "buffer"}


# ── Tests: TaskStatus ───────────────────────────────────────────


class TestTaskStatus:
    """TaskStatus enum contains expected values."""

    def test_has_pending(self):
        from arcgis_agent.api.schemas.tasks import TaskStatus

        assert TaskStatus.PENDING.value == "pending"

    def test_has_running(self):
        from arcgis_agent.api.schemas.tasks import TaskStatus

        assert TaskStatus.RUNNING.value == "running"

    def test_has_completed(self):
        from arcgis_agent.api.schemas.tasks import TaskStatus

        assert TaskStatus.COMPLETED.value == "completed"

    def test_has_failed(self):
        from arcgis_agent.api.schemas.tasks import TaskStatus

        assert TaskStatus.FAILED.value == "failed"


# ── Tests: TaskCreate ───────────────────────────────────────────


class TestTaskCreate:
    """TaskCreate validates tool_name and arguments."""

    def test_valid_task_create(self):
        """Valid TaskCreate with required tool_name."""
        from arcgis_agent.api.schemas.tasks import TaskCreate

        task = TaskCreate(tool_name="gp_buffer", arguments={"distance": 100})
        assert task.tool_name == "gp_buffer"
        assert task.arguments == {"distance": 100}

    def test_tool_name_is_required(self):
        """tool_name must be provided."""
        from arcgis_agent.api.schemas.tasks import TaskCreate

        with pytest.raises(ValidationError):
            TaskCreate()  # type: ignore[call-arg]

    def test_arguments_defaults_to_empty_dict(self):
        """arguments defaults to {} when not specified."""
        from arcgis_agent.api.schemas.tasks import TaskCreate

        task = TaskCreate(tool_name="gp_buffer")
        assert task.arguments == {}


# ── Tests: TaskResult ───────────────────────────────────────────


class TestTaskResult:
    """TaskResult carries full task execution state."""

    def test_task_result_fields(self):
        """TaskResult has all expected fields with defaults."""
        from arcgis_agent.api.schemas.tasks import TaskResult, TaskStatus

        result = TaskResult(
            task_id="t1",
            status=TaskStatus.PENDING,
            tool_name="gp_buffer",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert result.task_id == "t1"
        assert result.status == TaskStatus.PENDING
        assert result.tool_name == "gp_buffer"
        assert result.result is None
        assert result.error is None
        assert result.progress == 0.0

    def test_progress_constrained_0_to_100(self):
        """progress must be between 0 and 100."""
        from arcgis_agent.api.schemas.tasks import TaskResult, TaskStatus

        with pytest.raises(ValidationError):
            TaskResult(
                task_id="t1",
                status=TaskStatus.PENDING,
                tool_name="gp_buffer",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-01T00:00:00Z",
                progress=150.0,
            )


# ── Tests: ProgressEvent ────────────────────────────────────────


class TestProgressEvent:
    """ProgressEvent carries progress data for SSE streaming."""

    def test_progress_event_default(self):
        """ProgressEvent has event="progress" by default."""
        from arcgis_agent.api.schemas.events import ProgressEvent

        evt = ProgressEvent(data={"percent": 50.0, "message": "Processing..."})
        assert evt.event == "progress"
        assert evt.data == {"percent": 50.0, "message": "Processing..."}


# ── Tests: TokenEvent ───────────────────────────────────────────


class TestTokenEvent:
    """TokenEvent carries streaming token data."""

    def test_token_event_default(self):
        """TokenEvent has event="token" by default."""
        from arcgis_agent.api.schemas.events import TokenEvent

        evt = TokenEvent(data={"content": "Hello"})
        assert evt.event == "token"
        assert evt.data == {"content": "Hello"}


# ── Tests: ErrorEvent ───────────────────────────────────────────


class TestErrorEvent:
    """ErrorEvent carries error data for SSE streaming."""

    def test_error_event_default(self):
        """ErrorEvent has event="error" by default."""
        from arcgis_agent.api.schemas.events import ErrorEvent

        evt = ErrorEvent(data={"code": "ERR-01", "message": "Something went wrong"})
        assert evt.event == "error"
        assert evt.data == {"code": "ERR-01", "message": "Something went wrong"}


# ── Tests: pyproject.toml ───────────────────────────────────────


class TestPyprojectToml:
    """pyproject.toml contains required dependencies and entry points."""

    @pytest.fixture
    def pyproject_path(self) -> Path:
        """Path to the project's pyproject.toml."""
        return Path(__file__).parent.parent.parent / "pyproject.toml"

    @pytest.fixture
    def pyproject_content(self, pyproject_path: Path) -> str:
        """Read pyproject.toml content."""
        return pyproject_path.read_text(encoding="utf-8")

    def test_has_arcgis_agent_web_entry_point(self, pyproject_content: str):
        """pyproject.toml contains arcgis-agent-web entry point."""
        assert "arcgis-agent-web" in pyproject_content

    def test_has_fastapi_dependency(self, pyproject_content: str):
        """pyproject.toml contains fastapi dependency."""
        assert "fastapi" in pyproject_content

    def test_has_uvicorn_dependency(self, pyproject_content: str):
        """pyproject.toml contains uvicorn dependency."""
        assert "uvicorn" in pyproject_content

    def test_has_python_multipart_dependency(self, pyproject_content: str):
        """pyproject.toml contains python-multipart dependency."""
        assert "python-multipart" in pyproject_content

    def test_has_sse_starlette_dependency(self, pyproject_content: str):
        """pyproject.toml contains sse-starlette dependency."""
        assert "sse-starlette" in pyproject_content
