"""对话请求/响应 Schema"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """来自前端的对话消息"""

    session_id: str = Field(description="会话ID，前端生成UUID")
    message: str = Field(description="用户消息内容")
    stream: bool = Field(default=True, description="是否SSE流式响应")


class ToolCallEvent(BaseModel):
    """SSE 流式工具调用通知"""

    event: str = Field(description="事件类型: tool_start, tool_end")
    data: dict = Field(description="工具调用数据")
