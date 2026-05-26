# Project Research Summary

**Project:** ArcGIS Pro CLI Agent
**Domain:** GIS Geoprocessing Automation CLI + MCP Server
**Researched:** 2026-05-25
**Confidence:** MEDIUM

## Executive Summary

This project is a CLI tool and MCP server that wraps ArcGIS Pro's `arcpy` library into an AI-agent-friendly interface. The tool must run inside ArcGIS Pro's conda environment (`arcgispro-py3`), expose geoprocessing operations as composable JSON-outputting commands, and serve as both a standalone CLI and an MCP tool server for Claude Code / Claude Desktop. The research unanimously recommends **Click** (not Typer) for the CLI framework, **FastMCP** (from the official `mcp` SDK) for the MCP server, and a **layered architecture** with an Adapter pattern to isolate `arcpy`.

The critical constraint is that `arcpy` is only available inside ArcGIS Pro's bundled Python environment -- it cannot be pip-installed, and all development must happen there. This shapes every architectural decision: lazy imports, environment detection at startup, wrapper scripts for agent invocation, and careful conda dependency management. The second major risk is Windows-specific encoding issues (Chinese paths, console encoding) which must be handled from day one.

The recommended build approach is bottom-up: foundation (project structure, plugin system, environment detection) first, then data operations, then map production, then MCP server, then advanced analysis. Each phase builds on the previous one's adapter layer. The research identifies 17 pitfalls, of which 5 are critical and must be resolved in Phase 0/1 before any feature work begins.

## Key Findings

### Recommended Stack

The stack is tightly constrained by ArcGIS Pro's environment. Python 3.9-3.11 (matching the installed Pro version), `arcpy` from the Pro conda env, and pip-installed dependencies added carefully to avoid breaking Esri's pinned packages. The recommendation is to clone the default `arcgispro-py3` env before adding any packages.

**Core technologies:**
- **Python 3.9-3.11** (via ArcGIS Pro conda): Required runtime -- must match installed Pro version
- **arcpy** (from Pro): GIS geoprocessing engine -- only available inside Pro's conda env, cannot be pip-installed
- **Click 8.1+**: CLI framework -- mature plugin system via `Group.add_command()`, better than Typer for dynamic command loading
- **FastMCP** (from `mcp` SDK 1.x+): MCP server -- decorator-based (`@mcp.tool()`), minimal boilerplate, official Anthropic SDK
- **Pydantic 2.x**: Data validation -- JSON schema generation useful for MCP tool schemas
- **Rich**: Terminal formatting -- tables, progress bars, colors for CLI output
- **hatchling**: Build backend -- lightweight, works with src layout and pyproject.toml (PEP 621)

**Critical version constraints:**
- Do NOT use `uv`, `poetry`, or `pdm` -- they manage their own Python envs, conflicting with ArcGIS conda
- Do NOT use `Typer` -- adds abstraction over Click without solving the plugin registration problem
- Do NOT install `fastmcp` as standalone package -- it's merged into the official `mcp` SDK
- Use `pip install --no-deps` when possible to avoid overwriting Esri's pinned numpy/pandas

### Expected Features

Based on analysis of Esri's `arcgis-python-api` (59,930 code snippets), the feature space covers 80 operations across 4 domains: Map Production, GIS Data Processing, Spatial Analysis, and Project Management.

**Must have (table stakes) -- 25 features:**
- **Discovery commands** (P0): `workspace set/get`, `data list/describe/fields/extent`, `map list-layers`, `project info`, `env list` -- agent cannot function without knowing what data exists
- **Basic data ops** (P0): `data copy/delete/rename`, `data convert` (shp/gdb/csv), `data select/clip/buffer/intersect/union/dissolve/spatial-join`
- **Project ops** (P0): `project create/open/save`, `workspace set/get`
- **Map production** (P1): `map create/add-layer/remove-layer/export`, `layout create/add-element/export`, `mapseries list/export`

**Should have (differentiators) -- 25 features:**
- `map symbolize/label`, `layout template/dynamic-text` -- automated cartography
- `data validate/repair-geometry/simplify/smooth` -- data quality
- `analysis kernel-density/idw/kriging` -- density/interpolation
- `analysis slope/aspect/viewshed/watershed` -- terrain analysis
- `analysis route/service-area/closest-facility` -- network analysis

**Defer (v2+):**
- Deep learning inference, knowledge graph operations, full raster function chains
- Full 3D scene authoring, topology editing, real-time streaming
- Geodatabase version management (Enterprise-only)

### Architecture Approach

Four-layer architecture: Entry Points (CLI + MCP) -> Command Layer (plugin-based) -> Service Layer (business logic) -> Adapter Layer (arcpy isolation). The key insight is that CLI and MCP are two faces of the same service layer -- both call identical service methods, differing only in input/output format.

**Major components:**
1. **CLI Entry** (`cli.py`): Click group with plugin auto-discovery via `importlib.metadata` entry points
2. **MCP Server** (`mcp_server.py`): FastMCP with parallel plugin registration via entry points
3. **Plugin System**: `pyproject.toml` entry points (`arcgis_agent.commands`, `arcgis_agent.mcp_tools`) -- no core code changes needed to add modules
4. **Service Layer**: Business logic with dependency injection -- `MapService`, `DataService`, `AnalysisService`, `ProjectService`
5. **Adapter Layer**: ABC interfaces (`IGeoProcessor`, `IMapDocument`, `IDataAccessor`) with real (`ArcPyAdapter`) and mock implementations -- never import arcpy in commands/services directly
6. **Result Model**: Standardized JSON output (`success`, `code`, `message`, `data`, `warnings`) for all commands

**Key patterns:**
- Lazy `import arcpy` inside adapter constructors, never at module level
- `importlib.metadata.entry_points()` for plugin discovery -- pip-installable third-party plugins
- `try/finally` for all arcpy resource cleanup (cursors, project locks, extension check-in)
- `arcpy.EnvManager` context manager for workspace isolation per command
- Strict stdout/stderr separation: JSON only on stdout, logs on stderr

### Critical Pitfalls

1. **arcpy import fails outside proenv** -- CLI must detect Pro Python path at startup and provide a wrapper `.bat` script. Handle in Phase 1.
2. **ArcGIS Pro license not available** -- Check license status at startup, use `CheckOutExtension`/`CheckInExtension` with `try/finally` for extensions. Handle in Phase 1.
3. **Geodatabase schema locks** -- Always close cursors with context managers, call `ClearWorkspaceCache_management()`, warn if Pro GUI is running. Handle in Phase 2.
4. **arcpy.env.workspace not set** -- Set explicitly in every command using `EnvManager` context manager. Handle in Phase 1.
5. **arcpy is NOT thread-safe** -- Never use `threading`, use `multiprocessing` or serialize calls with a lock in MCP async handlers. Handle in Phase 5 (MCP).
6. **Windows path encoding (Chinese characters)** -- Use `pathlib.Path`, set `PYTHONUTF8=1`, test with Chinese paths. Handle in Phase 1.
7. **Console output encoding** -- Force `sys.stdout.reconfigure(encoding='utf-8')` at CLI entry. Handle in Phase 1.
8. **Conda dependency conflicts** -- Clone `arcgispro-py3` env before adding packages. Handle in Phase 0.
9. **Agent subprocess invocation** -- Provide wrapper `.bat` that activates proenv. Handle in Phase 1.
10. **Plugin import side effects** -- Defer all arcpy imports to function level, never at module top. Handle in Phase 1.

## Implications for Roadmap

### Phase 0: Project Setup & Environment

**Rationale:** Everything depends on a working conda environment and proper project structure. Getting this wrong means rework later.
**Delivers:** Cloned conda env with dependencies installed, project skeleton with pyproject.toml, wrapper batch script, environment detection.

### Phase 1: CLI Foundation & Core Infrastructure

**Rationale:** Plugin system, Result model, and adapter interfaces must exist before any features.
**Delivers:** Working `arcgis-agent --help`, plugin loader, Result model, adapter ABC interfaces, mock adapters, CLI output discipline.

### Phase 2: Data Operations (Discovery + Management)

**Rationale:** Data discovery is the prerequisite for everything else -- the agent needs to know what data exists before it can process it.
**Delivers:** `data list/describe/fields/extent/count`, `data copy/delete/rename`, `data convert`, `workspace set/get`

### Phase 3: Geoprocessing Operations

**Rationale:** Core overlay/proximity analysis commands that form the backbone of GIS workflows.
**Delivers:** `data select/clip/buffer/intersect/union/dissolve/spatial-join`, `data merge/project`, `analysis summary-statistics`

### Phase 4: Map Production

**Rationale:** Map creation and export are the primary deliverables for many GIS workflows.
**Delivers:** `map create/add-layer/remove-layer/list-layers/set-extent/export`, `layout create/add-element/export`

### Phase 5: MCP Server

**Rationale:** MCP server is the AI agent integration layer. It reuses all service logic from Phases 2-4.
**Delivers:** Working MCP server that exposes all operations as MCP tools.

### Phase 6: Advanced Analysis (v1.1)

**Rationale:** Higher-complexity operations that extend the tool's capabilities. Can be added incrementally.
**Delivers:** `analysis hot-spot/cluster`, `analysis kernel-density/idw`, `analysis slope/aspect/viewshed`, network analysis commands

---
*Research completed: 2026-05-25*
*Ready for roadmap: yes*
