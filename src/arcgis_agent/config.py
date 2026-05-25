"""Workspace configuration persistence."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

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
