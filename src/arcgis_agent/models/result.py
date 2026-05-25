"""Standardized Result model for all CLI command output."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Result(BaseModel):
    """Unified output model for all commands.

    Every command returns a Result serialized as JSON to stdout.
    Warnings and logs go to stderr.
    """

    success: bool
    code: str = "OK"
    message: str = ""
    data: Optional[dict[str, Any]] = None
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def ok(cls, data: dict[str, Any] | None = None, message: str = "OK") -> Result:
        return cls(success=True, code="OK", message=message, data=data)

    @classmethod
    def error(cls, code: str, message: str, data: dict[str, Any] | None = None) -> Result:
        return cls(success=False, code=code, message=message, data=data)

    @classmethod
    def from_exception(cls, exc: Exception) -> Result:
        from arcgis_agent.exceptions import map_exception_to_code

        code = map_exception_to_code(exc)
        return cls(success=False, code=code, message=str(exc))

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)
