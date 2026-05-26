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
        if not self._data.exists(source):
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Source not found: {source}",
            )

        if no_overwrite and self._data.exists(destination):
            return Result.error(
                code="FILE_EXISTS",
                message=f"Destination already exists: {destination}. "
                        f"Use without --no-overwrite to overwrite.",
            )

        try:
            result_path = self._data.copy(Path(source), Path(destination))
            return Result.ok(
                data={"source": source, "destination": str(result_path)},
                message=f"Copied {Path(source).name} to {result_path}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def delete(self, dataset_path: str) -> Result:
        """Delete dataset (MGMT-02)."""
        if not self._data.exists(dataset_path):
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            self._data.delete(Path(dataset_path))
            return Result.ok(
                data={"path": dataset_path},
                message=f"Deleted: {Path(dataset_path).name}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def rename(self, old_path: str, new_name: str) -> Result:
        """Rename dataset (MGMT-03)."""
        if not self._data.exists(old_path):
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {old_path}",
            )

        new_full = Path(old_path).parent / new_name
        if self._data.exists(str(new_full)):
            return Result.error(
                code="FILE_EXISTS",
                message=f"Target name already exists: {new_name}",
            )

        try:
            result_path = self._data.rename(Path(old_path), new_name)
            return Result.ok(
                data={"old_path": old_path, "new_path": str(result_path)},
                message=f"Renamed to {new_name}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def convert(self, source: str, destination: str,
                output_format: str, no_overwrite: bool = False) -> Result:
        """Convert dataset format (MGMT-04).

        Supported formats: shp, gdb, csv, geojson.
        """
        if not self._data.exists(source):
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

        if no_overwrite and self._data.exists(destination):
            return Result.error(
                code="FILE_EXISTS",
                message=f"Destination already exists: {destination}. "
                        f"Use without --no-overwrite to overwrite.",
            )

        try:
            result_path = self._data.convert(Path(source), Path(destination), output_format)
            return Result.ok(
                data={"source": source, "destination": str(result_path),
                       "format": output_format},
                message=f"Converted to {output_format}: {result_path.name}",
            )
        except Exception as e:
            return Result.from_exception(e)
