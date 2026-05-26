"""Tests for WorkspaceConfig (Phase 2)."""
import json
import pytest
from pathlib import Path

from arcgis_agent.config import WorkspaceConfig
from arcgis_agent.exceptions import FileNotFoundError_


class TestWorkspaceConfig:
    """WorkspaceConfig unit tests."""

    def test_config_creates_on_save(self, tmp_path):
        """set_workspace creates config file."""
        cfg_path = tmp_path / "config.json"
        cfg = WorkspaceConfig(config_path=cfg_path)
        ws = tmp_path / "my_workspace"
        ws.mkdir()
        cfg.set_workspace(ws)
        assert cfg_path.exists()

    def test_config_get_returns_none_when_empty(self, tmp_path):
        """get_workspace returns None on fresh config."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        assert cfg.get_workspace() is None

    def test_config_set_and_get(self, tmp_path):
        """Set then get returns the same path."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        ws = tmp_path / "workspace"
        ws.mkdir()
        cfg.set_workspace(ws)
        result = cfg.get_workspace()
        assert result == ws.resolve()

    def test_config_persists_across_instances(self, tmp_path):
        """Two instances with same path share data."""
        cfg_path = tmp_path / "config.json"
        ws = tmp_path / "workspace"
        ws.mkdir()

        cfg1 = WorkspaceConfig(config_path=cfg_path)
        cfg1.set_workspace(ws)

        cfg2 = WorkspaceConfig(config_path=cfg_path)
        assert cfg2.get_workspace() == ws.resolve()

    def test_config_handles_missing_file(self, tmp_path):
        """get_workspace on nonexistent config file returns None."""
        cfg = WorkspaceConfig(config_path=tmp_path / "nonexistent.json")
        assert cfg.get_workspace() is None

    def test_config_handles_corrupt_json(self, tmp_path):
        """Corrupt config file -> get_workspace returns None."""
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text("not valid json!!!", encoding="utf-8")
        cfg = WorkspaceConfig(config_path=cfg_path)
        assert cfg.get_workspace() is None

    def test_config_set_nonexistent_raises(self, tmp_path):
        """set_workspace with nonexistent path raises FileNotFoundError_."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        with pytest.raises(FileNotFoundError_):
            cfg.set_workspace(Path("/nonexistent/workspace"))

    def test_config_resolves_symlinks(self, tmp_path):
        """set_workspace resolves to absolute path."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        ws = tmp_path / "workspace"
        ws.mkdir()
        cfg.set_workspace(ws)
        result = cfg.get_workspace()
        assert result.is_absolute()
