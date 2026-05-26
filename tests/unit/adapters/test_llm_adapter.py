"""Unit tests for ILLMProvider adapter implementations (07-03 Task 1)."""
import os
import pytest
from arcgis_agent.adapters.mock_llm import MockLLMProvider
from arcgis_agent.adapters.llm import OpenAICompatibleProvider
from arcgis_agent.adapters.gis_tools import ALL_GIS_TOOLS
from arcgis_agent.config import LLMProviderConfig, LLMConfig


class TestILLMProviderABC:
    """Test ILLMProvider ABC cannot be instantiated directly."""

    def test_cannot_instantiate_abc(self):
        """ILLMProvider ABC 无法直接实例化（abc.abstractmethod 保护）."""
        from arcgis_agent.adapters.base import ILLMProvider
        with pytest.raises(TypeError, match="abstract"):
            ILLMProvider()  # type: ignore

    def test_abc_has_required_methods(self):
        """ILLMProvider ABC defines chat, chat_with_tools, register_tools."""
        from arcgis_agent.adapters.base import ILLMProvider
        assert hasattr(ILLMProvider, 'chat')
        assert hasattr(ILLMProvider, 'chat_with_tools')
        assert hasattr(ILLMProvider, 'register_tools')


class TestLLMConfig:
    """Test LLMConfig.from_env() behavior."""

    def test_from_env_reads_dashscope_key(self, monkeypatch):
        """LLMConfig.from_env() 从环境变量 DASHSCOPE_API_KEY 读取 Qwen 配置."""
        monkeypatch.setenv('DASHSCOPE_API_KEY', 'test-dashscope-key')
        monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        config = LLMConfig.from_env()
        qwen = config.providers['qwen']
        assert qwen.api_key == 'test-dashscope-key'
        assert qwen.provider == 'qwen'
        assert qwen.model == 'qwen-plus'

    def test_from_env_defaults_when_no_env(self, monkeypatch):
        """LLMConfig.from_env() 在未设置环境变量时 api_key 为空字符串，不崩溃."""
        monkeypatch.delenv('DASHSCOPE_API_KEY', raising=False)
        monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        monkeypatch.delenv('LLM_DEFAULT_PROVIDER', raising=False)
        monkeypatch.delenv('QWEN_MODEL', raising=False)
        monkeypatch.delenv('DEEPSEEK_MODEL', raising=False)
        monkeypatch.delenv('OPENAI_MODEL', raising=False)
        config = LLMConfig.from_env()
        assert config.default == 'qwen'
        assert config.providers['qwen'].api_key == ''
        assert config.providers['deepseek'].api_key == ''
        assert config.providers['openai'].api_key == ''

    def test_from_env_all_providers(self, monkeypatch):
        """LLMConfig.from_env() loads all 3 provider configs."""
        monkeypatch.setenv('DASHSCOPE_API_KEY', 'qwen-key')
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'ds-key')
        monkeypatch.setenv('OPENAI_API_KEY', 'oai-key')
        monkeypatch.setenv('LLM_DEFAULT_PROVIDER', 'deepseek')
        config = LLMConfig.from_env()
        assert config.default == 'deepseek'
        assert config.providers['qwen'].api_key == 'qwen-key'
        assert config.providers['deepseek'].api_key == 'ds-key'
        assert config.providers['openai'].api_key == 'oai-key'

    def test_get_provider_config_returns_correct(self, monkeypatch):
        """LLMConfig.get_provider_config() returns correct LLMProviderConfig."""
        monkeypatch.setenv('DASHSCOPE_API_KEY', 'test-key')
        monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)
        config = LLMConfig.from_env()
        provider = config.get_provider_config('qwen')
        assert provider.provider == 'qwen'
        assert provider.api_key == 'test-key'

    def test_get_provider_config_unknown_raises(self, monkeypatch):
        """get_provider_config() with unknown name raises ValueError."""
        config = LLMConfig.from_env()
        with pytest.raises(ValueError, match="Unknown provider"):
            config.get_provider_config('nonexistent')

    def test_get_provider_config_uses_default(self, monkeypatch):
        """get_provider_config() with no arg uses default provider."""
        monkeypatch.setenv('LLM_DEFAULT_PROVIDER', 'openai')
        monkeypatch.setenv('OPENAI_API_KEY', 'oai-key')
        config = LLMConfig.from_env()
        provider = config.get_provider_config()
        assert provider.provider == 'openai'

    def test_config_model_defaults(self, monkeypatch):
        """LLMConfig provider model defaults are correct."""
        monkeypatch.delenv('DASHSCOPE_API_KEY', raising=False)
        monkeypatch.delenv('QWEN_MODEL', raising=False)
        monkeypatch.delenv('DEEPSEEK_MODEL', raising=False)
        monkeypatch.delenv('OPENAI_MODEL', raising=False)
        config = LLMConfig.from_env()
        assert config.providers['qwen'].model == 'qwen-plus'
        assert config.providers['deepseek'].model == 'deepseek-chat'
        assert config.providers['openai'].model == 'gpt-4o'


class TestMockLLMProvider:
    """Test MockLLMProvider implementation."""

    def test_chat_returns_aimessage(self):
        """MockLLMProvider.chat('hello') 返回 AIMessage."""
        provider = MockLLMProvider()
        result = provider.chat("hello")
        assert result is not None
        assert result.content is not None
        assert len(result.content) > 0
        # Must be LangChain AIMessage
        from langchain_core.messages import AIMessage
        assert isinstance(result, AIMessage)

    def test_chat_default_response(self):
        """MockLLMProvider.chat returns mock content."""
        provider = MockLLMProvider()
        result = provider.chat("hello world")
        assert "hello world" in result.content

    def test_chat_with_tools_returns_tuple(self):
        """MockLLMProvider.chat_with_tools returns (AIMessage, list)."""
        provider = MockLLMProvider()
        provider.register_tools(ALL_GIS_TOOLS[:5])
        result, tool_log = provider.chat_with_tools("buffer roads by 100m")
        from langchain_core.messages import AIMessage
        assert isinstance(result, AIMessage)
        assert isinstance(tool_log, list)

    def test_chat_with_tools_accepts_max_iterations(self):
        """MockLLMProvider.chat_with_tools accepts max_iterations parameter."""
        provider = MockLLMProvider()
        result, tool_log = provider.chat_with_tools("test", max_iterations=3)
        assert isinstance(tool_log, list)

    def test_register_tools(self):
        """MockLLMProvider.register_tools stores tools."""
        provider = MockLLMProvider()
        provider.register_tools(ALL_GIS_TOOLS)
        assert len(provider._tools) == len(ALL_GIS_TOOLS)

    def test_chat_without_tools_returns_empty_log(self):
        """chat_with_tools without tools returns empty tool_log."""
        provider = MockLLMProvider()
        result, tool_log = provider.chat_with_tools("hello")
        assert isinstance(result.content, str)
        assert isinstance(tool_log, list)

    def test_chat_accepts_history(self):
        """MockLLMProvider.chat accepts history parameter."""
        from langchain_core.messages import HumanMessage
        provider = MockLLMProvider()
        history = [HumanMessage(content="previous")]
        result = provider.chat("hello", history=history)
        assert result.content is not None


class TestOpenAICompatibleProvider:
    """Test OpenAICompatibleProvider implementation."""

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

    def test_register_tools(self):
        """OpenAICompatibleProvider.register_tools stores tools."""
        config = LLMProviderConfig(
            provider="test", model="m", base_url="http://x", api_key="k",
        )
        provider = OpenAICompatibleProvider(config)
        provider.register_tools(ALL_GIS_TOOLS[:3])
        assert len(provider._tools) == 3

    def test_chat_with_tools_raises_without_registration(self):
        """chat_with_tools raises RuntimeError if no tools registered."""
        config = LLMProviderConfig(
            provider="test", model="m",
            base_url="https://test.api.com/v1",
            api_key="sk-test",
        )
        provider = OpenAICompatibleProvider(config)
        with pytest.raises(RuntimeError, match="No tools registered"):
            provider.chat_with_tools("hello")

    def test_system_prompt_present(self):
        """OpenAICompatibleProvider has SYSTEM_PROMPT constant."""
        from arcgis_agent.adapters.llm import SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 0
        assert "GIS" in SYSTEM_PROMPT


class TestGISTools:
    """Test GIS tool definitions."""

    def test_all_tools_have_name_and_description(self):
        for tool in ALL_GIS_TOOLS:
            assert tool.name, f"Tool missing name"
            assert tool.description, f"Tool '{tool.name}' missing description"

    def test_all_tools_have_args_schema(self):
        for tool in ALL_GIS_TOOLS:
            assert tool.args_schema is not None, \
                f"Tool '{tool.name}' missing args_schema"

    def test_tool_count_at_least_33(self):
        """Verify tool count is >= 33 (D-04: full coverage)."""
        assert len(ALL_GIS_TOOLS) >= 33, \
            f"Expected >= 33 tools, got {len(ALL_GIS_TOOLS)}"

    def test_key_tools_present(self):
        """Key GIS tools are in the list."""
        names = [t.name for t in ALL_GIS_TOOLS]
        assert 'gp_buffer' in names
        assert 'map_export' in names
        assert 'data_list' in names
