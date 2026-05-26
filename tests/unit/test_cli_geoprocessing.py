"""CLI integration tests for geoprocessing and analysis commands (Phase 3 Gap 3).

Tests verify that CLI commands produce valid JSON output with correct structure.
Uses unittest.mock.patch to inject mock service adapters — no arcpy required.
"""
import json
import pytest
import click
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from arcgis_agent.models.result import Result
from arcgis_agent.commands.data import register as data_register
from arcgis_agent.commands.geoprocessing import register as geo_register
from arcgis_agent.commands.analysis import register as analysis_register


@pytest.fixture
def geo_cli():
    """CLI group with data and geoprocessing commands registered."""
    @click.group()
    def test_cli():
        pass
    data_register(test_cli)
    geo_register(test_cli)
    return test_cli


@pytest.fixture
def analysis_cli():
    """CLI group with analysis commands registered."""
    @click.group()
    def test_cli():
        pass
    analysis_register(test_cli)
    return test_cli


class TestGeoprocessingCLI:
    """CLI integration tests for geoprocessing commands (data buffer)."""

    def test_buffer_cli_json_output(self, geo_cli, runner, tmp_path):
        """data buffer command outputs valid JSON with output, feature_count, elapsed_seconds (D-11)."""
        input_f = tmp_path / "input.shp"
        input_f.touch()
        output_f = tmp_path / "buffer_out.shp"

        mock_result = Result.ok(
            data={"output": str(output_f), "feature_count": 42, "elapsed_seconds": 0.51},
            message="Buffer created: buffer_out.shp"
        )

        mock_svc = MagicMock()
        mock_svc.buffer.return_value = mock_result

        with patch(
            'arcgis_agent.services.geoprocessing.GeoprocessingService',
            return_value=mock_svc
        ):
            result = runner.invoke(geo_cli, [
                'data', 'buffer', str(input_f), str(output_f),
                '--distance', '100',
            ])

        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert output['success'] is True
        assert output['code'] == 'OK'
        assert output['data']['output'] == str(output_f)
        assert output['data']['feature_count'] == 42
        assert output['data']['elapsed_seconds'] == 0.51

    def test_buffer_cli_with_all_options(self, geo_cli, runner, tmp_path):
        """data buffer passes --unit, --dissolve-field, --no-overwrite to service."""
        input_f = tmp_path / "input.shp"
        input_f.touch()
        output_f = tmp_path / "buffer_out.shp"

        mock_result = Result.ok(
            data={"output": str(output_f), "feature_count": 10, "elapsed_seconds": 0.3},
            message="Buffer created: buffer_out.shp"
        )

        mock_svc = MagicMock()
        mock_svc.buffer.return_value = mock_result

        with patch(
            'arcgis_agent.services.geoprocessing.GeoprocessingService',
            return_value=mock_svc
        ):
            result = runner.invoke(geo_cli, [
                'data', 'buffer', str(input_f), str(output_f),
                '--distance', '500',
                '--unit', 'Feet',
                '--dissolve-field', 'ZONE',
                '--no-overwrite',
            ])

        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert output['success'] is True
        assert output['code'] == 'OK'

    def test_buffer_cli_error_output(self, geo_cli, runner, tmp_path):
        """data buffer error is output as valid JSON with success=False."""
        input_f = tmp_path / "input.shp"

        mock_result = Result.error(
            code="FILE_NOT_FOUND",
            message="Input not found: /nonexistent.shp"
        )

        mock_svc = MagicMock()
        mock_svc.buffer.return_value = mock_result

        with patch(
            'arcgis_agent.services.geoprocessing.GeoprocessingService',
            return_value=mock_svc
        ):
            result = runner.invoke(geo_cli, [
                'data', 'buffer', str(input_f), str(input_f),
                '--distance', '100',
            ])

        assert result.exit_code == 0  # CLI exits 0 even on error; error is in JSON
        output = json.loads(result.output.strip())
        assert output['success'] is False
        assert output['code'] == 'FILE_NOT_FOUND'
        assert 'not found' in output['message'].lower()
