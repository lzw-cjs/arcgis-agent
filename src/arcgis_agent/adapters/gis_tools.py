"""GIS tool definitions for LLM function calling (Phase 7, Plan 07-03 Task 2).

Each tool is a LangChain StructuredTool with Pydantic args_schema, wrapping
the existing Service layer. Tool names match the MCP tool names in mcp_server.py.

Thread safety: Tools are synchronous LangChain StructuredTool functions that
directly call Service layer methods. The calling agent loop (07-04 ChatService)
is responsible for wrapping tool invocations in asyncio.to_thread() to ensure
arcpy COM calls don't block the FastAPI event loop.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.tools import tool


# ════════════════════════════════════════════════════════════════
# Workspace Tools
# ════════════════════════════════════════════════════════════════

class WorkspaceSetInput(BaseModel):
    path: str = Field(description="Workspace directory path containing ArcGIS Pro project files")

@tool(args_schema=WorkspaceSetInput)
def workspace_set(path: str) -> str:
    """Set the current workspace directory. Must contain ArcGIS Pro project files.

    Use this when the user asks to set a working directory, workspace path,
    or when starting a new GIS session.
    """
    from arcgis_agent.services.workspace_service import WorkspaceService
    result = WorkspaceService().set_workspace(path)
    return f"Workspace set to: {path}. Success: {result.success}"


class WorkspaceGetInput(BaseModel):
    pass

@tool(args_schema=WorkspaceGetInput)
def workspace_get() -> str:
    """Get the current workspace directory path.

    Use this when the user asks what the current workspace is, or to verify
    the configured workspace before performing operations.
    """
    from arcgis_agent.services.workspace_service import WorkspaceService
    result = WorkspaceService().get_workspace()
    ws = result.data.get('workspace', 'not set') if result.data else 'not set'
    return f"Current workspace: {ws}"


# ════════════════════════════════════════════════════════════════
# Project Tools
# ════════════════════════════════════════════════════════════════

class ProjectInfoInput(BaseModel):
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")

@tool(args_schema=ProjectInfoInput)
def project_info(project_path: str) -> str:
    """Get ArcGIS Pro project info: maps, databases, and project path.

    Use this when the user asks about project contents, available maps,
    or project metadata.
    """
    from arcgis_agent.services.project_service import ProjectService
    result = ProjectService().info(project_path)
    if result.success and result.data:
        maps = result.data.get('maps', [])
        dbs = result.data.get('databases', [])
        return (f"Project: {project_path}. "
                f"Maps: {len(maps)} ({', '.join(maps[:5])}{'...' if len(maps) > 5 else ''}). "
                f"Databases: {len(dbs)}. Success: {result.success}")
    return f"Project info: {result.message}. Success: {result.success}"


# ════════════════════════════════════════════════════════════════
# Data Discovery Tools
# ════════════════════════════════════════════════════════════════

class DataListInput(BaseModel):
    workspace: Optional[str] = Field(default=None, description="Workspace directory path (uses current workspace if omitted)")
    dataset_type: Optional[str] = Field(default=None, description="Filter by type: FeatureClass, Table, RasterDataset")
    name_pattern: Optional[str] = Field(default=None, description="Glob pattern for name filtering, e.g. 'roads*'")

@tool(args_schema=DataListInput)
def data_list(workspace: Optional[str] = None, dataset_type: Optional[str] = None,
              name_pattern: Optional[str] = None) -> str:
    """List feature classes and datasets in a workspace directory (GDB or folder).

    Use this when the user asks to list available data, see what layers exist,
    or explore the workspace contents. Different from map_list_layers which lists
    layers already loaded in a map.
    """
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    result = DataDiscoveryService().list_datasets(
        workspace=workspace, dataset_type=dataset_type, name_pattern=name_pattern
    )
    if result.success and result.data:
        datasets = result.data.get('datasets', [])
        return (f"Found {result.data.get('count', 0)} datasets: "
                f"{', '.join(datasets[:20])}{'...' if len(datasets) > 20 else ''}. "
                f"Success: {result.success}")
    return f"Data list: {result.message}. Success: {result.success}"


class DataDescribeInput(BaseModel):
    path: str = Field(description="Path to the dataset to describe")

@tool(args_schema=DataDescribeInput)
def data_describe(path: str) -> str:
    """Describe a dataset: type, spatial reference, feature count, extent.

    Use this when the user asks about dataset properties, data type, or
    spatial reference information.
    """
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    result = DataDiscoveryService().describe(path)
    if result.success and result.data:
        dtype = result.data.get('dataType', 'unknown')
        name = result.data.get('name', path)
        return (f"Dataset '{name}': type={dtype}. "
                f"Path: {result.data.get('catalogPath', path)}. "
                f"Success: {result.success}")
    return f"Describe: {result.message}. Success: {result.success}"


class DataFieldsInput(BaseModel):
    path: str = Field(description="Path to the dataset")

@tool(args_schema=DataFieldsInput)
def data_fields(path: str) -> str:
    """List fields (name, type, length) of a dataset.

    Use this when the user asks about available fields, column names,
    or field types in a dataset. Useful before running attribute queries.
    """
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    result = DataDiscoveryService().get_fields(path)
    if result.success and result.data:
        fields = result.data.get('fields', [])
        field_names = [f"{f.get('name', '?')}({f.get('type', '?')})" for f in fields]
        return (f"Fields in {path}: {', '.join(field_names)}. "
                f"Count: {result.data.get('count', 0)}. Success: {result.success}")
    return f"Fields: {result.message}. Success: {result.success}"


class DataExtentInput(BaseModel):
    path: str = Field(description="Path to the dataset")

@tool(args_schema=DataExtentInput)
def data_extent(path: str) -> str:
    """Get the spatial extent (xmin, ymin, xmax, ymax) of a dataset.

    Use this when the user asks about the geographic coverage, bounding box,
    or spatial range of a dataset.
    """
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    result = DataDiscoveryService().get_extent(path)
    if result.success and result.data:
        ext = result.data
        return (f"Extent of {path}: "
                f"xmin={ext.get('xmin')}, ymin={ext.get('ymin')}, "
                f"xmax={ext.get('xmax')}, ymax={ext.get('ymax')}. "
                f"Success: {result.success}")
    return f"Extent: {result.message}. Success: {result.success}"


class DataCountInput(BaseModel):
    path: str = Field(description="Path to the dataset")

@tool(args_schema=DataCountInput)
def data_count(path: str) -> str:
    """Get the number of features/rows in a dataset.

    Use this when the user asks about feature count, record count,
    or dataset size in terms of rows.
    """
    from arcgis_agent.services.data_discovery import DataDiscoveryService
    result = DataDiscoveryService().get_count(path)
    if result.success and result.data:
        return (f"Feature count for {path}: {result.data.get('count', 0)}. "
                f"Success: {result.success}")
    return f"Count: {result.message}. Success: {result.success}"


# ════════════════════════════════════════════════════════════════
# Data Management Tools
# ════════════════════════════════════════════════════════════════

class DataCopyInput(BaseModel):
    source: str = Field(description="Source dataset path")
    destination: str = Field(description="Destination path for the copied dataset")
    no_overwrite: bool = Field(default=False, description="If True, fail if destination already exists")

@tool(args_schema=DataCopyInput)
def data_copy(source: str, destination: str, no_overwrite: bool = False) -> str:
    """Copy a dataset to a new location.

    Use this when the user asks to duplicate, copy, or backup a dataset.
    """
    from arcgis_agent.services.data_management import DataManagementService
    result = DataManagementService().copy(source, destination, no_overwrite=no_overwrite)
    return f"Copy {source} -> {destination}. {result.message}. Success: {result.success}"


class DataDeleteInput(BaseModel):
    path: str = Field(description="Path to the dataset to delete permanently")

@tool(args_schema=DataDeleteInput)
def data_delete(path: str) -> str:
    """Delete a dataset permanently. THIS OPERATION IS DESTRUCTIVE.

    Use this ONLY when the user explicitly confirms they want to delete data.
    Always confirm with the user before calling this tool.
    """
    from arcgis_agent.services.data_management import DataManagementService
    result = DataManagementService().delete(path)
    return f"Delete {path}. {result.message}. Success: {result.success}"


class DataRenameInput(BaseModel):
    old_path: str = Field(description="Current path of the dataset")
    new_name: str = Field(description="New name for the dataset (filename only, not full path)")

@tool(args_schema=DataRenameInput)
def data_rename(old_path: str, new_name: str) -> str:
    """Rename a dataset.

    Use this when the user asks to rename a layer, feature class, or table.
    """
    from arcgis_agent.services.data_management import DataManagementService
    result = DataManagementService().rename(old_path, new_name)
    return f"Rename {old_path} -> {new_name}. {result.message}. Success: {result.success}"


class DataConvertInput(BaseModel):
    source: str = Field(description="Source dataset path")
    destination: str = Field(description="Destination path for the converted dataset")
    output_format: str = Field(description="Output format: shp, gdb, csv, or geojson")
    no_overwrite: bool = Field(default=False, description="If True, fail if destination already exists")

@tool(args_schema=DataConvertInput)
def data_convert(source: str, destination: str, output_format: str,
                 no_overwrite: bool = False) -> str:
    """Convert a dataset between formats (shapefile, geodatabase, CSV, GeoJSON).

    Use this when the user asks to convert data formats, export to a specific
    format, or change the storage format of a dataset.
    Supported formats: shp, gdb, csv, geojson.
    """
    from arcgis_agent.services.data_management import DataManagementService
    result = DataManagementService().convert(
        source, destination, output_format, no_overwrite=no_overwrite
    )
    return f"Convert {source} to {output_format}. {result.message}. Success: {result.success}"


# ════════════════════════════════════════════════════════════════
# Geoprocessing Tools
# ════════════════════════════════════════════════════════════════

class SelectInput(BaseModel):
    input_fc: str = Field(description="Input feature class path")
    output_fc: str = Field(description="Output feature class path")
    where_clause: str = Field(description="SQL WHERE clause for attribute selection, e.g. \"POPULATION > 100000\"")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=SelectInput)
def gp_select(input_fc: str, output_fc: str, where_clause: str,
              no_overwrite: bool = False) -> str:
    """Select features by SQL attribute query and save to new dataset.

    Use this when the user asks to filter, query, or select features by
    attribute values. The where_clause uses standard SQL syntax.
    Example: \"NAME = 'Beijing' AND POP2020 > 1000000\"
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().select_by_attribute(
        input_fc, output_fc, where_clause, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Select from {input_fc}: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class ClipInput(BaseModel):
    input_fc: str = Field(description="Input feature class to be clipped")
    clip_features: str = Field(description="Boundary feature class used for clipping")
    output_fc: str = Field(description="Output feature class path")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=ClipInput)
def gp_clip(input_fc: str, clip_features: str, output_fc: str,
            no_overwrite: bool = False) -> str:
    """Clip features to a boundary polygon layer.

    Use this when the user asks to clip, trim, or cut features to fit within
    a boundary. Clip keeps only the portions of input features that fall
    INSIDE the clip boundary. Differs from intersect which computes the
    geometric overlap of ALL input layers.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().clip(
        input_fc, clip_features, output_fc, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Clip {input_fc} by {clip_features}: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class BufferInput(BaseModel):
    input_fc: str = Field(description="Input feature class path")
    output_fc: str = Field(description="Output feature class path")
    distance: float = Field(description="Buffer distance", gt=0)
    unit: str = Field(default="Meters", description="Distance unit: Meters, Kilometers, Feet, Miles, Yards")
    dissolve_field: Optional[str] = Field(default=None, description="Optional field to dissolve overlapping buffers by")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=BufferInput)
def gp_buffer(input_fc: str, output_fc: str, distance: float,
              unit: str = "Meters", dissolve_field: Optional[str] = None,
              no_overwrite: bool = False) -> str:
    """Create buffer polygons around features at a specified distance.

    Use this when the user asks to create a buffer zone, proximity area,
    or distance-based analysis around geographic features. For example:
    "buffer the roads by 100 meters" or "create a 1km zone around schools".
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().buffer(
        input_fc, output_fc, distance, unit=unit,
        dissolve_field=dissolve_field, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    elapsed = result.data.get('elapsed_seconds', 'N/A') if result.success and result.data else 'N/A'
    return (f"Buffer {distance} {unit} around {input_fc}: {result.message}. "
            f"Features: {count}. Time: {elapsed}s. Success: {result.success}")


class IntersectInput(BaseModel):
    inputs: list[str] = Field(description="List of input feature class paths (at least 2)")
    output_fc: str = Field(description="Output feature class path")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=IntersectInput)
def gp_intersect(inputs: list[str], output_fc: str,
                 no_overwrite: bool = False) -> str:
    """Compute the geometric intersection of multiple input layers.

    Use this when the user asks to find overlapping areas between layers,
    compute the common area shared by multiple layers, or overlay analysis.
    Intersect keeps only areas where ALL inputs overlap.
    Differs from clip: clip uses one boundary to cut another; intersect
    computes the shared area of all inputs equally.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().intersect(inputs, output_fc, no_overwrite=no_overwrite)
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Intersect {len(inputs)} layers: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class UnionInput(BaseModel):
    inputs: list[str] = Field(description="List of polygon feature class paths (at least 2)")
    output_fc: str = Field(description="Output feature class path")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=UnionInput)
def gp_union(inputs: list[str], output_fc: str,
             no_overwrite: bool = False) -> str:
    """Compute the geometric union of multiple polygon layers.

    Use this when the user asks to combine, merge by overlay, or union
    polygon feature classes. Union keeps ALL areas from ALL inputs,
    splitting features at overlap boundaries.
    Differs from merge: merge simply appends features (no overlay geometry).
    Differs from intersect: intersect keeps only shared areas; union keeps all areas.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().union(inputs, output_fc, no_overwrite=no_overwrite)
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Union {len(inputs)} layers: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class DissolveInput(BaseModel):
    input_fc: str = Field(description="Input feature class path")
    output_fc: str = Field(description="Output feature class path")
    dissolve_field: str = Field(description="Field to dissolve by — features with the same value are merged")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=DissolveInput)
def gp_dissolve(input_fc: str, output_fc: str, dissolve_field: str,
                no_overwrite: bool = False) -> str:
    """Dissolve features by a field, merging boundaries with matching values.

    Use this when the user asks to dissolve, merge by attribute, or combine
    adjacent features that share a common attribute value. For example:
    "dissolve counties into states" or "merge parcels by owner name".
    THIS OPERATION CAN BE DESTRUCTIVE — it replaces input features with dissolved output.
    Confirm with the user before running if they expect to keep the original data.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().dissolve(
        input_fc, output_fc, dissolve_field, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Dissolve {input_fc} by {dissolve_field}: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class SpatialJoinInput(BaseModel):
    target_fc: str = Field(description="Target feature class that receives attributes")
    join_fc: str = Field(description="Join feature class that provides attributes")
    output_fc: str = Field(description="Output feature class path")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=SpatialJoinInput)
def gp_spatial_join(target_fc: str, join_fc: str, output_fc: str,
                    no_overwrite: bool = False) -> str:
    """Join attributes from one layer to another based on spatial relationship.

    Use this when the user asks to transfer attributes between layers based
    on location, e.g., "add county names to each parcel" or "find which
    neighborhood each building is in".
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().spatial_join(
        target_fc, join_fc, output_fc, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Spatial join {join_fc} -> {target_fc}: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class MergeInput(BaseModel):
    inputs: list[str] = Field(description="List of feature class paths to merge (at least 2)")
    output_fc: str = Field(description="Output feature class path")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=MergeInput)
def gp_merge(inputs: list[str], output_fc: str,
             no_overwrite: bool = False) -> str:
    """Merge multiple feature classes into a single dataset (append, no overlay).

    Use this when the user asks to combine, append, or merge feature classes
    without performing geometric overlay. All features from all inputs are
    simply appended into one output.
    Differs from union: union performs geometric overlay and splits features;
    merge just appends them together.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().merge(inputs, output_fc, no_overwrite=no_overwrite)
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Merge {len(inputs)} layers: {result.message}. "
            f"Features: {count}. Success: {result.success}")


class ProjectInput(BaseModel):
    input_fc: str = Field(description="Input feature class path")
    output_fc: str = Field(description="Output feature class path")
    spatial_ref_wkid: str = Field(description="Target spatial reference EPSG WKID, e.g. '4326' for WGS84, '3857' for Web Mercator")
    no_overwrite: bool = Field(default=False, description="If True, fail if output already exists")

@tool(args_schema=ProjectInput)
def gp_project(input_fc: str, output_fc: str, spatial_ref_wkid: str,
               no_overwrite: bool = False) -> str:
    """Project a feature class to a different coordinate system by EPSG WKID.

    Use this when the user asks to reproject, change CRS, or convert coordinate
    systems. The spatial_ref_wkid is an EPSG code like '4326' or '3857'.
    """
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    result = GeoprocessingService().project(
        input_fc, output_fc, spatial_ref_wkid, no_overwrite=no_overwrite
    )
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Project {input_fc} to EPSG:{spatial_ref_wkid}: {result.message}. "
            f"Features: {count}. Success: {result.success}")


# ════════════════════════════════════════════════════════════════
# Analysis Tools
# ════════════════════════════════════════════════════════════════

class SummaryStatsInput(BaseModel):
    input_fc: str = Field(description="Input feature class or table path")
    field_spec: str = Field(description="Field:STAT specification, e.g. 'pop:SUM,area:MEAN'. Valid stats: SUM,MEAN,MIN,MAX,COUNT,STD,MEDIAN")
    case_field: Optional[str] = Field(default=None, description="Optional field to group results by")
    output_table: Optional[str] = Field(default=None, description="Output table path (auto-generated if omitted)")

@tool(args_schema=SummaryStatsInput)
def analysis_summary_stats(input_fc: str, field_spec: str,
                           case_field: Optional[str] = None,
                           output_table: Optional[str] = None) -> str:
    """Compute summary statistics (SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN) for fields.

    Use this when the user asks for statistics, summaries, averages, totals,
    or aggregate calculations on a dataset. The field_spec format is
    'field_name:STAT_TYPE' with multiple fields separated by commas.
    Example: 'population:SUM,area:MEAN,income:MEDIAN'
    """
    from arcgis_agent.services.analysis_service import AnalysisService
    result = AnalysisService().summary_statistics(
        input_fc, field_spec, case_field=case_field, output_table=output_table
    )
    output = result.data.get('output', output_table or 'N/A') if result.success and result.data else 'N/A'
    count = result.data.get('feature_count', 'N/A') if result.success and result.data else 'N/A'
    return (f"Summary statistics for {input_fc}: {result.message}. "
            f"Output: {output}. Rows: {count}. Success: {result.success}")


# ════════════════════════════════════════════════════════════════
# Map Tools
# ════════════════════════════════════════════════════════════════

class MapCreateInput(BaseModel):
    map_name: str = Field(description="Name for the new map")
    project_path: Optional[str] = Field(default=None, description="ArcGIS Pro project path (uses workspace default if omitted)")

@tool(args_schema=MapCreateInput)
def map_create(map_name: str, project_path: Optional[str] = None) -> str:
    """Create a new map in an ArcGIS Pro project.

    Use this when the user asks to create a new map, add a map to a project,
    or start a new mapping document.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().create_map(project_path, map_name)
    return f"Create map '{map_name}': {result.message}. Success: {result.success}"


class MapAddLayerInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    data_path: str = Field(description="Path to the data layer to add")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")

@tool(args_schema=MapAddLayerInput)
def map_add_layer(map_name: str, data_path: str, project_path: str) -> str:
    """Add a data layer to a map in an ArcGIS Pro project.

    Use this when the user asks to add a layer, load data into a map,
    or display a dataset on the map.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().add_layer(project_path, map_name, data_path)
    return f"Add layer '{data_path}' to map '{map_name}': {result.message}. Success: {result.success}"


class MapRemoveLayerInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    layer_name: Optional[str] = Field(default=None, description="Name of the layer to remove (preferred)")
    layer_index: Optional[int] = Field(default=None, description="Index of the layer to remove (fallback, 0-based)")

@tool(args_schema=MapRemoveLayerInput)
def map_remove_layer(map_name: str, project_path: str,
                     layer_name: Optional[str] = None,
                     layer_index: Optional[int] = None) -> str:
    """Remove a layer from a map by name or index.

    Use this when the user asks to remove, delete from map, or hide a layer
    from the current map view. This removes the layer from the map but does
    NOT delete the underlying data file.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().remove_layer(
        project_path, map_name, layer_name=layer_name, layer_index=layer_index
    )
    return f"Remove layer from map '{map_name}': {result.message}. Success: {result.success}"


class MapListLayersInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")

@tool(args_schema=MapListLayersInput)
def map_list_layers(map_name: str, project_path: str) -> str:
    """List all layers in a map with names, data sources, and feature counts.

    Use this when the user asks what layers are in a map, to check map contents,
    or to verify which layers are currently loaded.
    Different from data_list which lists datasets on disk, not necessarily in a map.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().list_layers(project_path, map_name)
    if result.success and result.data:
        layers = result.data.get('layers', [])
        layer_names = [l.get('name', '?') for l in layers]
        return (f"Layers in map '{map_name}': {', '.join(layer_names)}. "
                f"Count: {result.data.get('count', len(layers))}. Success: {result.success}")
    return f"List layers: {result.message}. Success: {result.success}"


class MapSetExtentInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    zoom_to_layer: str = Field(description="Name of the layer to zoom to")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")

@tool(args_schema=MapSetExtentInput)
def map_set_extent(map_name: str, zoom_to_layer: str, project_path: str) -> str:
    """Set the map extent to match a specific layer (zoom to layer).

    Use this when the user asks to zoom to a layer, focus on specific data,
    or set the visible area of the map to a particular dataset.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().set_extent(project_path, map_name, zoom_to_layer)
    return f"Zoom map '{map_name}' to layer '{zoom_to_layer}': {result.message}. Success: {result.success}"


class MapExportInput(BaseModel):
    map_name: str = Field(description="Name of the map to export")
    output_path: str = Field(description="Output file path (.png or .pdf)")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    format: str = Field(default="PNG", description="Export format: PNG or PDF")
    dpi: int = Field(default=300, description="Output resolution in DPI (96, 150, 300, 600)")
    transparent: bool = Field(default=False, description="If True, export with transparent background (PNG only)")

@tool(args_schema=MapExportInput)
def map_export(map_name: str, output_path: str, project_path: str,
               format: str = "PNG", dpi: int = 300,
               transparent: bool = False) -> str:
    """Export a map to PNG or PDF file.

    Use this when the user asks to export, save, or output a map as an image
    or PDF file. Supports PNG (with optional transparency) and PDF formats.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().export_map(
        project_path, map_name, output_path,
        format=format, dpi=dpi, transparent=transparent
    )
    output = result.data.get('output', output_path) if result.success and result.data else output_path
    return (f"Export map '{map_name}' to {format}: {result.message}. "
            f"Output: {output}. DPI: {dpi}. Success: {result.success}")


class MapSymbolizeInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    layer_name: str = Field(description="Name of the layer to symbolize")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    symbology_type: str = Field(default="simple", description="Symbol type: simple, unique_values, or graduated_colors")
    field: Optional[str] = Field(default=None, description="Field for unique_values or graduated_colors symbology")
    color: Optional[str] = Field(default=None, description="Fill color as R,G,B, e.g. '255,0,0' for red")
    outline_color: Optional[str] = Field(default=None, description="Outline color as R,G,B")
    size: int = Field(default=8, description="Symbol size in points")
    opacity: int = Field(default=100, description="Fill opacity 0-100")
    color_ramp: Optional[str] = Field(default=None, description="Color ramp name for graduated/unique colors")
    values: Optional[str] = Field(default=None, description="JSON array of custom symbol values for unique_values")
    classification_method: str = Field(default="NaturalBreaks", description="Classification method: NaturalBreaks, Quantile, EqualInterval")
    break_count: int = Field(default=5, description="Number of class breaks (2-7) for graduated_colors")

@tool(args_schema=MapSymbolizeInput)
def map_symbolize(map_name: str, layer_name: str, project_path: str,
                  symbology_type: str = "simple", field: Optional[str] = None,
                  color: Optional[str] = None, outline_color: Optional[str] = None,
                  size: int = 8, opacity: int = 100,
                  color_ramp: Optional[str] = None, values: Optional[str] = None,
                  classification_method: str = "NaturalBreaks",
                  break_count: int = 5) -> str:
    """Apply symbology to a layer: simple, unique_values, or graduated_colors.

    Use this when the user asks to style, color, symbolize, or change the
    appearance of a layer on the map. Supports three symbology types:
    - simple: uniform symbol (color, size, opacity)
    - unique_values: different colors by field value
    - graduated_colors: graduated colors by numeric field value
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().symbolize_layer(
        project_path, map_name, layer_name,
        symbology_type=symbology_type, field=field,
        color=color, outline_color=outline_color,
        size=size, opacity=opacity, color_ramp=color_ramp,
        values=values, classification_method=classification_method,
        break_count=break_count,
    )
    return (f"Symbolize layer '{layer_name}' in map '{map_name}' "
            f"({symbology_type}): {result.message}. Success: {result.success}")


class MapLabelInput(BaseModel):
    map_name: str = Field(description="Name of the target map")
    layer_name: str = Field(description="Name of the layer to label")
    field: str = Field(description="Field to use for label text")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    font_size: int = Field(default=10, description="Label font size in points")
    color: str = Field(default="0,0,0", description="Label color as R,G,B, e.g. '255,0,0'")
    bold: bool = Field(default=False, description="If True, use bold font style")

@tool(args_schema=MapLabelInput)
def map_label(map_name: str, layer_name: str, field: str, project_path: str,
              font_size: int = 10, color: str = "0,0,0",
              bold: bool = False) -> str:
    """Set labels on a layer using a field value.

    Use this when the user asks to add labels, show names on the map,
    or display field values as text on a layer.
    """
    from arcgis_agent.services.map_service import MapService
    result = MapService().set_label(
        project_path, map_name, layer_name, field,
        font_size=font_size, color=color, bold=bold,
    )
    return (f"Label layer '{layer_name}' with field '{field}': "
            f"{result.message}. Success: {result.success}")


# ════════════════════════════════════════════════════════════════
# Layout Tools
# ════════════════════════════════════════════════════════════════

class LayoutCreateInput(BaseModel):
    layout_name: str = Field(description="Name for the new layout")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    page_size: str = Field(default="A4", description="Page size: A4, A3, Letter, Tabloid")
    orientation: str = Field(default="portrait", description="Page orientation: portrait or landscape")

@tool(args_schema=LayoutCreateInput)
def layout_create(layout_name: str, project_path: str,
                  page_size: str = "A4", orientation: str = "portrait") -> str:
    """Create a new layout (page) in an ArcGIS Pro project.

    Use this when the user asks to create a layout, set up a page for printing,
    or prepare a map for export with specific page dimensions.
    """
    from arcgis_agent.services.layout_service import LayoutService
    result = LayoutService().create_layout(
        project_path, layout_name, page_size=page_size, orientation=orientation
    )
    return f"Create layout '{layout_name}' ({page_size} {orientation}): {result.message}. Success: {result.success}"


class LayoutAddElementInput(BaseModel):
    layout_name: str = Field(description="Name of the target layout")
    element_type: str = Field(description="Element type: text, legend, scale-bar, north-arrow, map-frame, image")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    position: Optional[str] = Field(default=None, description="Preset position: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right")
    params: Optional[str] = Field(default=None, description="Additional parameters as key=value pairs, comma-separated. e.g. 'text=My Title,font_size=24'")

@tool(args_schema=LayoutAddElementInput)
def layout_add_element(layout_name: str, element_type: str, project_path: str,
                       position: Optional[str] = None,
                       params: Optional[str] = None) -> str:
    """Add an element to a layout: text, legend, scale-bar, north-arrow, map-frame, image.

    Use this when the user asks to add map elements to a layout page for
    printing or export. Common elements include:
    - text: title, subtitle, notes (params: text=..., font_size=...)
    - legend: map legend with symbol explanations
    - scale-bar: graphic scale indicator
    - north-arrow: compass direction indicator
    - map-frame: embeds a map view into the layout
    - image: inserts a picture (params: source=<path>)
    """
    from arcgis_agent.services.layout_service import LayoutService
    result = LayoutService().add_element(
        project_path, layout_name, element_type,
        position=position, params=params,
    )
    return (f"Add {element_type} to layout '{layout_name}': "
            f"{result.message}. Success: {result.success}")


class LayoutExportInput(BaseModel):
    layout_name: str = Field(description="Name of the layout to export")
    output_path: str = Field(description="Output file path (.png or .pdf)")
    project_path: str = Field(description="Path to the ArcGIS Pro project file (.aprx)")
    format: str = Field(default="PDF", description="Export format: PNG or PDF")
    dpi: int = Field(default=300, description="Output resolution in DPI (96, 150, 300, 600)")
    transparent: bool = Field(default=False, description="If True, export with transparent background (PNG only)")

@tool(args_schema=LayoutExportInput)
def layout_export(layout_name: str, output_path: str, project_path: str,
                  format: str = "PDF", dpi: int = 300,
                  transparent: bool = False) -> str:
    """Export a layout to PNG or PDF file.

    Use this when the user asks to export, print, or save a layout page
    as an image or PDF. This is the final step for producing printable
    map outputs with all layout elements included.
    """
    from arcgis_agent.services.layout_service import LayoutService
    result = LayoutService().export_layout(
        project_path, layout_name, output_path,
        format=format, dpi=dpi, transparent=transparent,
    )
    output = result.data.get('output', output_path) if result.success and result.data else output_path
    return (f"Export layout '{layout_name}' to {format}: {result.message}. "
            f"Output: {output}. DPI: {dpi}. Success: {result.success}")


# ════════════════════════════════════════════════════════════════
# Tool Registry
# ════════════════════════════════════════════════════════════════

ALL_GIS_TOOLS = [
    # Workspace (2)
    workspace_set, workspace_get,

    # Project (1)
    project_info,

    # Data Discovery (5)
    data_list, data_describe, data_fields, data_extent, data_count,

    # Data Management (4)
    data_copy, data_delete, data_rename, data_convert,

    # Geoprocessing (9)
    gp_select, gp_clip, gp_buffer, gp_intersect, gp_union,
    gp_dissolve, gp_spatial_join, gp_merge, gp_project,

    # Analysis (1)
    analysis_summary_stats,

    # Map (8)
    map_create, map_add_layer, map_remove_layer, map_list_layers,
    map_set_extent, map_export, map_symbolize, map_label,

    # Layout (3)
    layout_create, layout_add_element, layout_export,
]

# Sanity check: exactly 33 tools matching mcp_server.py
assert len(ALL_GIS_TOOLS) == 33, (
    f"Expected 33 tools (matching mcp_server.py @mcp.tool() count), "
    f"got {len(ALL_GIS_TOOLS)}"
)
