"""Adapter interfaces (ABC) for arcpy isolation."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class IGeoProcessor(ABC):
    """Interface for geoprocessing operations (buffer, clip, intersect, etc.)."""

    @abstractmethod
    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        """Create buffer around features."""
        ...

    @abstractmethod
    def clip(self, input_fc: str, clip_fc: str,
             output_fc: str) -> Path:
        """Clip features to boundary."""
        ...

    @abstractmethod
    def intersect(self, inputs: list[str], output_fc: str) -> Path:
        """Intersect multiple feature classes."""
        ...


class IMapDocument(ABC):
    """Interface for ArcGIS Pro project/map document operations."""

    @abstractmethod
    def create_map(self, project_path: Path, map_name: str) -> Path:
        """Create a new map in an ArcGIS Pro project."""
        ...

    @abstractmethod
    def add_layer(self, project_path: Path, map_name: str,
                  layer_path: Path) -> None:
        """Add a layer to a map."""
        ...

    @abstractmethod
    def export_map(self, project_path: Path, map_name: str,
                   output_path: Path, format: str, dpi: int) -> Path:
        """Export a map to image/PDF."""
        ...


class IDataAccessor(ABC):
    """Interface for data access and metadata operations."""

    @abstractmethod
    def list_feature_classes(self, workspace: Path) -> list[str]:
        """List all feature classes in a workspace."""
        ...

    @abstractmethod
    def describe(self, dataset_path: Path) -> dict[str, Any]:
        """Describe a dataset (type, fields, spatial reference, extent)."""
        ...

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path,
                output_format: str) -> Path:
        """Convert data between formats (shp/gdb/csv/geojson)."""
        ...
