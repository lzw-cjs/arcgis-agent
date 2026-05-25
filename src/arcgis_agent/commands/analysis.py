"""Analysis commands: summary statistics."""
import click

from arcgis_agent.models.result import Result


def register(cli_group: click.Group) -> None:
    """Register analysis commands with CLI."""

    @cli_group.group("analysis")
    def analysis_group():
        """Spatial analysis operations."""
        pass

    # --- GEO-10: Summary Statistics ---
    @analysis_group.command("summary-stats")
    @click.argument("input_fc")
    @click.option("--field", required=True,
                  help="Field statistics specification: 'field1:STAT,field2:STAT'. "
                       "Valid stats: SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN. "
                       "Example: --field pop:SUM,area:MEAN")
    @click.option("--case-field", default=None,
                  help="Group statistics by this field (optional).")
    @click.option("--output", "output_table", default=None,
                  help="Output table path. Auto-generated if not specified.")
    @click.pass_context
    def analysis_summary_stats(ctx, input_fc, field, case_field, output_table):
        """Compute summary statistics on a feature class or table (GEO-10).

        INPUT_FC is the input feature class or table path.
        Example: analysis summary-stats census.shp --field pop:SUM,area:MEAN --case-field STATE
        """
        from arcgis_agent.services.analysis_service import AnalysisService
        svc = AnalysisService()
        result = svc.summary_statistics(
            input_fc, field,
            case_field=case_field,
            output_table=output_table
        )
        click.echo(result.to_json())
