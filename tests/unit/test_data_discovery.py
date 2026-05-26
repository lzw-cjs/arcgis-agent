"""Tests for DataDiscoveryService (Phase 2)."""
import pytest
from pathlib import Path

from arcgis_agent.services.data_discovery import DataDiscoveryService
from arcgis_agent.adapters.mock_adapter import MockDataAccessor
from arcgis_agent.config import WorkspaceConfig


class TestDataDiscoveryService:
    """DataDiscoveryService unit tests."""

    def test_list_datasets_with_workspace(self, tmp_path):
        """Returns Result.ok with datasets."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        ws = tmp_path / "workspace"
        ws.mkdir()
        result = svc.list_datasets(workspace=str(ws))
        assert result.success
        assert "datasets" in result.data
        assert result.data["count"] >= 1

    def test_list_datasets_no_workspace(self, tmp_path):
        """Returns Result.error with FILE_NOT_FOUND when no workspace set."""
        mock_data = MockDataAccessor()
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        svc = DataDiscoveryService(data=mock_data, config=cfg)
        result = svc.list_datasets()
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_list_datasets_with_config(self, tmp_path):
        """Uses configured workspace."""
        mock_data = MockDataAccessor()
        cfg = WorkspaceConfig(config_path=tmp_path / "config.json")
        ws = tmp_path / "workspace"
        ws.mkdir()
        cfg.set_workspace(ws)
        svc = DataDiscoveryService(data=mock_data, config=cfg)
        result = svc.list_datasets()
        assert result.success
        assert result.data["workspace"] == str(ws.resolve())

    def test_describe_valid(self, tmp_path):
        """Returns Result.ok with metadata."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        f = tmp_path / "test.shp"
        f.touch()
        result = svc.describe(str(f))
        assert result.success
        assert "name" in result.data

    def test_describe_nonexistent(self):
        """Returns Result.error with FILE_NOT_FOUND."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        result = svc.describe("/nonexistent/test.shp")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_get_fields_valid(self, tmp_path):
        """Returns Result.ok with fields list."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        f = tmp_path / "test.shp"
        f.touch()
        result = svc.get_fields(str(f))
        assert result.success
        assert "fields" in result.data
        assert isinstance(result.data["fields"], list)
        assert len(result.data["fields"]) >= 1

    def test_get_fields_nonexistent(self):
        """Returns Result.error."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        result = svc.get_fields("/nonexistent/test.shp")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_get_extent_valid(self, tmp_path):
        """Returns Result.ok with xmin/ymin/xmax/ymax."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        f = tmp_path / "test.shp"
        f.touch()
        result = svc.get_extent(str(f))
        assert result.success
        assert "xmin" in result.data
        assert "xmax" in result.data
        assert "ymin" in result.data
        assert "ymax" in result.data

    def test_get_count_valid(self, tmp_path):
        """Returns Result.ok with count."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        f = tmp_path / "test.shp"
        f.touch()
        result = svc.get_count(str(f))
        assert result.success
        assert result.data["count"] == 42

    def test_get_count_nonexistent(self):
        """Returns Result.error."""
        mock_data = MockDataAccessor()
        svc = DataDiscoveryService(data=mock_data)
        result = svc.get_count("/nonexistent/test.shp")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"
