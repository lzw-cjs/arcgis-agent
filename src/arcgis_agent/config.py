"""Application configuration: workspace persistence and LLM providers."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Phase 7: LLM Provider Configuration ──


@dataclass
class LLMProviderConfig:
    """Configuration for a single LLM provider (OpenAI-compatible API).

    Each provider (Qwen, DeepSeek, OpenAI) uses the same ChatOpenAI client
    with a different base_url + api_key + model triplet.
    """

    provider: str                      # "qwen", "deepseek", "openai"
    model: str                         # API model ID: "qwen-plus", "deepseek-chat", "gpt-4o"
    base_url: str                      # OpenAI-compatible endpoint URL
    api_key: str                       # 从环境变量读取，绝不硬编码
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 2


@dataclass
class LLMConfig:
    """Multi-provider LLM configuration loaded from environment variables.

    Usage:
        config = LLMConfig.from_env()
        provider_config = config.get_provider_config("qwen")
    """

    default: str = "qwen"              # 默认使用哪个 provider
    providers: dict[str, LLMProviderConfig] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables.

        Reads DASHSCOPE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY from env.
        Falls back to empty string for api_key when env vars are not set.
        """
        return cls(
            default=os.getenv("LLM_DEFAULT_PROVIDER", "qwen"),
            providers={
                "qwen": LLMProviderConfig(
                    provider="qwen",
                    model=os.getenv("QWEN_MODEL", "qwen-plus"),
                    base_url=os.getenv(
                        "QWEN_BASE_URL",
                        "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    ),
                    api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                ),
                "deepseek": LLMProviderConfig(
                    provider="deepseek",
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    base_url=os.getenv(
                        "DEEPSEEK_BASE_URL",
                        "https://api.deepseek.com/v1",
                    ),
                    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                ),
                "openai": LLMProviderConfig(
                    provider="openai",
                    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                    base_url=os.getenv(
                        "OPENAI_BASE_URL",
                        "https://api.openai.com/v1",
                    ),
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                ),
            },
        )

    def get_provider_config(self, name: str | None = None) -> LLMProviderConfig:
        """Get configuration for a specific provider.

        Args:
            name: Provider name ("qwen", "deepseek", "openai").
                  Uses self.default if None.

        Returns:
            LLMProviderConfig for the requested provider.

        Raises:
            ValueError: If the provider name is unknown.
        """
        name = name or self.default
        if name not in self.providers:
            raise ValueError(
                f"Unknown provider '{name}'. Available: {list(self.providers)}"
            )
        return self.providers[name]


CONFIG_DIR = Path.home() / ".arcgis-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"


class WorkspaceConfig:
    """Manages persistent workspace configuration.

    Stores workspace path in ~/.arcgis-agent/config.json.
    Thread-safe for single-process CLI usage.
    """

    def __init__(self, config_path: Path | None = None):
        self._path = config_path or CONFIG_FILE
        self._data: dict = self._load()

    def _load(self) -> dict:
        """Load config from disk, return empty dict if missing/corrupt."""
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Config file corrupt, starting fresh: %s", e)
            return {}

    def _save(self) -> None:
        """Persist config to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_workspace(self) -> Path | None:
        """Return current workspace path, or None if not set."""
        ws = self._data.get("workspace")
        if ws is None:
            return None
        p = Path(ws)
        return p if p.exists() else None

    def set_workspace(self, path: Path) -> None:
        """Set and persist the workspace path."""
        resolved = path.resolve()
        if not resolved.exists():
            from arcgis_agent.exceptions import FileNotFoundError_
            raise FileNotFoundError_(
                message=f"Workspace path does not exist: {resolved}"
            )
        self._data["workspace"] = str(resolved)
        self._save()
