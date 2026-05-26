"""Map commands: creation, layer management, symbology, labeling, and export."""
import click

from arcgis_agent.models.result import Result


def _make_service():
    from arcgis_agent.services.map_service import MapService
    return MapService()


def _run(fn):
    try:
        svc = _make_service()
        result = fn(svc)
    except Exception as e:
        result = Result.from_exception(e)
    click.echo(result.to_json())


def register(cli_group: click.Group) -> None:
    """Register map commands with CLI."""

    @cli_group.group("map")
    def map_group():
        """Map creation and management commands."""
        pass

    @map_group.command("create")
    @click.argument("name")
    @click.option("--project", "-p", default=None,
                  help="Path to .aprx file (overrides workspace auto-detect).")
    @click.pass_context
    def map_create(ctx, name, project):
        """Create a new map (MAP-01)."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.create_map(project, name)
        click.echo(result.to_json())

    @map_group.command("add-layer")
    @click.argument("map_name")
    @click.argument("data_path")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_add_layer(ctx, map_name, data_path, project):
        """Add a data layer to a map (MAP-02)."""
        _run(lambda svc: svc.add_layer(project, map_name, data_path))

    @map_group.command("remove-layer")
    @click.argument("map_name")
    @click.option("--layer", "-l", default=None,
                  help="Layer name to remove (D-02: name-first).")
    @click.option("--layer-index", type=int, default=None,
                  help="Layer index to remove (fallback, 0-based).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_remove_layer(ctx, map_name, layer, layer_index, project):
        """Remove a layer from a map by name or index (MAP-03)."""
        _run(lambda svc: svc.remove_layer(project, map_name, layer, layer_index))

    @map_group.command("list-layers")
    @click.argument("map_name")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_list_layers(ctx, map_name, project):
        """List all layers in a map (MAP-04)."""
        _run(lambda svc: svc.list_layers(project, map_name))

    @map_group.command("set-extent")
    @click.argument("map_name")
    @click.option("--zoom-to", "-z", required=True,
                  help="Layer name to zoom the map extent to (D-03).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_set_extent(ctx, map_name, zoom_to, project):
        """Set map extent by zooming to a layer (MAP-05)."""
        _run(lambda svc: svc.set_extent(project, map_name, zoom_to))

    @map_group.command("export")
    @click.argument("map_name")
    @click.argument("output")
    @click.option("--format", "-f", "fmt", default="PNG",
                  type=click.Choice(["PNG", "PDF"], case_sensitive=False),
                  help="Export format (PNG or PDF).")
    @click.option("--dpi", type=click.Choice(["96", "150", "300", "600"]),
                  default="300", help="Output resolution (96|150|300|600).")
    @click.option("--transparent", is_flag=True, default=False,
                  help="Use transparent background (PNG only).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_export(ctx, map_name, output, fmt, dpi, transparent, project):
        """Export a map to PNG or PDF (MAP-06)."""
        _run(lambda svc: svc.export_map(
            project, map_name, output, fmt, int(dpi), transparent))

    @map_group.command("symbolize")
    @click.argument("map_name")
    @click.argument("layer_name")
    @click.option("--type", "-t", "symbology_type", required=True,
                  type=click.Choice(["simple", "unique_values", "graduated_colors"]),
                  help="Symbolization type (MAP-07, D-09).")
    @click.option("--field", "-f", default=None,
                  help="Field name (required for unique_values and graduated_colors).")
    @click.option("--color", default=None,
                  help="Fill color as R,G,B (e.g. 255,0,0).")
    @click.option("--outline-color", default=None,
                  help="Outline color as R,G,B (e.g. 0,0,0).")
    @click.option("--size", type=int, default=8,
                  help="Symbol size in points (default: 8).")
    @click.option("--opacity", type=int, default=100,
                  help="Opacity 0-100 (default: 100).")
    @click.option("--color-ramp", default=None,
                  help="Color ramp name (e.g. 'Cyan to Purple').")
    @click.option("--values", default=None,
                  help="JSON string for manual value overrides.")
    @click.option("--classification-method", default="NaturalBreaks",
                  type=click.Choice(["NaturalBreaks", "Quantile", "EqualInterval"]),
                  help="Classification method (default: NaturalBreaks).")
    @click.option("--break-count", type=int, default=5,
                  help="Number of classes 2-7 (default: 5).")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_symbolize(ctx, map_name, layer_name, symbology_type, field, color,
                      outline_color, size, opacity, color_ramp, values,
                      classification_method, break_count, project):
        """Apply symbology to a layer (MAP-07)."""
        _run(lambda svc: svc.symbolize_layer(
            project, map_name, layer_name, symbology_type,
            field=field, color=color, outline_color=outline_color,
            size=size, opacity=opacity, color_ramp=color_ramp,
            values=values, classification_method=classification_method,
            break_count=break_count))

    @map_group.command("label")
    @click.argument("map_name")
    @click.argument("layer_name")
    @click.option("--field", "-f", required=True,
                  help="Field name to use for labels (D-16).")
    @click.option("--font-size", type=int, default=10,
                  help="Font size in points (default: 10).")
    @click.option("--color", default="0,0,0",
                  help="Label color as R,G,B (default: 0,0,0).")
    @click.option("--bold", is_flag=True, default=False,
                  help="Use bold font style.")
    @click.option("--project", "-p", required=True,
                  help="Path to .aprx file.")
    @click.pass_context
    def map_label(ctx, map_name, layer_name, field, font_size, color, bold, project):
        """Set labeling on a layer (MAP-08)."""
        _run(lambda svc: svc.set_label(
            project, map_name, layer_name, field,
            font_size=font_size, color=color, bold=bold))
