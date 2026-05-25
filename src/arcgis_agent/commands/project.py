"""Project commands: view project information."""
import click


def register(cli_group: click.Group) -> None:
    """Register project commands with CLI."""

    @cli_group.group("project")
    def project_group():
        """Manage ArcGIS Pro projects."""
        pass

    @project_group.command("info")
    @click.option("--project", "-p", "project_path", required=True,
                  help="Path to .aprx project file.")
    @click.pass_context
    def project_info(ctx, project_path):
        """Show project information (maps, databases)."""
        from arcgis_agent.services.project_service import ProjectService
        svc = ProjectService()
        result = svc.info(project_path)
        click.echo(result.to_json())
