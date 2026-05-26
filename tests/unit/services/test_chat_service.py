"""Unit tests for ChatService agent loop."""
import pytest
from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.adapters.gis_tools import ALL_GIS_TOOLS
from arcgis_agent.services.chat_service import ChatService, TEMPLATE_SUGGESTIONS
from arcgis_agent.api.dependencies import ConversationStore

pytestmark = pytest.mark.anyio


@pytest.fixture
def service():
    """ChatService with MockLLMProvider."""
    provider = MockLLMProvider()
    provider.register_tools(ALL_GIS_TOOLS)
    store = ConversationStore()
    return ChatService(llm_provider=provider, store=store)


class TestChatServiceBasics:
    async def test_stream_chat_produces_events(self, service):
        events = []
        async for event in service.stream_chat("sid1", "hello"):
            events.append(event)
        assert len(events) >= 1
        event_types = [e["event"] for e in events]
        assert "done" in event_types or "token" in event_types

    async def test_stream_chat_has_done_event(self, service):
        events = []
        async for event in service.stream_chat("sid2", "test message"):
            events.append(event)
        assert any(e["event"] == "done" for e in events), \
            "Stream should always end with 'done' event"


class TestTemplateSuggestions:
    def test_buffer_suggestion(self):
        from arcgis_agent.services.chat_service import ChatService
        service = ChatService(llm_provider=MockLLMProvider(), store=ConversationStore())
        tool_log = [{"name": "gp_buffer", "success": True, "args": {}, "result": "OK"}]
        suggestions = service._get_suggestions(tool_log)
        assert len(suggestions) >= 1
        assert any("叠加分析" in s for s in suggestions)

    def test_no_tools_no_matches(self):
        from arcgis_agent.services.chat_service import ChatService
        service = ChatService(llm_provider=MockLLMProvider(), store=ConversationStore())
        suggestions = service._get_suggestions([])
        assert len(suggestions) >= 1
        assert suggestions[0] == TEMPLATE_SUGGESTIONS["_default"]

    def test_suggestions_max_three(self):
        tool_log = [
            {"name": "gp_buffer", "success": True, "args": {}, "result": "OK"},
            {"name": "gp_clip", "success": True, "args": {}, "result": "OK"},
            {"name": "gp_intersect", "success": True, "args": {}, "result": "OK"},
            {"name": "map_export", "success": True, "args": {}, "result": "OK"},
        ]
        service = ChatService(llm_provider=MockLLMProvider(), store=ConversationStore())
        suggestions = service._get_suggestions(tool_log)
        assert len(suggestions) <= 3
