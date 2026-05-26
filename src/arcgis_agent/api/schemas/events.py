"""SSE event schemas for streaming progress, tokens, and errors."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProgressEvent(BaseModel):
    """SSE event for tool execution progress updates."""

    event: str = "progress"
    data: dict = Field(description="{percent: float, message: str}")


class TokenEvent(BaseModel):
    """SSE event for streaming LLM token output."""

    event: str = "token"
    data: dict = Field(description="{content: str}")


class ErrorEvent(BaseModel):
    """SSE event for error notifications during streaming."""

    event: str = "error"
    data: dict = Field(description="{code: str, message: str}")
