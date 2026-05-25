"""Data commands: discovery and management operations."""
import click

from arcgis_agent.models.result import Result


def _make_service():
    """Create DataDiscoveryService, returning (svc, None) or (None, error_json)."""
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return DataDiscoveryService()


def _run(fn):
    """Run fn(service) -> Result, catching init errors as JSON."""
    try:
        svc = _make_service()
        result = fn(svc)
    except Exception as e:
        result = Result.from_exception(e)
    click.echo(result.to_json())


def register(cli_group: click.Group) -> None:
    """Register data commands with CLI."""

    @cli_group.group("data")
    def data_group():
        """Discover and inspect workspace data."""
        pass

    @data_group.command("list")
    @click.option("--workspace", "-w", default=None,
                  help="Workspace path (overrides configured workspace).")
    @click.option("--type", "dataset_type", default=None,
                  help="Filter by type: FeatureClass, Table, RasterDataset, FeatureDataset.")
    @click.option("--pattern", default=None,
                  help="Glob pattern for name filtering (e.g., 'roads*').")
    @click.pass_context
    def data_list(ctx, workspace, dataset_type, pattern):
        """List datasets in workspace (DISC-01)."""
        _run(lambda svc: svc.list_datasets(
            workspace=workspace,
            dataset_type=dataset_type,
            name_pattern=pattern,
        ))

    @data_group.command("describe")
    @click.argument("path")
    @click.pass_context
    def data_describe(ctx, path):
        """Describe dataset metadata (DISC-02).

        PATH is the full path to the dataset.
        """
        _run(lambda svc: svc.describe(path))

    @data_group.command("fields")
    @click.argument("path")
    @click.pass_context
    def data_fields(ctx, path):
        """List field definitions (DISC-03).

        PATH is the full path to the dataset.
        """
        _run(lambda svc: svc.get_fields(path))

    @data_group.command("extent")
    @click.argument("path")
    @click.pass_context
    def data_extent(ctx, path):
        """Get spatial extent (DISC-04).

        PATH is the full path to the dataset.
        Returns xmin, ymin, xmax, ymax, spatialReference.
        """
        _run(lambda svc: svc.get_extent(path))

    @data_group.command("count")
    @click.argument("path")
    @click.pass_context
    def data_count(ctx, path):
        """Get record count (DISC-05).

        PATH is the full path to the dataset.
        """
        _run(lambda svc: svc.get_count(path))

    # --- Management commands (MGMT-01 through MGMT-04) ---

    @data_group.command("copy")
    @click.argument("source")
    @click.argument("destination")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if destination already exists.")
    @click.pass_context
    def data_copy(ctx, source, destination, no_overwrite):
        """Copy dataset (MGMT-01)."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        result = svc.copy(source, destination, no_overwrite=no_overwrite)
        click.echo(result.to_json())

    @data_group.command("delete")
    @click.argument("path")
    @click.pass_context
    def data_delete(ctx, path):
        """Delete dataset (MGMT-02)."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        result = svc.delete(path)
        click.echo(result.to_json())

    @data_group.command("rename")
    @click.argument("old_path")
    @click.argument("new_name")
    @click.pass_context
    def data_rename(ctx, old_path, new_name):
        """Rename dataset (MGMT-03).

        OLD_PATH is the full path to the dataset.
        NEW_NAME is the new name (not full path).
        """
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        result = svc.rename(old_path, new_name)
        click.echo(result.to_json())

    @data_group.command("convert")
    @click.argument("source")
    @click.argument("destination")
    @click.option("--format", "output_format", required=True,
                  help="Output format: shp, gdb, csv, geojson.")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if destination already exists.")
    @click.pass_context
    def data_convert(ctx, source, destination, output_format, no_overwrite):
        """Convert dataset format (MGMT-04)."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        result = svc.convert(source, destination, output_format,
                             no_overwrite=no_overwrite)
        click.echo(result.to_json())
