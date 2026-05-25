"""Geoprocessing commands: buffer, clip, intersect, union, dissolve, spatial-join, merge, project, select."""
import click

from arcgis_agent.models.result import Result


def register(cli_group: click.Group) -> None:
    """Register geoprocessing commands with CLI."""
    from arcgis_agent.commands.data import data_group

    # --- GEO-01: Select by Attribute ---
    @data_group.command("select")
    @click.argument("input_fc")
    @click.argument("output")
    @click.option("--where", required=True, help="SQL WHERE clause for attribute selection.")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_select(ctx, input_fc, output, where, no_overwrite):
        """Select features by attribute (GEO-01).

        INPUT_FC is the input feature class path.
        OUTPUT is the output feature class path.
        Example: data select roads.shp major_roads.shp --where "LANES >= 4"
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.select_by_attribute(input_fc, output, where,
                                          no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-02: Clip ---
    @data_group.command("clip")
    @click.argument("input_fc")
    @click.argument("clip_features")
    @click.argument("output")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_clip(ctx, input_fc, clip_features, output, no_overwrite):
        """Clip features to boundary (GEO-02).

        INPUT_FC is the input feature class.
        CLIP_FEATURES is the clipping boundary (must be polygon).
        OUTPUT is the output feature class path.
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.clip(input_fc, clip_features, output,
                          no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-03: Buffer (per D-05 units, D-06 separate --distance/--unit, D-07 dissolve-field) ---
    @data_group.command("buffer")
    @click.argument("input_fc")
    @click.argument("output")
    @click.option("--distance", type=float, required=True,
                  help="Buffer distance (numeric).")
    @click.option("--unit", default="Meters",
                  type=click.Choice(["Meters", "Kilometers", "Feet", "Miles",
                                     "Yards", "DecimalDegrees"]),
                  help="Distance unit (default: Meters). Per D-05.")
    @click.option("--dissolve-field", default=None,
                  help="Dissolve overlapping buffers by this field. Per D-07.")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_buffer(ctx, input_fc, output, distance, unit, dissolve_field, no_overwrite):
        """Create buffer around features (GEO-03).

        INPUT_FC is the input feature class.
        OUTPUT is the output feature class path.
        Example: data buffer points.shp buffer.shp --distance 100 --unit Meters
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.buffer(input_fc, output, distance, unit,
                            dissolve_field=dissolve_field,
                            no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-04: Intersect (per D-09 comma-separated, D-12 min 2 inputs) ---
    @data_group.command("intersect")
    @click.argument("inputs")
    @click.argument("output")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_intersect(ctx, inputs, output, no_overwrite):
        """Intersect multiple feature classes (GEO-04).

        INPUTS is a comma-separated list of feature class paths.
        Example: data intersect a.shp,b.shp,c.shp out.shp
        """
        input_list = [i.strip() for i in inputs.split(",")]
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.intersect(input_list, output, no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-05: Union (per D-09 comma-separated) ---
    @data_group.command("union")
    @click.argument("inputs")
    @click.argument("output")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_union(ctx, inputs, output, no_overwrite):
        """Union (overlay) multiple polygon feature classes (GEO-05).

        INPUTS is a comma-separated list of polygon feature class paths.
        Example: data union parcels.shp,zoning.shp combined.shp
        """
        input_list = [i.strip() for i in inputs.split(",")]
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.union(input_list, output, no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-06: Dissolve ---
    @data_group.command("dissolve")
    @click.argument("input_fc")
    @click.argument("output")
    @click.option("--field", required=True, help="Field to dissolve by.")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_dissolve(ctx, input_fc, output, field, no_overwrite):
        """Dissolve features by field (GEO-06).

        INPUT_FC is the input feature class.
        OUTPUT is the output feature class path.
        Example: data dissolve counties.shp regions.shp --field STATE
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.dissolve(input_fc, output, field,
                              no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-07: Spatial Join ---
    @data_group.command("spatial-join")
    @click.argument("target_features")
    @click.argument("join_features")
    @click.argument("output")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_spatial_join(ctx, target_features, join_features, output, no_overwrite):
        """Spatial join: transfer attributes based on spatial relationship (GEO-07).

        TARGET_FEATURES receives the joined attributes.
        JOIN_FEATURES provides the attributes to join.
        OUTPUT is the output feature class path.
        Example: data spatial-join points.shp polygons.shp joined.shp
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.spatial_join(target_features, join_features, output,
                                   no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-08: Merge (per D-09 comma-separated, D-12 min 2 inputs) ---
    @data_group.command("merge")
    @click.argument("inputs")
    @click.argument("output")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_merge(ctx, inputs, output, no_overwrite):
        """Merge multiple feature classes into one (GEO-08).

        INPUTS is a comma-separated list of feature class paths.
        Example: data merge region1.shp,region2.shp combined.shp
        """
        input_list = [i.strip() for i in inputs.split(",")]
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.merge(input_list, output, no_overwrite=no_overwrite)
        click.echo(result.to_json())

    # --- GEO-09: Project ---
    @data_group.command("project")
    @click.argument("input_fc")
    @click.argument("output")
    @click.option("--sr", required=True,
                  help="Target spatial reference (WKID integer, e.g., 4326 for WGS84).")
    @click.option("--no-overwrite", is_flag=True, default=False,
                  help="Fail if output already exists.")
    @click.pass_context
    def data_project(ctx, input_fc, output, sr, no_overwrite):
        """Project features to a different coordinate system (GEO-09).

        INPUT_FC is the input feature class.
        OUTPUT is the output feature class path.
        --sr is the target spatial reference WKID.
        Example: data project input.shp output.shp --sr 4326
        """
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        result = svc.project(input_fc, output, sr,
                             no_overwrite=no_overwrite)
        click.echo(result.to_json())
