"""Workspace management service."""
from pathlib import Path
from arcgis_agent.config import WorkspaceConfig
from arcgis_agent.models.result import Result


class WorkspaceService:
    """Manages workspace path (PROJ-01, PROJ-02).

    Does NOT inherit BaseService -- workspace config is independent
    of arcpy adapters (no adapter injection needed).
    """

    def __init__(self, config: WorkspaceConfig | None = None):
        self._config = config or WorkspaceConfig()

    def set_workspace(self, path: str) -> Result:
        """Set current workspace path (PROJ-01)."""
        p = Path(path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Path does not exist: {path}",
            )
        if not p.is_dir():
            return Result.error(
                code="INVALID_FORMAT",
                message=f"Path is not a directory: {path}",
            )
        self._config.set_workspace(p)
        return Result.ok(
            data={"workspace": str(p.resolve())},
            message=f"Workspace set to {p.resolve()}",
        )

    def get_workspace(self) -> Result:
        """Get current workspace path (PROJ-02)."""
        ws = self._config.get_workspace()
        if ws is None:
            return Result.ok(
                data={"workspace": None},
                message="No workspace set. Use 'workspace set <path>' first.",
            )
        return Result.ok(
            data={"workspace": str(ws)},
            message=f"Current workspace: {ws}",
        )
