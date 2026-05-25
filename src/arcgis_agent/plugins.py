"""Plugin loader via importlib.metadata entry_points."""
import logging
import click
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


def load_plugins(cli_group: click.Group) -> None:
    """Discover and register all command plugins.

    Uses entry_points(group="arcgis_agent.commands") to find registered
    plugins. Each plugin must expose a register(cli_group) function.
    Plugin failures are logged as warnings but never crash the CLI.
    """
    eps = entry_points(group="arcgis_agent.commands")
    for ep in sorted(eps, key=lambda e: e.name):
        try:
            register_fn = ep.load()
            register_fn(cli_group)
            logger.debug("Loaded plugin: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load plugin '%s': %s", ep.name, e)
