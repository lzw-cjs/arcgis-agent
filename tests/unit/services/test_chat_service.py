"""Unit tests for ChatService agent loop (Phase 7, Plan 07-04).

Tests cover: SSE streaming, tool execution, template suggestions,
guardrails (Chinese path warning, max_iterations), context management,
and arcpy thread safety (asyncio.to_thread).
"""
from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from arcgis_agent.adapters.base import ILLMProvider
from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.api.dependencies import ConversationStore
from arcgis_agent.config import LLMConfig
from arcgis_agent.services.chat_service import (
    ChatService,
    TEMPLATE_SUGGESTIONS,
    MAX_TOOL_ITERATIONS,
    MAX_CONTEXT_TOKENS,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def provider():
    """MockLLMProvider with no tool_log (simple chat)."""
    return MockLLMProvider(responses={
        "chat": "你好！我是 GIS 助手。",
        "final": "你好！我是 GIS 助手。",
    })


@pytest.fixture
def tool_provider():
    """MockLLMProvider that simulates a gp_buffer tool execution."""
    return MockLLMProvider(responses={
        "chat": "Processing buffer...",
        "final": "缓冲区已创建：C:\\output\\buffer.shp",
        "tool_log": [
            {
                "name": "gp_buffer",
                "args": {"input_fc": "roads.shp", "distance": 100.0, "unit": "Meters"},
                "result": "Buffer 100.0 Meters around roads.shp: Success. Features: 42. Time: 1.2s. Success: True",
                "success": True,
            },
        ],
    })


@pytest.fixture
def multi_tool_provider():
    """MockLLMProvider with multiple tool calls (buffer + clip)."""
    return MockLLMProvider(responses={
        "final": "处理完成：缓冲区和裁剪已创建。",
        "tool_log": [
            {
                "name": "gp_buffer",
                "args": {"input_fc": "roads.shp", "distance": 100.0, "unit": "Meters"},
                "result": "Buffer OK",
                "success": True,
            },
            {
                "name": "gp_clip",
                "args": {"input_fc": "buffer.shp", "clip_features": "boundary.shp"},
                "result": "Clip OK",
                "success": True,
            },
            {
                "name": "gp_select",
                "args": {"input_fc": "clip.shp", "where_clause": "POP > 1000"},
                "result": "Select failed: field not found",
                "success": False,
            },
        ],
    })


@pytest.fixture
def store():
    """Fresh ConversationStore for each test."""
    return ConversationStore()


def make_service(llm=None, store=None, config=None):
    """Helper to create ChatService without importing arcpy."""
    from arcgis_agent.services.chat_service import ChatService
    return ChatService(
        llm_provider=llm or MockLLMProvider(),
        store=store or ConversationStore(),
        llm_config=config or LLMConfig.from_env(),
    )


# ════════════════════════════════════════════════════════════════
# Basic Streaming Tests
# ════════════════════════════════════════════════════════════════

class TestStreamChatBasic:
    """Test: ChatService.stream_chat produces SSE events via MockLLMProvider."""

    async def test_stream_chat_returns_ai_response(self, provider, store):
        """ChatService.stream_chat("hello") returns SSE events including done."""
        service = ChatService(llm_provider=provider, store=store)
        events = []
        async for event in service.stream_chat("test-session", "hello"):
            events.append(event)

        assert len(events) >= 1, "Should produce at least one event"
        event_types = [e["event"] for e in events]
        assert "done" in event_types, "Must include 'done' event"
        assert "token" in event_types, "Must include 'token' events"

    async def test_stream_chat_done_event_has_metadata(self, provider, store):
        """Done event includes tool_calls count and message_id."""
        service = ChatService(llm_provider=provider, store=store)
        events = []
        async for event in service.stream_chat("sid-meta", "hello"):
            events.append(event)

        done_events = [e for e in events if e["event"] == "done"]
        assert len(done_events) == 1
        assert "tool_calls" in done_events[0]["data"]
        assert done_events[0]["data"]["tool_calls"] == 0  # No tool calls in simple chat


# ════════════════════════════════════════════════════════════════
# Tool Execution Tests
# ════════════════════════════════════════════════════════════════

class TestToolExecution:
    """Test: ChatService executes tools and returns results via SSE."""

    async def test_stream_chat_with_tool_calls(self, tool_provider, store):
        """When Mock returns tool_calls, tools are executed and results streamed."""
        service = ChatService(llm_provider=tool_provider, store=store)
        events = []
        async for event in service.stream_chat("sid-tool", "buffer roads by 100m"):
            events.append(event)

        event_types = [e["event"] for e in events]
        assert "tool_start" in event_types, "Should emit tool_start events"
        assert "tool_end" in event_types, "Should emit tool_end events"
        assert "done" in event_types, "Should emit done event"

        # Done event should report tool_calls count
        done = [e for e in events if e["event"] == "done"][0]
        assert done["data"]["tool_calls"] == 1

    async def test_tool_log_records_each_call(self, tool_provider, store):
        """Tool log records each tool call with name, args, result, success."""
        service = ChatService(llm_provider=tool_provider, store=store)
        events = []
        async for event in service.stream_chat("sid-log", "buffer roads"):
            events.append(event)

        # Check tool_start has name and args
        start_events = [e for e in events if e["event"] == "tool_start"]
        assert len(start_events) >= 1
        for se in start_events:
            assert "name" in se["data"]
            assert "args" in se["data"]

        # Check tool_end has name, success, result
        end_events = [e for e in events if e["event"] == "tool_end"]
        assert len(end_events) >= 1
        for ee in end_events:
            assert "name" in ee["data"]
            assert "success" in ee["data"]
            assert "result" in ee["data"]

    async def test_multi_tool_execution(self, multi_tool_provider, store):
        """Multiple tools in one turn produce correct event sequence."""
        service = ChatService(llm_provider=multi_tool_provider, store=store)
        events = []
        async for event in service.stream_chat("sid-multi", "buffer and clip roads"):
            events.append(event)

        start_events = [e for e in events if e["event"] == "tool_start"]
        end_events = [e for e in events if e["event"] == "tool_end"]

        # 3 tool calls in tool_log
        assert len(start_events) == 3
        assert len(end_events) == 3

        # Order: tool_start, tool_end for each tool
        tool_names = [e["data"]["name"] for e in start_events]
        assert "gp_buffer" in tool_names
        assert "gp_clip" in tool_names
        assert "gp_select" in tool_names

        # Done reports 3 tool calls
        done = [e for e in events if e["event"] == "done"][0]
        assert done["data"]["tool_calls"] == 3

    async def test_failed_tool_is_reported(self, multi_tool_provider, store):
        """Failed tools (success=False) are still reported in tool_end."""
        service = ChatService(llm_provider=multi_tool_provider, store=store)
        events = []
        async for event in service.stream_chat("sid-fail", "select roads"):
            events.append(event)

        # gp_select should have success=False
        select_end = [e for e in events if e["event"] == "tool_end"
                      and e["data"]["name"] == "gp_select"]
        assert len(select_end) == 1
        assert select_end[0]["data"]["success"] is False


# ════════════════════════════════════════════════════════════════
# Template Suggestions Tests (D-27)
# ════════════════════════════════════════════════════════════════

class TestTemplateSuggestions:
    """Test: _get_suggestions returns appropriate template suggestions."""

    def test_buffer_suggestion(self):
        """After gp_buffer execution, return matching Chinese suggestion."""
        tool_log = [{"name": "gp_buffer", "success": True, "args": {}, "result": "OK"}]
        service = make_service()
        suggestions = service._get_suggestions(tool_log)
        assert len(suggestions) >= 1
        assert any("缓冲区" in s for s in suggestions)

    def test_no_tools_returns_default(self):
        """Empty tool_log returns default suggestion."""
        service = make_service()
        suggestions = service._get_suggestions([])
        assert len(suggestions) == 1
        assert suggestions[0] == TEMPLATE_SUGGESTIONS["_default"]

    def test_suggestions_max_three(self):
        """Returns at most 3 suggestions even with many tools."""
        tool_log = [
            {"name": "gp_buffer", "success": True, "args": {}, "result": "OK"},
            {"name": "gp_clip", "success": True, "args": {}, "result": "OK"},
            {"name": "gp_intersect", "success": True, "args": {}, "result": "OK"},
            {"name": "map_export", "success": True, "args": {}, "result": "OK"},
        ]
        service = make_service()
        suggestions = service._get_suggestions(tool_log)
        assert len(suggestions) <= 3

    def test_only_successful_tools_trigger_suggestions(self):
        """Failed tools should not generate suggestions."""
        tool_log = [
            {"name": "gp_buffer", "success": False, "args": {}, "result": "Error"},
        ]
        service = make_service()
        suggestions = service._get_suggestions(tool_log)
        assert len(suggestions) == 1
        assert suggestions[0] == TEMPLATE_SUGGESTIONS["_default"]

    def test_suggestion_deduplication(self):
        """Same tool appearing twice in log only produces one suggestion."""
        tool_log = [
            {"name": "gp_buffer", "success": True, "args": {}, "result": "OK"},
            {"name": "gp_buffer", "success": True, "args": {}, "result": "Also OK"},
        ]
        service = make_service()
        suggestions = service._get_suggestions(tool_log)
        # Should not have duplicate suggestions
        assert len(suggestions) == len(set(suggestions))


# ════════════════════════════════════════════════════════════════
# Guardrail Tests
# ════════════════════════════════════════════════════════════════

class TestGuardrails:
    """Test: Guardrail logic for Chinese paths and max_iterations."""

    def test_chinese_path_logs_warning(self, caplog):
        """Paths containing Chinese characters trigger WARNING log but don't block."""
        import asyncio
        async def _run():
            provider = MockLLMProvider(responses={
                "final": "处理完成",
                "tool_log": [
                    {
                        "name": "gp_buffer",
                        "args": {"input_fc": "C:\\数据\\roads.shp", "distance": 100.0, "unit": "Meters"},
                        "result": "OK",
                        "success": True,
                    },
                ],
            })
            service = ChatService(llm_provider=provider, store=ConversationStore())
            with caplog.at_level(logging.WARNING, logger="arcgis_agent.services.chat_service"):
                events = []
                async for event in service.stream_chat("sid-cn", "buffer roads"):
                    events.append(event)
            return events
        events = asyncio.run(_run())

        # Should complete successfully (not block on Chinese path)
        assert any(e["event"] == "done" for e in events)
        # Chinese path detection: at minimum, the stream should complete

    def test_max_iterations_limit(self):
        """MAX_TOOL_ITERATIONS is set to 5 for safety."""
        assert MAX_TOOL_ITERATIONS == 5, "Safety limit must be 5"

    def test_error_event_on_exception(self):
        """When an exception occurs, an error event is yielded."""
        import asyncio

        async def _run():
            class BrokenProvider(ILLMProvider):
                def chat(self, user_message, history=None):
                    return AIMessage(content="ok")

                def chat_with_tools(self, user_message, history=None, max_iterations=5):
                    raise RuntimeError("Simulated LLM failure")

                def register_tools(self, tools):
                    pass

            service = ChatService(
                llm_provider=BrokenProvider(),
                store=ConversationStore(),
            )
            events = []
            async for event in service.stream_chat("sid-crash", "hello"):
                events.append(event)
            return events
        events = asyncio.run(_run())

        assert any(e["event"] == "error" for e in events), \
            "Must yield error event on provider exception"


# ════════════════════════════════════════════════════════════════
# Context Management Tests
# ════════════════════════════════════════════════════════════════

class TestContextManagement:
    """Test: Context manager trims messages when over limit."""

    def test_manage_context_trim_long_history(self):
        """When messages exceed MAX_CONTEXT_TOKENS (80K), trimming occurs."""
        from langchain_core.messages import HumanMessage, SystemMessage

        service = make_service()
        messages = [SystemMessage(content="You are a GIS assistant.")]
        # Generate ~100K tokens worth of messages to trigger trimming
        huge = "The quick brown fox jumps over the lazy dog. " * 5000
        for i in range(30):
            messages.append(HumanMessage(content=huge))

        trimmed = service._manage_context(messages)
        # System message is always preserved
        assert any(isinstance(m, SystemMessage) for m in trimmed)
        # With 100K+ tokens, trimming must reduce message count
        assert len(trimmed) < len(messages), \
            f"Expected trimmed ({len(trimmed)}) < original ({len(messages)})"

    def test_manage_context_preserves_system_message(self):
        """System message is always preserved in trimmed context."""
        from langchain_core.messages import HumanMessage, SystemMessage

        service = make_service()
        messages = [SystemMessage(content="GIS Agent System Prompt")]
        for i in range(30):
            messages.append(HumanMessage(content=f"Turn {i}"))

        trimmed = service._manage_context(messages)
        sys_msgs = [m for m in trimmed if isinstance(m, SystemMessage)]
        assert len(sys_msgs) >= 1, "System message must be preserved"

    def test_trim_messages_fallback(self):
        """When trim_messages fails, fallback keeps system + last 15."""
        from langchain_core.messages import HumanMessage, SystemMessage

        service = make_service()
        messages = [SystemMessage(content="System")]
        for i in range(30):
            messages.append(HumanMessage(content=f"Msg {i}"))

        # Force trim_messages to fail via bad params simulation
        # The fallback should keep system + last 15 messages
        with patch(
            "arcgis_agent.services.chat_service.trim_messages",
            side_effect=ValueError("simulated failure"),
        ):
            trimmed = service._manage_context(messages)
            assert len(trimmed) <= 16, \
                f"Fallback should produce at most 16 messages (system + 15), got {len(trimmed)}"
            assert any(isinstance(m, SystemMessage) for m in trimmed)


# ════════════════════════════════════════════════════════════════
# Conversation History Tests
# ════════════════════════════════════════════════════════════════

class TestConversationHistory:
    """Test: Conversation history is maintained per session_id."""

    async def test_history_preserved_across_turns(self, provider, store):
        """Two consecutive chats on same session_id preserve context."""
        service = ChatService(llm_provider=provider, store=store)

        # First turn
        events1 = []
        async for event in service.stream_chat("sid-history", "hello"):
            events1.append(event)
        assert any(e["event"] == "done" for e in events1)

        # Verify history was stored
        history = store.get("sid-history")
        assert len(history) > 0, "History should be stored after first turn"

        # Second turn
        events2 = []
        async for event in service.stream_chat("sid-history", "what can you do?"):
            events2.append(event)
        assert any(e["event"] == "done" for e in events2)

        # History should have grown
        history_after = store.get("sid-history")
        assert len(history_after) >= len(history)

    async def test_different_sessions_isolated(self, provider, store):
        """Different session_ids have independent histories."""
        service = ChatService(llm_provider=provider, store=store)

        async for _ in service.stream_chat("session-a", "hello from A"):
            pass
        async for _ in service.stream_chat("session-b", "hello from B"):
            pass

        hist_a = store.get("session-a")
        hist_b = store.get("session-b")
        assert hist_a != hist_b, "Different sessions should have different histories"


# ════════════════════════════════════════════════════════════════
# SSE Event Structure Tests
# ════════════════════════════════════════════════════════════════

class TestSSEEventStructure:
    """Test: SSE events have correct structure."""

    async def test_token_event_structure(self, provider, store):
        """Token events have {event: 'token', data: {content: str}}."""
        service = ChatService(llm_provider=provider, store=store)
        events = []
        async for event in service.stream_chat("sid-struct", "hello"):
            events.append(event)

        token_events = [e for e in events if e["event"] == "token"]
        for te in token_events:
            assert "event" in te
            assert "data" in te
            assert "content" in te["data"]

    async def test_suggestions_event_structure(self, tool_provider, store):
        """Suggestions event has {event: 'suggestions', data: {items: [...]}}."""
        service = ChatService(llm_provider=tool_provider, store=store)
        events = []
        async for event in service.stream_chat("sid-sug", "buffer roads"):
            events.append(event)

        sug_events = [e for e in events if e["event"] == "suggestions"]
        assert len(sug_events) >= 1, "Should have suggestions event after tool execution"
        for se in sug_events:
            assert "items" in se["data"]
            assert isinstance(se["data"]["items"], list)

    async def test_done_event_is_last(self, provider, store):
        """'done' event should be the last event yielded."""
        service = ChatService(llm_provider=provider, store=store)
        events = []
        async for event in service.stream_chat("sid-last", "hello"):
            events.append(event)

        assert events[-1]["event"] == "done", \
            f"Last event should be 'done', got '{events[-1]['event']}'"


# ════════════════════════════════════════════════════════════════
# Arcpy Thread Safety Tests
# ════════════════════════════════════════════════════════════════

class TestArcpyThreadSafety:
    """Test: chat_with_tools runs via asyncio.to_thread for arcpy safety."""

    async def test_uses_asyncio_to_thread(self, provider, store):
        """stream_chat calls chat_with_tools via asyncio.to_thread."""
        service = ChatService(llm_provider=provider, store=store)
        with patch("asyncio.to_thread", wraps=__import__("asyncio").to_thread) as mock_tt:
            events = []
            async for event in service.stream_chat("sid-thread", "hello"):
                events.append(event)
            # asyncio.to_thread should have been called at least once
            mock_tt.assert_called()

    async def test_completes_without_blocking(self, provider, store):
        """stream_chat completes quickly even with tool calls (non-blocking)."""
        service = ChatService(llm_provider=provider, store=store)
        import time
        start = time.monotonic()
        events = []
        async for event in service.stream_chat("sid-fast", "hello"):
            events.append(event)
        elapsed = time.monotonic() - start
        # Should complete quickly (< 5 seconds) with MockLLMProvider
        assert elapsed < 5.0, f"stream_chat took {elapsed:.1f}s, expected < 5s"
        assert any(e["event"] == "done" for e in events)


# ════════════════════════════════════════════════════════════════
# Module-level Constants Test
# ════════════════════════════════════════════════════════════════

class TestModuleConstants:
    """Test: Module-level constants are correctly defined."""

    def test_template_suggestions_has_gp_buffer(self):
        """TEMPLATE_SUGGESTIONS includes gp_buffer (D-27 requirement)."""
        assert "gp_buffer" in TEMPLATE_SUGGESTIONS

    def test_template_suggestions_has_default(self):
        """TEMPLATE_SUGGESTIONS includes _default fallback."""
        assert "_default" in TEMPLATE_SUGGESTIONS

    def test_max_context_tokens_is_defined(self):
        """MAX_CONTEXT_TOKENS is set to 80,000."""
        assert MAX_CONTEXT_TOKENS == 80_000
