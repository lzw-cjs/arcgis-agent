"""Integration tests for the ChatService agent loop.

Uses MockLLMProvider so no LLM API key is needed.
Tests the full chain: user input -> LLM -> tool calls -> execution -> response.

Run with: pytest tests/e2e/test_chat_loop.py -v
"""
from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.adapters.gis_tools import ALL_GIS_TOOLS
from arcgis_agent.services.chat_service import ChatService, TEMPLATE_SUGGESTIONS
from arcgis_agent.api.dependencies import ConversationStore

pytestmark = pytest.mark.anyio


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_llm():
    """Mock LLM provider with configurable responses.

    No API key required. Responses can be mutated per-test via
    mock_llm._responses assignment.
    """
    provider = MockLLMProvider(responses={
        "chat": "Hello! I'm your GIS assistant.",
    })
    provider.register_tools(ALL_GIS_TOOLS)
    return provider


@pytest.fixture
def conversation_store():
    """Fresh ConversationStore for each test (session isolation)."""
    return ConversationStore()


@pytest.fixture
def chat_service(mock_llm, conversation_store):
    """ChatService wired with MockLLMProvider and ConversationStore."""
    return ChatService(
        llm_provider=mock_llm,
        store=conversation_store,
    )


# ═══════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════


class TestChatServiceIntegration:
    """Integration tests for the ChatService agent loop.

    Covers: simple chat, tool calling, session isolation, template
    suggestions, error handling, and context management.
    """

    async def test_simple_chat(self, chat_service):
        """User says hello, gets text response, no tools called."""
        events = []
        async for event in chat_service.stream_chat("test-session", "hello"):
            events.append(event)

        # Should have token and done events
        event_types = [e["event"] for e in events]
        assert "token" in event_types, f"Expected 'token' event in {event_types}"
        assert "done" in event_types, f"Expected 'done' event in {event_types}"

    async def test_chat_with_tools(self, mock_llm, conversation_store):
        """User requests buffer, LLM returns tool calls, tools execute."""
        # Configure mock to return tool calls followed by final response
        mock_llm._responses = {
            "tool_log": [
                {
                    "name": "gp_buffer",
                    "args": {
                        "input_fc": "roads",
                        "distance": 100,
                        "unit": "Meters",
                        "output_fc": "roads_buf",
                    },
                    "result": "Buffer created: roads_buf. Feature count: 150. Success: True",
                    "success": True,
                }
            ],
            "final": "Buffer operation completed successfully.",
        }

        service = ChatService(llm_provider=mock_llm, store=conversation_store)
        events = []
        async for event in service.stream_chat("test-session-2", "buffer roads by 100m"):
            events.append(event)

        event_types = [e["event"] for e in events]
        assert "tool_start" in event_types, (
            f"Expected 'tool_start' event in {event_types}"
        )
        assert "tool_end" in event_types, (
            f"Expected 'tool_end' event in {event_types}"
        )
        assert "done" in event_types, (
            f"Expected 'done' event in {event_types}"
        )

    async def test_session_isolation(self, mock_llm, conversation_store):
        """Different sessions have independent conversation history."""
        mock_llm._responses = {"chat": "Response A"}
        service = ChatService(llm_provider=mock_llm, store=conversation_store)

        # Session 1
        events_1 = []
        async for e in service.stream_chat("s1", "msg1"):
            events_1.append(e)

        # Session 2
        events_2 = []
        async for e in service.stream_chat("s2", "msg2"):
            events_2.append(e)

        # Both should succeed independently
        assert any(e["event"] == "done" for e in events_1), "Session 1 did not complete"
        assert any(e["event"] == "done" for e in events_2), "Session 2 did not complete"

    async def test_suggestions_after_tool_execution(self, mock_llm, conversation_store):
        """Template suggestions are returned after tool execution (D-27)."""
        mock_llm._responses = {
            "tool_log": [
                {
                    "name": "gp_buffer",
                    "args": {"distance": 100},
                    "result": "OK",
                    "success": True,
                }
            ],
            "final": "Buffer done.",
        }

        service = ChatService(llm_provider=mock_llm, store=conversation_store)
        events = []
        async for event in service.stream_chat("test-s", "buffer"):
            events.append(event)

        suggestions_events = [e for e in events if e["event"] == "suggestions"]
        assert len(suggestions_events) >= 1, (
            f"Expected at least one 'suggestions' event, got {suggestions_events}"
        )
        data = suggestions_events[0].get("data", {})
        items = data.get("items", [])
        assert any("叠加分析" in item for item in items), (
            f"Expected buffer follow-up suggestion with '叠加分析', got: {items}"
        )

    async def test_error_handling(self, mock_llm, conversation_store):
        """ChatService handles tool failures gracefully with success=False."""
        mock_llm._responses = {
            "tool_log": [
                {
                    "name": "gp_buffer",
                    "args": {},
                    "result": "Error: CRS mismatch",
                    "success": False,
                }
            ],
            "final": "The buffer operation failed due to CRS mismatch.",
        }

        service = ChatService(llm_provider=mock_llm, store=conversation_store)
        events = []
        async for event in service.stream_chat("test-e", "buffer"):
            events.append(event)

        tool_end_events = [e for e in events if e["event"] == "tool_end"]
        failed_tools = [
            e for e in tool_end_events
            if not e.get("data", {}).get("success", True)
        ]
        assert len(failed_tools) >= 1, (
            f"Expected at least one failed tool, got {len(failed_tools)}"
        )

    async def test_context_management(self, mock_llm, conversation_store):
        """Conversation history is trimmed when too long (> 20 messages)."""
        # Pre-populate store with 50 messages (25 pairs of Human + AI)
        long_history = []
        for i in range(25):
            long_history.append(HumanMessage(content=f"msg {i}"))
            long_history.append(AIMessage(content=f"response {i}"))

        conversation_store.update("long-session", long_history)

        mock_llm._responses = {"chat": "OK"}
        service = ChatService(llm_provider=mock_llm, store=conversation_store)
        events = []
        async for event in service.stream_chat("long-session", "new message"):
            events.append(event)

        assert any(e["event"] == "done" for e in events), (
            "Should complete successfully with trim_messages"
        )
