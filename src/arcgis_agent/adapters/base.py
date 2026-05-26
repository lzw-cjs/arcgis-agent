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

    @abstractmethod
    def remove_layer(self, project_path: Path, map_name: str,
                     layer_name: str, layer_index: int | None = None) -> None:
        """Remove a layer from a map by name (preferred) or index (fallback)."""
        ...

    @abstractmethod
    def list_layers(self, project_path: Path, map_name: str) -> list[dict]:
        """List layers in a map. Each dict: {name, datasource, feature_count}."""
        ...

    @abstractmethod
    def set_extent(self, project_path: Path, map_name: str,
                   zoom_to_layer: str) -> None:
        """Set map extent by zooming to a specified layer."""
        ...

    @abstractmethod
    def symbolize_layer(self, project_path: Path, map_name: str,
                        layer_name: str, symbology_config: dict) -> None:
        """Apply symbology to a layer (Simple, UniqueValues, or GraduatedColors)."""
        ...

    @abstractmethod
    def set_label(self, project_path: Path, map_name: str,
                  layer_name: str, label_config: dict) -> None:
        """Set labeling on a layer with field expression and style."""
        ...


class ILayoutDocument(ABC):
    """Interface for ArcGIS Pro layout operations (MAP-09 through MAP-11)."""

    @abstractmethod
    def create_layout(self, project_path: Path, layout_name: str,
                      page_width: float, page_height: float,
                      page_units: str) -> Path:
        """Create a new layout with specified page dimensions (MAP-09)."""
        ...

    @abstractmethod
    def add_element(self, project_path: Path, layout_name: str,
                    element_type: str, element_config: dict) -> None:
        """Add an element to a layout (text, legend, scale-bar, north-arrow, map-frame, image)."""
        ...

    @abstractmethod
    def export_layout(self, project_path: Path, layout_name: str,
                      output_path: Path, format: str, dpi: int,
                      **kwargs) -> Path:
        """Export a layout to PNG or PDF (MAP-11)."""
        ...


class IDataAccessor(ABC):
    """Interface for data access and metadata operations."""

    @abstractmethod
    def exists(self, dataset_path: str) -> bool:
        """Check if a dataset exists (using arcpy catalog, not filesystem)."""
        ...

    @abstractmethod
    def list_feature_classes(self, workspace: Path) -> list[str]:
        """List all feature classes in a workspace."""
        ...

    @abstractmethod
    def list_datasets(self, workspace, dataset_type=None, name_pattern=None) -> list[str]:
        """List all datasets in a workspace with optional type/name filters."""
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

    @abstractmethod
    def get_count(self, dataset_path) -> int:
        """Get record/feature count for a dataset."""
        ...

    @abstractmethod
    def get_fields(self, dataset_path) -> list[dict]:
        """Get field definitions for a dataset."""
        ...

    @abstractmethod
    def get_extent(self, dataset_path) -> dict:
        """Get spatial extent of a dataset."""
        ...

    @abstractmethod
    def copy(self, src, dst) -> Path:
        """Copy a dataset to a new location."""
        ...

    @abstractmethod
    def delete(self, dataset_path) -> None:
        """Delete a dataset."""
        ...

    @abstractmethod
    def rename(self, dataset_path, new_name) -> Path:
        """Rename a dataset."""
        ...
