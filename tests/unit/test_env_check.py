"""Tests for environment detection module."""
from arcgis_agent.env_check import EnvironmentStatus, check_environment


def test_check_environment_returns_status():
    """check_environment() returns an EnvironmentStatus instance."""
    status = check_environment()
    assert isinstance(status, EnvironmentStatus)


def test_check_environment_has_required_fields():
    """EnvironmentStatus has all required fields."""
    status = check_environment()
    assert hasattr(status, 'available')
    assert hasattr(status, 'message')
    assert hasattr(status, 'arcpy_version')
    assert hasattr(status, 'license_level')


def test_check_environment_available_type():
    """status.available is a bool."""
    status = check_environment()
    assert isinstance(status.available, bool)


def test_check_environment_message_type():
    """status.message is a non-empty string."""
    status = check_environment()
    assert isinstance(status.message, str)
    assert len(status.message) > 0
