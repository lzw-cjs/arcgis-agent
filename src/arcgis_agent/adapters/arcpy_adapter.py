"""Real ArcPy adapter implementations with lazy import."""
from pathlib import Path
from typing import Any

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


class ArcPyGeoProcessor(IGeoProcessor):
    """Geoprocessing operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def _check_crs_match(self, inputs: list[str]) -> None:
        """Verify all inputs share the same spatial reference (D-10, D-16).

        Raises UserError(code="CRS_MISMATCH") if inputs have different CRS.
        This is a pre-check before overlay operations (intersect/union/merge).
        When ArcPy is unavailable, ArcPyGeoProcessor cannot be constructed at all (D-16).
        """
        from arcgis_agent.exceptions import UserError

        codes = {}
        for fc in inputs:
            desc = self._arcpy.Describe(fc)
            sr = desc.spatialReference
            codes[fc] = (sr.factoryCode, sr.name)

        unique = set(code for code, _ in codes.values())
        if len(unique) > 1:
            details = ", ".join(
                f"{fc} ({name}, EPSG:{code})"
                for fc, (code, name) in codes.items()
            )
            raise UserError(
                code="CRS_MISMATCH",
                message=(
                    f"Input layers have different coordinate systems: {details}. "
                    f"Use 'data project' to reproject inputs to a common CRS first."
                ),
            )

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str,
               dissolve_field: str | None = None) -> Path:
        try:
            dist_str = f"{distance} {unit}"
            if dissolve_field:
                self._arcpy.analysis.Buffer(
                    input_fc, output_fc, dist_str,
                    dissolve_option="LIST", dissolve_field=[dissolve_field]
                )
            else:
                self._arcpy.analysis.Buffer(input_fc, output_fc, dist_str)
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
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.analysis.Intersect(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_INTERSECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def select_by_attribute(self, input_fc: str, output_fc: str,
                            where_clause: str) -> Path:
        try:
            temp_layer = "temp_select_layer"
            self._arcpy.management.MakeFeatureLayer(input_fc, temp_layer)
            try:
                self._arcpy.management.SelectLayerByAttribute(
                    temp_layer, "NEW_SELECTION", where_clause
                )
                self._arcpy.management.CopyFeatures(temp_layer, output_fc)
            finally:
                self._arcpy.management.Delete(temp_layer)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_SELECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def union(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.analysis.Union(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_UNION_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def dissolve(self, input_fc: str, output_fc: str,
                 dissolve_field: str) -> Path:
        try:
            self._arcpy.management.Dissolve(
                input_fc, output_fc, dissolve_field
            )
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_DISSOLVE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def spatial_join(self, target_fc: str, join_fc: str,
                     output_fc: str) -> Path:
        try:
            self._arcpy.analysis.SpatialJoin(target_fc, join_fc, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_SPATIAL_JOIN_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def merge(self, inputs: list[str], output_fc: str) -> Path:
        try:
            self._check_crs_match(inputs)  # Pre-check CRS consistency (D-10)
            self._arcpy.management.Merge(inputs, output_fc)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_MERGE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def project(self, input_fc: str, output_fc: str,
                spatial_reference: str) -> Path:
        try:
            sr = self._arcpy.SpatialReference(int(spatial_reference))
            self._arcpy.management.Project(input_fc, output_fc, sr)
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_PROJECT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

    def summary_statistics(self, input_fc: str, output_table: str,
                           statistics_fields: list[list[str]],
                           case_field: str | None = None) -> Path:
        try:
            if case_field:
                self._arcpy.analysis.Statistics(
                    input_fc, output_table, statistics_fields, case_field
                )
            else:
                self._arcpy.analysis.Statistics(
                    input_fc, output_table, statistics_fields
                )
            return Path(output_table)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_STATISTICS_FAILED",
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

    def get_count(self, dataset_path) -> int:
        try:
            result = self._arcpy.management.GetCount(str(dataset_path))
            return int(result[0])
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="DATA_COUNT_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
