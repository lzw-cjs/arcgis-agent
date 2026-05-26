"""Tests for MapService (Phase 04: MAP-01 through MAP-08)."""
import pytest
from pathlib import Path

from arcgis_agent.services.map_service import MapService
from arcgis_agent.adapters.mock_adapter import MockMapDocument


class TestCreateMap:
    """MAP-01: create_map tests."""

    def test_create_map_success(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_map(str(f), "MyMap")
        assert result.success
        assert result.data["map_name"] == "MyMap"
        assert "elapsed_seconds" in result.data

    def test_create_map_uses_adapter(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        svc.create_map(str(f), "MyMap")
        assert len(mock_map.calls) == 1
        assert mock_map.calls[0][0] == "create_map"

    def test_create_map_empty_name(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_map(str(f), "")
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_create_map_project_not_found(self):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        result = svc.create_map("/nonexistent/path.aprx", "MyMap")
        assert not result.success
        assert "FILE_NOT_FOUND" in result.code


class TestAddLayer:
    """MAP-02: add_layer tests."""

    def test_add_layer_success(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f_aprx = tmp_path / "test.aprx"
        f_aprx.touch()
        f_data = tmp_path / "data.shp"
        f_data.touch()
        result = svc.add_layer(str(f_aprx), "MyMap", str(f_data))
        assert result.success
        assert mock_map.calls[0][0] == "add_layer"

    def test_add_layer_data_not_found(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f_aprx = tmp_path / "test.aprx"
        f_aprx.touch()
        result = svc.add_layer(str(f_aprx), "MyMap", "/nonexistent/data.shp")
        assert not result.success
        assert "FILE_NOT_FOUND" in result.code


class TestRemoveLayer:
    """MAP-03: remove_layer tests (D-02)."""

    def test_remove_by_name(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.remove_layer(str(f), "MyMap", layer_name="Roads")
        assert result.success
        assert mock_map.calls[0][0] == "remove_layer"
        assert mock_map.calls[0][3] == "Roads"

    def test_remove_by_index(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.remove_layer(str(f), "MyMap", layer_index=2)
        assert result.success
        assert mock_map.calls[0][4] == 2

    def test_remove_no_identifier(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.remove_layer(str(f), "MyMap")
        assert not result.success
        assert "INVALID_INPUT" in result.code


class TestListLayers:
    """MAP-04: list_layers tests (D-07)."""

    def test_list_layers_returns_data(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.list_layers(str(f), "MyMap")
        assert result.success
        layers = result.data["layers"]
        assert len(layers) == 2
        assert "name" in layers[0]
        assert "datasource" in layers[0]
        assert "feature_count" in layers[0]


class TestSetExtent:
    """MAP-05: set_extent tests (D-03)."""

    def test_set_extent_zoom_to_layer(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.set_extent(str(f), "MyMap", "Roads")
        assert result.success
        assert mock_map.calls[0][0] == "set_extent"
        assert mock_map.calls[0][3] == "Roads"

    def test_set_extent_empty_layer(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.set_extent(str(f), "MyMap", "")
        assert not result.success
        assert "INVALID_INPUT" in result.code


class TestExportMap:
    """MAP-06: export_map tests (D-28, D-30, D-31)."""

    def test_export_png_default(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.png"
        result = svc.export_map(str(f), "MyMap", str(out))
        assert result.success
        assert mock_map.calls[0][0] == "export_map"

    def test_export_pdf(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.pdf"
        result = svc.export_map(str(f), "MyMap", str(out), format="PDF")
        assert result.success

    def test_export_invalid_dpi(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.png"
        result = svc.export_map(str(f), "MyMap", str(out), dpi=999)
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_export_invalid_format(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.tiff"
        result = svc.export_map(str(f), "MyMap", str(out), format="TIFF")
        assert not result.success
        assert "INVALID_FORMAT" in result.code


class TestSymbolize:
    """MAP-07: symbolize_layer tests (D-09 through D-15)."""

    def test_symbolize_simple(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "simple",
                                      color="255,0,0", outline_color="0,0,0",
                                      size=8, opacity=80)
        assert result.success
        assert mock_map.calls[0][0] == "symbolize_layer"
        config = mock_map.calls[0][4]
        assert config["type"] == "simple"
        assert config["color"] == [255, 0, 0]
        assert config["opacity"] == 80

    def test_symbolize_unique_values(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "unique_values",
                                      field="TYPE", color_ramp="Cyan to Purple")
        assert result.success
        config = mock_map.calls[0][4]
        assert config["type"] == "unique_values"
        assert config["field"] == "TYPE"

    def test_symbolize_graduated_colors(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "graduated_colors",
                                      field="POP", classification_method="Quantile",
                                      break_count=7)
        assert result.success
        config = mock_map.calls[0][4]
        assert config["type"] == "graduated_colors"
        assert config["classification_method"] == "Quantile"
        assert config["break_count"] == 7

    def test_symbolize_invalid_type(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "invalid_type")
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_symbolize_invalid_color(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "simple",
                                      color="300,0,0")
        assert not result.success
        assert "INVALID_COLOR" in result.code

    def test_symbolize_break_count_out_of_range(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "graduated_colors",
                                      field="POP", break_count=10)
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_symbolize_opacity_out_of_range(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.symbolize_layer(str(f), "MyMap", "Roads", "simple",
                                      color="255,0,0", opacity=150)
        assert not result.success
        assert "INVALID_INPUT" in result.code


class TestLabel:
    """MAP-08: set_label tests (D-16)."""

    def test_set_label_success(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.set_label(str(f), "MyMap", "Roads", "NAME",
                                font_size=12, color="255,0,0", bold=True)
        assert result.success
        assert mock_map.calls[0][0] == "set_label"
        config = mock_map.calls[0][4]
        assert config["field"] == "NAME"
        assert config["font_size"] == 12
        assert config["bold"] is True

    def test_set_label_missing_field(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.set_label(str(f), "MyMap", "Roads", "")
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_set_label_font_size_invalid(self, tmp_path):
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.set_label(str(f), "MyMap", "Roads", "NAME", font_size=500)
        assert not result.success
        assert "INVALID_INPUT" in result.code
