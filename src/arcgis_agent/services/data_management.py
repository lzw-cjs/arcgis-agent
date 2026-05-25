"""Data management service: copy, delete, rename, convert."""
from pathlib import Path
from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


class DataManagementService(BaseService):
    """Write operations for data management (MGMT-01 through MGMT-04).

    All operations use self._data (IDataAccessor) adapter.
    Supports --no-overwrite safety (Pitfall #11).
    """

    def __init__(self, data=None):
        super().__init__(data=data)

    def copy(self, source: str, destination: str,
             no_overwrite: bool = False) -> Result:
        """Copy dataset to new location (MGMT-01)."""
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Source not found: {source}",
            )

        if no_overwrite and dst.exists():
            return Result.error(
                code="FILE_EXISTS",
                message=f"Destination already exists: {destination}. "
                        f"Use without --no-overwrite to overwrite.",
            )

        try:
            result_path = self._data.copy(src, dst)
            return Result.ok(
                data={"source": str(src), "destination": str(result_path)},
                message=f"Copied {src.name} to {result_path}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def delete(self, dataset_path: str) -> Result:
        """Delete dataset (MGMT-02)."""
        p = Path(dataset_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            self._data.delete(p)
            return Result.ok(
                data={"path": str(p)},
                message=f"Deleted: {p.name}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def rename(self, old_path: str, new_name: str) -> Result:
        """Rename dataset (MGMT-03)."""
        p = Path(old_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {old_path}",
            )

        new_full = p.parent / new_name
        if new_full.exists():
            return Result.error(
                code="FILE_EXISTS",
                message=f"Target name already exists: {new_name}",
            )

        try:
            result_path = self._data.rename(p, new_name)
            return Result.ok(
                data={"old_path": str(p), "new_path": str(result_path)},
                message=f"Renamed to {new_name}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def convert(self, source: str, destination: str,
                output_format: str, no_overwrite: bool = False) -> Result:
        """Convert dataset format (MGMT-04).

        Supported formats: shp, gdb, csv, geojson.
        """
        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Source not found: {source}",
            )

        valid_formats = {"shp", "gdb", "csv", "geojson"}
        if output_format.lower() not in valid_formats:
            return Result.error(
                code="INVALID_FORMAT",
                message=f"Unsupported format: {output_format}. "
                        f"Supported: {', '.join(sorted(valid_formats))}",
            )

        if no_overwrite and dst.exists():
            return Result.error(
                code="FILE_EXISTS",
                message=f"Destination already exists: {destination}. "
                        f"Use without --no-overwrite to overwrite.",
            )

        try:
            result_path = self._data.convert(src, dst, output_format)
            return Result.ok(
                data={"source": str(src), "destination": str(result_path),
                       "format": output_format},
                message=f"Converted to {output_format}: {result_path.name}",
            )
        except Exception as e:
            return Result.from_exception(e)
