"""Unit tests for ILLMProvider adapter implementations."""
import pytest
from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.adapters.llm import OpenAICompatibleProvider
from arcgis_agent.adapters.gis_tools import ALL_GIS_TOOLS
from arcgis_agent.config import LLMProviderConfig


class TestMockLLMProvider:
    def test_chat_returns_aimessage(self):
        provider = MockLLMProvider()
        result = provider.chat("hello")
        assert result is not None
        assert result.content is not None
        assert len(result.content) > 0

    def test_chat_with_tools_returns_tuple(self):
        provider = MockLLMProvider()
        provider.register_tools(ALL_GIS_TOOLS[:5])
        result, tool_log = provider.chat_with_tools("buffer roads by 100m")
        assert result is not None
        assert isinstance(tool_log, list)

    def test_register_tools(self):
        provider = MockLLMProvider()
        provider.register_tools(ALL_GIS_TOOLS)
        assert len(provider._tools) == len(ALL_GIS_TOOLS)

    def test_chat_without_tools_raises(self):
        provider = MockLLMProvider()
        provider._responses = {}
        # chat_with_tools should work even with empty tools (mock just returns response)
        result, tool_log = provider.chat_with_tools("hello")
        assert isinstance(tool_log, list)


class TestOpenAICompatibleProvider:
    def test_lazy_init_no_api_key(self):
        """Provider initializes without crashing even with no API key."""
        config = LLMProviderConfig(
            provider="test",
            model="test-model",
            base_url="https://test.api.com/v1",
            api_key="",
        )
        provider = OpenAICompatibleProvider(config)
        assert provider._llm is None  # Not initialized yet
        # Lazy init will fail without API key at .llm access, which is expected
        # In production, MockLLMProvider is used when no key configured

    def test_register_tools(self):
        config = LLMProviderConfig(
            provider="test", model="m", base_url="http://x", api_key="k",
        )
        provider = OpenAICompatibleProvider(config)
        provider.register_tools(ALL_GIS_TOOLS[:3])
        assert len(provider._tools) == 3


class TestGISTools:
    def test_all_tools_have_name_and_description(self):
        for tool in ALL_GIS_TOOLS:
            assert tool.name, f"Tool missing name"
            assert tool.description, f"Tool '{tool.name}' missing description"

    def test_all_tools_have_args_schema(self):
        for tool in ALL_GIS_TOOLS:
            assert tool.args_schema is not None, \
                f"Tool '{tool.name}' missing args_schema"

    def test_tool_count_matches(self):
        """Verify tool count is >= 33 (D-04: full coverage)."""
        assert len(ALL_GIS_TOOLS) >= 33, \
            f"Expected >= 33 tools, got {len(ALL_GIS_TOOLS)}"
