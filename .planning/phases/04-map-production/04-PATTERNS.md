# Phase 04: 地图生产 - Pattern Map

**Mapped:** 2026-05-26
**Files classified:** 14 (10 new, 4 modified)
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/arcgis_agent/commands/map.py` | controller (CLI command group) | request-response | `src/arcgis_agent/commands/data.py` | exact |
| `src/arcgis_agent/commands/layout.py` | controller (CLI command group) | request-response | `src/arcgis_agent/commands/geoprocessing.py` | exact |
| `src/arcgis_agent/services/map_service.py` | service | CRUD/transform | `src/arcgis_agent/services/geoprocessing.py` | exact |
| `src/arcgis_agent/services/layout_service.py` | service | CRUD/transform | `src/arcgis_agent/services/analysis_service.py` | exact |
| `tests/unit/test_map_service.py` | test (unit/service) | CRUD | `tests/unit/test_project_service.py` | exact |
| `tests/unit/test_layout_service.py` | test (unit/service) | CRUD | `tests/unit/test_project_service.py` | exact |
| `tests/unit/test_map_commands.py` | test (CLI integration) | request-response | `tests/unit/test_cli.py` | exact |
| `tests/unit/test_layout_commands.py` | test (CLI integration) | request-response | `tests/unit/test_cli.py` | exact |
| `src/arcgis_agent/adapters/base.py` (MODIFY) | model/interface (ABC) | CRUD | (same file, extend existing) | self |
| `src/arcgis_agent/adapters/arcpy_adapter.py` (MODIFY) | adapter (arcpy) | CRUD/file-I/O | (same file, extend existing) | self |
| `src/arcgis_agent/adapters/mock_adapter.py` (MODIFY) | adapter (mock/test) | CRUD | (same file, extend existing) | self |
| `src/arcgis_agent/services/base.py` (MODIFY) | service (base factory) | dependency-injection | (same file, extend existing) | self |
| `tests/conftest.py` (MODIFY) | test (fixtures) | setup | (same file, extend existing) | self |
| `pyproject.toml` (MODIFY) | config | build | (same file, extend existing) | self |

## Pattern Assignments

---

### `src/arcgis_agent/commands/map.py` (controller: CLI command group, request-response)

**Analog:** `src/arcgis_agent/commands/data.py` (lines 1-49)

**Imports pattern** (lines 1-4):
```python
"""Map commands: creation, layer management, symbology, labeling, and export."""
import click

from arcgis_agent.models.result import Result
```

**Register + group pattern** (lines 26-35):
```python
def register(cli_group: click.Group) -> None:
    """Register map commands with CLI."""

    @cli_group.group("map")
    def map_group():
        """Map creation and management commands."""
        pass
```

**_run helper pattern** (lines 10-23, adapted for map commands):
```python
def _make_service():
    """Create MapService, returning svc or raising."""
    from arcgis_agent.services.map_service import MapService
    return MapService()


def _run(fn):
    """Run fn(service) -> Result, catching init errors as JSON."""
    try:
        svc = _make_service()
        result = fn(svc)
    except Exception as e:
        result = Result.from_exception(e)
    click.echo(result.to_json())
```

**Individual command pattern** (lines 37-51, adapted for simple command -- no _run, direct service call):
```python
    @map_group.command("create")
    @click.argument("name")
    @click.option("--project", "-p", default=None,
                  help="Path to .aprx file (overrides workspace auto-detect).")
    @click.pass_context
    def map_create(ctx, name, project):
        """Create a new map (MAP-01)."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.create_map(project, name)
        click.echo(result.to_json())
```

**Command with _run helper pattern** (lines 38-51, for lighter commands):
```python
    @data_group.command("list")
    @click.option("--workspace", "-w", default=None)
    @click.pass_context
    def data_list(ctx, workspace, dataset_type, pattern):
        """List datasets in workspace (DISC-01)."""
        _run(lambda svc: svc.list_datasets(
            workspace=workspace,
            dataset_type=dataset_type,
            name_pattern=pattern,
        ))
```

---

### `src/arcgis_agent/commands/layout.py` (controller: CLI command group, request-response)

**Analog:** `src/arcgis_agent/commands/geoprocessing.py` (lines 1-30, 120-138)

**Same pattern as map.py** but registering a `layout` group at the top-level (not as a subgroup of another command). Import `Result` directly, use `@cli_group.group("layout")` as a top-level group (D-08).

```python
def register(cli_group: click.Group) -> None:
    """Register layout commands with CLI."""

    @cli_group.group("layout")
    def layout_group():
        """Layout creation and export commands."""
        pass

    @layout_group.command("create")
    @click.argument("name")
    @click.option("--project", "-p", default=None)
    @click.pass_context
    def layout_create(ctx, name, project):
        """Create a new layout (MAP-09)."""
        from arcgis_agent.services.layout_service import LayoutService
        svc = LayoutService()
        result = svc.create_layout(project, name)
        click.echo(result.to_json())
```

**Note:** Since `map` and `layout` are peer groups (D-08), both register at `cli_group` level. This differs from `geoprocessing.py` which registers on `data_group` (a subgroup).

---

### `src/arcgis_agent/services/map_service.py` (service: CRUD/transform)

**Analog:** `src/arcgis_agent/services/geoprocessing.py` (full file, lines 1-264)

**Imports and class declaration pattern** (lines 1-19):
```python
"""Map operations service: create, layer management, symbology, labeling, extent, export."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


class MapService(BaseService):
    """Map production operations (MAP-01 through MAP-08).

    Uses self._map (IMapDocument) for map operations.
    """

    def __init__(self, map_doc=None, data=None):
        super().__init__(map_doc=map_doc, data=data)
```

**Input validation + try/catch service method pattern** (lines 34-56):
```python
    def create_map(self, project_path: str | None, map_name: str) -> Result:
        """Create a new map in a project (MAP-01)."""
        if not map_name:
            return Result.error(code="INVALID_INPUT",
                                message="Map name is required.")
        # Resolve project path from workspace config or --project option (D-04)
        if project_path is None:
            # Auto-detect .aprx from workspace
            from arcgis_agent.config import WorkspaceConfig
            cfg = WorkspaceConfig()
            ws = cfg.get_workspace()
            if ws is None:
                return Result.error(code="NO_WORKSPACE",
                                    message="No workspace set. Use 'workspace set' first.")
            import glob as _glob
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
                message=f"Map '{map_name}' created."
            )
        except Exception as e:
            return Result.from_exception(e)
```

**Service method with additional validation helper** (lines 20-32, for multi-input validation):
```python
    def _validate_input(self, input_path: str) -> Path | Result:
        """Validate input path exists. Returns Path if OK, Result.error if not."""
        p = Path(input_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Not found: {input_path}")
        return p
```

---

### `src/arcgis_agent/services/layout_service.py` (service: CRUD/transform)

**Analog:** `src/arcgis_agent/services/analysis_service.py` (lines 1-92, the parse_stat_fields helper + service pattern)

**Same class structure as GeoprocessingService/AnalysisService** but uses `self._layout` (ILayoutDocument) adapter. Page size mapping (D-26) defined as module-level constant.

```python
"""Layout operations service: create, add elements, export."""
from pathlib import Path
import time

from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result


PAGE_SIZES = {
    "A4":       (210, 297, "MILLIMETER"),
    "A3":       (297, 420, "MILLIMETER"),
    "Letter":   (8.5, 11, "INCH"),
    "Tabloid":  (11, 17, "INCH"),
}


class LayoutService(BaseService):
    """Layout production operations (MAP-09 through MAP-11).

    Uses self._layout (ILayoutDocument) for layout operations.
    """

    def __init__(self, layout_doc=None, data=None):
        super().__init__(layout_doc=layout_doc, data=data)
```

---

### `tests/unit/test_map_service.py` (test: unit/service, CRUD)

**Analog:** `tests/unit/test_project_service.py` (full file, lines 1-59)

**Imports and class structure pattern:**
```python
"""Tests for MapService (Phase 4)."""
import pytest
from pathlib import Path

from arcgis_agent.services.map_service import MapService
from arcgis_agent.adapters.mock_adapter import MockMapDocument


class TestMapService:
    """MapService unit tests."""

    def test_create_map_success(self, tmp_path):
        """create_map() returns Result.ok with project info."""
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        # ... test assertions ...

    def test_add_layer_success(self, tmp_path):
        """add_layer() calls adapter and records correctly."""
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        # ... test assertions ...

    def test_remove_layer_by_name(self, tmp_path):
        """remove_layer() removes by layer name."""
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        # ... test assertions ...
```

**Fixture-based test with MockMapDocument calls assertion** (lines 30-36, 50-58):
```python
    def test_create_map_valid(self, tmp_path):
        """Returns Result.ok with map created."""
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        result = svc.create_map(str(f), "MyMap")
        assert result.success
        assert "MyMap" in result.data["map_name"]

    def test_create_map_uses_adapter(self, tmp_path):
        """Verify MockMapDocument.create_map was called."""
        mock_map = MockMapDocument()
        svc = MapService(map_doc=mock_map)
        f = tmp_path / "test.aprx"
        f.touch()
        svc.create_map(str(f), "MyMap")
        assert len(mock_map.calls) == 1
        assert mock_map.calls[0][0] == "create_map"
```

---

### `tests/unit/test_layout_service.py` (test: unit/service, CRUD)

**Analog:** `tests/unit/test_project_service.py` (same as above)

Same class-based test structure as test_map_service.py, but testing LayoutService with MockLayoutDocument.

---

### `tests/unit/test_map_commands.py` (test: CLI integration, request-response)

**Analog:** `tests/unit/test_cli.py` (lines 1-38)

**Imports and fixture pattern:**
```python
"""CLI integration tests for 'map' commands."""
import click
from click.testing import CliRunner

from arcgis_agent.cli import cli


def test_map_create_help(runner):
    """map create --help shows options."""
    result = runner.invoke(cli, ['map', 'create', '--help'])
    assert result.exit_code == 0
    assert '--project' in result.output


def test_map_create_no_name(runner, monkeypatch):
    """map create without name argument shows error."""
    # Use monkeypatch to inject mock service
    result = runner.invoke(cli, ['map', 'create'])
    assert result.exit_code != 0


def test_map_list_layers_empty(monkeypatch):
    """map list-layers returns JSON with empty list."""
    from arcgis_agent.services.map_service import MapService
    from arcgis_agent.adapters.mock_adapter import MockMapDocument

    mock = MockMapDocument()
    monkeypatch.setattr(MapService, '__init__',
                        lambda self, **kw: None)
    # ...
```

---

### `tests/unit/test_layout_commands.py` (test: CLI integration, request-response)

**Analog:** `tests/unit/test_cli.py` (same as above)

Same pattern as test_map_commands.py but for `layout` commands.

---

### `src/arcgis_agent/adapters/base.py` (MODIFY: model/interface, ABC, CRUD)

**Analog:** Same file, lines 70-88 (existing IMapDocument pattern to extend)

**Extend IMapDocument** -- add new abstract methods after `export_map` (line 88):

```python
    # --- New methods for Phase 04 ---

    @abstractmethod
    def remove_layer(self, project_path: Path, map_name: str,
                     layer_name: str) -> None:
        """Remove a layer from a map (MAP-03)."""
        ...

    @abstractmethod
    def list_layers(self, project_path: Path, map_name: str) -> list[dict]:
        """List layers in a map with name, datasource, feature count (MAP-04)."""
        ...

    @abstractmethod
    def set_extent(self, project_path: Path, map_name: str,
                   zoom_to_layer: str) -> None:
        """Set map extent by zooming to a layer (MAP-05)."""
        ...

    @abstractmethod
    def symbolize_layer(self, project_path: Path, map_name: str,
                        layer_name: str, symbology_config: dict) -> None:
        """Apply symbology to a layer (MAP-07)."""
        ...

    @abstractmethod
    def set_label(self, project_path: Path, map_name: str,
                  layer_name: str, label_config: dict) -> None:
        """Set labeling on a layer (MAP-08)."""
        ...
```

**Add new ILayoutDocument ABC** after IMapDocument:

```python
class ILayoutDocument(ABC):
    """Interface for ArcGIS Pro layout operations (MAP-09 through MAP-11)."""

    @abstractmethod
    def create_layout(self, project_path: Path, layout_name: str,
                      page_width: float, page_height: float,
                      page_units: str) -> Path:
        """Create a new layout in a project (MAP-09)."""
        ...

    @abstractmethod
    def add_element(self, project_path: Path, layout_name: str,
                    element_type: str, element_config: dict) -> None:
        """Add an element to a layout (MAP-10)."""
        ...

    @abstractmethod
    def export_layout(self, project_path: Path, layout_name: str,
                      output_path: Path, format: str, dpi: int,
                      **kwargs) -> Path:
        """Export a layout to PNG/PDF (MAP-11)."""
        ...
```

---

### `src/arcgis_agent/adapters/arcpy_adapter.py` (MODIFY: adapter, arcpy, CRUD/file-I/O)

**Analog:** Same file, lines 217-267 (existing ArcPyMapDocument) for the method structure, and lines 8-58 (ArcPyGeoProcessor.__init__) for `__init__` construction pattern

**Extend ArcPyMapDocument** -- add new methods following the existing pattern:

**Core pattern for each new method** (from lines 224-267):
```python
def remove_layer(self, project_path: Path, map_name: str,
                 layer_name: str) -> None:
    try:
        aprx = self._arcpy.mp.ArcGISProject(str(project_path))
        m = aprx.listMaps(map_name)[0]
        lyr = m.listLayers(layer_name)[0]
        m.removeLayer(lyr)
        aprx.save()
    except self._arcpy.ExecuteError as e:
        from arcgis_agent.exceptions import ArcGISError
        raise ArcGISError(
            code="MAP_REMOVE_LAYER_FAILED",
            message=str(e),
            arcpy_messages=self._arcpy.GetMessages()
        )
    finally:
        del aprx  # Release file lock (D-06)
```

**Add new ArcPyLayoutDocument class** after ArcPyMapDocument, following the same init and method pattern:

```python
class ArcPyLayoutDocument(ILayoutDocument):
    """Layout document operations using real arcpy."""

    def __init__(self):
        import arcpy  # LAZY: inside constructor, not at module level
        self._arcpy = arcpy

    def create_layout(self, project_path: Path, layout_name: str,
                      page_width: float, page_height: float,
                      page_units: str) -> Path:
        try:
            aprx = self._arcpy.mp.ArcGISProject(str(project_path))
            aprx.createLayout(page_width, page_height, page_units, layout_name)
            aprx.save()
            return project_path
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="LAYOUT_CREATE_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )
        finally:
            del aprx
```

---

### `src/arcgis_agent/adapters/mock_adapter.py` (MODIFY: adapter, mock/test, CRUD)

**Analog:** Same file, lines 97-128 (existing MockMapDocument) for the pattern to extend, and lines 8-94 (MockGeoProcessor) for the calls list pattern

**Extend MockMapDocument** -- add method stubs after `get_project_info` (line 128):

```python
    def remove_layer(self, project_path: Path, map_name: str,
                     layer_name: str) -> None:
        self.calls.append(("remove_layer", str(project_path), map_name, layer_name))

    def list_layers(self, project_path: Path, map_name: str) -> list[dict]:
        self.calls.append(("list_layers", str(project_path), map_name))
        return [
            {"name": "mock_layer", "datasource": "/fake/path", "feature_count": 42}
        ]

    def set_extent(self, project_path: Path, map_name: str,
                   zoom_to_layer: str) -> None:
        self.calls.append(("set_extent", str(project_path), map_name, zoom_to_layer))

    def symbolize_layer(self, project_path: Path, map_name: str,
                        layer_name: str, symbology_config: dict) -> None:
        self.calls.append(("symbolize_layer", str(project_path), map_name,
                           layer_name, symbology_config))

    def set_label(self, project_path: Path, map_name: str,
                  layer_name: str, label_config: dict) -> None:
        self.calls.append(("set_label", str(project_path), map_name,
                           layer_name, label_config))
```

**Add new MockLayoutDocument class** after MockMapDocument:

```python
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
```

---

### `src/arcgis_agent/services/base.py` (MODIFY: service, base factory, dependency-injection)

**Analog:** Same file, lines 1-47

**Extend** -- add `layout_doc` parameter and `_make_layout` factory:

```python
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor, ILayoutDocument

class BaseService:
    def __init__(
        self,
        gp: IGeoProcessor | None = None,
        map_doc: IMapDocument | None = None,
        data: IDataAccessor | None = None,
        layout_doc: ILayoutDocument | None = None,  # NEW
    ):
        self._gp = gp if gp is not None else self._make_gp()
        self._map = map_doc if map_doc is not None else self._make_map()
        self._data = data if data is not None else self._make_data()
        self._layout = layout_doc if layout_doc is not None else self._make_layout()  # NEW

    @staticmethod
    def _make_layout() -> ILayoutDocument:  # NEW
        from arcgis_agent.adapters.arcpy_adapter import ArcPyLayoutDocument
        return ArcPyLayoutDocument()
```

---

### `tests/conftest.py` (MODIFY: test, fixtures, setup)

**Analog:** Same file, lines 1-51

**Extend** -- add new fixtures after `mock_adapters` (line 36):

```python
@pytest.fixture
def mock_map_doc():
    """Mock MapDocument adapter with extended Phase-04 methods."""
    from arcgis_agent.adapters.mock_adapter import MockMapDocument
    return MockMapDocument()


@pytest.fixture
def mock_layout():
    """Mock LayoutDocument adapter."""
    from arcgis_agent.adapters.mock_adapter import MockLayoutDocument
    return MockLayoutDocument()
```

---

### `pyproject.toml` (MODIFY: config, build)

**Analog:** Same file, lines 24-30

**Extend** `[project.entry-points."arcgis_agent.commands"]` -- uncomment `map` and add `layout`:

```toml
[project.entry-points."arcgis_agent.commands"]
workspace = "arcgis_agent.commands.workspace:register"
project = "arcgis_agent.commands.project:register"
data = "arcgis_agent.commands.data:register"
geoprocessing = "arcgis_agent.commands.geoprocessing:register"
analysis = "arcgis_agent.commands.analysis:register"
map = "arcgis_agent.commands.map:register"
layout = "arcgis_agent.commands.layout:register"
```

---

## Shared Patterns

### Lazy ArcPy Import Pattern
**Source:** `src/arcgis_agent/adapters/arcpy_adapter.py` lines 11-12, 220-222, 272-273
**Apply to:** ArcPyMapDocument (new methods), ArcPyLayoutDocument
```python
def __init__(self):
    import arcpy  # LAZY: inside constructor, not at module level
    self._arcpy = arcpy
```

### ArcPy Error Handling Pattern
**Source:** `src/arcgis_agent/adapters/arcpy_adapter.py` lines 72-78
**Apply to:** All new ArcPy adapter methods
```python
except self._arcpy.ExecuteError as e:
    from arcgis_agent.exceptions import ArcGISError
    raise ArcGISError(
        code="MAP_<OP>_FAILED",  # or LAYOUT_<OP>_FAILED
        message=str(e),
        arcpy_messages=self._arcpy.GetMessages()
    )
```

### APRX Lock Management Pattern (try/finally with del aprx)
**Source:** CONTEXT.md D-06, RESEARCH.md Pattern 1
**Apply to:** All ArcPyMapDocument and ArcPyLayoutDocument methods that open an .aprx
```python
try:
    aprx = self._arcpy.mp.ArcGISProject(str(project_path))
    # ... operations ...
    aprx.save()
except self._arcpy.ExecuteError as e:
    # ... ArcGISError ...
finally:
    del aprx  # Release file lock (D-06)
```

### Service Result.ok Pattern
**Source:** `src/arcgis_agent/services/geoprocessing.py` lines 49-53
**Apply to:** All map_service and layout_service methods
```python
return Result.ok(
    data={"output": str(result_path), "feature_count": count,
          "elapsed_seconds": round(elapsed, 2)},
    message=f"Operation completed: {result_path.name}"
)
```

### Service Result.error Pattern
**Source:** `src/arcgis_agent/services/geoprocessing.py` lines 23-26
**Apply to:** All service method input validations
```python
if not p_in.exists():
    return Result.error(code="FILE_NOT_FOUND",
                        message=f"Input not found: {input_fc}")
```

### Service Result.from_exception Pattern
**Source:** `src/arcgis_agent/services/geoprocessing.py` lines 55-56
**Apply to:** All service method exception handlers
```python
except Exception as e:
    return Result.from_exception(e)
```

### CLI Command Registration Pattern
**Source:** `src/arcgis_agent/commands/data.py` lines 26-35
**Apply to:** commands/map.py, commands/layout.py
```python
def register(cli_group: click.Group) -> None:
    """Register <group> commands with CLI."""
    @cli_group.group("<group>")
    def subgroup():
        """<description>."""
        pass
    # ... commands under subgroup ...
```

### Test: Mock Adapter Calls Assertion Pattern
**Source:** `tests/unit/test_project_service.py` lines 50-58
**Apply to:** All test_map_service.py and test_layout_service.py tests
```python
def test_operation_uses_adapter(self, tmp_path):
    """Verify Mock adapter method was called."""
    mock_map = MockMapDocument()
    svc = MapService(map_doc=mock_map)
    # ... setup and call ...
    assert len(mock_map.calls) == 1
    assert mock_map.calls[0][0] == "expected_method_name"
```

### Error Code Naming Convention
**Source:** `src/arcgis_agent/exceptions.py` lines 38-39, 48-49 (existing) + CONTEXT.md D-06
**Apply to:** All new error codes
```
MAP_CREATE_FAILED, MAP_ADD_LAYER_FAILED, MAP_REMOVE_LAYER_FAILED,
MAP_LIST_LAYERS_FAILED, MAP_SET_EXTENT_FAILED, MAP_EXPORT_FAILED,
MAP_SYMBOLIZE_FAILED, MAP_SET_LABEL_FAILED,
LAYOUT_CREATE_FAILED, LAYOUT_ADD_ELEMENT_FAILED, LAYOUT_EXPORT_FAILED
```

### Color Parsing Pattern
**Source:** RESEARCH.md "Input Validation: Color Parsing" section
**Apply to:** map_service.py validation helpers for symbology commands
```python
def parse_color(color_str: str) -> list[int]:
    """Parse 'R,G,B' string into [R,G,B] list."""
    parts = color_str.split(",")
    if len(parts) != 3:
        raise InvalidFormatError(code="INVALID_COLOR",
                                 message=f"Expected R,G,B, got: {color_str}")
    values = [int(p.strip()) for p in parts]
    for v in values:
        if not (0 <= v <= 255):
            raise InvalidFormatError(code="INVALID_COLOR",
                                     message=f"Color values must be 0-255, got: {v}")
    return values
```

---

## No Analog Found

All Phase 04 files have exact pattern analogs in the existing codebase. No files require the planner to fall back to RESEARCH.md patterns alone. The symbology-specific logic (updateRenderer pattern, color ramp matching) is documented in RESEARCH.md with verified code examples but follows the same adapter method structure as all existing ArcPyMapDocument methods.

---

## Metadata

**Analog search scope:** `src/arcgis_agent/adapters/`, `src/arcgis_agent/services/`, `src/arcgis_agent/commands/`, `tests/unit/`, `tests/conftest.py`, `pyproject.toml`
**Files scanned:** 14 (base.py, arcpy_adapter.py, mock_adapter.py, base.py (services), geoprocessing.py, analysis_service.py, data.py, geoprocessing.py (commands), cli.py, plugins.py, exceptions.py, result.py, conftest.py, pyproject.toml, test_cli.py, test_project_service.py, test_services.py)
**Pattern extraction date:** 2026-05-26
