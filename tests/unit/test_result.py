"""Tests for Result model."""
import json

from arcgis_agent.models.result import Result
from arcgis_agent.exceptions import ArcGISError


def test_result_ok_defaults():
    """Result.ok() produces correct defaults."""
    r = Result.ok()
    assert r.success is True
    assert r.code == "OK"
    assert r.message == "OK"
    assert r.data is None
    assert r.warnings == []


def test_result_ok_with_data():
    """Result.ok(data, message) sets data and message."""
    r = Result.ok({"key": "val"}, "Done")
    assert r.success is True
    assert r.data == {"key": "val"}
    assert r.message == "Done"


def test_result_error():
    """Result.error() produces success=False with given code."""
    r = Result.error("ERR", "something broke")
    assert r.success is False
    assert r.code == "ERR"
    assert r.message == "something broke"
    assert r.data is None


def test_result_from_agent_error():
    """Result.from_exception(ArcGISError) maps to the error's code."""
    exc = ArcGISError(code="GP_FAIL", message="fail")
    r = Result.from_exception(exc)
    assert r.success is False
    assert r.code == "GP_FAIL"
    assert "fail" in r.message


def test_result_from_generic_exception():
    """Result.from_exception(ValueError) maps to UNKNOWN_ERROR."""
    r = Result.from_exception(ValueError("oops"))
    assert r.success is False
    assert r.code == "UNKNOWN_ERROR"
    assert "oops" in r.message


def test_result_to_json_valid():
    """to_json() produces valid JSON with all 5 keys."""
    r = Result.ok()
    parsed = json.loads(r.to_json())
    assert "success" in parsed
    assert "code" in parsed
    assert "message" in parsed
    assert "data" in parsed
    assert "warnings" in parsed


def test_result_to_json_indent():
    """to_json(indent=None) produces compact JSON (no newlines)."""
    r = Result.ok({"key": "value"})
    compact = r.to_json(indent=None)
    assert "\n" not in compact
    # Should still be valid JSON
    parsed = json.loads(compact)
    assert parsed["success"] is True


def test_result_warnings_default_factory():
    """Two Result instances do not share the same warnings list."""
    r1 = Result.ok()
    r2 = Result.ok()
    r1.warnings.append("warning1")
    assert len(r1.warnings) == 1
    assert len(r2.warnings) == 0
