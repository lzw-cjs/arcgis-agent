"""Mock LLM provider for testing and offline development (Phase 7).

Provides canned responses mimicking an LLM without requiring an API key.
Implements ILLMProvider ABC for drop-in replacement in tests.
"""
from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage

from arcgis_agent.adapters.base import ILLMProvider


class MockLLMProvider(ILLMProvider):
    """Mock LLM provider returning preset responses.

    Does NOT call any external API. Responses are configured via the
    `responses` dict passed to __init__.

    Usage:
        provider = MockLLMProvider(responses={
            "chat": "Mock response for simple chat",
            "final": "Operation completed (mock).",
            "tool_log": [
                {"name": "gp_buffer", "args": {"distance": 100}, "result": "Buffer OK", "success": True},
            ],
        })
        response = provider.chat("hello")
        response, log = provider.chat_with_tools("buffer roads")
    """

    def __init__(self, responses: dict | None = None) -> None:
        self._responses = responses or {}
        self._tools: list = []
        self._call_count = 0

    def register_tools(self, tools: list) -> None:
        """Register GIS tools (stored for test assertions, not called)."""
        self._tools = list(tools)

    def chat(
        self,
        user_message: str,
        history: list[BaseMessage] | None = None,
    ) -> AIMessage:
        """Return a canned response for the given message.

        Returns the value of self._responses["chat"] if configured,
        otherwise a default message including the user input.
        """
        self._call_count += 1
        msg = self._responses.get("chat", "Mock response for: " + user_message)
        return AIMessage(content=msg)

    def chat_with_tools(
        self,
        user_message: str,
        history: list[BaseMessage] | None = None,
        max_iterations: int = 5,
    ) -> tuple[AIMessage, list[dict]]:
        """Return a canned (response, tool_log) tuple.

        Uses self._responses["tool_log"] for the tool execution log and
        self._responses["final"] for the final text response.
        """
        self._call_count += 1
        tool_log: list[dict] = self._responses.get("tool_log", [])
        msg = self._responses.get("final", "Operation completed (mock).")
        return AIMessage(content=msg), tool_log
