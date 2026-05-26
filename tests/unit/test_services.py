"""Tests for BaseService dependency injection."""
from arcgis_agent.services.base import BaseService
from arcgis_agent.adapters.mock_adapter import (
    MockGeoProcessor, MockMapDocument, MockDataAccessor,
)
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


def test_base_service_inject_all(mock_adapters):
    """BaseService(**mock_adapters) stores all three mocks."""
    svc = BaseService(**mock_adapters)
    assert svc._gp is mock_adapters["gp"]
    assert svc._map is mock_adapters["map_doc"]
    assert svc._data is mock_adapters["data"]


def test_base_service_inject_single(mock_gp):
    """BaseService(gp=mock_gp) stores mock_gp as the adapter."""
    svc = BaseService(gp=mock_gp)
    assert svc._gp is mock_gp


def test_base_service_injected_implements_interfaces():
    """Injected adapters satisfy interface contracts."""
    svc = BaseService(
        gp=MockGeoProcessor(),
        map_doc=MockMapDocument(),
        data=MockDataAccessor(),
    )
    assert isinstance(svc._gp, IGeoProcessor)
    assert isinstance(svc._map, IMapDocument)
    assert isinstance(svc._data, IDataAccessor)


def test_base_service_inject_none(monkeypatch):
    """BaseService() with no args uses _make_* to create adapters."""
    monkeypatch.setattr(
        BaseService, "_make_gp",
        staticmethod(lambda: MockGeoProcessor()),
    )
    monkeypatch.setattr(
        BaseService, "_make_map",
        staticmethod(lambda: MockMapDocument()),
    )
    monkeypatch.setattr(
        BaseService, "_make_data",
        staticmethod(lambda: MockDataAccessor()),
    )
    svc = BaseService()
    assert isinstance(svc._gp, MockGeoProcessor)
    assert isinstance(svc._map, MockMapDocument)
    assert isinstance(svc._data, MockDataAccessor)
