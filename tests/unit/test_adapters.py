"""Tests for mock adapter implementations."""
import importlib
from pathlib import Path

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


def test_mock_gp_buffer_records_call(mock_gp):
    """MockGeoProcessor.buffer records call and returns Path."""
    result = mock_gp.buffer("in_fc", "out_fc", 100, "Meters")
    assert len(mock_gp.calls) == 1
    assert mock_gp.calls[0] == ("buffer", "in_fc", "out_fc", 100, "Meters", None)
    assert isinstance(result, Path)
    assert result.name == "out_fc"


def test_mock_gp_clip_records_call(mock_gp):
    """MockGeoProcessor.clip records call."""
    result = mock_gp.clip("in_fc", "clip_fc", "out_fc")
    assert len(mock_gp.calls) == 1
    assert mock_gp.calls[0] == ("clip", "in_fc", "clip_fc", "out_fc")
    assert isinstance(result, Path)


def test_mock_gp_intersect_records_call(mock_gp):
    """MockGeoProcessor.intersect records call."""
    result = mock_gp.intersect(["fc1", "fc2"], "out_fc")
    assert len(mock_gp.calls) == 1
    assert mock_gp.calls[0] == ("intersect", ["fc1", "fc2"], "out_fc")
    assert isinstance(result, Path)


def test_mock_map_create_records_call(mock_map):
    """MockMapDocument.create_map records call."""
    result = mock_map.create_map(Path("/test/aprx"), "Map1")
    assert len(mock_map.calls) == 1
    assert mock_map.calls[0] == ("create_map", str(Path("/test/aprx")), "Map1")
    assert isinstance(result, Path)


def test_mock_map_add_layer_records_call(mock_map):
    """MockMapDocument.add_layer records call."""
    mock_map.add_layer(Path("/test/aprx"), "Map1", Path("/test/lyr"))
    assert len(mock_map.calls) == 1
    assert mock_map.calls[0] == ("add_layer", str(Path("/test/aprx")), "Map1",
                                  str(Path("/test/lyr")))


def test_mock_map_export_records_call(mock_map):
    """MockMapDocument.export_map records call and returns Path."""
    result = mock_map.export_map(Path("/test/aprx"), "Map1",
                                  Path("/test/out.png"), "PNG", 300)
    assert len(mock_map.calls) == 1
    assert mock_map.calls[0] == ("export_map", str(Path("/test/aprx")), "Map1",
                                  str(Path("/test/out.png")), "PNG", 300, False)
    assert isinstance(result, Path)


def test_mock_data_list_returns_stub(mock_data):
    """MockDataAccessor.list_feature_classes returns stub list."""
    result = mock_data.list_feature_classes(Path("/test/ws"))
    assert result == ["mock_feature_class"]
    assert len(mock_data.calls) == 1


def test_mock_data_describe_returns_dict(mock_data):
    """MockDataAccessor.describe returns dict with dataType key."""
    result = mock_data.describe(Path("test.shp"))
    assert isinstance(result, dict)
    assert "dataType" in result
    assert result["dataType"] == "FeatureClass"
    assert result["name"] == "test"


def test_mock_data_convert_records_call(mock_data):
    """MockDataAccessor.convert records call and returns Path."""
    result = mock_data.convert(Path("/test/in.shp"), Path("/test/out.csv"),
                                "CSV")
    assert len(mock_data.calls) == 1
    assert mock_data.calls[0] == ("convert", str(Path("/test/in.shp")),
                                   str(Path("/test/out.csv")), "CSV")
    assert isinstance(result, Path)


def test_mock_gp_implements_interface(mock_gp):
    """MockGeoProcessor is an instance of IGeoProcessor."""
    assert isinstance(mock_gp, IGeoProcessor)


def test_mock_map_implements_interface(mock_map):
    """MockMapDocument is an instance of IMapDocument."""
    assert isinstance(mock_map, IMapDocument)


def test_mock_data_implements_interface(mock_data):
    """MockDataAccessor is an instance of IDataAccessor."""
    assert isinstance(mock_data, IDataAccessor)


def test_arcpy_adapter_module_importable():
    """arcpy_adapter module can be imported without triggering arcpy import."""
    mod = importlib.import_module("arcgis_agent.adapters.arcpy_adapter")
    assert hasattr(mod, "ArcPyGeoProcessor")
    assert hasattr(mod, "ArcPyMapDocument")
    assert hasattr(mod, "ArcPyDataAccessor")
