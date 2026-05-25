"""Mock adapter implementations for unit testing (no arcpy needed)."""
from pathlib import Path
from typing import Any

from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor


class MockGeoProcessor(IGeoProcessor):
    """Mock geoprocessing -- records calls for test assertions."""

    def __init__(self):
        self.calls: list[tuple] = []

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        self.calls.append(("buffer", input_fc, output_fc, distance, unit))
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
                   output_path: Path, format: str, dpi: int) -> Path:
        self.calls.append(("export_map", str(project_path), map_name,
                           str(output_path), format, dpi))
        p = Path(output_path)
        if p.parent.exists():
            p.touch()
        return p


class MockDataAccessor(IDataAccessor):
    """Mock data accessor -- records calls and returns stub data."""

    def __init__(self):
        self.calls: list[tuple] = []

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
