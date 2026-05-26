"""Chat service with LLM agent loop (Phase 7, Plan 07-04).

Orchestrates the full agent loop: receive message -> LLM call -> tool detection ->
tool execution -> result feedback -> final response. Provides streaming SSE events
for the frontend via FastAPI EventSourceResponse.

Key design decisions:
- chat_with_tools() runs via asyncio.to_thread() for arcpy thread safety
- Context management uses langchain trim_messages (fallback: system + last 15)
- Template suggestions (D-27) based on last successful tool execution
- SSE event types: token, tool_start, tool_end, suggestions, error, done
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import AsyncGenerator

from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

from arcgis_agent.adapters.base import ILLMProvider
from arcgis_agent.adapters.gis_tools import ALL_GIS_TOOLS
from arcgis_agent.api.dependencies import ConversationStore
from arcgis_agent.config import LLMConfig

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5
MAX_CONTEXT_TOKENS = 80_000

# ══ Template Suggestions (D-27) ══
# Each tool execution success returns a Chinese template suggestion
# based on the tool name, guiding the user to next logical operations.
TEMPLATE_SUGGESTIONS: dict[str, str] = {
    "gp_buffer": "是否需要对这个缓冲区做叠加分析？",
    "gp_clip": "是否需要查看裁剪后的属性表？",
    "gp_intersect": "是否需要导出求交结果为地图？",
    "gp_union": "是否需要对合并结果做融合处理？",
    "gp_dissolve": "是否需要对比融合前后的数据？",
    "gp_select": "是否需要对筛选结果做空间分析？",
    "gp_project": "是否需要导出投影变换后的数据？",
    "map_export": "是否需要调整符号化？",
    "data_convert": "是否需要对新格式的数据做空间分析？",
    "data_copy": "是否需要对复制的数据做处理？",
    # Generic fallback when no specific tool matches
    "_default": "是否需要对结果做进一步分析？",
}


class ChatService:
    """Chat service wrapping an LLM provider with conversation state.

    Manages the agent loop: receive message -> call LLM -> parse tool calls ->
    execute tools -> return results. Uses asyncio.to_thread() for arcpy thread
    safety when calling the synchronous chat_with_tools() provider method.

    Usage:
        config = LLMConfig.from_env()
        provider = OpenAICompatibleProvider(config.get_provider_config())
        service = ChatService(llm_provider=provider, store=ConversationStore())
        async for event in service.stream_chat("session-id", "user message"):
            # event = {"event": "token", "data": {"content": "..."}}
            pass
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        store: ConversationStore | None = None,
        llm_config: LLMConfig | None = None,
    ):
        """Initialize the chat service.

        Args:
            llm_provider: LLM provider implementing ILLMProvider (required).
            store: ConversationStore for session history (auto-created if None).
            llm_config: LLM configuration (loaded from env if None).
        """
        self._provider = llm_provider
        self._store = store or ConversationStore()
        self._config = llm_config or LLMConfig.from_env()
        self._provider.register_tools(ALL_GIS_TOOLS)

    async def stream_chat(
        self, session_id: str, user_message: str
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response via SSE events.

        Yields SSE events as dicts: {event: str, data: dict}
        Event types: token, tool_start, tool_end, suggestions, error, done

        Arcpy thread safety: chat_with_tools() runs via asyncio.to_thread()
        to prevent blocking the FastAPI event loop and to execute arcpy COM
        calls on a thread pool thread (sharing _ARC_LOCK from dependencies.py).
        """
        try:
            # 1. Load or create history
            history = self._store.get(session_id)

            # 2. Context management: trim if too long
            if len(history) > 20:
                history = self._manage_context(history)

            # 3. Guardrail: detect Chinese characters in user message
            self._check_chinese_path(user_message)

            # 4. Run agent loop in thread pool for arcpy thread safety
            #    chat_with_tools() is synchronous (calls llm.invoke() +
            #    tool.invoke() -> Service -> arcpy). Running via
            #    asyncio.to_thread() prevents blocking the event loop and
            #    ensures arcpy COM calls execute on a proper thread.
            response, tool_log = await asyncio.to_thread(
                self._provider.chat_with_tools,
                user_message,
                history,
                MAX_TOOL_ITERATIONS,
            )

            # 5. Emit tool execution events
            for tc in tool_log:
                yield {
                    "event": "tool_start",
                    "data": {"name": tc["name"], "args": tc["args"]},
                }
                yield {
                    "event": "tool_end",
                    "data": {
                        "name": tc["name"],
                        "success": tc["success"],
                        "result": str(tc.get("result", ""))[:500],  # truncate
                    },
                }

            # 6. Update conversation history
            updated_history = self._build_updated_history(
                history, user_message, response, tool_log
            )
            self._store.update(session_id, updated_history)

            # 7. Stream final text response token by token
            full_text = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            # For SSE streaming of text tokens, yield in chunks
            chunk_size = 50
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i : i + chunk_size]
                yield {
                    "event": "token",
                    "data": {"content": chunk},
                }
                await asyncio.sleep(0.01)  # yield to event loop

            # 8. Suggestions based on last successfully executed tool
            suggestions = self._get_suggestions(tool_log)
            if suggestions:
                yield {
                    "event": "suggestions",
                    "data": {"items": suggestions},
                }

            # 9. Done
            yield {
                "event": "done",
                "data": {
                    "tool_calls": len(tool_log),
                    "message_id": getattr(response, "id", ""),
                },
            }

        except Exception as exc:
            logger.exception("ChatService error: %s", exc)
            yield {
                "event": "error",
                "data": {"code": "CHAT_ERROR", "message": str(exc)},
            }

    # ══ Internal Methods ══

    def _build_updated_history(
        self,
        history: list[BaseMessage],
        user_message: str,
        response: AIMessage,
        tool_log: list[dict],
    ) -> list[BaseMessage]:
        """Build the new history list after a chat turn.

        Appends the user message and final response to the existing history.
        Intermediate messages (tool calls, tool results) are handled by
        chat_with_tools() internally and not stored here.

        Args:
            history: Existing conversation history (may be empty).
            user_message: The user's input text.
            response: The final AIMessage from the LLM.
            tool_log: Tool execution log (used to count tool calls only).

        Returns:
            Updated message list for storage.
        """
        new_history = list(history) if history else []
        new_history.append(HumanMessage(content=user_message))
        return new_history

    def _manage_context(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """Trim conversation history to fit context window.

        Uses langchain's trim_messages with 'last' strategy to keep the most
        recent messages within MAX_CONTEXT_TOKENS. Falls back to keeping
        system message + last 15 messages if trim_messages fails.

        Args:
            messages: Full conversation history.

        Returns:
            Trimmed message list fitting within the context window.
        """
        try:
            return trim_messages(
                messages,
                strategy="last",
                token_counter=count_tokens_approximately,
                max_tokens=MAX_CONTEXT_TOKENS,
                start_on="human",
                end_on=("human", "tool"),
                include_system=True,
            )
        except Exception:
            # Fallback: keep system + last 15 messages
            return [
                m for m in messages if isinstance(m, SystemMessage)
            ] + messages[-15:]

    def _get_suggestions(self, tool_log: list[dict]) -> list[str]:
        """Get template suggestions based on the last successfully executed tool.

        Scans the tool_log in reverse order and returns Chinese template
        suggestions for each unique successfully executed tool.

        Args:
            tool_log: List of tool call records with name, args, result, success.

        Returns:
            List of suggestion strings (max 3).
        """
        suggestions: list[str] = []
        seen: set[str] = set()
        for tc in reversed(tool_log):
            if tc.get("success"):
                tool_name = tc["name"]
                if tool_name in TEMPLATE_SUGGESTIONS and tool_name not in seen:
                    suggestions.append(TEMPLATE_SUGGESTIONS[tool_name])
                    seen.add(tool_name)
        if not suggestions:
            suggestions.append(TEMPLATE_SUGGESTIONS["_default"])
        return suggestions[:3]  # Max 3 suggestions

    def _check_chinese_path(self, text: str) -> None:
        """Guardrail: log WARNING if text contains Chinese characters.

        Chinese characters in file paths are a known issue with arcpy
        (especially arcpy.mp). This guardrail does NOT block execution --
        it only logs a warning to help with debugging.

        Args:
            text: The user message or any text to check.
        """
        if re.search(r"[一-鿿]", text):
            logger.warning(
                "Chinese characters detected in input. "
                "This may cause issues with arcpy (known bug with Chinese "
                "usernames/paths). If operations fail, try using ASCII-only paths."
            )
