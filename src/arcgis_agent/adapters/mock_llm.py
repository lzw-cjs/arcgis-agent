"""Mock LLM provider for testing and offline development (Phase 7).

Provides canned responses mimicking an LLM without requiring an API key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MockMessage:
    """Minimal message class mimicking LangChain AIMessage."""

    content: str


class MockLLMProvider:
    """Mock LLM provider returning canned GIS responses."""

    def __init__(self) -> None:
        self._tools: list = []
        self._responses: dict[str, Any] = {}

    def chat(self, message: str) -> MockMessage:
        """Return a canned response for the given message."""
        if not message:
            return MockMessage(content="请提供具体的GIS操作需求")
        return MockMessage(content=f"收到您的请求：{message}。我将使用GIS工具为您处理。")

    def register_tools(self, tools: list) -> None:
        """Register GIS tools available for function calling."""
        self._tools = list(tools)

    def chat_with_tools(self, message: str) -> tuple[MockMessage, list]:
        """Process a message with available tools and return (response, tool_log)."""
        tool_log: list[dict[str, Any]] = []
        response_content = f"处理请求：{message}"

        if self._tools:
            # Simulate tool usage for GIS-related keywords
            tool_names = [getattr(t, "name", str(t)) for t in self._tools]
            if "buffer" in message.lower():
                tool_log.append({
                    "name": "gp_buffer",
                    "success": True,
                    "args": {"distance": 100},
                    "result": "缓冲区分析完成",
                })
                response_content = "已完成缓冲区分析。"
            elif any(kw in message.lower() for kw in ("clip", "裁剪", "intersect", "叠加")):
                tool_log.append({
                    "name": "gp_clip",
                    "success": True,
                    "args": {},
                    "result": "裁剪操作完成",
                })
                response_content = "已完成裁剪操作。"

        return MockMessage(content=response_content), tool_log
