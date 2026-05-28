"""任务状态 Schema"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """异步 GIS 任务执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    """创建新异步 GIS 任务的请求"""

    tool_name: str = Field(description="工具名称")
    arguments: dict = Field(default_factory=dict, description="工具参数")


class TaskResult(BaseModel):
    """异步 GIS 任务执行结果"""

    task_id: str
    status: TaskStatus
    tool_name: str
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: str
    updated_at: str
