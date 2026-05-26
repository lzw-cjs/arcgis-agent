"""Tests for CLI options, flags, and exit codes."""
import sys

import click
import pytest

from arcgis_agent.cli import cli, main
from arcgis_agent.exceptions import UserError, SystemError_, ArcGISError


def test_help(runner):
    """--help shows all global options."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert '--json' in result.output
    assert '--verbose' in result.output
    assert '--quiet' in result.output
    assert '--version' in result.output


def test_version(runner):
    """--version prints version string."""
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'arcgis-agent' in result.output
    assert '0.1.0' in result.output


def test_json_flag(runner):
    """--json flag sets ctx.obj['json'] to True."""
    @cli.command("test-json-flag")
    @click.pass_context
    def test_cmd(ctx):
        click.echo(f"json={ctx.obj.get('json', False)}")

    try:
        result = runner.invoke(cli, ['--json', 'test-json-flag'])
        assert result.exit_code == 0
        assert 'json=True' in result.output
    finally:
        cli.commands.pop("test-json-flag", None)


def test_verbose_quiet_conflict(runner):
    """--verbose and --quiet together exits 1 with error message."""
    result = runner.invoke(cli, ['--verbose', '--quiet'])
    assert result.exit_code == 1
    assert 'mutually exclusive' in result.output


def test_utf8_stdout_encoding():
    """sys.stdout.encoding is utf-8 after importing cli module."""
    enc = sys.stdout.encoding
    assert enc is not None
    assert enc.lower().replace('-', '') in ('utf8', 'utf_8')


def test_exit_code_user_error(monkeypatch):
    """main() exits with code 1 for UserError."""
    @cli.command("test-raise-user")
    def cmd():
        raise UserError("test user error")

    try:
        monkeypatch.setattr(sys, 'argv', ['arcgis-agent', 'test-raise-user'])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    finally:
        cli.commands.pop("test-raise-user", None)


def test_exit_code_system_error(monkeypatch):
    """main() exits with code 2 for SystemError_."""
    @cli.command("test-raise-system")
    def cmd():
        raise SystemError_("test system error")

    try:
        monkeypatch.setattr(sys, 'argv', ['arcgis-agent', 'test-raise-system'])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2
    finally:
        cli.commands.pop("test-raise-system", None)


def test_exit_code_arcgis_error(monkeypatch):
    """main() exits with code 3 for ArcGISError."""
    @cli.command("test-raise-arcgis")
    def cmd():
        raise ArcGISError(code="GP_FAIL", message="test arcgis error")

    try:
        monkeypatch.setattr(sys, 'argv', ['arcgis-agent', 'test-raise-arcgis'])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 3
    finally:
        cli.commands.pop("test-raise-arcgis", None)
