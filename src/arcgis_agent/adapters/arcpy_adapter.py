"""Real ArcPy adapter implementations with lazy import."""
from pathlib import Path
from typing import Any

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


class ArcPyGeoProcessor(IGeoProcessor):
    """Geoprocessing operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        try:
            self._arcpy.analysis.Buffer(
                input_fc, output_fc, f"{distance} {unit}"
            )
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_BUFFER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def clip(self, input_fc: str, clip_fc: str,
             output_fc: str) -> Path:
        try:
            self._arcpy.analysis.Clip(input_fc, clip_fc, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_CLIP_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def intersect(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._arcpy.analysis.Intersect(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_INTERSECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )


class ArcPyMapDocument(IMapDocument):
    """Map document operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def create_map(self, project_path: Path, map_name: str) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            aprx.createMap(map_name)
            aprx.save()
            return project_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_CREATE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def add_layer(self, project_path: Path, map_name: str,
                  layer_path: Path) -> None:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            m.addDataFromPath(str(layer_path))
            aprx.save()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_ADD_LAYER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def export_map(self, project_path: Path, map_name: str,
                   output_path: Path, format: str, dpi: int) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            m = aprx.listMaps(map_name)[0]
            m.exportToPNG(str(output_path), dpi=dpi)
            return output_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="MAP_EXPORT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )


class ArcPyDataAccessor(IDataAccessor):
    """Data access operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def list_feature_classes(self, workspace: Path) -> list[str]:
        try:
            self._arcpy.env.workspace = str(workspace)
            return self._arcpy.ListFeatureClasses()
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_LIST_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def describe(self, dataset_path: Path) -> dict[str, Any]:
        try:
            desc = self._arcpy.Describe(str(dataset_path))
            return {
                "dataType": desc.dataType,
                "name": desc.name,
                "catalogPath": desc.catalogPath,
            }
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_DESCRIBE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def convert(self, input_path: Path, output_path: Path,
                output_format: str) -> Path:
        try:
            self._arcpy.conversion.FeatureClassToFeatureClass(
                str(input_path), str(output_path.parent),
                output_path.name
            )
            return output_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_CONVERT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
