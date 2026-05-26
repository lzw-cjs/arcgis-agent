"""Layout operations service: create, add elements, export."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result

# D-26: Page size dimensions (width, height, units)
PAGE_SIZES = {
    "A4":       (210, 297, "MILLIMETER"),
    "A3":       (297, 420, "MILLIMETER"),
    "Letter":   (8.5, 11, "INCH"),
    "Tabloid":  (11, 17, "INCH"),
}

ALLOWED_PAGE_SIZES = set(PAGE_SIZES.keys())
ALLOWED_ORIENTATIONS = {"portrait", "landscape"}
ALLOWED_ELEMENT_TYPES = {"text", "legend", "scale-bar", "north-arrow", "map-frame", "image"}
ALLOWED_DPI = {96, 150, 300, 600}
ALLOWED_FORMATS = {"PNG", "PDF"}
ALLOWED_SCALE_BAR_STYLES = {"Alternating", "Bar", "DoubleAlternating"}
ALLOWED_NORTH_ARROW_STYLES = {"Default", "Arrow"}
ALLOWED_EXTENT_MODES = {"full_extent", "current_view"}
ALLOWED_POSITIONS = {
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
}


class LayoutService(BaseService):
    """Layout production operations (MAP-09 through MAP-11).

    Uses self._layout (ILayoutDocument) for layout operations.
    """

    def __init__(self, layout_doc=None, data=None):
        super().__init__(layout_doc=layout_doc, data=data)

    def create_layout(self, project_path: str, layout_name: str,
                      page_size: str = "A4", orientation: str = "portrait") -> Result:
        if not layout_name:
            return Result.error(code="INVALID_INPUT",
                                message="Layout name is required.")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")
        if page_size not in ALLOWED_PAGE_SIZES:
            return Result.error(code="INVALID_INPUT",
                                message=f"Page size must be one of {sorted(ALLOWED_PAGE_SIZES)}, got: {page_size}")
        if orientation not in ALLOWED_ORIENTATIONS:
            return Result.error(code="INVALID_INPUT",
                                message=f"Orientation must be portrait or landscape, got: {orientation}")
        w, h, units = PAGE_SIZES[page_size]
        if orientation == "landscape":
            w, h = h, w
        t0 = time.perf_counter()
        try:
            result_path = self._layout.create_layout(p, layout_name, w, h, units)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"project_path": str(result_path), "layout_name": layout_name,
                      "page_size": page_size, "orientation": orientation,
                      "width": w, "height": h, "units": units,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Layout '{layout_name}' created ({page_size} {orientation})."
            )
        except Exception as e:
            return Result.from_exception(e)

    def add_element(self, project_path: str, layout_name: str,
                    element_type: str,
                    position: str | None = None,
                    params: str | None = None) -> Result:
        if not layout_name:
            return Result.error(code="INVALID_INPUT",
                                message="Layout name is required.")
        if element_type not in ALLOWED_ELEMENT_TYPES:
            return Result.error(code="INVALID_INPUT",
                                message=f"Element type must be one of {sorted(ALLOWED_ELEMENT_TYPES)}, got: {element_type}")
        if position and position not in ALLOWED_POSITIONS:
            return Result.error(code="INVALID_INPUT",
                                message=f"Position must be one of {sorted(ALLOWED_POSITIONS)}, got: {position}")
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Project not found: {project_path}")

        # Parse --params key=value string into dict (D-27)
        config: dict = {}
        if params:
            for pair in params.split(","):
                pair = pair.strip()
                if "=" in pair:
                    key, _, val = pair.partition("=")
                    key, val = key.strip(), val.strip()
                    # Type coercion for numeric values
                    try:
                        if "." in val:
                            config[key] = float(val)
                        else:
                            config[key] = int(val)
                    except ValueError:
                        # Boolean strings
                        if val.lower() == "true":
                            config[key] = True
                        elif val.lower() == "false":
                            config[key] = False
                        else:
                            config[key] = val

        if position:
            config["position"] = position

        # Element-type-specific validation
        if element_type == "image":
            source = config.get("source", "")
            if not source:
                return Result.error(code="INVALID_INPUT",
                                    message="image element requires source=<path> in --params.")
            img = Path(source)
            if not img.exists():
                return Result.error(code="FILE_NOT_FOUND",
                                    message=f"Image not found: {source}")
            suffix = img.suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
                return Result.error(code="INVALID_FORMAT",
                                    message=f"Image format not supported: {suffix}. Use PNG, JPG, BMP, or GIF.")
            config["source"] = str(img)

        if element_type == "scale-bar":
            style = config.get("style", "Alternating")
            if style not in ALLOWED_SCALE_BAR_STYLES:
                return Result.error(code="INVALID_INPUT",
                                    message=f"Scale bar style must be one of {sorted(ALLOWED_SCALE_BAR_STYLES)}")

        if element_type == "north-arrow":
            style = config.get("style", "Default")
            if style not in ALLOWED_NORTH_ARROW_STYLES:
                return Result.error(code="INVALID_INPUT",
                                    message=f"North arrow style must be one of {sorted(ALLOWED_NORTH_ARROW_STYLES)}")

        if element_type == "map-frame":
            extent = config.get("extent", "full_extent")
            if extent not in ALLOWED_EXTENT_MODES:
                return Result.error(code="INVALID_INPUT",
                                    message=f"Extent must be one of {sorted(ALLOWED_EXTENT_MODES)}")

        t0 = time.perf_counter()
        try:
            self._layout.add_element(p, layout_name, element_type, config)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"layout_name": layout_name, "element_type": element_type,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Added '{element_type}' element to layout '{layout_name}'."
            )
        except Exception as e:
            return Result.from_exception(e)

    def export_layout(self, project_path: str, layout_name: str,
                      output_path: str, format: str = "PDF",
                      dpi: int = 300, transparent: bool = False) -> Result:
        if not layout_name:
            return Result.error(code="INVALID_INPUT",
                                message="Layout name is required.")
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
            kwargs = {}
            if transparent:
                kwargs["transparent"] = True
            result_path = self._layout.export_layout(p, layout_name, out, fmt, dpi, **kwargs)
            elapsed = time.perf_counter() - t0
            return Result.ok(
                data={"output": str(result_path), "format": fmt, "dpi": dpi,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Layout '{layout_name}' exported to '{result_path}'."
            )
        except Exception as e:
            return Result.from_exception(e)
