"""CLI integration tests for 'map' commands."""
from click.testing import CliRunner
from arcgis_agent.cli import cli


def test_map_help(runner):
    """map --help shows available subcommands."""
    result = runner.invoke(cli, ['map', '--help'])
    assert result.exit_code == 0
    assert 'create' in result.output
    assert 'add-layer' in result.output
    assert 'remove-layer' in result.output
    assert 'list-layers' in result.output
    assert 'set-extent' in result.output
    assert 'export' in result.output
    assert 'symbolize' in result.output
    assert 'label' in result.output


def test_map_create_help(runner):
    """map create --help shows options."""
    result = runner.invoke(cli, ['map', 'create', '--help'])
    assert result.exit_code == 0
    assert '--project' in result.output


def test_map_export_help(runner):
    """map export --help shows format and DPI options."""
    result = runner.invoke(cli, ['map', 'export', '--help'])
    assert result.exit_code == 0
    assert '--format' in result.output
    assert '--dpi' in result.output


def test_map_symbolize_help(runner):
    """map symbolize --help shows symbology options."""
    result = runner.invoke(cli, ['map', 'symbolize', '--help'])
    assert result.exit_code == 0
    assert '--type' in result.output
    assert '--color-ramp' in result.output


def test_map_add_layer_missing_project(tmp_path, runner):
    """map add-layer without --project shows error (JSON output)."""
    data = tmp_path / "data.shp"
    data.touch()
    result = runner.invoke(cli, ['map', 'add-layer', 'MyMap', str(data)])
    assert 'error' in result.output.lower() or result.exit_code != 0
