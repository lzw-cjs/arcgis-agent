"""Tests for BaseService dependency injection."""
from arcgis_agent.services.base import BaseService
from arcgis_agent.adapters.mock_adapter import (
    MockGeoProcessor, MockMapDocument, MockDataAccessor,
)
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


def test_inject_all_mocks():
    """BaseService stores injected mock adapters."""
    mock_gp = MockGeoProcessor()
    mock_map = MockMapDocument()
    mock_data = MockDataAccessor()
    svc = BaseService(gp=mock_gp, map_doc=mock_map, data=mock_data)
    assert svc._gp is mock_gp
    assert svc._map is mock_map
    assert svc._data is mock_data


def test_inject_single_adapter():
    """BaseService with one injected adapter uses it."""
    mock_gp = MockGeoProcessor()
    svc = BaseService(gp=mock_gp)
    assert svc._gp is mock_gp


def test_injected_adapters_are_instances_of_interfaces():
    """Injected adapters satisfy interface contracts."""
    svc = BaseService(
        gp=MockGeoProcessor(),
        map_doc=MockMapDocument(),
        data=MockDataAccessor(),
    )
    assert isinstance(svc._gp, IGeoProcessor)
    assert isinstance(svc._map, IMapDocument)
    assert isinstance(svc._data, IDataAccessor)


def test_default_creates_real_adapters():
    """BaseService with no args lazy-creates real ArcPy adapters."""
    # This test will only pass in an ArcGIS Pro environment
    # In CI without arcpy, _make_* will raise ImportError
    try:
        svc = BaseService()
        assert svc._gp is not None
        assert svc._map is not None
        assert svc._data is not None
    except ImportError:
        # Expected when arcpy is not available
        pass


def test_make_gp_returns_correct_type():
    """_make_gp() returns ArcPyGeoProcessor."""
    from arcgis_agent.adapters.arcpy_adapter import ArcPyGeoProcessor
    gp = BaseService._make_gp()
    assert isinstance(gp, ArcPyGeoProcessor)


def test_make_map_returns_correct_type():
    """_make_map() returns ArcPyMapDocument."""
    from arcgis_agent.adapters.arcpy_adapter import ArcPyMapDocument
    m = BaseService._make_map()
    assert isinstance(m, ArcPyMapDocument)


def test_make_data_returns_correct_type():
    """_make_data() returns ArcPyDataAccessor."""
    from arcgis_agent.adapters.arcpy_adapter import ArcPyDataAccessor
    d = BaseService._make_data()
    assert isinstance(d, ArcPyDataAccessor)
