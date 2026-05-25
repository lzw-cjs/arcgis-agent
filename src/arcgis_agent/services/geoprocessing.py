"""Geoprocessing service: buffer, clip, intersect, union, dissolve, spatial-join, merge, project, select."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


class GeoprocessingService(BaseService):
    """Geoprocessing operations (GEO-01 through GEO-09).

    All operations use self._gp (IGeoProcessor) for spatial operations
    and self._data (IDataAccessor) for get_count on outputs.
    """

    VALID_UNITS = {"Meters", "Kilometers", "Feet", "Miles", "Yards", "DecimalDegrees"}

    def __init__(self, gp=None, data=None):
        super().__init__(gp=gp, data=data)

    def _validate_multi_inputs(self, inputs: list[str]) -> Result | None:
        """Validate multi-input operations. Returns Result.error if invalid, None if OK."""
        if len(inputs) < 2:
            return Result.error(
                code="INVALID_INPUT",
                message="At least 2 input layers required."
            )
        for inp in inputs:
            if not Path(inp).exists():
                return Result.error(code="FILE_NOT_FOUND",
                                    message=f"Input not found: {inp}")
        return None

    def select_by_attribute(self, input_fc: str, output_fc: str,
                            where_clause: str,
                            no_overwrite: bool = False) -> Result:
        """Select features by attribute query (GEO-01)."""
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.select_by_attribute(input_fc, output_fc, where_clause)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Selected features: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def clip(self, input_fc: str, clip_fc: str, output_fc: str,
             no_overwrite: bool = False) -> Result:
        """Clip features to boundary (GEO-02)."""
        p_in = Path(input_fc)
        p_clip = Path(clip_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if not p_clip.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Clip features not found: {clip_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.clip(input_fc, clip_fc, output_fc)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Clipped: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str = "Meters",
               dissolve_field: str | None = None,
               no_overwrite: bool = False) -> Result:
        """Create buffer around features (GEO-03).

        Args:
            input_fc: Input feature class path.
            output_fc: Output feature class path.
            distance: Buffer distance.
            unit: Distance unit (Meters, Kilometers, Feet, Miles, Yards, DecimalDegrees).
            dissolve_field: Optional field to dissolve overlapping buffers.
            no_overwrite: Fail if output exists.
        """
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if unit not in self.VALID_UNITS:
            return Result.error(code="INVALID_UNIT",
                                message=f"Invalid unit: '{unit}'. "
                                        f"Valid: {', '.join(sorted(self.VALID_UNITS))}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.buffer(input_fc, output_fc, distance, unit,
                                           dissolve_field=dissolve_field)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Buffer created: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def intersect(self, inputs: list[str], output_fc: str,
                  no_overwrite: bool = False) -> Result:
        """Intersect multiple feature classes (GEO-04)."""
        err = self._validate_multi_inputs(inputs)
        if err:
            return err
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.intersect(inputs, output_fc)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Intersect: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def union(self, inputs: list[str], output_fc: str,
              no_overwrite: bool = False) -> Result:
        """Union (overlay) multiple polygon feature classes (GEO-05)."""
        err = self._validate_multi_inputs(inputs)
        if err:
            return err
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.union(inputs, output_fc)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Union: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def dissolve(self, input_fc: str, output_fc: str,
                 dissolve_field: str,
                 no_overwrite: bool = False) -> Result:
        """Dissolve features by field (GEO-06)."""
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.dissolve(input_fc, output_fc, dissolve_field)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Dissolved: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def spatial_join(self, target_fc: str, join_fc: str, output_fc: str,
                     no_overwrite: bool = False) -> Result:
        """Spatial join: transfer attributes from join features to target (GEO-07)."""
        p_target = Path(target_fc)
        p_join = Path(join_fc)
        if not p_target.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Target not found: {target_fc}")
        if not p_join.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Join features not found: {join_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.spatial_join(target_fc, join_fc, output_fc)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Spatial join: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def merge(self, inputs: list[str], output_fc: str,
              no_overwrite: bool = False) -> Result:
        """Merge multiple feature classes into one (GEO-08)."""
        err = self._validate_multi_inputs(inputs)
        if err:
            return err
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.merge(inputs, output_fc)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Merged: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)

    def project(self, input_fc: str, output_fc: str,
                spatial_reference: str,
                no_overwrite: bool = False) -> Result:
        """Project features to a different coordinate system (GEO-09)."""
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        t0 = time.perf_counter()
        try:
            result_path = self._gp.project(input_fc, output_fc, spatial_reference)
            elapsed = time.perf_counter() - t0
            count = self._data.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Projected: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)
