"""Shared test fixtures for arcgis-agent tests."""
import pytest
from click.testing import CliRunner
from arcgis_agent.adapters.mock_adapter import (
    MockGeoProcessor, MockMapDocument, MockDataAccessor
)


@pytest.fixture
def runner():
    """Click CliRunner for CLI testing."""
    return CliRunner()


@pytest.fixture
def mock_gp():
    """Mock GeoProcessor adapter."""
    return MockGeoProcessor()


@pytest.fixture
def mock_map():
    """Mock MapDocument adapter."""
    return MockMapDocument()


@pytest.fixture
def mock_data():
    """Mock DataAccessor adapter."""
    return MockDataAccessor()


@pytest.fixture
def mock_adapters(mock_gp, mock_map, mock_data):
    """All three mock adapters as a dict."""
    return {"gp": mock_gp, "map_doc": mock_map, "data": mock_data}


@pytest.fixture
def mock_map_doc():
    """Mock MapDocument adapter with extended Phase-04 methods."""
    from arcgis_agent.adapters.mock_adapter import MockMapDocument
    return MockMapDocument()


@pytest.fixture
def mock_layout():
    """Mock LayoutDocument adapter."""
    from arcgis_agent.adapters.mock_adapter import MockLayoutDocument
    return MockLayoutDocument()


@pytest.fixture
def workspace_config(tmp_path):
    """WorkspaceConfig with temporary config file."""
    from arcgis_agent.config import WorkspaceConfig
    return WorkspaceConfig(config_path=tmp_path / "config.json")


@pytest.fixture
def workspace_service(workspace_config):
    """WorkspaceService with temporary config."""
    from arcgis_agent.services.workspace_service import WorkspaceService
    return WorkspaceService(config=workspace_config)
