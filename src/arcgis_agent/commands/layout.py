"""Layout commands: creation, element placement, and export."""
import click

from arcgis_agent.models.result import Result


def _make_service():
    from arcgis_agent.services.layout_service import LayoutService
    return LayoutService()


def _run(fn):
    try:
        svc = _make_service()
        result = fn(svc)
    except Exception as e:
        result = Result.from_exception(e)
    click.echo(result.to_json())


def register(cli_group: click.Group) -> None:
    """Register layout commands with CLI."""

    @cli_group.group("layout")
    def layout_group():
        """Layout creation and export commands."""
        pass

    @layout_group.command("create")
    @click.argument("name")
    @click.option("--page-size", default="A4",
                  type=click.Choice(["A4", "A3", "Letter", "Tabloid"]),
                  help="Page size (default: A4, D-26).")
    @click.option("--orientation", default="portrait",
                  type=click.Choice(["portrait", "landscape"]),
                  help="Page orientation (default: portrait).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def layout_create(ctx, name, page_size, orientation, project):
        """Create a new layout (MAP-09)."""
        _run(lambda svc: svc.create_layout(
            project, name, page_size, orientation))

    @layout_group.command("add-element")
    @click.argument("layout_name")
    @click.option("--type", "-t", "element_type", required=True,
                  type=click.Choice(["text", "legend", "scale-bar",
                                     "north-arrow", "map-frame", "image"]),
                  help="Element type (D-18).")
    @click.option("--position", default=None,
                  type=click.Choice(["top-left", "top-center", "top-right",
                                     "center-left", "center", "center-right",
                                     "bottom-left", "bottom-center", "bottom-right"]),
                  help="Preset position (D-19).")
    @click.option("--params", default=None,
                  help='Key=value pairs, comma-separated (D-27). '
                       'Example: "text=My Title,font_size=24,color=0,0,0,bold=true"')
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def layout_add_element(ctx, layout_name, element_type, position, params, project):
        """Add an element to a layout (MAP-10)."""
        _run(lambda svc: svc.add_element(
            project, layout_name, element_type,
            position=position, params=params))

    @layout_group.command("export")
    @click.argument("layout_name")
    @click.argument("output")
    @click.option("--format", "-f", "fmt", default="PDF",
                  type=click.Choice(["PNG", "PDF"], case_sensitive=False),
                  help="Export format (default: PDF).")
    @click.option("--dpi", type=click.Choice(["96", "150", "300", "600"]),
                  default="300", help="Output resolution (96|150|300|600).")
    @click.option("--transparent", is_flag=True, default=False,
                  help="Use transparent background (PNG only, D-31).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def layout_export(ctx, layout_name, output, fmt, dpi, transparent, project):
        """Export a layout to PNG or PDF (MAP-11)."""
        _run(lambda svc: svc.export_layout(
            project, layout_name, output, fmt, int(dpi), transparent))
