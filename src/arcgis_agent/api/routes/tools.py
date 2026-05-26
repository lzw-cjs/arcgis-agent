"""GIS tool REST API endpoints (Phase 7).

Exposes 33 GIS operations as REST endpoints under /api/v1/tools/.
All arcpy calls are serialized through _run_in_thread().
Long-running operations return task_id for async polling.
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter

from arcgis_agent.api.dependencies import _run_in_thread
from arcgis_agent.services.task_service import TaskStore

router = APIRouter(prefix="/api/v1/tools", tags=["Tools"])

# ── Long-running tool set ─────────────────────────────────────
# These tools may take significant time (seconds to minutes) and
# return a task_id + status instead of a synchronous result.
_LONG_RUNNING: set[str] = {
    "gp_buffer", "gp_clip", "gp_intersect", "gp_union", "gp_dissolve",
    "gp_spatial_join", "gp_merge", "gp_project", "data_convert",
    "map_export", "layout_export",
}


async def _execute_long(task_id: str, fn, *args: Any, **kwargs: Any) -> None:
    """Execute a long-running tool in background, updating TaskStore."""
    store = TaskStore()
    try:
        store.update(task_id, status="running")
        result = await _run_in_thread(lambda: fn(*args, **kwargs))
        store.update(task_id, status="completed", result=result, progress=100.0)
    except Exception as exc:
        store.update(task_id, status="failed", error=str(exc))


# ── Workspace ──────────────────────────────────────────────────

@router.post("/workspace/set")
async def workspace_set(body: dict):
    def _execute():
        from arcgis_agent.services.workspace_service import WorkspaceService
        return WorkspaceService().set_workspace(body["path"])
    return await _run_in_thread(_execute)


@router.get("/workspace/get")
async def workspace_get():
    def _execute():
        from arcgis_agent.services.workspace_service import WorkspaceService
        return WorkspaceService().get_workspace()
    return await _run_in_thread(_execute)


# ── Project ────────────────────────────────────────────────────

@router.get("/project/info")
async def project_info(project_path: str | None = None):
    def _execute():
        from arcgis_agent.services.project_service import ProjectService
        return ProjectService().info(project_path)
    return await _run_in_thread(_execute)


# ── Data Discovery ─────────────────────────────────────────────

@router.post("/data/list")
async def data_list(body: dict):
    def _execute():
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        return DataDiscoveryService().list_datasets(
            workspace=body.get("workspace"),
            dataset_type=body.get("dataset_type"),
            name_pattern=body.get("name_pattern"),
        )
    return await _run_in_thread(_execute)


@router.post("/data/describe")
async def data_describe(body: dict):
    def _execute():
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        return DataDiscoveryService().describe(body["dataset_path"])
    return await _run_in_thread(_execute)


@router.post("/data/fields")
async def data_fields(body: dict):
    def _execute():
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        return DataDiscoveryService().get_fields(body["dataset_path"])
    return await _run_in_thread(_execute)


@router.post("/data/extent")
async def data_extent(body: dict):
    def _execute():
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        return DataDiscoveryService().get_extent(body["dataset_path"])
    return await _run_in_thread(_execute)


@router.post("/data/count")
async def data_count(body: dict):
    def _execute():
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        return DataDiscoveryService().get_count(body["dataset_path"])
    return await _run_in_thread(_execute)


# ── Data Management ────────────────────────────────────────────

@router.post("/data/copy")
async def data_copy(body: dict):
    def _execute():
        from arcgis_agent.services.data_management import DataManagementService
        return DataManagementService().copy(body["src"], body["dst"])
    return await _run_in_thread(_execute)


@router.post("/data/delete")
async def data_delete(body: dict):
    def _execute():
        from arcgis_agent.services.data_management import DataManagementService
        return DataManagementService().delete(body["dataset_path"])
    return await _run_in_thread(_execute)


@router.post("/data/rename")
async def data_rename(body: dict):
    def _execute():
        from arcgis_agent.services.data_management import DataManagementService
        return DataManagementService().rename(body["dataset_path"], body["new_name"])
    return await _run_in_thread(_execute)


@router.post("/data/convert", status_code=201)
async def data_convert(body: dict):
    task_store = TaskStore()
    task = task_store.create("data_convert", body)
    def _execute():
        from arcgis_agent.services.data_management import DataManagementService
        return DataManagementService().convert(
            body["src"], body["dst"], body["output_format"],
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


# ── Geoprocessing ──────────────────────────────────────────────

@router.post("/gp/select")
async def gp_select(body: dict):
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().select_by_attribute(
            body["input_fc"], body["output_fc"], body["where_clause"],
        )
    return await _run_in_thread(_execute)


@router.post("/gp/clip", status_code=201)
async def gp_clip(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_clip", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().clip(
            body["input_fc"], body["clip_fc"], body["output_fc"],
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/buffer", status_code=201)
async def gp_buffer(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_buffer", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().buffer(
            body["input_fc"], body["output_fc"], body["distance"],
            unit=body.get("unit", "Meters"),
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/intersect", status_code=201)
async def gp_intersect(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_intersect", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().intersect(body["inputs"], body["output_fc"])
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/union", status_code=201)
async def gp_union(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_union", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().union(body["inputs"], body["output_fc"])
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/dissolve", status_code=201)
async def gp_dissolve(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_dissolve", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().dissolve(
            body["input_fc"], body["output_fc"], body["dissolve_field"],
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/spatial-join", status_code=201)
async def gp_spatial_join(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_spatial_join", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().spatial_join(
            body["target_fc"], body["join_fc"], body["output_fc"],
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/merge", status_code=201)
async def gp_merge(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_merge", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().merge(body["inputs"], body["output_fc"])
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/gp/project", status_code=201)
async def gp_project(body: dict):
    task_store = TaskStore()
    task = task_store.create("gp_project", body)
    def _execute():
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        return GeoprocessingService().project(
            body["input_fc"], body["output_fc"], body["spatial_reference"],
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


# ── Map ────────────────────────────────────────────────────────

@router.post("/map/create")
async def map_create(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().create_map(
            map_name=body["map_name"],
            project_path=body.get("project_path"),
        )
    return await _run_in_thread(_execute)


@router.post("/map/add-layer")
async def map_add_layer(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().add_layer(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            data_path=body["layer_path"],
        )
    return await _run_in_thread(_execute)


@router.post("/map/remove-layer")
async def map_remove_layer(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().remove_layer(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            layer_name=body.get("layer_name"),
        )
    return await _run_in_thread(_execute)


@router.post("/map/list-layers")
async def map_list_layers(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().list_layers(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
        )
    return await _run_in_thread(_execute)


@router.post("/map/set-extent")
async def map_set_extent(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().set_extent(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            zoom_to_layer=body["zoom_to_layer"],
        )
    return await _run_in_thread(_execute)


@router.post("/map/export", status_code=201)
async def map_export(body: dict):
    task_store = TaskStore()
    task = task_store.create("map_export", body)
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().export_map(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            output_path=body["output_path"],
            format=body.get("format", "PNG"),
            dpi=body.get("dpi", 150),
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


@router.post("/map/symbolize")
async def map_symbolize(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().symbolize_layer(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            layer_name=body["layer_name"],
            symbology_type=body.get("symbology_type", "simple"),
            field=body.get("field"),
            color=body.get("color"),
            outline_color=body.get("outline_color"),
            size=body.get("size", 8),
            opacity=body.get("opacity", 100),
            color_ramp=body.get("color_ramp"),
            values=body.get("values"),
            classification_method=body.get("classification_method", "NaturalBreaks"),
            break_count=body.get("break_count", 5),
        )
    return await _run_in_thread(_execute)


@router.post("/map/label")
async def map_label(body: dict):
    def _execute():
        from arcgis_agent.services.map_service import MapService
        return MapService().set_label(
            project_path=body.get("project_path", ""),
            map_name=body["map_name"],
            layer_name=body["layer_name"],
            field=body["field"],
            font_size=body.get("font_size", 10),
            color=body.get("color", "0,0,0"),
            bold=body.get("bold", False),
        )
    return await _run_in_thread(_execute)


# ── Layout ─────────────────────────────────────────────────────

@router.post("/layout/create")
async def layout_create(body: dict):
    def _execute():
        from arcgis_agent.services.layout_service import LayoutService
        return LayoutService().create_layout(
            project_path=body.get("project_path", ""),
            layout_name=body["layout_name"],
            page_size=body.get("page_size", "A4"),
            orientation=body.get("orientation", "portrait"),
        )
    return await _run_in_thread(_execute)


@router.post("/layout/add-element")
async def layout_add_element(body: dict):
    def _execute():
        from arcgis_agent.services.layout_service import LayoutService
        return LayoutService().add_element(
            project_path=body.get("project_path", ""),
            layout_name=body["layout_name"],
            element_type=body["element_type"],
            position=body.get("position"),
            params=body.get("params"),
        )
    return await _run_in_thread(_execute)


@router.post("/layout/export", status_code=201)
async def layout_export(body: dict):
    task_store = TaskStore()
    task = task_store.create("layout_export", body)
    def _execute():
        from arcgis_agent.services.layout_service import LayoutService
        return LayoutService().export_layout(
            project_path=body.get("project_path", ""),
            layout_name=body["layout_name"],
            output_path=body["output_path"],
            format=body.get("format", "PDF"),
            dpi=body.get("dpi", 300),
        )
    asyncio.create_task(_execute_long(task.task_id, _execute))
    return {"task_id": task.task_id, "status": task.status}


# ── Analysis ───────────────────────────────────────────────────

@router.post("/analysis/summary-stats")
async def analysis_summary_stats(body: dict):
    def _execute():
        from arcgis_agent.services.analysis_service import AnalysisService
        return AnalysisService().summary_statistics(
            input_fc=body["input_fc"],
            field_spec=body["statistics_fields"],
            case_field=body.get("case_field"),
            output_table=body.get("output_table"),
        )
    return await _run_in_thread(_execute)
