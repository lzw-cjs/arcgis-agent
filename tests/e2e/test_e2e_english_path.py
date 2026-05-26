"""E2E test: full Map + Layout workflow on English path (no Chinese chars).

Run from ArcGIS Pro conda environment:
    conda activate arcgis-agent
    python -m pytest tests/e2e/test_e2e_english_path.py -v -s

To keep output files for inspection:
    set KEEP_TEST_OUTPUT=1
    python -m pytest tests/e2e/test_e2e_english_path.py -v -s

Prerequisite: ArcGIS Pro with valid license.
All data is under D:/arcgis_e2e_test/ (English path to avoid arcpy encoding bug).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

# Test workspace uses English-only path to avoid arcpy encoding bug
E2E_WORKSPACE = Path("D:/arcgis_e2e_test")


def _require_arcpy():
    """Skip all tests if arcpy is not available."""
    try:
        import arcpy  # noqa: F401
    except ImportError:
        pytest.skip("arcpy not available (requires ArcGIS Pro conda environment)")


def _ensure_workspace():
    """Create E2E workspace if it doesn't exist."""
    E2E_WORKSPACE.mkdir(parents=True, exist_ok=True)


def _cleanup_workspace():
    """Remove E2E workspace unless KEEP_TEST_OUTPUT=1 is set."""
    if os.environ.get("KEEP_TEST_OUTPUT") == "1":
        print(f"\n  [KEEP] Test output preserved at: {E2E_WORKSPACE}")
        return
    if E2E_WORKSPACE.exists():
        shutil.rmtree(str(E2E_WORKSPACE), ignore_errors=True)


@pytest.fixture(scope="module")
def e2e_workspace():
    """Module-scoped fixture: create clean workspace, yield it, teardown."""
    _require_arcpy()
    import arcpy

    _cleanup_workspace()
    _ensure_workspace()

    # Create a file GDB for test data (delete stale one first)
    gdb_path = str(E2E_WORKSPACE / "test_data.gdb")
    if arcpy.Exists(gdb_path):
        arcpy.management.Delete(gdb_path)
    arcpy.management.CreateFileGDB(str(E2E_WORKSPACE), "test_data.gdb")

    # Create a sample feature class in the GDB
    sample_fc = str(E2E_WORKSPACE / "test_data.gdb" / "cities")
    arcpy.management.CreateFeatureclass(
        gdb_path, "cities", "POINT",
        spatial_reference=arcpy.SpatialReference(4326)
    )
    # Add fields
    arcpy.management.AddField(sample_fc, "NAME", "TEXT", field_length=50)
    arcpy.management.AddField(sample_fc, "POP", "LONG")

    # Insert some features
    with arcpy.da.InsertCursor(sample_fc, ["SHAPE@", "NAME", "POP"]) as cursor:
        import math
        cities = [
            ("Beijing", 116.4, 39.9, 21500000),
            ("Shanghai", 121.5, 31.2, 24870000),
            ("Guangzhou", 113.3, 23.1, 18670000),
            ("Shenzhen", 114.1, 22.5, 17560000),
            ("Chengdu", 104.1, 30.6, 20930000),
            ("Wuhan", 114.3, 30.6, 13720000),
            ("Hangzhou", 120.2, 30.3, 11930000),
            ("Nanjing", 118.8, 32.1, 9310000),
        ]
        for name, lon, lat, pop in cities:
            point = arcpy.Point(lon, lat)
            cursor.insertRow([point, name, pop])

    # Create a second FC for geoprocessing tests
    buffer_fc = str(E2E_WORKSPACE / "test_data.gdb" / "study_areas")
    arcpy.analysis.Buffer(sample_fc, buffer_fc, "2 DecimalDegrees")

    yield {
        "gdb": gdb_path,
        "cities": sample_fc,
        "study_areas": buffer_fc,
    }

    # Teardown
    _cleanup_workspace()


@pytest.fixture(scope="module")
def project_path(e2e_workspace):
    """Create a fresh blank ArcGIS Pro project for E2E tests.

    arcpy.mp.ArcGISProject(path) creates a new blank project when the
    file does not exist (well-known undocumented arcpy behavior).

    Known issue: arcpy.mp.ArcGISProject() may throw OSError on systems
    with non-ASCII Windows usernames due to internal temp path handling
    in the underlying C++ component (arcgisscripting._mapping).
    """
    import arcpy

    aprx_path = str(E2E_WORKSPACE / "e2e_project.aprx")
    try:
        aprx = arcpy.mp.ArcGISProject(aprx_path)
    except OSError:
        pytest.skip(
            "arcpy.mp.ArcGISProject() not available on this system "
            "(see arcpy Chinese username bug)"
        )
    try:
        aprx.save()
    except OSError:
        pass
    yield aprx_path
    del aprx
    p = Path(aprx_path)
    if p.exists():
        p.unlink()


# ── E2E Test Suite ────────────────────────────────────────────


class TestE2EMapWorkflow:
    """Complete map workflow: create -> add layer -> symbolize -> label -> export."""

    def test_01_create_map(self, e2e_workspace, project_path):
        """MAP-01: Create a new map in the project."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.create_map(project_path, "Cities Map")
        assert result.success, f"Create map failed: {result.message}"
        print(f"  [OK] Map created: {result.data}")

    def test_02_add_layer(self, e2e_workspace, project_path):
        """MAP-02: Add a layer to the map."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.add_layer(project_path, "Cities Map", e2e_workspace["cities"])
        assert result.success, f"Add layer failed: {result.message}"
        print(f"  [OK] Layer added: {result.data}")

    def test_03_list_layers(self, e2e_workspace, project_path):
        """MAP-04: List layers in the map."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.list_layers(project_path, "Cities Map")
        assert result.success, f"List layers failed: {result.message}"
        assert result.data["count"] >= 1
        print(f"  [OK] Layers: {result.data['count']} found")

    def test_04_set_extent(self, e2e_workspace, project_path):
        """MAP-05: Zoom to a specific layer."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.set_extent(project_path, "Cities Map", "cities")
        assert result.success, f"Set extent failed: {result.message}"
        print(f"  [OK] Extent set to 'cities'")

    def test_05_simple_symbolize(self, e2e_workspace, project_path):
        """MAP-07: Apply simple symbology to layer."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.symbolize_layer(
            project_path, "Cities Map", "cities",
            symbology_type="simple",
            color="255,0,0",
            size=12,
            opacity=80,
        )
        assert result.success, f"Symbolize failed: {result.message}"
        print(f"  [OK] Simple symbology applied")

    def test_06_unique_values_symbolize(self, e2e_workspace, project_path):
        """MAP-07: Apply unique values symbology."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.symbolize_layer(
            project_path, "Cities Map", "cities",
            symbology_type="unique_values",
            field="NAME",
            color_ramp="Basic Random",
        )
        assert result.success, f"Unique values symbolize failed: {result.message}"
        print(f"  [OK] Unique values symbology applied")

    def test_07_graduated_colors_symbolize(self, e2e_workspace, project_path):
        """MAP-07: Apply graduated colors symbology."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.symbolize_layer(
            project_path, "Cities Map", "cities",
            symbology_type="graduated_colors",
            field="POP",
            classification_method="NaturalBreaks",
            break_count=5,
            color_ramp="Blues",
        )
        assert result.success, f"Graduated colors failed: {result.message}"
        print(f"  [OK] Graduated colors symbology applied")

    def test_08_set_label(self, e2e_workspace, project_path):
        """MAP-08: Set label on layer."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.set_label(
            project_path, "Cities Map", "cities",
            field="NAME",
            font_size=11,
            color="0,0,0",
            bold=True,
        )
        assert result.success, f"Set label failed: {result.message}"
        print(f"  [OK] Labels applied")

    def test_09_export_map_png(self, e2e_workspace, project_path):
        """MAP-06: Export map to PNG."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        output = str(E2E_WORKSPACE / "output_map.png")
        result = svc.export_map(project_path, "Cities Map", output,
                               format="PNG", dpi=150)
        assert result.success, f"Export map failed: {result.message}"
        assert Path(result.data["output"]).exists(), "Output file not created"
        print(f"  [OK] Map exported to PNG: {result.data['output']}")

    def test_10_export_map_pdf(self, e2e_workspace, project_path):
        """MAP-06: Export map to PDF."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        output = str(E2E_WORKSPACE / "output_map.pdf")
        result = svc.export_map(project_path, "Cities Map", output,
                               format="PDF", dpi=300)
        assert result.success, f"Export map PDF failed: {result.message}"
        assert Path(result.data["output"]).exists(), "Output file not created"
        print(f"  [OK] Map exported to PDF: {result.data['output']}")

    def test_11_remove_layer(self, e2e_workspace, project_path):
        """MAP-03: Remove layer from map."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.add_layer(project_path, "Cities Map", e2e_workspace["study_areas"])
        assert result.success
        result = svc.remove_layer(project_path, "Cities Map", layer_name="study_areas")
        assert result.success, f"Remove layer failed: {result.message}"
        print(f"  [OK] Layer removed")


class TestE2ELayoutWorkflow:
    """Complete layout workflow: create -> add elements -> export."""

    def test_01_create_layout(self, e2e_workspace, project_path):
        """MAP-09: Create a layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.create_layout(project_path, "Main Layout",
                                   page_size="A4", orientation="landscape")
        assert result.success, f"Create layout failed: {result.message}"
        print(f"  [OK] Layout created: {result.data}")

    def test_02_add_map_frame(self, e2e_workspace, project_path):
        """MAP-10: Add map frame element to layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.add_element(
            project_path, "Main Layout",
            element_type="map-frame",
            position="center",
            params="width=7.0,height=5.0,extent=full_extent",
        )
        assert result.success, f"Add map frame failed: {result.message}"
        print(f"  [OK] Map frame added")

    def test_03_add_title(self, e2e_workspace, project_path):
        """MAP-10: Add text element (title) to layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.add_element(
            project_path, "Main Layout",
            element_type="text",
            position="top-center",
            params="text=China Major Cities Map,font_size=18,bold=true",
        )
        assert result.success, f"Add title failed: {result.message}"
        print(f"  [OK] Title added")

    def test_04_add_legend(self, e2e_workspace, project_path):
        """MAP-10: Add legend element to layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.add_element(
            project_path, "Main Layout",
            element_type="legend",
            position="bottom-left",
            params="title=Legend,width=2.0,height=2.5",
        )
        assert result.success, f"Add legend failed: {result.message}"
        print(f"  [OK] Legend added")

    def test_05_add_scale_bar(self, e2e_workspace, project_path):
        """MAP-10: Add scale bar element to layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.add_element(
            project_path, "Main Layout",
            element_type="scale-bar",
            position="bottom-center",
            params="style=Alternating,width=3.0,height=0.5",
        )
        assert result.success, f"Add scale bar failed: {result.message}"
        print(f"  [OK] Scale bar added")

    def test_06_add_north_arrow(self, e2e_workspace, project_path):
        """MAP-10: Add north arrow element to layout."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.add_element(
            project_path, "Main Layout",
            element_type="north-arrow",
            position="top-right",
            params="style=Default,width=0.8,height=0.8",
        )
        assert result.success, f"Add north arrow failed: {result.message}"
        print(f"  [OK] North arrow added")

    def test_07_export_layout_png(self, e2e_workspace, project_path):
        """MAP-11: Export layout to PNG."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        output = str(E2E_WORKSPACE / "output_layout.png")
        result = svc.export_layout(project_path, "Main Layout", output,
                                   format="PNG", dpi=150)
        assert result.success, f"Export layout failed: {result.message}"
        assert Path(result.data["output"]).exists(), "Output file not created"
        print(f"  [OK] Layout exported to PNG: {result.data['output']}")

    def test_08_export_layout_pdf(self, e2e_workspace, project_path):
        """MAP-11: Export layout to PDF."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        output = str(E2E_WORKSPACE / "output_layout.pdf")
        result = svc.export_layout(project_path, "Main Layout", output,
                                   format="PDF", dpi=300)
        assert result.success, f"Export layout PDF failed: {result.message}"
        assert Path(result.data["output"]).exists(), "Output file not created"
        print(f"  [OK] Layout exported to PDF: {result.data['output']}")


class TestE2EGeoprocessing:
    """Geoprocessing operations E2E."""

    def test_01_buffer(self, e2e_workspace):
        """GEO-01: Buffer analysis."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_buffered")
        result = svc.buffer(e2e_workspace["cities"], output,
                           distance=1.0, unit="DecimalDegrees")
        assert result.success, f"Buffer failed: {result.message}"
        print(f"  [OK] Buffer: {result.data}")

    def test_02_clip(self, e2e_workspace):
        """GEO-02: Clip analysis."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_clipped")
        result = svc.clip(
            e2e_workspace["cities"],
            e2e_workspace["study_areas"],
            output,
        )
        assert result.success, f"Clip failed: {result.message}"
        print(f"  [OK] Clip: {result.data}")

    def test_03_select_by_attribute(self, e2e_workspace):
        """GEO-03: Select by attribute."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_selected")
        result = svc.select_by_attribute(
            e2e_workspace["cities"], output,
            "POP > 15000000"
        )
        assert result.success, f"Select failed: {result.message}"
        print(f"  [OK] Select: {result.data}")

    def test_04_dissolve(self, e2e_workspace):
        """GEO-05: Dissolve - note: points don't dissolve well, use buffer output."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        # Create buffered polygons first, then dissolve
        buf_out = str(E2E_WORKSPACE / "test_data.gdb" / "cities_buf4dissolve")
        svc.buffer(e2e_workspace["cities"], buf_out, distance=1.0, unit="DecimalDegrees")
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_dissolved")
        result = svc.dissolve(buf_out, output, dissolve_field="NAME")
        assert result.success, f"Dissolve failed: {result.message}"
        print(f"  [OK] Dissolve: {result.data}")

    def test_05_merge(self, e2e_workspace):
        """GEO-07: Merge - merge cities with itself as a proxy test."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_merged")
        # Need two datasets to merge; select two subsets
        sel1 = str(E2E_WORKSPACE / "test_data.gdb" / "cities_sel1")
        sel2 = str(E2E_WORKSPACE / "test_data.gdb" / "cities_sel2")
        svc.select_by_attribute(e2e_workspace["cities"], sel1, "POP > 15000000")
        svc.select_by_attribute(e2e_workspace["cities"], sel2, "POP <= 15000000")
        result = svc.merge([sel1, sel2], output)
        assert result.success, f"Merge failed: {result.message}"
        print(f"  [OK] Merge: {result.data}")

    def test_06_project(self, e2e_workspace):
        """GEO-08: Project to different coordinate system."""
        from arcgis_agent.services.geoprocessing import GeoprocessingService
        svc = GeoprocessingService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_projected")
        # WGS84 -> Web Mercator
        result = svc.project(e2e_workspace["cities"], output, "3857")
        assert result.success, f"Project failed: {result.message}"
        print(f"  [OK] Project: {result.data}")

    def test_07_summary_statistics(self, e2e_workspace):
        """GEO-10: Summary statistics."""
        from arcgis_agent.services.analysis_service import AnalysisService
        svc = AnalysisService()
        output = str(E2E_WORKSPACE / "test_data.gdb" / "cities_stats")
        result = svc.summary_statistics(
            e2e_workspace["cities"],
            field_spec="POP:SUM,POP:MEAN,POP:MIN,POP:MAX",
            output_table=output,
        )
        assert result.success, f"Summary stats failed: {result.message}"
        print(f"  [OK] Summary stats: {result.data}")


class TestE2EDataOperations:
    """Data discovery and management E2E."""

    def test_01_list_datasets(self, e2e_workspace):
        """DISC-01: List datasets in workspace."""
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        svc = DataDiscoveryService()
        result = svc.list_datasets(workspace=e2e_workspace["gdb"])
        assert result.success, f"List failed: {result.message}"
        assert len(result.data["datasets"]) > 0, "No datasets found"
        print(f"  [OK] List: {result.data['datasets']}")

    def test_02_describe(self, e2e_workspace):
        """DISC-02: Describe a dataset."""
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        svc = DataDiscoveryService()
        result = svc.describe(e2e_workspace["cities"])
        assert result.success, f"Describe failed: {result.message}"
        print(f"  [OK] Describe: {result.data}")

    def test_03_fields(self, e2e_workspace):
        """DISC-03: List fields of a dataset."""
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        svc = DataDiscoveryService()
        result = svc.get_fields(e2e_workspace["cities"])
        assert result.success, f"Fields failed: {result.message}"
        print(f"  [OK] Fields: {result.data}")

    def test_04_extent(self, e2e_workspace):
        """DISC-04: Get extent of a dataset."""
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        svc = DataDiscoveryService()
        result = svc.get_extent(e2e_workspace["cities"])
        assert result.success, f"Extent failed: {result.message}"
        print(f"  [OK] Extent: {result.data}")

    def test_05_count(self, e2e_workspace):
        """DISC-05: Count features."""
        from arcgis_agent.services.data_discovery import DataDiscoveryService
        svc = DataDiscoveryService()
        result = svc.get_count(e2e_workspace["cities"])
        assert result.success, f"Count failed: {result.message}"
        assert result.data["count"] == 8, f"Expected 8, got {result.data['count']}"
        print(f"  [OK] Count: {result.data['count']}")

    def test_06_copy(self, e2e_workspace):
        """MGMT-01: Copy dataset."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        dst = str(E2E_WORKSPACE / "test_data.gdb" / "cities_copy")
        result = svc.copy(e2e_workspace["cities"], dst)
        assert result.success, f"Copy failed: {result.message}"
        print(f"  [OK] Copy: {result.data}")

    def test_07_rename(self, e2e_workspace):
        """MGMT-03: Rename dataset."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        src = str(E2E_WORKSPACE / "test_data.gdb" / "cities_copy")
        result = svc.rename(src, "cities_renamed")
        assert result.success, f"Rename failed: {result.message}"
        print(f"  [OK] Rename: {result.data}")

    def test_08_delete(self, e2e_workspace):
        """MGMT-02: Delete dataset."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        target = str(E2E_WORKSPACE / "test_data.gdb" / "cities_renamed")
        result = svc.delete(target)
        assert result.success, f"Delete failed: {result.message}"
        print(f"  [OK] Delete: {result.data}")

    def test_09_convert(self, e2e_workspace):
        """MGMT-04: Convert format (GDB -> shapefile)."""
        from arcgis_agent.services.data_management import DataManagementService
        svc = DataManagementService()
        src = e2e_workspace["cities"]
        dst = str(E2E_WORKSPACE / "cities_export.shp")
        result = svc.convert(src, dst, "shp")
        assert result.success, f"Convert failed: {result.message}"
        assert Path(dst).exists(), "Converted file not created"
        print(f"  [OK] Convert: {result.data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
