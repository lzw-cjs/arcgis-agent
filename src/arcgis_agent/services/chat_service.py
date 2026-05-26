"""Chat service with LLM agent loop (Phase 7).

Handles conversation flow, tool calling, and response generation.
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from arcgis_agent.adapters.mock_llm import MockLLMProvider


TEMPLATE_SUGGESTIONS: dict[str, str] = {
    "_default": "您还可以尝试什么操作？",
    "gp_buffer": "叠加分析：对缓冲区结果进行 intersect 或 union 操作",
    "gp_clip": "叠加分析：对裁剪结果进行空间连接",
    "gp_intersect": "继续分析：导出结果为 shapefile 或 geodatabase",
    "map_export": "继续优化：调整符号化配色方案",
}


class ChatService:
    """Chat service wrapping an LLM provider with conversation state.

    Manages the agent loop: receive message → call LLM → parse tool calls →
    execute tools → return results.
    """

    def __init__(
        self,
        llm_provider: Any = None,
        store: Any = None,
    ) -> None:
        self._llm = llm_provider or MockLLMProvider()
        self._store = store

    async def stream_chat(
        self, session_id: str, message: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat responses as SSE events.

        Yields dicts with format: {"event": "token"|"done", "data": ...}
        """
        # Get LLM response
        result = self._llm.chat(message)
        response_text = getattr(result, "content", str(result))

        # Yield token events (simulated — in production this would stream tokens)
        for word in response_text.split():
            yield {"event": "token", "data": word}
            # In production: await asyncio.sleep(0)

        # Always end with done event
        yield {
            "event": "done",
            "data": {
                "session_id": session_id,
                "response": response_text,
            },
        }

    def _get_suggestions(self, tool_log: list[dict[str, Any]]) -> list[str]:
        """Generate follow-up suggestions based on tool execution results.

        Returns up to 3 suggestions matching the executed tools.
        """
        if not tool_log:
            return [TEMPLATE_SUGGESTIONS["_default"]]

        suggestions: list[str] = []
        seen: set[str] = set()
        for entry in tool_log:
            tool_name = entry.get("name", "")
            if tool_name in TEMPLATE_SUGGESTIONS and tool_name not in seen:
                suggestions.append(TEMPLATE_SUGGESTIONS[tool_name])
                seen.add(tool_name)

        if not suggestions:
            suggestions.append(TEMPLATE_SUGGESTIONS["_default"])

        # Cap at 3 suggestions
        return suggestions[:3]
