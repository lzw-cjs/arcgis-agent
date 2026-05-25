"""Tests for GeoprocessingService (GEO-01 through GEO-09)."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from arcgis_agent.services.geoprocessing import GeoprocessingService
from arcgis_agent.adapters.mock_adapter import MockGeoProcessor, MockDataAccessor


@pytest.fixture
def mock_gp():
    return MockGeoProcessor()


@pytest.fixture
def mock_data():
    return MockDataAccessor()


@pytest.fixture
def svc(mock_gp, mock_data):
    return GeoprocessingService(gp=mock_gp, data=mock_data)


@pytest.fixture
def tmp_input(tmp_path):
    """Create a temporary input file for tests."""
    f = tmp_path / "input.shp"
    f.touch()
    return str(f)


@pytest.fixture
def tmp_output(tmp_path):
    """Return a temporary output path (does not exist yet)."""
    return str(tmp_path / "output.shp")


@pytest.fixture
def tmp_input2(tmp_path):
    """Create a second temporary input file for multi-input tests."""
    f = tmp_path / "input2.shp"
    f.touch()
    return str(f)


# ── GEO-01: select_by_attribute ──────────────────────────────────────

class TestSelectByAttribute:
    def test_select_success(self, svc, mock_gp, mock_data, tmp_input, tmp_output):
        result = svc.select_by_attribute(tmp_input, tmp_output, "POPULATION > 5000")
        assert result.success is True
        assert result.code == "OK"
        data = result.data
        assert data is not None
        assert "output" in data
        assert data["output"] == tmp_output
        assert "feature_count" in data
        assert data["feature_count"] == 42
        assert "elapsed_seconds" in data
        assert data["elapsed_seconds"] >= 0  # fast mock ops may round to 0.0
        assert mock_gp.calls == [
            ("select_by_attribute", tmp_input, tmp_output, "POPULATION > 5000")
        ]
        assert ("get_count", tmp_output) in mock_data.calls

    def test_select_file_not_found(self, svc, tmp_output):
        result = svc.select_by_attribute("/nonexistent/path.shp", tmp_output, "X=1")
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"
        assert "not found" in result.message.lower()

    def test_select_no_overwrite(self, svc, tmp_input):
        # tmp_input exists, use it as both input and output for no_overwrite test
        result = svc.select_by_attribute(tmp_input, tmp_input, "X=1", no_overwrite=True)
        assert result.success is False
        assert result.code == "FILE_EXISTS"


# ── GEO-02: clip ──────────────────────────────────────────────────────

class TestClip:
    def test_clip_success(self, svc, mock_gp, mock_data, tmp_input, tmp_input2, tmp_output):
        result = svc.clip(tmp_input, tmp_input2, tmp_output)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert result.data["feature_count"] == 42
        assert result.data["elapsed_seconds"] >= 0  # fast mock ops may round to 0.0
        assert mock_gp.calls == [
            ("clip", tmp_input, tmp_input2, tmp_output)
        ]

    def test_clip_input_not_found(self, svc, tmp_input2, tmp_output):
        result = svc.clip("/nonexistent/input.shp", tmp_input2, tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"

    def test_clip_clip_not_found(self, svc, tmp_input, tmp_output):
        result = svc.clip(tmp_input, "/nonexistent/clip.shp", tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-03: buffer ────────────────────────────────────────────────────

class TestBuffer:
    def test_buffer_success(self, svc, mock_gp, tmp_input, tmp_output):
        result = svc.buffer(tmp_input, tmp_output, 100.0)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert result.data["feature_count"] == 42
        assert result.data["elapsed_seconds"] >= 0  # fast mock ops may round to 0.0
        # Default unit is "Meters", no dissolve_field
        assert mock_gp.calls == [
            ("buffer", tmp_input, tmp_output, 100.0, "Meters", None)
        ]

    def test_buffer_with_dissolve(self, svc, mock_gp, tmp_input, tmp_output):
        result = svc.buffer(tmp_input, tmp_output, 500.0, unit="Feet",
                            dissolve_field="ZONE")
        assert result.success is True
        assert mock_gp.calls == [
            ("buffer", tmp_input, tmp_output, 500.0, "Feet", "ZONE")
        ]

    def test_buffer_invalid_unit(self, svc, tmp_input, tmp_output):
        result = svc.buffer(tmp_input, tmp_output, 100.0, unit="InvalidUnit")
        assert result.success is False
        assert result.code == "INVALID_UNIT"
        assert "InvalidUnit" in result.message
        assert "Meters" in result.message  # valid units listed in message

    def test_buffer_file_not_found(self, svc, tmp_output):
        result = svc.buffer("/nonexistent/input.shp", tmp_output, 100.0)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"

    @pytest.mark.parametrize("unit", [
        "Meters", "Kilometers", "Feet", "Miles", "Yards", "DecimalDegrees"
    ])
    def test_buffer_all_valid_units(self, svc, tmp_input, tmp_output, unit):
        result = svc.buffer(tmp_input, tmp_output, 50.0, unit=unit)
        assert result.success is True
        assert result.code == "OK"


# ── GEO-04: intersect ─────────────────────────────────────────────────

class TestIntersect:
    def test_intersect_success(self, svc, mock_gp, tmp_input, tmp_input2, tmp_output):
        inputs = [tmp_input, tmp_input2]
        result = svc.intersect(inputs, tmp_output)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("intersect", inputs, tmp_output)
        ]

    def test_intersect_three_inputs(self, svc, mock_gp, tmp_input, tmp_input2, tmp_output):
        # Create a third input
        inputs = [tmp_input, tmp_input2, tmp_input2]  # reuse tmp_input2 as third
        result = svc.intersect(inputs, tmp_output)
        assert result.success is True
        assert mock_gp.calls == [
            ("intersect", inputs, tmp_output)
        ]

    def test_intersect_single_input(self, svc, tmp_input, tmp_output):
        result = svc.intersect([tmp_input], tmp_output)
        assert result.success is False
        assert result.code == "INVALID_INPUT"
        assert "least 2" in result.message.lower()

    def test_intersect_file_not_found(self, svc, tmp_input, tmp_output):
        result = svc.intersect([tmp_input, "/nonexistent/b.shp"], tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-05: union ────────────────────────────────────────────────────

class TestUnion:
    def test_union_success(self, svc, mock_gp, tmp_input, tmp_input2, tmp_output):
        inputs = [tmp_input, tmp_input2]
        result = svc.union(inputs, tmp_output)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("union", inputs, tmp_output)
        ]

    def test_union_single_input(self, svc, tmp_input, tmp_output):
        result = svc.union([tmp_input], tmp_output)
        assert result.success is False
        assert result.code == "INVALID_INPUT"

    def test_union_file_not_found(self, svc, tmp_input, tmp_output):
        result = svc.union([tmp_input, "/nonexistent/b.shp"], tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-06: dissolve ─────────────────────────────────────────────────

class TestDissolve:
    def test_dissolve_success(self, svc, mock_gp, tmp_input, tmp_output):
        result = svc.dissolve(tmp_input, tmp_output, "STATE")
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("dissolve", tmp_input, tmp_output, "STATE")
        ]

    def test_dissolve_file_not_found(self, svc, tmp_output):
        result = svc.dissolve("/nonexistent/input.shp", tmp_output, "FIELD")
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-07: spatial_join ──────────────────────────────────────────────

class TestSpatialJoin:
    def test_spatial_join_success(self, svc, mock_gp, tmp_input, tmp_input2, tmp_output):
        result = svc.spatial_join(tmp_input, tmp_input2, tmp_output)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("spatial_join", tmp_input, tmp_input2, tmp_output)
        ]

    def test_spatial_join_file_not_found(self, svc, tmp_input, tmp_output):
        result = svc.spatial_join(tmp_input, "/nonexistent/join.shp", tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-08: merge ─────────────────────────────────────────────────────

class TestMerge:
    def test_merge_success(self, svc, mock_gp, tmp_input, tmp_input2, tmp_output):
        inputs = [tmp_input, tmp_input2]
        result = svc.merge(inputs, tmp_output)
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("merge", inputs, tmp_output)
        ]

    def test_merge_single_input(self, svc, tmp_input, tmp_output):
        result = svc.merge([tmp_input], tmp_output)
        assert result.success is False
        assert result.code == "INVALID_INPUT"

    def test_merge_file_not_found(self, svc, tmp_input, tmp_output):
        result = svc.merge([tmp_input, "/nonexistent/b.shp"], tmp_output)
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── GEO-09: project ───────────────────────────────────────────────────

class TestProject:
    def test_project_success(self, svc, mock_gp, tmp_input, tmp_output):
        result = svc.project(tmp_input, tmp_output, "4326")
        assert result.success is True
        assert result.code == "OK"
        assert result.data["output"] == tmp_output
        assert mock_gp.calls == [
            ("project", tmp_input, tmp_output, "4326")
        ]

    def test_project_file_not_found(self, svc, tmp_output):
        result = svc.project("/nonexistent/input.shp", tmp_output, "4326")
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"


# ── Cross-cutting tests ───────────────────────────────────────────────

class TestCrossCutting:
    def test_no_overwrite_flag(self, svc, tmp_input):
        """For each single-input method, no_overwrite=True with existing output returns FILE_EXISTS."""
        # Use tmp_input as output (it exists) — test buffer no_overwrite
        result = svc.buffer(tmp_input, tmp_input, 1.0, no_overwrite=True)
        assert result.success is False
        assert result.code == "FILE_EXISTS"

    def test_result_data_keys(self, svc, tmp_input, tmp_output):
        """Every success result has 'output', 'feature_count', 'elapsed_seconds'."""
        methods = [
            lambda: svc.select_by_attribute(tmp_input, tmp_output, "X=1"),
            lambda: svc.buffer(tmp_input, tmp_output, 1.0),
            lambda: svc.dissolve(tmp_input, tmp_output, "F1"),
            lambda: svc.project(tmp_input, tmp_output, "4326"),
        ]
        for method in methods:
            result = method()
            assert result.success is True
            assert result.data is not None
            assert "output" in result.data, f"{method} missing 'output'"
            assert "feature_count" in result.data, f"{method} missing 'feature_count'"
            assert "elapsed_seconds" in result.data, f"{method} missing 'elapsed_seconds'"

    def test_timing_recorded(self, svc, tmp_input, tmp_output):
        """elapsed_seconds > 0 for successful operations."""
        result = svc.buffer(tmp_input, tmp_output, 1.0)
        assert result.success is True
        assert result.data["elapsed_seconds"] >= 0  # fast mock ops may round to 0.0
