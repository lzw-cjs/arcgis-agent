"""Task status schemas for the task execution API."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Execution status of an async GIS task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    """Request to create a new async GIS task."""

    tool_name: str = Field(description="工具名称")
    arguments: dict = Field(default_factory=dict, description="工具参数")


class TaskResult(BaseModel):
    """Result of an async GIS task execution."""

    task_id: str
    status: TaskStatus
    tool_name: str
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: str
    updated_at: str
