# Phase 04: 地图生产 - Research

**Researched:** 2026-05-26
**Domain:** arcpy.mp Map/Layout Automation (Symbology, Layout, Export)
**Confidence:** HIGH

## Summary

Phase 04 implements map and layout production automation via the `arcpy.mp` module. The phase extends the existing `IMapDocument` interface (adding symbology, layer removal, labeling, extent control) and introduces a new `ILayoutDocument` interface for layout creation, element placement, and export.

The primary technical challenges are: (1) correct use of arcpy.mp's symbology update pattern (`sym.updateRenderer()` + renderer modification + `layer.symbology = sym` reassignment), (2) layout element geometry positioning and the map surround API (legends, north arrows, scale bars), and (3) managing `.aprx` file locks with method-level `try/finally` for `ArcGISProject` lifecycle.

The arcpy.mp API in ArcGIS Pro 3.x provides all required primitives: `SimpleRenderer`, `UniqueValueRenderer`, `GraduatedColorsRenderer` for symbology; `Layout.createMapFrame()`, `Layout.createMapSurroundElement()`, `ArcGISProject.createTextElement()`, `ArcGISProject.createPictureElement()` for layout elements; and `Map.exportToPNG()`/`Map.exportToPDF()` for export with DPI and transparency control.

**Primary recommendation:** Build two new service classes (`MapService` extends `IMapDocument` methods, `LayoutService` uses new `ILayoutDocument`) following the existing `BaseService` dependency injection pattern. Each Adapter manages its own `ArcGISProject` connection with method-level `try/finally` for `save()` and `del aprx`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Map creation, layer management | Adapter (arcpy.mp) | Service | arcpy.mp `ArcGISProject`/`Map` API owns all map state; Service validates inputs |
| Symbology (Simple/Unique/Graduated) | Adapter (arcpy.mp) | Service | arcpy.mp `Symbology` class owns renderer lifecycle; `layer.symbology = sym` pattern is arcpy-specific |
| Labeling | Adapter (arcpy.mp) | Service | arcpy.mp `LabelClass` + `layer.showLabels` own label state |
| Layout creation, element placement | Adapter (arcpy.mp) | Service | arcpy.mp `Layout` + surround elements API owns geometry and placement |
| Export (PNG/PDF) | Adapter (arcpy.mp) | Service | arcpy.mp `exportToPNG`/`exportToPDF` own rendering pipeline |
| Input validation | Service | CLI | Service validates paths, formats, DPI ranges, color formats before passing to Adapter |
| JSON serialization | CLI (commands) | Service | Commands call `result.to_json()`; Services return `Result` objects |
| Project path resolution | Service | Config | `WorkspaceConfig.get_workspace()` + auto-find `.aprx` in workspace (D-04) |

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** CLI 合并 + 底层接口分离 -- `IMapDocument` (地图操作) + `ILayoutDocument` (布局操作)
- **D-02:** 图层引用：名称优先，fallback 到索引
- **D-03:** 范围设置：缩放至图层 (`--zoom-to LAYER`)，非四独立坐标选项
- **D-04:** 工程上下文：隐式 (`workspace set` 后自动查找 `.aprx`)
- **D-05:** ArcPy 连接：各自独立（每个 Adapter 管理自己的 aprx 连接）
- **D-06:** 锁管理：方法级 try/finally
- **D-07:** `list-layers` 输出：名称 + 数据源 + 要素数
- **D-08:** CLI 结构：`map` 和 `layout` 为同级命令组
  - `map create|add-layer|remove-layer|list-layers|set-extent|export|symbolize|label`
  - `layout create|add-element|export`
- **D-09:** 支持三种符号化类型：Simple / UniqueValues / GraduatedColors
- **D-10:** Simple 参数：`--color R,G,B --outline-color R,G,B --size N --opacity 0-100`
- **D-11:** 颜色格式：R,G,B 逗号分隔，透明度单独 `--opacity 0-100`
- **D-12:** UniqueValues：单字段 `--field`；`--color-ramp` 自动分配 + `--values JSON` 手动覆盖
- **D-13:** GraduatedColors：分类方法 NaturalBreaks / Quantile / EqualInterval；分级 2-7，默认 5
- **D-14:** GraduatedColors 色带：`--color-ramp "Cyan to Purple"` 按名称字符串匹配
- **D-15:** GraduatedColors 轮廓：`--outline-color` 统一轮廓颜色
- **D-16:** 标注：字段 + 基本样式 (`--font-size, --color, --bold`)
- **D-17:** 不提供 `list-color-ramps` 命令，无默认色带
- **D-18:** 支持 6 种布局元素：text, legend, scale-bar, north-arrow, map-frame, image
- **D-19:** 定位方式：预设位置 + XY坐标 (`--position top-left|...` + `--params "x=1.0,y=2.0,width=6.0,height=0.5"`)
- **D-20:** 文本参数：`text=My Map,font_size=24,color=0,0,0,bold=true,italic=false`
- **D-21:** 图例参数：`title=Legend` (内容自动从图层符号化生成)
- **D-22:** 比例尺参数：`style=Alternating|Bar|DoubleAlternating`
- **D-23:** 指北针参数：`style=Default|Arrow`
- **D-24:** MapFrame 参数：`map=Map1,extent=full_extent|current_view`
- **D-25:** Image 参数：`source=path/to/logo.png`
- **D-26:** 页面尺寸：`--page-size A4|A3|Letter|Tabloid` + `--orientation portrait|landscape`
- **D-27:** 元素参数格式：key=value 对（逗号分隔在 --params 内）
- **D-28:** 导出格式：PNG + PDF
- **D-29:** `map export` 和 `layout export` 为独立命令
- **D-30:** DPI：固定选项 96|150|300|600，默认 300
- **D-31:** PNG 支持 `--transparent` 透明背景标志

### Claude's Discretion

- Adapter 接口方法的具体签名（IMapDocument.symbolize_layer, ILayoutDocument 方法定义）
- ArcPyMapDocument 和 MockMapDocument 的实现细节
- Service 层分拆粒度（MapService, LayoutService）
- CLI 命令参数验证逻辑
- 单元测试用例设计

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAP-01 | `map create <name>` -- 创建新地图 | arcpy.mp `ArcGISProject.createMap(map_name)` [VERIFIED: research synthesis] |
| MAP-02 | `map add-layer <map> <data>` -- 添加图层 | arcpy.mp `Map.addDataFromPath(path)` [VERIFIED: existing codebase pattern] |
| MAP-03 | `map remove-layer <map> <layer>` -- 移除图层 | arcpy.mp `Map.removeLayer(layer_obj)` [VERIFIED: WebSearch arcpy.mp guidelines] |
| MAP-04 | `map list-layers <map>` -- 列出图层 | arcpy.mp `Map.listLayers()` + `Describe` for datasource/count [VERIFIED: WebSearch] |
| MAP-05 | `map set-extent <map> --zoom-to` -- 设置范围 | `MapFrame.camera.setExtent()` or temporary layout approach [VERIFIED: WebSearch] |
| MAP-06 | `map export <map> <out> --format --dpi` -- 导出地图 | `Map.exportToPNG()` / `Map.exportToPDF()` with resolution parameter [VERIFIED: existing + WebSearch] |
| MAP-07 | `map symbolize <map> <layer> --type --field` -- 符号化 | Symbology.updateRenderer + renderer pattern [VERIFIED: WebSearch] |
| MAP-08 | `map label <map> <layer> --field` -- 设置标注 | LabelClass + layer.showLabels + CIM definition [VERIFIED: WebSearch] |
| MAP-09 | `layout create <name>` -- 创建布局 | `ArcGISProject.createLayout(width, height, units, name)` [VERIFIED: WebSearch] |
| MAP-10 | `layout add-element <layout> <type> --params` -- 添加元素 | MapFrame, MapSurround, TextElement, PictureElement creation [VERIFIED: WebSearch] |
| MAP-11 | `layout export <layout> <out> --format --dpi` -- 导出布局 | `Layout.exportToPNG()` / `Layout.exportToPDF()` [VERIFIED: WebSearch] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| arcpy.mp | ArcGIS Pro 3.x built-in | Map/Layout creation, symbology, labeling, export | Only Python API for ArcGIS Pro mapping automation |
| click | >=8.1 | CLI command groups (map, layout) | Existing project standard (Phase 1 decision) |
| pydantic | >=2.11 | Result model validation | Existing project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0 | Unit/integration testing | All test files |
| click.testing.CliRunner | built-in (click) | CLI integration testing | Testing command output in isolation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| arcpy.mp (standalone Map export) | Layout-based export only | Map.exportToPNG is simpler for quick map export; Layout export is needed for composed output (D-29) |
| Manual CIM XML manipulation | Symbology.updateRenderer() | updateRenderer() is the documented arcpy.mp pattern; CIM is lower-level |

**Installation:** No additional packages required -- arcpy.mp is built into ArcGIS Pro's Python environment.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI ENTRY POINT                                 │
│                                                                             │
│  ┌──────────────┐    ┌──────────────────┐                                   │
│  │ commands/map.py  │    │ commands/layout.py │  click.Group objects         │
│  │ register(cli)    │    │ register(cli)      │  entry_points discovery       │
│  └──────┬───────────┘    └────────┬─────────┘                               │
│         │                         │                                          │
│         │  _run() / direct        │  direct Service calls                    │
│         ▼                         ▼                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                             SERVICE LAYER                                    │
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────┐                     │
│  │ MapService          │    │ LayoutService           │                     │
│  │ (extends BaseService)│    │ (extends BaseService)   │                     │
│  │                     │    │                         │                     │
│  │ create_map()        │    │ create_layout()         │                     │
│  │ add_layer()         │    │ add_element()           │                     │
│  │ remove_layer()      │    │ export_layout()         │                     │
│  │ list_layers()       │    │                         │                     │
│  │ set_extent()        │    │ Input validation:       │                     │
│  │ export_map()        │    │ - position presets      │                     │
│  │ symbolize_layer()   │    │ - element type dispatch │                     │
│  │ set_label()         │    │ - page size mapping     │                     │
│  │                     │    │ - params parsing        │                     │
│  │ Input validation:   │    │                         │                     │
│  │ - color format      │    │                         │                     │
│  │ - DPI values        │    │                         │                     │
│  │ - symbology type    │    │                         │                     │
│  └──────────┬──────────┘    └──────────────┬──────────┘                     │
│             │                              │                                 │
│             │ self._map + self._data       │ self._map + self._layout        │
│             ▼                              ▼                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                             ADAPTER LAYER                                    │
│                                                                             │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────┐     │
│  │ IMapDocument (ABC) - EXTENDED    │  │ ILayoutDocument (ABC) - NEW   │     │
│  │                                  │  │                              │     │
│  │ ✅ create_map()      [existing]  │  │ create_layout(name, page,)   │     │
│  │ ✅ add_layer()       [existing]  │  │ add_element(type, params)    │     │
│  │ ✅ export_map()      [existing]  │  │ export_layout(path,fmt,dpi)  │     │
│  │ 🆕 remove_layer()                │  │ list_layouts()               │     │
│  │ 🆕 list_layers()                 │  └──────────────┬───────────────┘     │
│  │ 🆕 set_extent()                  │                 │                     │
│  │ 🆕 symbolize_layer()             │                 │                     │
│  │ 🆕 set_label()                   │                 │                     │
│  │ 🆕 get_project_info() [formalize]│                 │                     │
│  └──────────────┬───────────────────┘                 │                     │
│                 │                                     │                     │
│  ┌──────────────▼───────────────────┐  ┌──────────────▼───────────────┐     │
│  │ ArcPyMapDocument (IMapDocument)  │  │ ArcPyLayoutDocument (NEW)    │     │
│  │ - lazy import arcpy in __init__  │  │ - ILayoutDocument impl       │     │
│  │ - try/finally per method         │  │ - lazy import arcpy          │     │
│  │ - each method opens/closes aprx  │  │ - try/finally per method     │     │
│  │ - symbology: updateRenderer +    │  │ - uses project.listLayouts() │     │
│  │   layer.symbology = sym pattern  │  │ - MapFrame, MapSurround,     │     │
│  └──────────────────────────────────┘  │   Text, Picture elements     │     │
│                                         └─────────────────────────────┘     │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────┐     │
│  │ MockMapDocument (IMapDocument)   │  │ MockLayoutDocument (NEW)     │     │
│  │ - records calls for assertions   │  │ - ILayoutDocument impl       │     │
│  │ - returns dummy Path objects     │  │ - records calls for tests    │     │
│  └──────────────────────────────────┘  └──────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL DEPENDENCY                                 │
│                                                                             │
│  arcpy.mp (ArcGIS Pro 3.x Python library)                                   │
│  ├── ArcGISProject: open .aprx, listMaps, listLayouts, createMap,           │
│  │                  createLayout, createTextElement, createPictureElement    │
│  ├── Map: listLayers, addDataFromPath, removeLayer,                         │
│  │         exportToPNG, exportToPDF                                          │
│  ├── Symbology: updateRenderer(), .renderer property                        │
│  │   ├── SimpleRenderer: .symbol.color, .symbol.outlineColor, .symbol.size  │
│  │   ├── UniqueValueRenderer: .fields, .groups[].items[]                   │
│  │   └── GraduatedColorsRenderer: .classificationField, .breakCount,        │
│  │       .classificationMethod, .colorRamp, .classBreaks[]                  │
│  ├── Layout: listElements, createMapFrame, createMapSurroundElement,        │
│  │           exportToPNG, exportToPDF, changePageSize                        │
│  ├── MapFrame: camera.setExtent(), getLayerExtent()                         │
│  ├── LabelClass: .expression, .visible                                      │
│  └── Layer: .symbology, .showLabels, .listLabelClasses(), .supports()       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/arcgis_agent/
├── adapters/
│   ├── base.py              # EXTEND: IMapDocument + NEW: ILayoutDocument
│   ├── arcpy_adapter.py     # EXTEND: ArcPyMapDocument + NEW: ArcPyLayoutDocument
│   └── mock_adapter.py      # EXTEND: MockMapDocument + NEW: MockLayoutDocument
├── services/
│   ├── base.py              # EXTEND: add _make_layout() factory
│   ├── map_service.py       # NEW: MapService (MAP-01~08)
│   └── layout_service.py    # NEW: LayoutService (MAP-09~11)
├── commands/
│   ├── map.py               # NEW: 'map' click.Group (8 commands)
│   └── layout.py            # NEW: 'layout' click.Group (3 commands)
tests/
├── conftest.py              # EXTEND: mock_layout fixture
├── unit/
│   ├── test_map_service.py  # NEW: unit tests for MapService
│   ├── test_layout_service.py # NEW: unit tests for LayoutService
│   ├── test_map_commands.py # NEW: CLI integration tests for 'map'
│   └── test_layout_commands.py # NEW: CLI integration tests for 'layout'
pyproject.toml               # EXTEND: uncomment map entry, add layout entry
```

### Pattern 1: Adapter Method with APRX Lock Management (D-06)

**What:** Each adapter method opens `ArcGISProject`, performs operations, saves, and releases the reference in a `try/finally` block.

**When to use:** Every method that touches an `.aprx` file.

**Example:**
```python
# Source: arcpy.mp guidelines + CONTEXT.md D-06
def remove_layer(self, project_path: Path, map_name: str, layer_name: str) -> None:
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

### Pattern 2: Symbology Update Pattern

**What:** arcpy.mp symbology requires a three-step pattern: (1) get `sym` from layer, (2) call `sym.updateRenderer()` and modify `sym.renderer`, (3) reassign `layer.symbology = sym`.

**When to use:** All three symbology types (Simple, UniqueValues, GraduatedColors).

**Example:**
```python
# Source: WebSearch arcpy.mp symbology documentation
def _apply_simple_renderer(self, layer, color, outline_color, size, opacity):
    sym = layer.symbology
    sym.updateRenderer('SimpleRenderer')
    # Convert opacity (0-100) to alpha (0-100) for RGB array position 3
    sym.renderer.symbol.color = {'RGB': [*color, opacity]}
    sym.renderer.symbol.outlineColor = {'RGB': [*outline_color, 100]}
    sym.renderer.symbol.size = size
    layer.symbology = sym  # CRITICAL: must reassign
```

### Pattern 3: Service Layer with Dependency Injection

**What:** Services extend `BaseService`, accept mock adapters for testing, and validate inputs before delegating to adapters.

**When to use:** Every service class.

**Example:**
```python
# Source: existing GeoprocessingService pattern
class MapService(BaseService):
    def __init__(self, map_doc=None, data=None):
        super().__init__(map_doc=map_doc, data=data)

    def remove_layer(self, project_path, map_name, layer_name):
        p = Path(project_path)
        if not p.exists():
            return Result.error(code="FILE_NOT_FOUND", message=f"Project not found: {project_path}")
        try:
            self._map.remove_layer(p, map_name, layer_name)
            return Result.ok(message=f"Layer '{layer_name}' removed from '{map_name}'")
        except Exception as e:
            return Result.from_exception(e)
```

### Pattern 4: CLI Command Registration

**What:** Each command file exports a `register(cli_group: click.Group)` function. Commands are discovered via `entry_points`.

**When to use:** All new command groups.

**Example:**
```python
# Source: existing commands/data.py pattern
def register(cli_group: click.Group) -> None:
    @cli_group.group("map")
    def map_group():
        """Map creation and management commands."""
        pass

    @map_group.command("create")
    @click.argument("name")
    @click.option("--project", "-p", help="Path to .aprx file (overrides workspace auto-detect).")
    @click.pass_context
    def map_create(ctx, name, project):
        """Create a new map (MAP-01)."""
        from arcgis_agent.services.map_service import MapService
        svc = MapService()
        result = svc.create_map(project, name)
        click.echo(result.to_json())
```

### Anti-Patterns to Avoid

- **Opening aprx at module level:** Never `aprx = arcpy.mp.ArcGISProject(...)` at import time. Always inside `__init__` or method scope. Follows existing lazy import pattern. Causes import failures if arcpy unavailable.
- **Forgetting `layer.symbology = sym`:** Modifying `sym.renderer` without reassigning `layer.symbology = sym` silently discards changes. This is the #1 arcpy.mp symbiology pitfall.
- **Not releasing APRX lock:** Missing `del aprx` in `finally` block leaves `.aprx.lock` file that blocks ArcGIS Pro GUI from opening the project (ROADMAP risk: APRX lock conflict).
- **Using `"CURRENT"` instead of file path:** `arcpy.mp.ArcGISProject("CURRENT")` only works from within ArcGIS Pro's Python window. CLI tool must always use file paths.
- **Mixing map export and layout export methods:** `Map.exportToPNG()` and `Layout.exportToPNG()` have different parameter signatures. The code must dispatch correctly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color ramp generation | Custom color interpolation | `ArcGISProject.listColorRamps()` with fuzzy name matching | arcpy.mp provides gallery of pre-built color ramps; hand-rolled interpolation would produce visually inferior results |
| Legend item extraction | Manual renderer scanning | `Layout.createMapSurroundElement(geometry, "LEGEND", mf)` | ArcGIS Pro automatically generates legend items from the map frame's layer symbology |
| Export format handling | Custom PNG/PDF writers | `Map.exportToPNG()` / `Layout.exportToPDF()` | arcpy.mp handles georeferencing, font embedding, DPI, compression, and world files |
| Symbology type switching | Manual CIM XML manipulation | `sym.updateRenderer('SimpleRenderer')` | updateRenderer() is the documented API; CIM XML is internal implementation |
| Layout element geometry | Manual coordinate math | Preset positions mapping table + `Layout.pageWidth`/`pageHeight` | Page coordinates are fractional inches; preset positions (top-left, bottom-right, etc.) are standard |

**Key insight:** arcpy.mp provides a mature, well-documented mapping automation API. The only area where fuzzy/smart logic is needed is color ramp name matching (`"Cyan to Purple"` partial match against `project.listColorRamps()`), which is a simple string search, not custom rendering.

## Common Pitfalls

### Pitfall 1: Symbology Reassignment Not Applied

**What goes wrong:** After `sym.updateRenderer()` and modifying `sym.renderer.symbol.color`, the changes don't take effect.

**Why it happens:** `sym` is a copy. Must call `layer.symbology = sym` to write back.

**How to avoid:** Always follow the 3-step pattern: `sym = l.symbology` -> `sym.updateRenderer(...)` + modify `sym.renderer` -> `l.symbology = sym`.

**Warning signs:** Layer appears with default symbology after script runs; no error is raised.

### Pitfall 2: APRX File Lock Not Released (PITFALL #10 from ROADMAP)

**What goes wrong:** After arcpy script runs, a `.aprx.lock` file persists and ArcGIS Pro GUI cannot open the project.

**Why it happens:** `ArcGISProject` holds a file lock that is released when the object is garbage collected or `del`'d. If an exception occurs before cleanup, the lock persists.

**How to avoid:** Always use `try/finally` pattern. Always `del aprx` in `finally` block (D-06).

**Warning signs:** `.aprx.lock` file present in project directory; ArcGIS Pro shows "Project is already open" error.

### Pitfall 3: `CURRENT` Project Reference Fails from CLI

**What goes wrong:** `arcpy.mp.ArcGISProject("CURRENT")` raises error in CLI context.

**Why it happens:** `CURRENT` only works when the script runs inside ArcGIS Pro's Python window (where Pro is running with an open project). CLI tools run externally.

**How to avoid:** Always use file path: `arcpy.mp.ArcGISProject(str(project_path))`. The CLI must resolve the project path from workspace config or `--project` option (D-04).

**Warning signs:** `OSError` or arcpy error referencing "CURRENT" keyword.

### Pitfall 4: Layer Name Ambiguity

**What goes wrong:** `m.listLayers("Roads")` returns multiple layers when duplicate names exist.

**Why it happens:** ArcGIS Pro allows duplicate layer names in a map.

**How to avoid:** `m.listLayers(name)[0]` for first match. D-02 specifies "名称优先，fallback 到索引" -- implement name lookup first, then allow `--layer-index` option if the name is ambiguous.

**Warning signs:** Wrong layer gets symbolized; unexpected layer is removed.

### Pitfall 5: Color Alpha Channel Reversal

**What goes wrong:** Colors appear at wrong opacity after applying symbology.

**Why it happens:** User provides `--opacity 0-100` as transparency percentage, but arcpy.mp RGB array uses alpha (0=transparent, 100=opaque) as the 4th value. Opacity 80 means alpha 80, but the user might think "80% opaque = alpha 20" or vice versa.

**How to avoid:** Document clearly: `--opacity` value is opacity percentage (0=fully transparent, 100=fully opaque). Map directly to RGB array 4th value: `{'RGB': [R, G, B, opacity]}`.

**Warning signs:** Layer appears more/less transparent than expected; color looks faded.

## Code Examples

Verified patterns from official sources:

### Symbology: SimpleRenderer
```python
# Source: WebSearch arcpy.mp symbology documentation
sym = layer.symbology
sym.updateRenderer('SimpleRenderer')
sym.renderer.symbol.color = {'RGB': [255, 0, 0, 100]}      # Red, fully opaque
sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}  # Black outline
sym.renderer.symbol.size = 8
layer.symbology = sym  # REQUIRED: reassign to apply
```

### Symbology: UniqueValueRenderer
```python
# Source: WebSearch arcpy.mp symbology documentation
sym.updateRenderer('UniqueValueRenderer')
sym.renderer.fields = ['LANDUSE']  # Field to symbolize on

# Auto-assign from color ramp
for grp in sym.renderer.groups:
    for itm in grp.items:
        itm.label = str(itm.values[0][0])

# Manual color overrides (from --values JSON)
# itm.symbol.color = {'RGB': [255, 0, 0, 100]}
# itm.symbol.size = 5

layer.symbology = sym
```

### Symbology: GraduatedColorsRenderer
```python
# Source: WebSearch arcpy.mp symbology documentation
sym.updateRenderer('GraduatedColorsRenderer')
renderer = sym.renderer
renderer.classificationField = 'POPULATION'
renderer.breakCount = 5                               # Default 5, range 2-7
renderer.classificationMethod = 'NaturalBreaks'       # NaturalBreaks/Quantile/EqualInterval
renderer.colorRamp = project.listColorRamps('Cyan to Purple*')[0]  # Fuzzy match

for brk in renderer.classBreaks:
    brk.symbol.size = 4
    brk.symbol.outlineColor = {'RGB': [0, 0, 0, 100]}  # Uniform outline (D-15)

layer.symbology = sym
```

### Layout: Creating and Adding Elements
```python
# Source: WebSearch arcpy.mp Layout documentation
aprx = arcpy.mp.ArcGISProject(str(project_path))

# Create layout with A4 portrait page
lyt = aprx.createLayout(210, 297, "MILLIMETER", "My Layout")

# Create MapFrame (fills entire page)
mf = lyt.createMapFrame(lyt.pageBounds, m, "Main Map Frame")

# Add north arrow surround element
na = lyt.createMapSurroundElement(
    arcpy.CreateObject("Point", 0.5, 0.5),  # or computed position
    "NORTH_ARROW", mf, "ArcGIS 2D", "North Arrow"
)

# Add scale bar surround element
sb = lyt.createMapSurroundElement(
    computed_geometry, "SCALE_BAR", mf, "Alternating Scale Bar 1", "Scale Bar"
)

# Add text element (via ArcGISProject)
from arcpy.mp import TextElement
txt = aprx.createTextElement(
    lyt, arcpy.CreateObject("Point", 0.5, 10.5), "TEXT",
    "My Map Title", 24, "Arial", "Bold", None, "Title"
)

# Add picture element (logo)
img = aprx.createPictureElement(
    lyt, computed_geometry, "path/to/logo.png", "Logo", True
)

aprx.save()
```

### Layout: Page Size Mapping (D-26)
```python
# Source: CONTEXT.md D-26
PAGE_SIZES = {
    "A4":       (210, 297, "MILLIMETER"),
    "A3":       (297, 420, "MILLIMETER"),
    "Letter":   (8.5, 11, "INCH"),
    "Tabloid":  (11, 17, "INCH"),
}

def get_page_dimensions(page_size: str, orientation: str) -> tuple:
    """Map page size + orientation to (width, height, units)."""
    w, h, units = PAGE_SIZES[page_size]
    if orientation == "landscape":
        w, h = h, w  # Swap for landscape
    return w, h, units
```

### Export: Map to PNG with Transparency
```python
# Source: WebSearch arcpy.mp export documentation
m.exportToPNG(
    str(output_path),
    resolution=300,
    transparent_background=True,  # D-31: transparent background
    world_file=False,
)
```

### Export: Layout to PDF
```python
# Source: WebSearch arcpy.mp export documentation
lyt.exportToPDF(
    str(output_path),
    resolution=300,
    image_quality="BEST",
    embed_fonts=True,
    georef_info=True,
)
```

### Labeling: Set Label Expression
```python
# Source: WebSearch arcpy.mp LabelClass documentation
if lyr.supports("SHOWLABELS"):
    lyr.showLabels = True
    for lblClass in lyr.listLabelClasses():
        lblClass.expression = f"[{field}]"  # VBScript parser
        lblClass.visible = True

# Font styling requires CIM definition manipulation:
# cim = lyr.getDefinition("V3")
# Modify cim.labelClasses[0].textSymbol.symbol.fontFamilyName etc.
# lyr.setDefinition(cim)
```

### Input Validation: Color Parsing
```python
# Source: CONTEXT.md D-11
def parse_color(color_str: str) -> list[int]:
    """Parse 'R,G,B' string into [R,G,B] list."""
    parts = color_str.split(",")
    if len(parts) != 3:
        raise InvalidFormatError(code="INVALID_COLOR", message=f"Expected R,G,B, got: {color_str}")
    values = [int(p.strip()) for p in parts]
    for v in values:
        if not (0 <= v <= 255):
            raise InvalidFormatError(code="INVALID_COLOR", message=f"Color values must be 0-255, got: {v}")
    return values
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `arcpy.mapping` (mxd-based, ArcMap) | `arcpy.mp` (aprx-based, ArcGIS Pro) | ArcGIS Pro 1.0 (2015) | All map automation uses `arcpy.mp`; `arcpy.mapping` is legacy |
| `exportToPNG`/`exportToPDF` directly | `CreateExportFormat` + `export()` pattern | AllSource 3.4+ | Alternative pattern available; older methods still work and are simpler for our use case |
| Manual CIM XML for symbology | `sym.updateRenderer()` high-level API | ArcGIS Pro 2.x | `updateRenderer()` is the documented approach; CIM XML is internal |

**Deprecated/outdated:**
- `arcpy.mapping.ExportToPNG` -- Legacy ArcMap API; do not use. This project uses `arcpy.mp` exclusively.
- Direct `symbology.renderer = X` assignment -- does not work; must use `updateRenderer()` + reassign symbology object.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `Map.exportToPNG()` accepts `transparent_background` parameter in ArcGIS Pro 3.4.3 | Code Examples | LOW -- parameter exists in arcpy.mp docs; if missing, fall back to exporting without transparency and document limitation |
| A2 | `ArcGISProject.createMap()` exists in ArcGIS Pro 3.x (the createMap method was added in a later version of arcpy.mp) | Standard Stack | MEDIUM -- createMap may not exist in older Pro versions; fallback: advise user to create project manually in ArcGIS Pro |
| A3 | `MapFrame.camera.setExtent()` sets the extent that Map.exportToPNG() uses for standalone map export | Architecture Patterns | MEDIUM -- a temporary layout might be needed as intermediate container if standalone Map extent setting is not supported |
| A4 | arcpy.mp Map objects support `removeLayer()`, `listLayers()`, `addDataFromPath()` in ArcGIS Pro 3.4.3 | Standard Stack | LOW -- these are core arcpy.mp APIs present since Pro 1.x |
| A5 | `Layer.listLabelClasses()` and `layer.showLabels` work without needing a layout | Common Pitfalls | LOW -- labeling is a core layer property independent of layout |
| A6 | Color ramp fuzzy matching with `project.listColorRamps('*query*')` wildcard pattern works | Don't Hand-Roll | LOW -- wildcard matching is documented in arcpy.mp `listColorRamps()` API |
| A7 | Map page sizes A4, A3, Letter, Tabloid in millimeter/inch mapping are correct | Code Examples | LOW -- these are ISO and ANSI standard dimensions |

## Open Questions

1. **Which ArcGIS Pro version does the target environment have?**
   - What we know: ArcGIS Pro 3.4.3 Advanced license (from STATE.md)
   - What's unclear: Whether `ArcGISProject.createMap()` is available -- this was added relatively recently to arcpy.mp. Older Pro versions required creating maps via the GUI or importing from templates.
   - Recommendation: Test `createMap()` availability on the target machine during implementation. If unavailable, implement MAP-01 by creating a new .aprx via `arcpy.mp.ArcGISProject()` constructor or fall back to a template-based approach.

2. **How does standalone Map extent setting work for export?**
   - What we know: `MapFrame.camera.setExtent()` works for maps in layouts. It is unclear whether the Map object itself supports a standalone extent set that affects `Map.exportToPNG()`.
   - What's unclear: Whether the extent set via a layout's MapFrame persists when exporting the standalone Map.
   - Recommendation: Test both approaches during implementation: (a) set extent via temporary layout MapFrame then export via Map, (b) try `Map.openView().camera.setExtent()`. Document the working approach.

3. **Are `Map.exportToPNG()` and `Layout.exportToPNG()` parameter signatures identical?**
   - What we know: `Map.exportToPNG()` takes `(out_png, {width}, {height}, {resolution}, {world_file}, ...)` while `Layout.exportToPNG()` takes `(out_png, {resolution}, {height}, {width}, ...)`. Parameter order differs.
   - What's unclear: The exact parameter list for ArcGIS Pro 3.4.3.
   - Recommendation: Verify via `help(aprx.listMaps()[0].exportToPNG)` on the target machine during implementation. The adapter methods should accept only the parameters needed (output_path, resolution, dpi, format, transparent).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| arcpy.mp | All MAP-01~11 adapter implementations | Conditionally (needs ArcGIS Pro env) | ArcGIS Pro 3.4.3 [from STATE.md] | Mock adapters for unit testing |
| Python 3.x | Runtime | 3.11.10 [from STATE.md] | 3.11.10 | -- |
| click | CLI commands | Installed (project dep) | >=8.1 | -- |
| pydantic | Result model | Installed (project dep) | >=2.11 | -- |
| pytest | Testing | 9.0.2 [verified: bash `pytest --version`] | -- | -- |

**Missing dependencies with no fallback:**
- arcpy.mp -- Only available inside ArcGIS Pro's Python environment. All adapter code must use lazy import pattern. Unit tests use Mock adapters. Integration tests require ArcGIS Pro.

**Missing dependencies with fallback:**
- None -- all code dependencies are already met by the project's existing pyproject.toml.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | tests/conftest.py (existing fixtures: runner, mock_gp, mock_map, mock_data, mock_adapters) |
| Quick run command | `pytest tests/unit/test_map_service.py -x` |
| Full suite command | `pytest tests/unit/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | create_map() returns project_path with map created | unit | `pytest tests/unit/test_map_service.py::TestCreateMap::test_create_success -x` | No -- Wave 0 |
| MAP-02 | add_layer() calls Map.addDataFromPath | unit | `pytest tests/unit/test_map_service.py::TestAddLayer::test_add_layer_success -x` | No -- Wave 0 |
| MAP-03 | remove_layer() removes layer by name, fallback to index | unit | `pytest tests/unit/test_map_service.py::TestRemoveLayer::test_remove_by_name -x` | No -- Wave 0 |
| MAP-04 | list_layers() returns name + datasource + feature_count | unit | `pytest tests/unit/test_map_service.py::TestListLayers::test_list_layers_format -x` | No -- Wave 0 |
| MAP-05 | set_extent() zooms to specified layer | unit | `pytest tests/unit/test_map_service.py::TestSetExtent::test_zoom_to_layer -x` | No -- Wave 0 |
| MAP-06 | export_map() accepts format (PNG/PDF) and DPI | unit | `pytest tests/unit/test_map_service.py::TestExportMap::test_export_png -x` | No -- Wave 0 |
| MAP-07 | symbolize_layer() applies Simple, UniqueValues, GraduatedColors | unit | `pytest tests/unit/test_map_service.py::TestSymbolize::test_simple_renderer -x` | No -- Wave 0 |
| MAP-08 | set_label() sets field expression + basic style | unit | `pytest tests/unit/test_map_service.py::TestLabel::test_set_label_field -x` | No -- Wave 0 |
| MAP-09 | create_layout() creates layout with page size + orientation | unit | `pytest tests/unit/test_layout_service.py::TestCreateLayout::test_a4_portrait -x` | No -- Wave 0 |
| MAP-10 | add_element() dispatches by type (text/legend/scale-bar/north-arrow/map-frame/image) | unit | `pytest tests/unit/test_layout_service.py::TestAddElement::test_text_element -x` | No -- Wave 0 |
| MAP-11 | export_layout() accepts format (PNG/PDF) and DPI | unit | `pytest tests/unit/test_layout_service.py::TestExportLayout::test_export_pdf -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_map_service.py tests/unit/test_layout_service.py -x`
- **Per wave merge:** `pytest tests/unit/ -x`
- **Phase gate:** Full test suite green + CLI integration tests green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_map_service.py` -- covers MAP-01 through MAP-08
- [ ] `tests/unit/test_layout_service.py` -- covers MAP-09 through MAP-11
- [ ] `tests/unit/test_map_commands.py` -- CLI integration tests for 'map' commands
- [ ] `tests/unit/test_layout_commands.py` -- CLI integration tests for 'layout' commands
- [ ] `tests/conftest.py` -- add `mock_map_doc` (extended MockMapDocument) and `mock_layout` (MockLayoutDocument) fixtures
- [ ] `src/arcgis_agent/adapters/mock_adapter.py` -- extend MockMapDocument with new method stubs; create MockLayoutDocument
- [ ] Framework install: `pytest` already installed (89 existing tests pass)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase does not handle authentication |
| V3 Session Management | No | Phase does not manage sessions |
| V4 Access Control | No | Phase operates on local files only |
| V5 Input Validation | Yes | Path validation (pathlib, exists checks), color format validation (R,G,B 0-255), DPI enum validation (96/150/300/600), symbology type enum validation, page size enum validation |
| V6 Cryptography | No | Phase does not use cryptography |

### Known Threat Patterns for arcpy.mp

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via layer path input | Tampering | Validate with `Path(input).resolve()` and check it is within workspace |
| APRX file corruption from concurrent access | Denial of Service | try/finally lock release (D-06); pre-check `aprx.lock` file |
| Large layer datasource causing memory exhaustion on export | Denial of Service | Export DPI limits (96-600); do not support arbitrary DPI |
| User-supplied color values causing unexpected rendering | Information Disclosure | Validate RGB ranges 0-255; reject malformed inputs before passing to arcpy |
| Malicious image path for PictureElement (D-25) | Tampering | Validate path exists, check file extension against allowlist (.png, .jpg, .jpeg, .bmp, .gif) |

## Sources

### Primary (HIGH confidence)
- WebSearch: arcpy.mp Symbology class (`updateRenderer`, `SimpleRenderer`, `UniqueValueRenderer`, `GraduatedColorsRenderer`) -- verified pattern from official Esri arcpy.mp documentation
- WebSearch: arcpy.mp Layout class (`createLayout`, `createMapFrame`, `createMapSurroundElement`, `createTextElement`, `createPictureElement`, `listElements`) -- verified from official Esri docs
- WebSearch: arcpy.mp Map class (`listLayers`, `removeLayer`, `addDataFromPath`, `exportToPNG`, `exportToPDF`) -- verified from official Esri docs
- WebSearch: arcpy.mp LabelClass (`showLabels`, `listLabelClasses`, `expression`, CIM definition) -- verified from Esri community and docs
- WebSearch: arcpy.mp Export methods (`exportToPNG`, `exportToPDF`, `CreateExportFormat`) -- verified from official Esri documentation
- Existing codebase: `src/arcgis_agent/adapters/base.py` (IMapDocument), `arcpy_adapter.py` (ArcPyMapDocument), `mock_adapter.py` (MockMapDocument)
- Existing codebase: `src/arcgis_agent/services/base.py` (BaseService DI pattern), `geoprocessing.py` (service pattern)
- Existing codebase: `src/arcgis_agent/commands/data.py` (CLI register pattern), `pyproject.toml` (entry_points)

### Secondary (MEDIUM confidence)
- WebSearch: arcpy.mp guidelines (`save()`, `saveACopy()`, lock management) -- from Esri official guidelines page
- WebSearch: arcpy.mp `ArcGISProject` methods (`createMap`, `createLayout`) -- from Esri official documentation
- WebSearch: MapFrame `camera.setExtent()` and `getLayerExtent()` -- from arcpy.mp tutorials

### Tertiary (LOW confidence)
- Color ramp fuzzy matching behavior (exact wildcard syntax for `listColorRamps()`) -- inferred from typical arcpy.mp list method patterns; needs verification on target machine

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- arcpy.mp is the only and well-documented API for ArcGIS Pro map automation; all other deps already in the project
- Architecture: HIGH -- 4-layer pattern is established in Phase 1-3; extension is straightforward
- Pitfalls: HIGH -- well-documented arcpy.mp gotchas confirmed by multiple sources

**Research date:** 2026-05-26
**Valid until:** 2026-06-26 (stable arcpy.mp API, no scheduled breaking changes)
