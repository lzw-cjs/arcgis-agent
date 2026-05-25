"""Click main entry point for arcgis-agent CLI.

Phase 1 will implement the full CLI framework.
This is a placeholder to verify entry_points work.
"""

import click


@click.group()
@click.version_option()
def cli():
    """AI Agent CLI for ArcGIS Pro automation."""
    pass
