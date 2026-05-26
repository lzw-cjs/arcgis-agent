"""LLM provider adapter using OpenAI-compatible API (Phase 7).

Supports any provider with an OpenAI-compatible chat completions endpoint.
"""
from __future__ import annotations

from typing import Any

from arcgis_agent.config import LLMProviderConfig


class OpenAICompatibleProvider:
    """LLM provider using OpenAI-compatible chat completions API.

    Uses lazy initialization: the underlying LLM client is created
    on first access to the .llm property (or on first chat call).
    """

    def __init__(self, config: LLMProviderConfig) -> None:
        self._config = config
        self._llm: Any = None
        self._tools: list = []

    def register_tools(self, tools: list) -> None:
        """Register GIS tools available for function calling."""
        self._tools = list(tools)
