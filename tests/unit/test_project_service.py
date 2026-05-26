"""Tests for ProjectService (Phase 2)."""
import pytest
from pathlib import Path

from arcgis_agent.services.project_service import ProjectService
from arcgis_agent.adapters.mock_adapter import MockMapDocument


class TestProjectService:
    """ProjectService unit tests."""

    def test_info_no_path(self):
        """Returns Result.error when no path specified."""
        mock_map = MockMapDocument()
        svc = ProjectService(map_doc=mock_map, data=None)
        result = svc.info(project_path=None)
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_info_not_aprx(self, tmp_path):
        """Returns Result.error with INVALID_FORMAT for non-aprx file."""
        mock_map = MockMapDocument()
        svc = ProjectService(map_doc=mock_map, data=None)
        f = tmp_path / "project.txt"
        f.touch()
        result = svc.info(str(f))
        assert not result.success
        assert result.code == "INVALID_FORMAT"

    def test_info_valid(self, tmp_path):
        """Returns Result.ok with maps and databases."""
        mock_map = MockMapDocument()
        svc = ProjectService(map_doc=mock_map, data=None)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.info(str(f))
        assert result.success
        assert "maps" in result.data
        assert "databases" in result.data
        assert isinstance(result.data["maps"], list)

    def test_info_nonexistent_file(self):
        """Returns Result.error with FILE_NOT_FOUND."""
        mock_map = MockMapDocument()
        svc = ProjectService(map_doc=mock_map, data=None)
        result = svc.info("/nonexistent/project.aprx")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_info_uses_adapter(self, tmp_path):
        """Verify MockMapDocument.get_project_info was called."""
        mock_map = MockMapDocument()
        svc = ProjectService(map_doc=mock_map, data=None)
        f = tmp_path / "test.aprx"
        f.touch()
        svc.info(str(f))
        assert len(mock_map.calls) == 1
        assert mock_map.calls[0][0] == "get_project_info"
