"""CLI integration tests for 'layout' commands."""
from click.testing import CliRunner
from arcgis_agent.cli import cli


def test_layout_help(runner):
    """layout --help shows available subcommands."""
    result = runner.invoke(cli, ['layout', '--help'])
    assert result.exit_code == 0
    assert 'create' in result.output
    assert 'add-element' in result.output
    assert 'export' in result.output


def test_layout_create_help(runner):
    """layout create --help shows page options."""
    result = runner.invoke(cli, ['layout', 'create', '--help'])
    assert result.exit_code == 0
    assert '--page-size' in result.output
    assert '--orientation' in result.output


def test_layout_add_element_help(runner):
    """layout add-element --help shows element type options."""
    result = runner.invoke(cli, ['layout', 'add-element', '--help'])
    assert result.exit_code == 0
    assert '--type' in result.output
    assert '--params' in result.output
    assert '--position' in result.output
    assert 'text' in result.output
    assert 'legend' in result.output


def test_layout_export_help(runner):
    """layout export --help shows export options."""
    result = runner.invoke(cli, ['layout', 'export', '--help'])
    assert result.exit_code == 0
    assert '--format' in result.output
    assert '--dpi' in result.output


def test_layout_create_missing_project(runner):
    """layout create without --project shows error."""
    result = runner.invoke(cli, ['layout', 'create', 'MyLayout'])
    assert result.exit_code != 0
