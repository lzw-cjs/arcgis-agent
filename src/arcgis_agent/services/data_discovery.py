"""Data discovery service: list, describe, fields, extent, count."""
from pathlib import Path
from arcgis_agent.services.base import BaseService
from arcgis_agent.config import WorkspaceConfig
from arcgis_agent.models.result import Result


class DataDiscoveryService(BaseService):
    """Read-only data discovery operations (DISC-01 through DISC-05).

    All operations use self._data (IDataAccessor) adapter.
    Workspace-aware: uses WorkspaceConfig to resolve relative paths.
    """

    def __init__(self, data=None, config: WorkspaceConfig | None = None):
        # Only inject data adapter (not gp/map -- not needed for discovery).
        # Skip super().__init__ to avoid importing arcpy for unused adapters.
        self._data = data if data is not None else self._make_data()
        self._gp = None
        self._map = None
        self._config = config or WorkspaceConfig()

    def _resolve_workspace(self, workspace: str | None) -> Path:
        """Resolve workspace path: explicit arg > config > error."""
        if workspace:
            p = Path(workspace)
            if not p.exists():
                from arcgis_agent.exceptions import FileNotFoundError_
                raise FileNotFoundError_(
                    message=f"Workspace not found: {workspace}"
                )
            return p

        ws = self._config.get_workspace()
        if ws is None:
            from arcgis_agent.exceptions import FileNotFoundError_
            raise FileNotFoundError_(
                message="No workspace set. Use 'workspace set <path>' or pass --workspace."
            )
        return ws

    def list_datasets(self, workspace: str | None = None,
                      dataset_type: str | None = None,
                      name_pattern: str | None = None) -> Result:
        """List all datasets in workspace (DISC-01).

        Args:
            workspace: Explicit workspace path, or None to use configured workspace.
            dataset_type: Filter by type (FeatureClass, Table, RasterDataset, FeatureDataset).
            name_pattern: Glob pattern for name filtering (e.g., "roads*").
        """
        try:
            ws = self._resolve_workspace(workspace)
            datasets = self._data.list_datasets(ws, dataset_type, name_pattern)
            return Result.ok(
                data={"datasets": datasets, "count": len(datasets),
                       "workspace": str(ws)},
                message=f"Found {len(datasets)} dataset(s)",
            )
        except Exception as e:
            return Result.from_exception(e)

    def describe(self, dataset_path: str) -> Result:
        """Describe dataset metadata (DISC-02)."""
        p = Path(dataset_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            desc = self._data.describe(p)
            return Result.ok(
                data=desc,
                message=f"Dataset: {desc.get('name', p.name)}",
            )
        except Exception as e:
            return Result.from_exception(e)

    def get_fields(self, dataset_path: str) -> Result:
        """List field definitions (DISC-03)."""
        p = Path(dataset_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            fields = self._data.get_fields(p)
            return Result.ok(
                data={"fields": fields, "count": len(fields)},
                message=f"Found {len(fields)} field(s)",
            )
        except Exception as e:
            return Result.from_exception(e)

    def get_extent(self, dataset_path: str) -> Result:
        """Get spatial extent (DISC-04)."""
        p = Path(dataset_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            extent = self._data.get_extent(p)
            return Result.ok(
                data=extent,
                message="Extent retrieved",
            )
        except Exception as e:
            return Result.from_exception(e)

    def get_count(self, dataset_path: str) -> Result:
        """Get record count (DISC-05)."""
        p = Path(dataset_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Dataset not found: {dataset_path}",
            )
        try:
            count = self._data.get_count(p)
            return Result.ok(
                data={"count": count, "path": str(p)},
                message=f"{count} record(s)",
            )
        except Exception as e:
            return Result.from_exception(e)
