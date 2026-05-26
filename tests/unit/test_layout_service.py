"""Tests for LayoutService (Phase 04: MAP-09 through MAP-11)."""
import pytest
from pathlib import Path

from arcgis_agent.services.layout_service import LayoutService
from arcgis_agent.adapters.mock_adapter import MockLayoutDocument


class TestCreateLayout:
    """MAP-09: create_layout tests (D-26)."""

    def test_create_a4_portrait(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_layout(str(f), "MyLayout", "A4", "portrait")
        assert result.success
        assert mock.calls[0][0] == "create_layout"
        assert mock.calls[0][3] == 210.0  # width
        assert mock.calls[0][4] == 297.0  # height

    def test_create_a3_landscape(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_layout(str(f), "MyLayout", "A3", "landscape")
        assert result.success
        assert mock.calls[0][3] == 420.0  # width (swapped for landscape)
        assert mock.calls[0][4] == 297.0  # height

    def test_create_letter_landscape(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_layout(str(f), "MyLayout", "Letter", "landscape")
        assert result.success
        assert mock.calls[0][3] == 11.0
        assert mock.calls[0][4] == 8.5

    def test_create_invalid_page_size(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_layout(str(f), "MyLayout", "B5", "portrait")
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_create_empty_name(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_layout(str(f), "")
        assert not result.success
        assert "INVALID_INPUT" in result.code


class TestAddElement:
    """MAP-10: add_element tests (D-18 through D-25, D-27)."""

    def test_add_text_element(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "text",
                                  position="top-center",
                                  params="text=My Map,font_size=24,color=0,0,0,bold=true")
        assert result.success
        assert mock.calls[0][0] == "add_element"
        assert mock.calls[0][3] == "text"
        config = mock.calls[0][4]
        assert config["text"] == "My Map"
        assert config["font_size"] == 24
        assert config["position"] == "top-center"

    def test_add_legend_element(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "legend",
                                  params="title=My Legend")
        assert result.success
        config = mock.calls[0][4]
        assert config["title"] == "My Legend"

    def test_add_scale_bar(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "scale-bar",
                                  params="style=Bar")
        assert result.success
        config = mock.calls[0][4]
        assert config["style"] == "Bar"

    def test_add_north_arrow(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "north-arrow",
                                  params="style=Arrow")
        assert result.success
        config = mock.calls[0][4]
        assert config["style"] == "Arrow"

    def test_add_map_frame(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "map-frame",
                                  params="map=Map1,extent=full_extent")
        assert result.success
        config = mock.calls[0][4]
        assert config["map"] == "Map1"
        assert config["extent"] == "full_extent"

    def test_add_image_element_not_found(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "image",
                                  params="source=/nonexistent/logo.png")
        assert not result.success
        assert "FILE_NOT_FOUND" in result.code

    def test_add_image_bad_extension(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        bad_img = tmp_path / "logo.svg"
        bad_img.touch()
        result = svc.add_element(str(f), "MyLayout", "image",
                                  params=f"source={bad_img}")
        assert not result.success
        assert "INVALID_FORMAT" in result.code

    def test_add_element_invalid_type(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "chart")
        assert not result.success
        assert "INVALID_INPUT" in result.code

    def test_add_element_invalid_position(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.add_element(str(f), "MyLayout", "text",
                                  position="middle")
        assert not result.success
        assert "INVALID_INPUT" in result.code


class TestExportLayout:
    """MAP-11: export_layout tests (D-28 through D-31)."""

    def test_export_pdf_default(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.pdf"
        result = svc.export_layout(str(f), "MyLayout", str(out))
        assert result.success
        assert mock.calls[0][0] == "export_layout"

    def test_export_png_transparent(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.png"
        result = svc.export_layout(str(f), "MyLayout", str(out),
                                    format="PNG", transparent=True)
        assert result.success

    def test_export_invalid_dpi(self, tmp_path):
        mock = MockLayoutDocument()
        svc = LayoutService(layout_doc=mock)
        f = tmp_path / "test.aprx"
        f.touch()
        out = tmp_path / "output.pdf"
        result = svc.export_layout(str(f), "MyLayout", str(out), dpi=72)
        assert not result.success
        assert "INVALID_INPUT" in result.code
