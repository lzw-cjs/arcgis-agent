"""Chat request/response schemas for the conversational API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    session_id: str = Field(description="会话ID，前端生成UUID")
    message: str = Field(description="用户消息内容")
    stream: bool = Field(default=True, description="是否SSE流式响应")


class ToolCallEvent(BaseModel):
    """Tool call notification for SSE streaming."""

    event: str = Field(description="事件类型: tool_start, tool_end")
    data: dict = Field(description="工具调用数据")
