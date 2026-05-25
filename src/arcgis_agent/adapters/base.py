"""Adapter interfaces (ABC) for arcpy isolation."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class IGeoProcessor(ABC):
    """Interface for geoprocessing operations (buffer, clip, intersect, etc.)."""

    @abstractmethod
    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str,
               dissolve_field: str | None = None) -> Path:
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

    @abstractmethod
    def select_by_attribute(self, input_fc: str, output_fc: str,
                            where_clause: str) -> Path:
        """Select features by attribute query and write to output."""
        ...

    @abstractmethod
    def union(self, inputs: list[str], output_fc: str) -> Path:
        """Union (overlay) multiple polygon feature classes."""
        ...

    @abstractmethod
    def dissolve(self, input_fc: str, output_fc: str,
                 dissolve_field: str) -> Path:
        """Dissolve features by field, merging overlapping polygons."""
        ...

    @abstractmethod
    def spatial_join(self, target_fc: str, join_fc: str,
                     output_fc: str) -> Path:
        """Spatial join: transfer attributes from join features to target."""
        ...

    @abstractmethod
    def merge(self, inputs: list[str], output_fc: str) -> Path:
        """Merge multiple feature classes into one (append, no overlay)."""
        ...

    @abstractmethod
    def project(self, input_fc: str, output_fc: str,
                spatial_reference: str) -> Path:
        """Project features to a different coordinate system."""
        ...

    @abstractmethod
    def summary_statistics(self, input_fc: str, output_table: str,
                           statistics_fields: list[list[str]],
                           case_field: str | None = None) -> Path:
        """Compute summary statistics on a feature class or table."""
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
