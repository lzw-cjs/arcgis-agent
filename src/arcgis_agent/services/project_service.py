"""Project information service."""
from pathlib import Path
from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


class ProjectService(BaseService):
    """Project information operations (PROJ-03).

    Uses IMapDocument adapter for project introspection.
    """

    def info(self, project_path: str | None = None) -> Result:
        """Get project information (PROJ-03).

        If project_path is None, returns info about the default project.
        Returns: path, GDB list, map list.
        """
        if project_path is None:
            return Result.error(
                code="FILE_NOT_FOUND",
                message="No project path specified. Provide --project or set a default.",
            )

        p = Path(project_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Project not found: {project_path}",
            )
        if p.suffix.lower() != ".aprx":
            return Result.error(
                code="INVALID_FORMAT",
                message=f"Not an ArcGIS Pro project file: {project_path}",
            )

        try:
            # Use IMapDocument adapter to introspect project
            project_info = self._map.get_project_info(p)
            return Result.ok(
                data={
                    "path": str(p.resolve()),
                    "maps": project_info.get("maps", []),
                    "databases": project_info.get("databases", []),
                },
                message=f"Project: {p.name}",
            )
        except Exception as e:
            return Result.from_exception(e)
