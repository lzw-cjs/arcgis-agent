"""Workspace commands: set and get current workspace."""
import click
from arcgis_agent.models.result import Result


def register(cli_group: click.Group) -> None:
    """Register workspace commands with CLI."""

    @cli_group.group("workspace")
    def workspace_group():
        """Manage the current workspace directory."""
        pass

    @workspace_group.command("set")
    @click.argument("path")
    @click.pass_context
    def workspace_set(ctx, path):
        """Set the current workspace directory.

        PATH must be an existing directory (folder or geodatabase).
        """
        from arcgis_agent.services.workspace_service import WorkspaceService
        svc = WorkspaceService()
        result = svc.set_workspace(path)
        click.echo(result.to_json())

    @workspace_group.command("get")
    @click.pass_context
    def workspace_get(ctx):
        """Show the current workspace directory."""
        from arcgis_agent.services.workspace_service import WorkspaceService
        svc = WorkspaceService()
        result = svc.get_workspace()
        click.echo(result.to_json())
