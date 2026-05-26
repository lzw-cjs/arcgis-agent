# Phase 2 Context: Data Operations (Discovery + Management)

## Goal

Implement data discovery and management commands, enabling AI Agents to understand and operate on workspace data.

## Requirements (from REQUIREMENTS.md)

### Workspace & Project (PROJ)

- **PROJ-01**: `workspace set <path>` — Set current workspace
- **PROJ-02**: `workspace get` — Get current workspace
- **PROJ-03**: `project info` — View current project info (path, GDB, map list)

### Data Discovery (DISC)

- **DISC-01**: `data list` — List datasets in workspace (with filtering)
- **DISC-02**: `data describe <path>` — Describe dataset metadata (type, CRS, record count)
- **DISC-03**: `data fields <path>` — List field info (name, type, length)
- **DISC-04**: `data extent <path>` — Get spatial extent (xmin/ymin/xmax/ymax)
- **DISC-05**: `data count <path>` — Get record count

### Data Management (MGMT)

- **MGMT-01**: `data copy <src> <dst>` — Copy dataset
- **MGMT-02**: `data delete <path>` — Delete dataset
- **MGMT-03**: `data rename <old> <new>` — Rename dataset
- **MGMT-04**: `data convert <src> <dst> --format` — Format conversion (shp/gdb/csv/geojson)

## Existing Codebase

### Adapter Layer (src/arcgis_agent/adapters/)

- **IDataAccessor** (base.py): `list_feature_classes`, `describe`, `convert`
- **ArcPyDataAccessor** (arcpy_adapter.py): Real arcpy implementation
- **MockDataAccessor** (mock_adapter.py): Mock for testing
- **IGeoProcessor**: `buffer`, `clip`, `intersect` (Phase 3, already defined)
- **IMapDocument**: `create_map`, `add_layer`, `export_map` (Phase 4, already defined)

### Service Layer (src/arcgis_agent/services/)

- **BaseService**: DI with gp, map_doc, data adapters

### CLI (src/arcgis_agent/)

- **cli.py**: Click group with --json, --verbose, --quiet
- **plugins.py**: Entry point plugin loader
- **models/result.py**: Result.ok(), Result.error(), Result.from_exception()
- **exceptions.py**: UserError, FileNotFoundError_, InvalidFormatError, ArcGISError

### pyproject.toml entry_points

```toml
[project.entry-points."arcgis_agent.commands"]
# Currently all commented out
```

## Key Design Decisions (from ARCHITECTURE.md)

1. Four-layer architecture: Entry → Command → Service → Adapter
2. CLI and MCP share Service layer
3. All commands return Result (JSON to stdout)
4. Lazy import arcpy inside constructor
5. Mock adapters for testing without ArcGIS Pro

## Pitfalls to Handle (from PITFALLS.md)

- **Pitfall #3**: GDB schema locks — use context managers, ClearWorkspaceCache
- **Pitfall #4**: workspace not set — explicit workspace in every command, EnvManager
- **Pitfall #6**: Chinese path encoding — pathlib, PYTHONUTF8=1
- **Pitfall #11**: overwriteOutput defaults to False — set True by default, --no-overwrite flag

## Scope Decisions

### In Scope

- workspace set/get (config-based, persisted)
- project info (read-only, no create/open/save — that's Phase 4)
- data list/describe/fields/extent/count (read operations)
- data copy/delete/rename/convert (write operations)

### Out of Scope (Phase 3+)

- Geoprocessing (buffer, clip, intersect) — Phase 3
- Map production — Phase 4
- MCP Server — Phase 5

## Plan Structure Recommendation

Split into 2-3 plans:

1. **02-01**: Adapter extensions + Workspace/Project service + commands
2. **02-02**: Data Discovery service + commands (list/describe/fields/extent/count)
3. **02-03**: Data Management service + commands (copy/delete/rename/convert) + tests

Or possibly 2 plans if scope is manageable.

## Testing Strategy

- All tests use Mock adapters (no ArcGIS Pro needed)
- CLI tests use click.testing.CliRunner
- Test both success and error paths
- Test with Chinese paths
- Test workspace isolation
