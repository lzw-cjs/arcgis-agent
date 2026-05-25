"""Tests for AnalysisService (GEO-10) and parse_stat_fields utility."""
import pytest
from pathlib import Path

from arcgis_agent.services.analysis_service import (
    AnalysisService, parse_stat_fields, VALID_STATS
)
from arcgis_agent.adapters.mock_adapter import MockGeoProcessor, MockDataAccessor


@pytest.fixture
def mock_gp():
    return MockGeoProcessor()


@pytest.fixture
def mock_data():
    return MockDataAccessor()


@pytest.fixture
def svc(mock_gp, mock_data):
    return AnalysisService(gp=mock_gp, data=mock_data)


@pytest.fixture
def tmp_input(tmp_path):
    """Create a temporary input file for tests."""
    f = tmp_path / "input.shp"
    f.touch()
    return str(f)


# ── parse_stat_fields tests ──────────────────────────────────────────

class TestParseStatFields:
    def test_parse_single_field(self):
        result = parse_stat_fields("pop:SUM")
        assert result == [["pop", "SUM"]]

    def test_parse_multiple_fields(self):
        result = parse_stat_fields("pop:SUM,area:MEAN")
        assert result == [["pop", "SUM"], ["area", "MEAN"]]

    @pytest.mark.parametrize("stat", ["SUM", "MEAN", "MIN", "MAX", "COUNT", "STD", "MEDIAN"])
    def test_parse_all_valid_stats(self, stat):
        result = parse_stat_fields(f"field:{stat}")
        assert result == [["field", stat]]

    def test_parse_invalid_syntax(self):
        with pytest.raises(ValueError, match="Invalid field:STAT syntax"):
            parse_stat_fields("bad_syntax")

    def test_parse_invalid_stat_type(self):
        with pytest.raises(ValueError, match="Invalid stat type"):
            parse_stat_fields("pop:INVALID")

    def test_parse_whitespace_tolerance(self):
        result = parse_stat_fields(" pop:SUM , area:MEAN ")
        assert result == [["pop", "SUM"], ["area", "MEAN"]]


# ── AnalysisService tests ────────────────────────────────────────────

class TestSummaryStatistics:
    def test_summary_stats_success(self, svc, mock_gp, mock_data, tmp_input):
        output_path = str(Path(tmp_input).parent / "input_stats")
        result = svc.summary_statistics(tmp_input, "pop:SUM")
        assert result.success is True
        assert result.code == "OK"
        data = result.data
        assert data is not None
        assert data["output"] == output_path
        assert data["feature_count"] == 42
        assert data["elapsed_seconds"] >= 0  # fast mock ops may round to 0.0
        assert mock_gp.calls == [
            ("summary_statistics", tmp_input, output_path, [["pop", "SUM"]], None)
        ]
        assert ("get_count", output_path) in mock_data.calls

    def test_summary_stats_with_case_field(self, svc, mock_gp, tmp_input):
        output_path = str(Path(tmp_input).parent / "input_stats")
        result = svc.summary_statistics(tmp_input, "pop:SUM", case_field="STATE")
        assert result.success is True
        assert mock_gp.calls == [
            ("summary_statistics", tmp_input, output_path, [["pop", "SUM"]], "STATE")
        ]

    def test_summary_stats_file_not_found(self, svc):
        result = svc.summary_statistics("/nonexistent/input.shp", "pop:SUM")
        assert result.success is False
        assert result.code == "FILE_NOT_FOUND"

    def test_summary_stats_invalid_field_spec(self, svc, tmp_input):
        result = svc.summary_statistics(tmp_input, "bad_syntax")
        assert result.success is False
        assert result.code == "INVALID_FIELD_SPEC"
        assert "Invalid field:STAT syntax" in result.message

    def test_summary_stats_no_overwrite(self, svc, tmp_input):
        # Pass tmp_input as explicit output_table (it exists) to trigger FILE_EXISTS
        result = svc.summary_statistics(tmp_input, "pop:SUM",
                                        no_overwrite=True,
                                        output_table=tmp_input)
        assert result.success is False
        assert result.code == "FILE_EXISTS"

    def test_summary_stats_auto_output(self, svc, mock_gp, tmp_input):
        """When output_table=None, auto-generates path from input stem."""
        result = svc.summary_statistics(tmp_input, "pop:SUM")
        expected_output = str(Path(tmp_input).parent / "input_stats")
        assert result.success is True
        assert result.data["output"] == expected_output
        assert mock_gp.calls[0][0] == "summary_statistics"
        assert mock_gp.calls[0][2] == expected_output


# ── VALID_STATS completeness ──────────────────────────────────────────

class TestValidStats:
    def test_valid_stats_types(self):
        expected = {"SUM", "MEAN", "MIN", "MAX", "COUNT", "STD", "MEDIAN"}
        assert VALID_STATS == expected
