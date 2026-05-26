"""OpenAI-compatible LLM provider adapter (Phase 7).

Production implementation of ILLMProvider wrapping langchain-openai's ChatOpenAI.
Supports any provider with an OpenAI-compatible chat completions endpoint:
Qwen (通义千问), DeepSeek, OpenAI, and custom deployments.
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from arcgis_agent.adapters.base import ILLMProvider
from arcgis_agent.config import LLMProviderConfig

SYSTEM_PROMPT = """You are a GIS assistant with access to geoprocessing and mapping tools.

## Your capabilities
- Create buffers, clips, intersections, unions, and dissolves
- Export maps to PDF, PNG, and JPEG formats
- Query layer metadata, field names, and feature counts
- Reproject data between coordinate reference systems

## Rules
- When asked to perform a GIS operation, ALWAYS use the appropriate tool.
- If a required parameter is missing, ask the user for clarification.
- After a tool completes, confirm the result with the output path.
- If a tool fails, explain why and suggest alternatives.
- GIS operations can be destructive (overwrite data). Confirm before overwriting.
- Output paths should use ASCII characters only. Use English directory names.
- Respond in the same language as the user's message."""


class OpenAICompatibleProvider(ILLMProvider):
    """Production LLM provider wrapping langchain-openai ChatOpenAI.

    Connects to any OpenAI-compatible API endpoint (Qwen, DeepSeek, etc.)
    by configuring base_url at construction time. Uses lazy initialization:
    the ChatOpenAI client is created on first access to the .llm property.

    Usage:
        config = LLMConfig.from_env().get_provider_config("qwen")
        provider = OpenAICompatibleProvider(config)
        provider.register_tools(ALL_GIS_TOOLS)
        response, tool_log = provider.chat_with_tools("buffer roads 100m")
    """

    def __init__(self, config: LLMProviderConfig) -> None:
        self._config = config
        self._llm: ChatOpenAI | None = None  # lazy init
        self._tools: list[BaseTool] = []

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-initialize ChatOpenAI on first access.

        Follows the same pattern as arcpy lazy import in existing adapters.
        ChatOpenAI validates api_key and base_url on first API call, not at
        construction time.
        """
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self._config.model,
                base_url=self._config.base_url,
                api_key=self._config.api_key,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
            )
        return self._llm

    def register_tools(self, tools: list[BaseTool]) -> None:
        """Register GIS tools with the provider.

        Must be called before chat_with_tools(). Tools are LangChain
        StructuredTool instances from gis_tools.py.
        """
        self._tools = list(tools)

    def chat(
        self,
        user_message: str,
        history: list[BaseMessage] | None = None,
    ) -> AIMessage:
        """Send a chat message and get a text response (no tool calling).

        Used for: greeting, clarification, explanation of results.
        The system prompt is automatically prepended if not already in history.
        """
        messages = list(history) if history else []
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
        messages.append(HumanMessage(content=user_message))
        return self.llm.invoke(messages)

    def chat_with_tools(
        self,
        user_message: str,
        history: list[BaseMessage] | None = None,
        max_iterations: int = 5,
    ) -> tuple[AIMessage, list[dict]]:
        """Execute the full chat-tool-response loop.

        Binds tools to the model, invokes with the user message, and iterates
        through tool calls until either the model returns a text response or
        max_iterations is reached.

        Returns:
            (final_response, tool_call_log) -- the model's final text
            response and a log of all tool invocations for the frontend.

        Raises:
            RuntimeError: If no tools have been registered.
        """
        if not self._tools:
            raise RuntimeError(
                "No tools registered. Call register_tools() before chat_with_tools()."
            )

        llm_with_tools = self.llm.bind_tools(self._tools)
        messages = list(history) if history else []

        # Ensure system prompt is present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
        messages.append(HumanMessage(content=user_message))

        tool_log: list[dict] = []
        iteration = 0
        response = llm_with_tools.invoke(messages)

        while response.tool_calls and iteration < max_iterations:
            iteration += 1
            messages.append(response)

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]

                # Execute tool via dispatch by name
                tool_fn = {t.name: t for t in self._tools}[tool_name]
                try:
                    result = tool_fn.invoke(tool_args)
                    tool_log.append({
                        "name": tool_name,
                        "args": tool_args,
                        "result": str(result),
                        "success": True,
                    })
                except Exception as exc:
                    error_msg = f"Tool '{tool_name}' failed: {exc}"
                    tool_log.append({
                        "name": tool_name,
                        "args": tool_args,
                        "result": error_msg,
                        "success": False,
                    })
                    result = error_msg

                messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                ))

            response = llm_with_tools.invoke(messages)

        messages.append(response)
        return response, tool_log
