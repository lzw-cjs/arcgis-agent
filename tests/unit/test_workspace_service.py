"""Tests for WorkspaceService (Phase 2)."""
import pytest
from pathlib import Path

from arcgis_agent.services.workspace_service import WorkspaceService
from arcgis_agent.config import WorkspaceConfig


class TestWorkspaceService:
    """WorkspaceService unit tests."""

    def test_set_workspace_valid(self, tmp_path):
        """set_workspace with valid dir returns Result.ok."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = WorkspaceService(config=cfg)
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = svc.set_workspace(str(ws))
        assert result.success
        assert result.data["workspace"] == str(ws.resolve())

    def test_set_workspace_nonexistent(self, tmp_path):
        """Returns Result.error with FILE_NOT_FOUND."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = WorkspaceService(config=cfg)
        result = svc.set_workspace("/nonexistent/path")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_set_workspace_file_not_dir(self, tmp_path):
        """Returns Result.error with INVALID_FORMAT for file path."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = WorkspaceService(config=cfg)
        f = tmp_path / "file.txt"
        f.touch()
        result = svc.set_workspace(str(f))
        assert not result.success
        assert result.code == "INVALID_FORMAT"

    def test_get_workspace_none(self, tmp_path):
        """Returns Result.ok with workspace=None."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = WorkspaceService(config=cfg)
        result = svc.get_workspace()
        assert result.success
        assert result.data["workspace"] is None

    def test_get_workspace_after_set(self, tmp_path):
        """Returns Result.ok with workspace path after set."""
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = WorkspaceService(config=cfg)
        ws = tmp_path / "workspace"
        ws.mkdir()
        svc.set_workspace(str(ws))
        result = svc.get_workspace()
        assert result.success
        assert result.data["workspace"] == str(ws.resolve())

    def test_set_workspace_persists(self, tmp_path):
        """Set in one service, get in another with same config."""
        cfg_path = tmp_path / "config.json"
        ws = tmp_path / "workspace"
        ws.mkdir()

        cfg1 = WorkspaceConfig(config_path=cfg_path)
        svc1 = WorkspaceService(config=cfg1)
        svc1.set_workspace(str(ws))

        cfg2 = WorkspaceConfig(config_path=cfg_path)
        svc2 = WorkspaceService(config=cfg2)
        result = svc2.get_workspace()
        assert result.success
        assert result.data["workspace"] == str(ws.resolve())
