"""Map operations service: create, layer management, symbology, labeling, extent, export."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


def _parse_color(color_str: str) -> list[int]:
    """Parse 'R,G,B' string into [R,G,B] list. Raises ValueError on bad input."""
    parts = color_str.split(",")
    if len(parts) != 3:
        raise ValueError(f"Expected R,G,B (e.g. 255,0,0), got: {color_str}")
    values = [int(p.strip()) for p in parts]
    for v in values:
        if not (0 <= v <= 255):
            raise ValueError(f"Color values must be 0-255, got: {v}")
    return values


ALLOWED_DPI = {96, 150, 300, 600}
ALLOWED_FORMATS = {"PNG", "PDF"}
ALLOWED_SYMBOLOGY_TYPES = {"simple", "unique_values", "graduated_colors"}
ALLOWED_CLASSIFICATION_METHODS = {"NaturalBreaks", "Quantile", "EqualInterval"}


class MapService(BaseService):
    """Map production operations (MAP-01 through MAP-08).

    Uses self._map (IMapDocument) for map operations.
    """

    def __init__(self, map_doc=None, data=None):
        super().__init__(map_doc=map_doc, data=data)

    def create_map(self, project_path: str | None, map_name: str) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        if project_path is None:
            from arcgis_agent.config import WorkspaceConfig
            cfg = WorkspaceConfig()
            ws = cfg.get_workspace()
            if ws is None:
                return Result.error(code="NO_WORKSPACE",
                                    message="No workspace set. Use 'workspace set' first.")
            aprx_files = list(Path(ws).glob("*.aprx"))
            if not aprx_files:
                return Result.error(code="NO_PROJECT",
                                    message=f"No .aprx found in workspace: {ws}")
            project_path = str(aprx_files[0])
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        t0 = time.perf_counter()
        try:
            result_path = self._map.create_map(p, map_name)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"project_path": str(result_path), "map_name": map_name,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Map '{map_name}' created in '{project_path}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def add_layer(self, project_path: str, map_name: str, data_path: str) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        data_p = Path(data_path)
        if not data_p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Data not found: {data_path}")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        t0 = time.perf_counter()
        try:
            self._map.add_layer(p, map_name, data_p)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"map_name": map_name, "layer_path": str(data_p),
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Layer '{data_p.name}' added to map '{map_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def remove_layer(self, project_path: str, map_name: str,
                     layer_name: str | None = None,
                     layer_index: int | None = None) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        if layer_name is None and layer_index is None:
            return Result.error(code="INVALID_INPUT",
                                message="Either --layer or --layer-index is required.")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        t0 = time.perf_counter()
        try:
            self._map.remove_layer(p, map_name, layer_name or "", layer_index)
            elapsed = time.perf_counter() - t0
            identifier = layer_name or f"index {layer_index}"
            return Result.ok(
                data={"map_name": map_name, "removed": identifier,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Layer '{identifier}' removed from map '{map_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def list_layers(self, project_path: str, map_name: str) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        t0 = time.perf_counter()
        try:
            layers = self._map.list_layers(p, map_name)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"map_name": map_name, "layers": layers,
                      "count": len(layers), "elapsed_seconds": round(elapsed, 2)},
                message=f"Found {len(layers)} layer(s) in map '{map_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def set_extent(self, project_path: str, map_name: str,
                   zoom_to_layer: str) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        if not zoom_to_layer:
            return Result.error(code="INVALID_INPUT",
                                message="--zoom-to LAYER_NAME is required.")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        t0 = time.perf_counter()
        try:
            self._map.set_extent(p, map_name, zoom_to_layer)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"map_name": map_name, "zoom_to_layer": zoom_to_layer,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Extent set to layer '{zoom_to_layer}' in map '{map_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def export_map(self, project_path: str, map_name: str,
                   output_path: str, format: str = "PNG",
                   dpi: int = 300, transparent: bool = False) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        fmt = format.upper()
        if fmt not in ALLOWED_FORMATS:
            return Result.error(code="INVALID_FORMAT",
                                message=f"Format must be PNG or PDF, got: {format}")
        if dpi not in ALLOWED_DPI:
            return Result.error(code="INVALID_INPUT",
                                message=f"DPI must be one of {sorted(ALLOWED_DPI)}, got: {dpi}")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        out = Path(output_path)
        if out.suffix.lower() != f".{format.lower()}":
            out = out.with_suffix(f".{format.lower()}")
        t0 = time.perf_counter()
        try:
            result_path = self._map.export_map(p, map_name, out, fmt, dpi, transparent)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"output": str(result_path), "format": fmt, "dpi": dpi,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Map '{map_name}' exported to '{result_path}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def symbolize_layer(self, project_path: str, map_name: str,
                        layer_name: str, symbology_type: str,
                        field: str | None = None,
                        color: str | None = None,
                        outline_color: str | None = None,
                        size: int = 8,
                        opacity: int = 100,
                        color_ramp: str | None = None,
                        values: str | None = None,
                        classification_method: str = "NaturalBreaks",
                        break_count: int = 5) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        if not layer_name:
            return Result.error(code="INVALID_INPUT", message="Layer name is required.")
        if symbology_type not in ALLOWED_SYMBOLOGY_TYPES:
            return Result.error(code="INVALID_INPUT",
                                message=f"Symbol type must be one of {sorted(ALLOWED_SYMBOLOGY_TYPES)}")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")

        config: dict = {"type": symbology_type}

        try:
            if color:
                config["color"] = _parse_color(color)
            if outline_color:
                config["outline_color"] = _parse_color(outline_color)
        except ValueError as e:
            return Result.error(code="INVALID_COLOR", message=str(e))

        if opacity < 0 or opacity > 100:
            return Result.error(code="INVALID_INPUT",
                                message=f"Opacity must be 0-100, got: {opacity}")
        config["size"] = size
        config["opacity"] = opacity

        if field:
            config["field"] = field

        if color_ramp:
            config["color_ramp"] = color_ramp

        if values:
            import json
            try:
                config["values"] = json.loads(values)
            except json.JSONDecodeError as e:
                return Result.error(code="INVALID_FORMAT",
                                    message=f"Invalid --values JSON: {e}")

        if classification_method not in ALLOWED_CLASSIFICATION_METHODS:
            return Result.error(code="INVALID_INPUT",
                                message=f"Classification method must be one of {sorted(ALLOWED_CLASSIFICATION_METHODS)}")
        config["classification_method"] = classification_method

        if break_count < 2 or break_count > 7:
            return Result.error(code="INVALID_INPUT",
                                message=f"Break count must be 2-7, got: {break_count}")
        config["break_count"] = break_count

        t0 = time.perf_counter()
        try:
            self._map.symbolize_layer(p, map_name, layer_name, config)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"map_name": map_name, "layer_name": layer_name,
                      "symbology_type": symbology_type,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Applied '{symbology_type}' symbology to layer '{layer_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def set_label(self, project_path: str, map_name: str,
                  layer_name: str, field: str,
                  font_size: int = 10,
                  color: str = "0,0,0",
                  bold: bool = False) -> Result:
        if not map_name:
            return Result.error(code="INVALID_INPUT", message="Map name is required.")
        if not layer_name:
            return Result.error(code="INVALID_INPUT", message="Layer name is required.")
        if not field:
            return Result.error(code="INVALID_INPUT",
                                message="--field is required for labeling.")
        if font_size < 1 or font_size > 200:
            return Result.error(code="INVALID_INPUT",
                                message=f"Font size must be 1-200, got: {font_size}")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        try:
            parsed_color = _parse_color(color)
        except ValueError as e:
            return Result.error(code="INVALID_COLOR", message=str(e))

        config = {"field": field, "font_size": font_size, "color": parsed_color, "bold": bold}
        t0 = time.perf_counter()
        try:
            self._map.set_label(p, map_name, layer_name, config)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"map_name": map_name, "layer_name": layer_name, "field": field,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Label set on layer '{layer_name}' using field '{field}'."
            )
        except Exception as e:
            return Result.from_exception(e)
