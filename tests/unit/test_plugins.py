"""Tests for plugin loader."""
import click
from unittest.mock import MagicMock

from arcgis_agent.plugins import load_plugins


def test_load_plugins_no_plugins(monkeypatch):
    """load_plugins with empty entry_points does not crash."""
    monkeypatch.setattr(
        "arcgis_agent.plugins.entry_points",
        lambda group=None: []
    )

    @click.group()
    def test_group():
        pass

    load_plugins(test_group)  # Should not raise


def test_load_plugins_discovers_plugins(monkeypatch):
    """load_plugins calls register(cli_group) for each discovered plugin."""
    registered = []

    def mock_register(group):
        registered.append(group)

    mock_ep = MagicMock()
    mock_ep.name = "test_plugin"
    mock_ep.load.return_value = mock_register

    monkeypatch.setattr(
        "arcgis_agent.plugins.entry_points",
        lambda group=None: [mock_ep]
    )

    @click.group()
    def test_group():
        pass

    load_plugins(test_group)
    assert len(registered) == 1
    assert registered[0] is test_group


def test_load_plugins_failure_no_crash(monkeypatch):
    """load_plugins logs warning but does not crash on plugin import failure."""
    mock_ep = MagicMock()
    mock_ep.name = "broken_plugin"
    mock_ep.load.side_effect = ImportError("no such module")

    monkeypatch.setattr(
        "arcgis_agent.plugins.entry_points",
        lambda group=None: [mock_ep]
    )

    @click.group()
    def test_group():
        pass

    # Should not raise despite the broken plugin
    load_plugins(test_group)
