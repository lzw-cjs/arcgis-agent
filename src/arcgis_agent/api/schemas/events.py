"""SSE 事件 Schema ： 流式传输的进度、token 和错误事件"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProgressEvent(BaseModel):
    """工具执行进度更新事件"""

    event: str = "progress"
    data: dict = Field(description="{percent: float, message: str}")


class TokenEvent(BaseModel):
    """LLM 流式 Token 输出事件"""

    event: str = "token"
    data: dict = Field(description="{content: str}")


class ErrorEvent(BaseModel):
    """流式传输错误通知事件"""

    event: str = "error"
    data: dict = Field(description="{code: str, message: str}")
