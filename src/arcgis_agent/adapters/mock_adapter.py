"""Mock adapter implementations for unit testing (no arcpy needed)."""
from pathlib import Path
from typing import Any

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor, ILayoutDocument


class MockGeoProcessor(IGeoProcessor):
    """Mock geoprocessing -- records calls for test assertions."""

    def __init__(self):
        self.calls: list[tuple] = []

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str,
               dissolve_field: str | None = None) -> Path:
        self.calls.append(("buffer", input_fc, output_fc, distance, unit,
                           dissolve_field))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def clip(self, input_fc: str, clip_fc: str,
             output_fc: str) -> Path:
        self.calls.append(("clip", input_fc, clip_fc, output_fc))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def intersect(self, inputs: list[str], output_fc: str) -> Path:
        self.calls.append(("intersect", inputs, output_fc))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def select_by_attribute(self, input_fc: str, output_fc: str,
                            where_clause: str) -> Path:
        self.calls.append(("select_by_attribute", input_fc, output_fc,
                           where_clause))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def union(self, inputs: list[str], output_fc: str) -> Path:
        self.calls.append(("union", inputs, output_fc))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def dissolve(self, input_fc: str, output_fc: str,
                 dissolve_field: str) -> Path:
        self.calls.append(("dissolve", input_fc, output_fc, dissolve_field))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def spatial_join(self, target_fc: str, join_fc: str,
                     output_fc: str) -> Path:
        self.calls.append(("spatial_join", target_fc, join_fc, output_fc))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def merge(self, inputs: list[str], output_fc: str) -> Path:
        self.calls.append(("merge", inputs, output_fc))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def project(self, input_fc: str, output_fc: str,
                spatial_reference: str) -> Path:
        self.calls.append(("project", input_fc, output_fc, spatial_reference))
        p = Path(output_fc)
        if p.parent.exists():
            p.touch()
        return p

    def summary_statistics(self, input_fc: str, output_table: str,
                           statistics_fields: list[list[str]],
                           case_field: str | None = None) -> Path:
        self.calls.append(("summary_statistics", input_fc, output_table,
                           statistics_fields, case_field))
        p = Path(output_table)
        if p.parent.exists():
            p.touch()
        return p


class MockMapDocument(IMapDocument):
    """Mock map document -- records calls for test assertions."""

    def __init__(self):
        self.calls: list[tuple] = []

    def create_map(self, project_path: Path, map_name: str) -> Path:
        self.calls.append(("create_map", str(project_path), map_name))
        return project_path

    def add_layer(self, project_path: Path, map_name: str,
                  layer_path: Path) -> None:
        self.calls.append(("add_layer", str(project_path), map_name,
                           str(layer_path)))

    def export_map(self, project_path: Path, map_name: str,
                   output_path: Path, format: str, dpi: int,
                   transparent: bool = False) -> Path:
        self.calls.append(("export_map", str(project_path), map_name,
                           str(output_path), format, dpi, transparent))
        p = Path(output_path)
        if p.parent.exists():
            p.touch()
        return p

    def get_project_info(self, project_path: Path) -> dict:
        self.calls.append(("get_project_info", str(project_path)))
        return {
            "project_path": str(project_path),
            "default_gdb": str(project_path.parent / "default.gdb"),
            "name": project_path.stem,
            "maps": ["Map"],
        }

    def remove_layer(self, project_path: Path, map_name: str,
                     layer_name: str, layer_index: int | None = None) -> None:
        self.calls.append(("remove_layer", str(project_path), map_name, layer_name, layer_index))

    def list_layers(self, project_path: Path, map_name: str) -> list[dict]:
        self.calls.append(("list_layers", str(project_path), map_name))
        return [
            {"name": "mock_layer_1", "datasource": "/mock/path/data.shp", "feature_count": 42},
            {"name": "mock_layer_2", "datasource": "/mock/path/roads.gdb", "feature_count": 15},
        ]

    def set_extent(self, project_path: Path, map_name: str,
                   zoom_to_layer: str) -> None:
        self.calls.append(("set_extent", str(project_path), map_name, zoom_to_layer))

    def symbolize_layer(self, project_path: Path, map_name: str,
                        layer_name: str, symbology_config: dict) -> None:
        self.calls.append(("symbolize_layer", str(project_path), map_name, layer_name, symbology_config))

    def set_label(self, project_path: Path, map_name: str,
                  layer_name: str, label_config: dict) -> None:
        self.calls.append(("set_label", str(project_path), map_name, layer_name, label_config))


class MockLayoutDocument(ILayoutDocument):
    """Mock layout document -- records calls for test assertions."""

    def __init__(self):
        self.calls: list[tuple] = []

    def create_layout(self, project_path: Path, layout_name: str,
                      page_width: float, page_height: float,
                      page_units: str) -> Path:
        self.calls.append(("create_layout", str(project_path), layout_name,
                           page_width, page_height, page_units))
        return project_path

    def add_element(self, project_path: Path, layout_name: str,
                    element_type: str, element_config: dict) -> None:
        self.calls.append(("add_element", str(project_path), layout_name,
                           element_type, element_config))

    def export_layout(self, project_path: Path, layout_name: str,
                      output_path: Path, format: str, dpi: int,
                      **kwargs) -> Path:
        self.calls.append(("export_layout", str(project_path), layout_name,
                           str(output_path), format, dpi, kwargs))
        p = Path(output_path)
        if p.parent.exists():
            p.touch()
        return p


class MockDataAccessor(IDataAccessor):
    """Mock data accessor -- records calls and returns stub data."""

    def __init__(self):
        self.calls: list[tuple] = []

    def list_datasets(self, workspace, dataset_type=None, name_pattern=None):
        self.calls.append(("list_datasets", str(workspace), dataset_type, name_pattern))
        return ["mock_feature_class", "mock_table"]

    def list_feature_classes(self, workspace: Path) -> list[str]:
        self.calls.append(("list_feature_classes", str(workspace)))
        return ["mock_feature_class"]

    def describe(self, dataset_path: Path) -> dict[str, Any]:
        self.calls.append(("describe", str(dataset_path)))
        return {
            "dataType": "FeatureClass",
            "name": dataset_path.stem,
            "catalogPath": str(dataset_path),
        }

    def convert(self, input_path: Path, output_path: Path,
                output_format: str) -> Path:
        self.calls.append(("convert", str(input_path), str(output_path),
                           output_format))
        p = Path(output_path)
        if p.parent.exists():
            p.touch()
        return p

    def get_count(self, dataset_path) -> int:
        self.calls.append(("get_count", str(dataset_path)))
        return 42

    def get_fields(self, dataset_path) -> list[dict]:
        self.calls.append(("get_fields", str(dataset_path)))
        return [
            {"name": "OBJECTID", "type": "Integer", "length": 4},
            {"name": "Shape", "type": "Geometry", "length": 0},
        ]

    def get_extent(self, dataset_path) -> dict:
        self.calls.append(("get_extent", str(dataset_path)))
        return {"xmin": 0.0, "ymin": 0.0, "xmax": 100.0, "ymax": 100.0}

    def copy(self, src, dst) -> Path:
        self.calls.append(("copy", str(src), str(dst)))
        p = Path(dst)
        if p.parent.exists():
            p.touch()
        return p

    def delete(self, dataset_path) -> None:
        self.calls.append(("delete", str(dataset_path)))

    def rename(self, dataset_path, new_name) -> Path:
        self.calls.append(("rename", str(dataset_path), new_name))
        p = Path(dataset_path).parent / new_name
        p.touch()
        return p
