"""Exception hierarchy with exit code mapping.

Exit codes:
  0 = success
  1 = user error (bad input, missing file, invalid format)
  2 = system error (internal failure, unexpected state)
  3 = ArcGIS error (arcpy failure, license issue)
"""


class AgentError(Exception):
    """Base exception for all arcgis-agent errors."""

    code: str = "UNKNOWN_ERROR"
    exit_code: int = 2

    def __init__(self, message: str = "", code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class UserError(AgentError):
    """Error caused by user input (exit code 1)."""

    code = "USER_ERROR"
    exit_code = 1


class FileNotFoundError_(UserError):
    """File or dataset not found."""

    code = "FILE_NOT_FOUND"


class InvalidFormatError(UserError):
    """Invalid format or unsupported operation."""

    code = "INVALID_FORMAT"


class SystemError_(AgentError):
    """Internal system error (exit code 2)."""

    code = "SYSTEM_ERROR"
    exit_code = 2


class ArcGISError(AgentError):
    """ArcGIS/arcpy error (exit code 3)."""

    code = "ARCGIS_ERROR"
    exit_code = 3

    def __init__(
        self,
        code: str = "ARCGIS_ERROR",
        message: str = "",
        arcpy_messages: str = "",
    ):
        super().__init__(message=message, code=code)
        self.arcpy_messages = arcpy_messages


def map_exception_to_code(exc: Exception) -> str:
    """Map an exception to its error code string."""
    if isinstance(exc, AgentError):
        return exc.code
    return "UNKNOWN_ERROR"
