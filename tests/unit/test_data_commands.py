"""CLI integration tests for all data commands (Phase 2)."""
import json
import pytest
import click
from click.testing import CliRunner

from arcgis_agent.commands.data import register as data_register


@pytest.fixture
def data_cli():
    """Create a CLI group with data commands registered."""
    @click.group()
    def test_cli():
        pass
    data_register(test_cli)
    return test_cli


class TestDataCommandsHelp:
    """Test help text for all data subcommands."""

    def test_data_help(self, data_cli, runner):
        """data --help shows all 9 subcommands."""
        result = runner.invoke(data_cli, ["data", "--help"])
        assert result.exit_code == 0
        for cmd in ["list", "describe", "fields", "extent", "count",
                     "copy", "delete", "rename", "convert"]:
            assert cmd in result.output

    def test_data_list_help(self, data_cli, runner):
        """data list --help shows --workspace/--type/--pattern."""
        result = runner.invoke(data_cli, ["data", "list", "--help"])
        assert result.exit_code == 0
        assert "--workspace" in result.output
        assert "--type" in result.output
        assert "--pattern" in result.output

    def test_data_describe_help(self, data_cli, runner):
        """data describe --help shows PATH argument."""
        result = runner.invoke(data_cli, ["data", "describe", "--help"])
        assert result.exit_code == 0
        assert "PATH" in result.output

    def test_data_count_help(self, data_cli, runner):
        """data count --help shows PATH argument."""
        result = runner.invoke(data_cli, ["data", "count", "--help"])
        assert result.exit_code == 0
        assert "PATH" in result.output

    def test_data_copy_help(self, data_cli, runner):
        """data copy --help shows SOURCE/DESTINATION and --no-overwrite."""
        result = runner.invoke(data_cli, ["data", "copy", "--help"])
        assert result.exit_code == 0
        assert "SOURCE" in result.output
        assert "DESTINATION" in result.output
        assert "--no-overwrite" in result.output

    def test_data_convert_help(self, data_cli, runner):
        """data convert --help shows --format option."""
        result = runner.invoke(data_cli, ["data", "convert", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output


class TestDataCommandErrors:
    """Test error handling in data commands."""

    def test_data_list_no_workspace(self, data_cli, runner):
        """Outputs JSON error when no workspace set."""
        result = runner.invoke(data_cli, ["data", "list"])
        assert result.exit_code == 0  # CLI always exits 0, error in JSON
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "FILE_NOT_FOUND"

    def test_data_describe_nonexistent(self, data_cli, runner):
        """Outputs JSON error for nonexistent dataset."""
        result = runner.invoke(data_cli, ["data", "describe", "/nonexistent/test.shp"])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "FILE_NOT_FOUND"

    def test_data_count_nonexistent(self, data_cli, runner):
        """Outputs JSON error for nonexistent dataset."""
        result = runner.invoke(data_cli, ["data", "count", "/nonexistent/test.shp"])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "FILE_NOT_FOUND"

    def test_data_copy_nonexistent(self, data_cli, runner):
        """Outputs JSON error for nonexistent source."""
        result = runner.invoke(data_cli, ["data", "copy", "/nonexistent/src.shp", "/tmp/dst.shp"])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "FILE_NOT_FOUND"

    def test_data_delete_nonexistent(self, data_cli, runner):
        """Outputs JSON error for nonexistent dataset."""
        result = runner.invoke(data_cli, ["data", "delete", "/nonexistent/test.shp"])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "FILE_NOT_FOUND"

    def test_data_convert_invalid_format(self, data_cli, runner, tmp_path):
        """Outputs JSON error for invalid format."""
        src = tmp_path / "input.shp"
        src.touch()
        result = runner.invoke(data_cli, [
            "data", "convert", str(src), str(tmp_path / "out.xyz"),
            "--format", "xyz",
        ])
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is False
        assert output["code"] == "INVALID_FORMAT"
