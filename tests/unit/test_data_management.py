"""Tests for DataManagementService (Phase 2)."""
import pytest
from pathlib import Path

from arcgis_agent.services.data_management import DataManagementService
from arcgis_agent.adapters.mock_adapter import MockDataAccessor


class TestDataManagementService:
    """DataManagementService unit tests."""

    def test_copy_valid(self, tmp_path):
        """Returns Result.ok with source/destination."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        src = tmp_path / "source.shp"
        src.touch()
        dst = tmp_path / "dest.shp"
        result = svc.copy(str(src), str(dst))
        assert result.success
        assert result.data["source"] == str(src)
        assert result.data["destination"] == str(dst)

    def test_copy_nonexistent(self):
        """Returns Result.error with FILE_NOT_FOUND."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        result = svc.copy("/nonexistent/src.shp", "/tmp/dst.shp")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_copy_no_overwrite(self, tmp_path):
        """Returns Result.error when dest exists and no_overwrite=True."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        src = tmp_path / "source.shp"
        src.touch()
        dst = tmp_path / "existing.shp"
        dst.touch()
        result = svc.copy(str(src), str(dst), no_overwrite=True)
        assert not result.success
        assert result.code == "FILE_EXISTS"

    def test_delete_valid(self, tmp_path):
        """Returns Result.ok."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        f = tmp_path / "test.shp"
        f.touch()
        result = svc.delete(str(f))
        assert result.success
        assert result.data["path"] == str(f)

    def test_delete_nonexistent(self):
        """Returns Result.error with FILE_NOT_FOUND."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        result = svc.delete("/nonexistent/test.shp")
        assert not result.success
        assert result.code == "FILE_NOT_FOUND"

    def test_rename_valid(self, tmp_path):
        """Returns Result.ok with new path."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        f = tmp_path / "old.shp"
        f.touch()
        result = svc.rename(str(f), "new.shp")
        assert result.success
        assert "new.shp" in result.data["new_path"]

    def test_convert_valid(self, tmp_path):
        """Returns Result.ok with format."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        src = tmp_path / "input.shp"
        src.touch()
        dst = tmp_path / "output.csv"
        result = svc.convert(str(src), str(dst), "csv")
        assert result.success
        assert result.data["format"] == "csv"
        assert result.data["source"] == str(src)

    def test_convert_invalid_format(self, tmp_path):
        """Returns Result.error with INVALID_FORMAT."""
        mock_data = MockDataAccessor()
        svc = DataManagementService(data=mock_data)
        src = tmp_path / "input.shp"
        src.touch()
        result = svc.convert(str(src), str(tmp_path / "out.xyz"), "xyz")
        assert not result.success
        assert result.code == "INVALID_FORMAT"
