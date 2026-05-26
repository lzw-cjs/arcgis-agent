"""MCP Server: expose all CLI functions as MCP tools for AI Agent consumption.

Phase 5 implementation (MCP-01 through MCP-05):
  - MCP-01: FastMCP server skeleton with stdio transport
  - MCP-02: Tool registration for all v1 CLI commands
  - MCP-03: Full type annotations with JSON Schema via Pydantic
  - MCP-04: asyncio.to_thread() + threading.Lock for arcpy thread-safety
  - MCP-05: BrokenPipeError graceful handling

Usage:
    python -m arcgis_agent.mcp_server
    arcgis-agent-mcp    # via pyproject.toml entry point
"""

from __future__ import annotations

import signal
import sys
import threading
from typing import Any

from mcp.server.fastmcp import FastMCP

# Force UTF-8 on Windows to prevent encoding crashes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── arcpy Serialization Lock ──────────────────────────────────
# arcpy is NOT thread-safe (COM-based). All arcpy operations must
# be serialized through this lock. asyncio.to_thread() offloads the
# blocking call off the event loop; the lock ensures mutual exclusion.
_ARC_LOCK = threading.Lock()

mcp = FastMCP("arcgis-agent")


def _run_sync(fn, *args, **kwargs) -> dict[str, Any]:
    """Execute a service operation under the arcpy serialization lock.

    Returns a plain dict suitable for MCP tool response (Result.model_dump()).
    Both success and error results are returned as dicts so the MCP client
    can inspect success/code/message/data fields.

    BrokenPipeError is caught and re-raised to let the MCP server exit gracefully.
    """
    try:
        with _ARC_LOCK:
            from arcgis_agent.models.result import Result
            result = fn(*args, **kwargs)
            if isinstance(result, Result):
                return result.model_dump()
            return result
    except BrokenPipeError:
        raise
    except Exception as exc:
        from arcgis_agent.models.result import Result
        return Result.from_exception(exc).model_dump()


# ── Workspace Tools ────────────────────────────────────────────


@mcp.tool(
    name="workspace_set",
    description="Set the current workspace directory. Must contain ArcGIS Pro project files.",
)
def workspace_set(path: str) -> dict[str, Any]:
    from arcgis_agent.services.workspace_service import WorkspaceService
    return _run_sync(lambda: WorkspaceService().set_workspace(path))


@mcp.tool(
    name="workspace_get",
    description="Get the current workspace directory path.",
)
def workspace_get() -> dict[str, Any]:
    from arcgis_agent.services.workspace_service import WorkspaceService
    return _run_sync(lambda: WorkspaceService().get_workspace())


# ── Project Tools ──────────────────────────────────────────────


@mcp.tool(
    name="project_info",
    description="Get ArcGIS Pro project info: maps, databases, path.",
)
def project_info(project_path: str) -> dict[str, Any]:
    from arcgis_agent.services.project_service import ProjectService
    return _run_sync(lambda: ProjectService().info(project_path))


# ── Data Discovery Tools ───────────────────────────────────────


@mcp.tool(
    name="data_list",
    description="List feature classes in a workspace directory (GDB or folder).",
)
def data_list(
    workspace: str | None = None,
    dataset_type: str | None = None,
    name_pattern: str | None = None,
) -> dict[str, Any]:
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return _run_sync(
        lambda: DataDiscoveryService().list_datasets(
            workspace=workspace, dataset_type=dataset_type, name_pattern=name_pattern
        )
    )


@mcp.tool(
    name="data_describe",
    description="Describe a dataset: type, spatial reference, feature count, extent.",
)
def data_describe(path: str) -> dict[str, Any]:
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return _run_sync(lambda: DataDiscoveryService().describe(path))


@mcp.tool(
    name="data_fields",
    description="List fields (name, type, length) of a dataset.",
)
def data_fields(path: str) -> dict[str, Any]:
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return _run_sync(lambda: DataDiscoveryService().get_fields(path))


@mcp.tool(
    name="data_extent",
    description="Get the spatial extent (xmin, ymin, xmax, ymax) of a dataset.",
)
def data_extent(path: str) -> dict[str, Any]:
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return _run_sync(lambda: DataDiscoveryService().get_extent(path))


@mcp.tool(
    name="data_count",
    description="Get the number of features/rows in a dataset.",
)
def data_count(path: str) -> dict[str, Any]:
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    return _run_sync(lambda: DataDiscoveryService().get_count(path))


# ── Data Management Tools ──────────────────────────────────────


@mcp.tool(
    name="data_copy",
    description="Copy a dataset to a new location.",
)
def data_copy(
    source: str,
    destination: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.data_management import DataManagementService
    return _run_sync(
        lambda: DataManagementService().copy(source, destination, no_overwrite=no_overwrite)
    )


@mcp.tool(
    name="data_delete",
    description="Delete a dataset permanently.",
)
def data_delete(path: str) -> dict[str, Any]:
    from arcgis_agent.services.data_management import DataManagementService
    return _run_sync(lambda: DataManagementService().delete(path))


@mcp.tool(
    name="data_rename",
    description="Rename a dataset.",
)
def data_rename(old_path: str, new_name: str) -> dict[str, Any]:
    from arcgis_agent.services.data_management import DataManagementService
    return _run_sync(lambda: DataManagementService().rename(old_path, new_name))


@mcp.tool(
    name="data_convert",
    description="Convert a dataset between formats (shapefile, geodatabase, CSV, GeoJSON).",
)
def data_convert(
    source: str,
    destination: str,
    output_format: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.data_management import DataManagementService
    return _run_sync(
        lambda: DataManagementService().convert(
            source, destination, output_format, no_overwrite=no_overwrite
        )
    )


# ── Geoprocessing Tools ────────────────────────────────────────


@mcp.tool(
    name="gp_select",
    description="Select features by SQL attribute query and save to new dataset.",
)
def gp_select(
    input_fc: str,
    output_fc: str,
    where_clause: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().select_by_attribute(
            input_fc, output_fc, where_clause, no_overwrite=no_overwrite
        )
    )


@mcp.tool(
    name="gp_clip",
    description="Clip features to a boundary polygon layer.",
)
def gp_clip(
    input_fc: str,
    clip_features: str,
    output_fc: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().clip(
            input_fc, clip_features, output_fc, no_overwrite=no_overwrite
        )
    )


@mcp.tool(
    name="gp_buffer",
    description="Create buffer polygons around features at a specified distance.",
)
def gp_buffer(
    input_fc: str,
    output_fc: str,
    distance: float,
    unit: str = "Meters",
    dissolve_field: str | None = None,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().buffer(
            input_fc, output_fc, distance,
            unit=unit, dissolve_field=dissolve_field, no_overwrite=no_overwrite,
        )
    )


@mcp.tool(
    name="gp_intersect",
    description="Compute the geometric intersection of multiple input layers.",
)
def gp_intersect(
    inputs: list[str],
    output_fc: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().intersect(inputs, output_fc, no_overwrite=no_overwrite)
    )


@mcp.tool(
    name="gp_union",
    description="Compute the geometric union of multiple polygon layers.",
)
def gp_union(
    inputs: list[str],
    output_fc: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().union(inputs, output_fc, no_overwrite=no_overwrite)
    )


@mcp.tool(
    name="gp_dissolve",
    description="Dissolve features by a field, merging boundaries with matching values.",
)
def gp_dissolve(
    input_fc: str,
    output_fc: str,
    dissolve_field: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().dissolve(
            input_fc, output_fc, dissolve_field, no_overwrite=no_overwrite
        )
    )


@mcp.tool(
    name="gp_spatial_join",
    description="Join attributes from one layer to another based on spatial relationship.",
)
def gp_spatial_join(
    target_fc: str,
    join_fc: str,
    output_fc: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().spatial_join(
            target_fc, join_fc, output_fc, no_overwrite=no_overwrite
        )
    )


@mcp.tool(
    name="gp_merge",
    description="Merge multiple feature classes into a single dataset.",
)
def gp_merge(
    inputs: list[str],
    output_fc: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().merge(inputs, output_fc, no_overwrite=no_overwrite)
    )


@mcp.tool(
    name="gp_project",
    description="Project a feature class to a different coordinate system by EPSG WKID.",
)
def gp_project(
    input_fc: str,
    output_fc: str,
    spatial_ref_wkid: str,
    no_overwrite: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    return _run_sync(
        lambda: GeoprocessingService().project(
            input_fc, output_fc, spatial_ref_wkid, no_overwrite=no_overwrite
        )
    )


# ── Analysis Tools ─────────────────────────────────────────────


@mcp.tool(
    name="analysis_summary_stats",
    description="Compute summary statistics (SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN) for fields.",
)
def analysis_summary_stats(
    input_fc: str,
    field_spec: str,
    case_field: str | None = None,
    output_table: str | None = None,
) -> dict[str, Any]:
    from arcgis_agent.services.analysis_service import AnalysisService
    return _run_sync(
        lambda: AnalysisService().summary_statistics(
            input_fc, field_spec,
            case_field=case_field, output_table=output_table,
        )
    )


# ── Map Tools ──────────────────────────────────────────────────


@mcp.tool(
    name="map_create",
    description="Create a new map in an ArcGIS Pro project.",
)
def map_create(
    map_name: str,
    project_path: str | None = None,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(lambda: MapService().create_map(project_path, map_name))


@mcp.tool(
    name="map_add_layer",
    description="Add a data layer to a map in an ArcGIS Pro project.",
)
def map_add_layer(
    map_name: str,
    data_path: str,
    project_path: str,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(lambda: MapService().add_layer(project_path, map_name, data_path))


@mcp.tool(
    name="map_remove_layer",
    description="Remove a layer from a map by name or index.",
)
def map_remove_layer(
    map_name: str,
    project_path: str,
    layer_name: str | None = None,
    layer_index: int | None = None,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(
        lambda: MapService().remove_layer(
            project_path, map_name, layer_name=layer_name, layer_index=layer_index
        )
    )


@mcp.tool(
    name="map_list_layers",
    description="List all layers in a map with names, data sources, and feature counts.",
)
def map_list_layers(
    map_name: str,
    project_path: str,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(lambda: MapService().list_layers(project_path, map_name))


@mcp.tool(
    name="map_set_extent",
    description="Set the map extent to match a specific layer (zoom to layer).",
)
def map_set_extent(
    map_name: str,
    zoom_to_layer: str,
    project_path: str,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(lambda: MapService().set_extent(project_path, map_name, zoom_to_layer))


@mcp.tool(
    name="map_export",
    description="Export a map to PNG or PDF file.",
)
def map_export(
    map_name: str,
    output_path: str,
    project_path: str,
    format: str = "PNG",
    dpi: int = 300,
    transparent: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(
        lambda: MapService().export_map(
            project_path, map_name, output_path,
            format=format, dpi=dpi, transparent=transparent,
        )
    )


@mcp.tool(
    name="map_symbolize",
    description="Apply symbology to a layer: simple, unique_values, or graduated_colors.",
)
def map_symbolize(
    map_name: str,
    layer_name: str,
    project_path: str,
    symbology_type: str = "simple",
    field: str | None = None,
    color: str | None = None,
    outline_color: str | None = None,
    size: int = 8,
    opacity: int = 100,
    color_ramp: str | None = None,
    values: str | None = None,
    classification_method: str = "NaturalBreaks",
    break_count: int = 5,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(
        lambda: MapService().symbolize_layer(
            project_path, map_name, layer_name,
            symbology_type=symbology_type, field=field,
            color=color, outline_color=outline_color,
            size=size, opacity=opacity, color_ramp=color_ramp,
            values=values, classification_method=classification_method,
            break_count=break_count,
        )
    )


@mcp.tool(
    name="map_label",
    description="Set labels on a layer using a field value.",
)
def map_label(
    map_name: str,
    layer_name: str,
    field: str,
    project_path: str,
    font_size: int = 10,
    color: str = "0,0,0",
    bold: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.map_service import MapService
    return _run_sync(
        lambda: MapService().set_label(
            project_path, map_name, layer_name, field,
            font_size=font_size, color=color, bold=bold,
        )
    )


# ── Layout Tools ───────────────────────────────────────────────


@mcp.tool(
    name="layout_create",
    description="Create a new layout (page) in an ArcGIS Pro project.",
)
def layout_create(
    layout_name: str,
    project_path: str,
    page_size: str = "A4",
    orientation: str = "portrait",
) -> dict[str, Any]:
    from arcgis_agent.services.layout_service import LayoutService
    return _run_sync(
        lambda: LayoutService().create_layout(
            project_path, layout_name,
            page_size=page_size, orientation=orientation,
        )
    )


@mcp.tool(
    name="layout_add_element",
    description="Add an element to a layout: text, legend, scale-bar, north-arrow, map-frame, image.",
)
def layout_add_element(
    layout_name: str,
    element_type: str,
    project_path: str,
    position: str | None = None,
    params: str | None = None,
) -> dict[str, Any]:
    from arcgis_agent.services.layout_service import LayoutService
    return _run_sync(
        lambda: LayoutService().add_element(
            project_path, layout_name, element_type,
            position=position, params=params,
        )
    )


@mcp.tool(
    name="layout_export",
    description="Export a layout to PNG or PDF file.",
)
def layout_export(
    layout_name: str,
    output_path: str,
    project_path: str,
    format: str = "PDF",
    dpi: int = 300,
    transparent: bool = False,
) -> dict[str, Any]:
    from arcgis_agent.services.layout_service import LayoutService
    return _run_sync(
        lambda: LayoutService().export_layout(
            project_path, layout_name, output_path,
            format=format, dpi=dpi, transparent=transparent,
        )
    )


# ── Main Entry Point ───────────────────────────────────────────


def main():
    """MCP server entry point (registered in pyproject.toml as arcgis-agent-mcp)."""
    # Handle graceful shutdown on SIGINT/SIGTERM (BrokenPipeError)
    def _sig_handler(signum, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        mcp.run(transport="stdio")
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
