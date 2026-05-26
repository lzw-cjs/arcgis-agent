# Architecture Patterns

**Domain:** ArcGIS Pro CLI Tool with MCP Server
**Researched:** 2026-05-25

## Recommended Architecture

### Layered Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Entry Points                            │
│  ┌──────────────────┐          ┌──────────────────────────┐ │
│  │   CLI (click)    │          │   MCP Server (FastMCP)   │ │
│  │   arcgis-agent   │          │   arcgis-agent-mcp       │ │
│  └────────┬─────────┘          └────────────┬─────────────┘ │
├───────────┼─────────────────────────────────┼───────────────┤
│           │         Command Layer           │               │
│  ┌────────▼─────────────────────────────────▼─────────────┐ │
│  │              Command Registry (plugins)                 │ │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌────────────┐  │ │
│  │  │  map    │ │  data   │ │ analysis │ │  project   │  │ │
│  │  │ commands│ │ commands│ │ commands │ │  commands  │  │ │
│  │  └────┬────┘ └────┬────┘ └────┬─────┘ └─────┬──────┘  │ │
│  └───────┼───────────┼──────────┼──────────────┼──────────┘ │
├──────────┼───────────┼──────────┼──────────────┼────────────┤
│          │       Core Layer     │              │            │
│  ┌───────▼───────────▼──────────▼──────────────▼──────────┐ │
│  │                   Service Layer                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │ │
│  │  │ MapSvc   │ │ DataSvc  │ │AnalysisSvc│ │ProjectSvc │  │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │ │
│  └───────┼────────────┼────────────┼──────────────┼────────┘ │
│          │        Adapter Layer    │              │          │
│  ┌───────▼────────────▼────────────▼──────────────▼────────┐ │
│  │              ArcGIS Adapter (arcpy wrapper)              │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │  GeoProcessor  │  MapDocument  │  DataAccessor   │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  └──────────────────────────┬──────────────────────────────┘ │
├─────────────────────────────┼───────────────────────────────┤
│                      arcpy (external)                        │
└─────────────────────────────┴───────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **CLI Entry** | Parse args, dispatch to commands, format output | Command Registry |
| **MCP Entry** | Expose tools via MCP protocol, translate MCP calls | Command Registry |
| **Command Registry** | Discover/register plugins, route commands to services | Entry Points, Services |
| **Map Commands** | Map creation, layer management, symbology, export | MapService |
| **Data Commands** | Format conversion, clip, merge, projection | DataService |
| **Analysis Commands** | Buffer, overlay, spatial query | AnalysisService |
| **Project Commands** | Project CRUD, layer listing, layout management | ProjectService |
| **Service Layer** | Business logic, input validation, orchestration | Commands, Adapter |
| **ArcGIS Adapter** | Isolate arcpy, provide clean interface | Services, arcpy |

## CLI Framework: Click (not Typer)

**Recommendation: Use Click directly, not Typer.**

Rationale:
- Click has a mature plugin ecosystem (`click-plugins`, `click-group-tree`)
- Click's `MultiCommand` class gives full control over dynamic command discovery
- Typer adds a layer of abstraction that complicates plugin registration
- Click's `Group.add_command()` is exactly the pattern needed for plugin loading
- More community examples for plugin architectures

### Click Group Pattern

```python
# arcgis_agent/cli.py
import click
from arcgis_agent.plugins import load_plugins

@click.group()
@click.version_option()
def cli():
    """ArcGIS Pro CLI - AI Agent friendly GIS automation."""
    pass

# Load plugins at startup
load_plugins(cli)
```

## Plugin Architecture: Entry Points + Registry

**Recommendation: Use `importlib.metadata` entry points for external plugins, with a built-in registry for internal modules.**

### Why Entry Points

| Approach | Pros | Cons |
|----------|------|------|
| **Entry Points** | Standard Python, pip-installable plugins, no import coupling | Requires package installation |
| **pluggy** | Powerful hooks, used by pytest | Overkill for CLI commands, adds dependency |
| **Namespace packages** | Simple file-based discovery | Fragile, import ordering issues |
| **Explicit registration** | Full control | Must edit core code to add plugins |

Entry points win because:
1. Third-party plugins can be `pip install arcgis-agent-xxx` and auto-discover
2. Internal modules use the same mechanism for consistency
3. No runtime directory scanning or import tricks

### Entry Point Configuration

```toml
# pyproject.toml (core)
[project.entry-points."arcgis_agent.commands"]
map = "arcgis_agent.commands.map:register"
data = "arcgis_agent.commands.data:register"
analysis = "arcgis_agent.commands.analysis:register"
project = "arcgis_agent.commands.project:register"
```

```python
# arcgis_agent/commands/map/__init__.py
import click

def register(cli_group: click.Group):
    """Register map commands with the CLI group."""
    
    @cli_group.group("map")
    def map_group():
        """Map creation, layers, symbology, export."""
        pass
    
    @map_group.command("create")
    @click.argument("project_path")
    @click.option("--name", default="Map", help="Map name")
    def create_map(project_path, name):
        from arcgis_agent.services.map_service import MapService
        result = MapService().create(project_path, name)
        click.echo(result.to_json())
    
    # ... more commands
```

### Plugin Loader

```python
# arcgis_agent/plugins.py
import click
from importlib.metadata import entry_points

def load_plugins(cli_group: click.Group):
    """Discover and load all registered command plugins."""
    eps = entry_points()
    group_eps = eps.get("arcgis_agent.commands", [])
    
    for ep in sorted(group_eps, key=lambda e: e.name):
        try:
            register_fn = ep.load()
            register_fn(cli_group)
        except Exception as e:
            # Log but don't crash - plugin failure shouldn't kill CLI
            import logging
            logging.warning(f"Failed to load plugin '{ep.name}': {e}")
```

## CLI + MCP Server: Shared Core Logic

**Key insight: CLI and MCP are two faces of the same service layer.**

### Architecture Pattern

```
CLI Commands ──┐
               ├──> Service Layer ──> ArcGIS Adapter ──> arcpy
MCP Tools   ───┘
```

Both CLI commands and MCP tools call the same service methods. The only difference is the entry point and output format.

### MCP Server Implementation

```python
# arcgis_agent/mcp_server.py
from mcp.server.fastmcp import FastMCP
from arcgis_agent.services.map_service import MapService
from arcgis_agent.services.data_service import DataService

mcp = FastMCP("arcgis-agent")

# Register MCP tools that map to service methods
@mcp.tool()
def create_map(project_path: str, name: str = "Map") -> str:
    """Create a new map in an ArcGIS Pro project."""
    result = MapService().create(project_path, name)
    return result.to_json()

@mcp.tool()
def convert_format(input_path: str, output_path: str, 
                   output_format: str) -> str:
    """Convert GIS data between formats (shp/gdb/csv/geojson)."""
    result = DataService().convert(input_path, output_path, output_format)
    return result.to_json()

@mcp.tool()
def buffer(input_path: str, output_path: str, 
           distance: float, unit: str = "Meters") -> str:
    """Create buffer around features."""
    result = AnalysisService().buffer(input_path, output_path, 
                                      distance, unit)
    return result.to_json()
```

### MCP Plugin Discovery

MCP tools can also be plugin-based using the same entry point mechanism:

```toml
[project.entry-points."arcgis_agent.mcp_tools"]
map = "arcgis_agent.mcp_plugins.map:register_tools"
data = "arcgis_agent.mcp_plugins.data:register_tools"
```

```python
# arcgis_agent/mcp_plugins/loader.py
from mcp.server.fastmcp import FastMCP
from importlib.metadata import entry_points

def load_mcp_tools(mcp: FastMCP):
    """Register all MCP tool plugins."""
    eps = entry_points()
    for ep in eps.get("arcgis_agent.mcp_tools", []):
        register_fn = ep.load()
        register_fn(mcp)
```

## ArcGIS Adapter Layer (arcpy Isolation)

**Critical design: Never import arcpy directly in commands or services.**

### Why Isolate arcpy

1. **Testability** - arcpy requires ArcGIS Pro license and Windows; unit tests need mocks
2. **Import safety** - arcpy import fails outside ArcGIS Pro environment
3. **API stability** - Esri changes arcpy APIs between versions; isolate the blast radius
4. **Error handling** - arcpy has inconsistent error patterns; normalize them

### Adapter Interface

```python
# arcgis_agent/adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

@dataclass
class FeatureLayer:
    name: str
    path: Path
    geometry_type: str
    spatial_reference: str
    feature_count: int

class IGeoProcessor(ABC):
    """Interface for geoprocessing operations."""
    
    @abstractmethod
    def buffer(self, input_fc: str, output_fc: str, 
               distance: float, unit: str) -> Path:
        ...
    
    @abstractmethod
    def clip(self, input_fc: str, clip_fc: str, 
             output_fc: str) -> Path:
        ...
    
    @abstractmethod
    def intersect(self, inputs: list[str], output_fc: str) -> Path:
        ...

class IMapDocument(ABC):
    """Interface for map document operations."""
    
    @abstractmethod
    def create_map(self, project_path: Path, 
                   map_name: str) -> Path:
        ...
    
    @abstractmethod
    def add_layer(self, project_path: Path, map_name: str,
                  layer_path: Path) -> None:
        ...
    
    @abstractmethod
    def export_map(self, project_path: Path, map_name: str,
                   output_path: Path, format: str, 
                   dpi: int) -> Path:
        ...

class IDataAccessor(ABC):
    """Interface for data access operations."""
    
    @abstractmethod
    def list_feature_classes(self, workspace: Path) -> list[str]:
        ...
    
    @abstractmethod
    def describe(self, dataset_path: Path) -> dict[str, Any]:
        ...
    
    @abstractmethod
    def convert(self, input_path: Path, output_path: Path,
                output_format: str) -> Path:
        ...
```

### Real Implementation (wraps arcpy)

```python
# arcgis_agent/adapters/arcpy_adapter.py
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor
from pathlib import Path
from typing import Any

class ArcPyGeoProcessor(IGeoProcessor):
    """Real implementation using arcpy."""
    
    def __init__(self):
        import arcpy  # Lazy import - only when actually needed
        self._arcpy = arcpy
    
    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        try:
            self._arcpy.analysis.Buffer(
                input_fc, output_fc, 
                f"{distance} {unit}"
            )
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            raise ArcGISError(
                code="GP_BUFFER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

class ArcPyMapDocument(IMapDocument):
    """Real implementation for ArcGIS Pro projects."""
    
    def __init__(self):
        import arcpy
        self._arcpy = arcpy
    
    def create_map(self, project_path: Path, 
                   map_name: str) -> Path:
        aprx = self._arcpy.mp.ArcGISProject(str(project_path))
        aprx.createMap(map_name)
        aprx.save()
        return project_path
```

### Mock Implementation (for testing)

```python
# arcgis_agent/adapters/mock_adapter.py
from arcgis_agent.adapters.base import IGeoProcessor
from pathlib import Path

class MockGeoProcessor(IGeoProcessor):
    """Mock for unit tests - no arcpy needed."""
    
    def __init__(self):
        self.calls = []  # Track calls for assertions
    
    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        self.calls.append(("buffer", input_fc, output_fc, 
                           distance, unit))
        # Create empty output file for path validation
        Path(output_fc).touch()
        return Path(output_fc)
```

### Service Layer with Dependency Injection

```python
# arcgis_agent/services/base.py
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor

class BaseService:
    """Base service with injected adapters."""
    
    def __init__(self, 
                 gp: IGeoProcessor = None,
                 map_doc: IMapDocument = None,
                 data: IDataAccessor = None):
        # Lazy import real adapters if not injected
        self._gp = gp or self._default_gp()
        self._map = map_doc or self._default_map()
        self._data = data or self._default_data()
    
    @staticmethod
    def _default_gp():
        from arcgis_agent.adapters.arcpy_adapter import ArcPyGeoProcessor
        return ArcPyGeoProcessor()
    
    @staticmethod
    def _default_map():
        from arcgis_agent.adapters.arcpy_adapter import ArcPyMapDocument
        return ArcPyMapDocument()
    
    @staticmethod
    def _default_data():
        from arcgis_agent.adapters.arcpy_adapter import ArcPyDataAccessor
        return ArcPyDataAccessor()
```

```python
# arcgis_agent/services/map_service.py
from arcgis_agent.services.base import BaseService
from arcgis_agent.models.result import Result
from pathlib import Path

class MapService(BaseService):
    """Business logic for map operations."""
    
    def create(self, project_path: str, 
               map_name: str) -> Result:
        # Input validation (before arcpy)
        p = Path(project_path)
        if not p.exists():
            return Result.error(
                code="FILE_NOT_FOUND",
                message=f"Project not found: {project_path}"
            )
        
        if not p.suffix == ".aprx":
            return Result.error(
                code="INVALID_FORMAT",
                message="Must be an .aprx file"
            )
        
        # Call adapter
        try:
            result_path = self._map.create_map(p, map_name)
            return Result.success(
                data={"project": str(result_path), "map": map_name},
                message=f"Map '{map_name}' created"
            )
        except Exception as e:
            return Result.from_exception(e)
```

## Command Registration: Auto-Discovery with Explicit Fallback

**Recommendation: Auto-discover via entry points, with explicit registration for built-in commands.**

### Registration Flow

```
1. CLI starts
2. Plugin loader reads entry_points("arcgis_agent.commands")
3. For each entry point:
   a. Load the register() function
   b. Call register(cli_group) to add commands
   c. Log success/failure
4. CLI ready
```

### Adding a New Command Module

Step 1: Create the command file:
```python
# arcgis_agent/commands/raster/__init__.py
import click

def register(cli_group: click.Group):
    @cli_group.group("raster")
    def raster_group():
        """Raster data operations."""
        pass
    
    @raster_group.command("clip")
    @click.argument("input_raster")
    @click.argument("output_raster")
    @click.option("--extent", required=True)
    def clip_raster(input_raster, output_raster, extent):
        from arcgis_agent.services.raster_service import RasterService
        result = RasterService().clip(input_raster, output_raster, extent)
        click.echo(result.to_json())
```

Step 2: Register in pyproject.toml:
```toml
[project.entry-points."arcgis_agent.commands"]
raster = "arcgis_agent.commands.raster:register"
```

Step 3: Install: `pip install -e .`

Done. No core code modified.

### MCP Tool Registration (parallel pattern)

```toml
[project.entry-points."arcgis_agent.mcp_tools"]
raster = "arcgis_agent.mcp_tools.raster:register"
```

```python
# arcgis_agent/mcp_tools/raster.py
from mcp.server.fastmcp import FastMCP

def register(mcp: FastMCP):
    @mcp.tool()
    def clip_raster(input_raster: str, output_raster: str,
                    extent: str) -> str:
        """Clip raster to extent."""
        from arcgis_agent.services.raster_service import RasterService
        result = RasterService().clip(input_raster, output_raster, extent)
        return result.to_json()
```

## Standardized Result Object

**All commands return a `Result` object, serialized as JSON.**

```python
# arcgis_agent/models/result.py
from dataclasses import dataclass, asdict
from typing import Any, Optional
import json

@dataclass
class Result:
    success: bool
    code: str  # "OK", "FILE_NOT_FOUND", "GP_ERROR", etc.
    message: str
    data: Optional[dict[str, Any]] = None
    warnings: list[str] = None
    metadata: dict[str, Any] = None
    
    @classmethod
    def success(cls, data: dict = None, message: str = "OK") -> "Result":
        return cls(success=True, code="OK", message=message, 
                   data=data, warnings=[])
    
    @classmethod
    def error(cls, code: str, message: str, 
              data: dict = None) -> "Result":
        return cls(success=False, code=code, message=message, 
                   data=data, warnings=[])
    
    @classmethod
    def from_exception(cls, exc: Exception) -> "Result":
        # Map exception types to error codes
        ...
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
```

## Data Flow

### CLI Command Flow

```
User Input
    │
    ▼
Click Parser (arg validation, type conversion)
    │
    ▼
Command Function
    │
    ▼
Service Method (business logic, input validation)
    │
    ▼
Adapter Method (arcpy wrapper, error translation)
    │
    ▼
arcpy (actual GIS operation)
    │
    ▼
Result Object (structured output)
    │
    ▼
JSON Serialization → stdout
```

### MCP Tool Flow

```
MCP Client (AI Agent)
    │
    ▼
JSON-RPC Message
    │
    ▼
FastMCP Router (tool dispatch)
    │
    ▼
Tool Function (thin wrapper)
    │
    ▼
Service Method (same as CLI)
    │
    ▼
Adapter Method (same as CLI)
    │
    ▼
arcpy
    │
    ▼
Result Object → JSON → MCP Response
```

## Error Handling Strategy

### Error Code Taxonomy

| Code Range | Category | Example |
|------------|----------|---------|
| OK | Success | `OK` |
| 1xxx | Input Error | `FILE_NOT_FOUND`, `INVALID_FORMAT`, `PARAM_OUT_OF_RANGE` |
| 2xxx | System Error | `PERMISSION_DENIED`, `DISK_FULL`, `PYTHON_ERROR` |
| 3xxx | ArcGIS Error | `GP_BUFFER_FAILED`, `LICENSE_ERROR`, `TOOL_NOT_FOUND` |

### Exit Codes

| Code | Meaning | When |
|------|---------|------|
| 0 | Success | Operation completed |
| 1 | User Error | Bad input, missing file |
| 2 | System Error | Permission, disk, Python error |
| 3 | ArcGIS Error | arcpy failure, license issue |

## Suggested Build Order

### Phase 1: Foundation (Week 1)

1. **Project structure** - Package layout, pyproject.toml, entry points config
2. **Result model** - Standardized output format
3. **Base service** - DI pattern, adapter loading
4. **Plugin loader** - Entry point discovery
5. **CLI skeleton** - Click group, --help, --version, --json flags

### Phase 2: First Commands (Week 2)

6. **ArcGIS adapter** - IMapDocument, ArcPyMapDocument (lazy import)
7. **Map commands** - `map create`, `map list`, `map export`
8. **Project commands** - `project info`, `project list-layers`

### Phase 3: Data Operations (Week 3)

9. **Data adapter** - IDataAccessor, ArcPyDataAccessor
10. **Data commands** - `data convert`, `data describe`, `data clip`
11. **Analysis adapter** - IGeoProcessor, ArcPyGeoProcessor
12. **Analysis commands** - `analysis buffer`, `analysis intersect`

### Phase 4: MCP Server (Week 4)

13. **MCP server skeleton** - FastMCP setup, tool registration
14. **MCP plugin loader** - Entry point discovery for MCP tools
15. **MCP tool wrappers** - Mirror CLI commands as MCP tools
16. **MCP resources** - Expose project info, layer metadata

### Phase 5: Polish (Week 5)

17. **Logging** - Unified logging, --verbose/--quiet flags
18. **Config** - Project > user > global config hierarchy
19. **Error handling** - Complete error codes, arcpy message extraction
20. **Testing** - Unit tests with mock adapters, integration test skeleton

## Directory Structure

```
arcgis-agent/
├── pyproject.toml
├── src/
│   └── arcgis_agent/
│       ├── __init__.py
│       ├── cli.py                    # Click entry point
│       ├── mcp_server.py             # FastMCP entry point
│       ├── plugins.py                # Plugin loader
│       ├── commands/                  # CLI command modules
│       │   ├── __init__.py
│       │   ├── map.py
│       │   ├── data.py
│       │   ├── analysis.py
│       │   └── project.py
│       ├── mcp_tools/                # MCP tool modules
│       │   ├── __init__.py
│       │   ├── map.py
│       │   ├── data.py
│       │   └── analysis.py
│       ├── services/                  # Business logic
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── map_service.py
│       │   ├── data_service.py
│       │   ├── analysis_service.py
│       │   └── project_service.py
│       ├── adapters/                  # arcpy isolation layer
│       │   ├── __init__.py
│       │   ├── base.py               # Interfaces (ABC)
│       │   ├── arcpy_adapter.py      # Real implementation
│       │   └── mock_adapter.py       # Test implementation
│       ├── models/                    # Data models
│       │   ├── __init__.py
│       │   └── result.py
│       ├── config.py                  # Config management
│       └── exceptions.py             # Custom exceptions
└── tests/
    ├── unit/                          # Mock-based tests
    │   ├── test_commands/
    │   ├── test_services/
    │   └── conftest.py               # Mock adapter fixtures
    └── integration/                   # Real arcpy tests
        └── test_map_flow.py
```

## Anti-Patterns to Avoid

### 1. Direct arcpy Import in Commands

**Bad:**
```python
@click.command("buffer")
def buffer_cmd(input_path, output_path, distance):
    import arcpy  # DON'T
    arcpy.analysis.Buffer(input_path, output_path, distance)
```

**Good:**
```python
@click.command("buffer")
def buffer_cmd(input_path, output_path, distance):
    from arcgis_agent.services.analysis_service import AnalysisService
    result = AnalysisService().buffer(input_path, output_path, distance)
    click.echo(result.to_json())
```

### 2. God Object Adapter

**Bad:** One giant adapter class with 200 methods.

**Good:** Split by domain: GeoProcessor, MapDocument, DataAccessor.

### 3. Synchronous-Only Design

**Bad:** All operations blocking, no progress feedback.

**Good:** Long operations should support progress callbacks (for CLI progress bars and MCP progress notifications).

### 4. Hardcoded Paths

**Bad:** `C:\Users\XXX\Documents\ArcGIS\Projects\...`

**Good:** Use `pathlib.Path`, resolve relative to project or config.

## Sources

- [Click Documentation - Multi-Command CLIs](https://click.palletsprojects.com/en/stable/commands/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [importlib.metadata - Entry Points](https://docs.python.org/3/library/importlib.metadata.html)
- [pluggy - Plugin Framework](https://pluggy.readthedocs.io/)
- Esri arcpy documentation (requires ArcGIS Pro installation)
