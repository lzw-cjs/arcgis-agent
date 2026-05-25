"""Tests for environment detection module."""
from dataclasses import fields

from arcgis_agent.env_check import EnvironmentStatus, check_environment


def test_environment_status_is_dataclass():
    """EnvironmentStatus is a dataclass with correct fields."""
    assert hasattr(EnvironmentStatus, '__dataclass_fields__')
    field_names = [f.name for f in fields(EnvironmentStatus)]
    assert 'available' in field_names
    assert 'message' in field_names
    assert 'arcpy_version' in field_names
    assert 'license_level' in field_names


def test_check_environment_returns_status():
    """check_environment() returns an EnvironmentStatus instance."""
    status = check_environment()
    assert isinstance(status, EnvironmentStatus)
    assert isinstance(status.available, bool)
    assert isinstance(status.message, str)


def test_check_environment_when_arcpy_available():
    """When arcpy is available, status has version info."""
    status = check_environment()
    if status.available:
        assert status.arcpy_version is not None
        assert status.license_level is not None
        assert 'ArcGIS Pro' in status.message
    else:
        # When arcpy is not available, message should be helpful
        assert 'arcpy not found' in status.message or 'arcpy error' in status.message


def test_check_environment_no_module_level_arcpy_import():
    """env_check.py should not import arcpy at module level."""
    import importlib
    import sys
    # If arcpy is not installed, this test is N/A
    # But we can verify the module loads without importing arcpy
    mod = importlib.import_module('arcgis_agent.env_check')
    source_file = mod.__file__
    with open(source_file) as f:
        source = f.read()
    # Check that 'import arcpy' only appears inside function bodies
    lines = source.split('\n')
    in_function = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('def '):
            in_function = True
        elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'"):
            if stripped.startswith('import arcpy'):
                assert in_function, "import arcpy must be inside a function, not at module level"
