# Technology Stack

**Project:** ArcGIS Pro CLI Agent
**Researched:** 2026-05-25
**Overall Confidence:** MEDIUM (training data; validate against local ArcGIS Pro 3.x installation)

---

## Recommended Stack

### Core Runtime

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.9 - 3.11 | Runtime | Must match ArcGIS Pro bundled Python. Pro 3.3+ ships 3.11; Pro 3.0-3.2 ships 3.9. Use whichever your installed Pro version provides. |
| arcpy | Matches Pro version (3.x) | GIS geoprocessing | Only available inside ArcGIS Pro's conda env. Cannot be pip-installed separately. |
| conda | Bundled with ArcGIS Pro | Package/env management | ArcGIS Pro uses conda internally. The `arcgispro-py3` env is the baseline. |

**CRITICAL CONSTRAINT:** All development and execution MUST happen inside the ArcGIS Pro conda environment. This is non-negotiable -- arcpy depends on Pro's internal DLLs and environment variables that only exist in this env.

Python path:
```
C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
```

Activation:
```bash
# Option 1: Use proenv.bat
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

# Option 2: conda activate
conda activate arcgispro-py3

# Option 3: ArcGIS Python Command Prompt (Start Menu shortcut)
```

---

### CLI Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Click | 8.1+ | CLI framework | Mature plugin system, `Group.add_command()` for dynamic plugin loading, `MultiCommand` for command discovery |

**Why Click over Typer:**

| Criterion | Click | Typer | Verdict |
|-----------|-------|-------|---------|
| Plugin architecture | `Group.add_command()` -- direct, explicit | Requires wrapping; `add_typer()` adds indirection | Click wins |
| Dynamic command loading | `MultiCommand` class for full control | Less flexible for runtime discovery | Click wins |
| Maturity | 10+ years, battle-tested | Built on Click, adds abstraction layer | Click wins |
| Type hints | Manual, but works | Native, less boilerplate | Typer wins |
| Shell completion | Manual setup | Built-in | Typer wins |
| Community patterns | Extensive examples for plugin CLIs | Fewer plugin architecture examples | Click wins |

**Decision:** Use Click. The plugin architecture requirement (entry points loading command groups at runtime) maps directly to Click's `Group.add_command()` pattern. Typer's type-hint convenience does not compensate for the added complexity when doing dynamic plugin registration.

**Do NOT use Typer** because:
- Typer is a wrapper around Click -- adds an abstraction layer without solving a problem we have
- Plugin registration via `add_typer()` is less straightforward than Click's native `add_command()`
- The "less boilerplate" benefit disappears when you need fine-grained control over command groups

---

### MCP Server

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| mcp (Python SDK) | 1.x+ | MCP server implementation | Official Anthropic SDK; includes FastMCP |
| FastMCP | Bundled in `mcp` package | High-level MCP server API | Decorator-based (`@mcp.tool()`, `@mcp.resource()`) -- minimal boilerplate |

**Install:**
```bash
pip install mcp
```

**Import:**
```python
from mcp.server.fastmcp import FastMCP
```

**Key point:** As of early 2025, FastMCP was merged into the official `mcp` Python SDK. Do NOT install `fastmcp` as a separate package -- use `pip install mcp` and import from `mcp.server.fastmcp`.

**Transport:** Use `stdio` transport for local MCP server (standard for Claude Desktop, Claude Code, and other MCP clients).

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arcgis-agent")

@mcp.tool()
def create_map(project_path: str, name: str = "Map") -> str:
    """Create a new map in an ArcGIS Pro project."""
    from arcgis_agent.services.map_service import MapService
    result = MapService().create(project_path, name)
    return result.to_json()

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Do NOT use:**
- `fastmcp` as a standalone package (merged into official SDK)
- SSE transport for local tools (stdio is simpler and standard)
- Low-level MCP SDK APIs (FastMCP covers our use case)

---

### Project Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pyproject.toml | PEP 621 | Project metadata & config | Modern standard, single source of truth |
| hatchling | Latest | Build backend | Lightweight, works well with src layout |
| pip | Bundled with conda | Package installer | Use what conda provides; do NOT fight the ArcGIS conda env |

**Do NOT use `uv`** for this project. Reason: `uv` manages its own Python installations and virtual environments, which conflicts with ArcGIS Pro's tightly coupled conda environment. Using `uv` would bypass the Pro Python env and break arcpy imports. Stick with conda/pip inside `arcgispro-py3`.

**pyproject.toml structure:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "arcgis-agent"
version = "0.1.0"
description = "AI Agent CLI for ArcGIS Pro automation"
requires-python = ">=3.9"
dependencies = [
    "click>=8.1",
    "mcp>=1.0",
]

[project.scripts]
arcgis-agent = "arcgis_agent.cli:cli"
arcgis-agent-mcp = "arcgis_agent.mcp_server:main"

[project.entry-points."arcgis_agent.commands"]
map = "arcgis_agent.commands.map:register"
data = "arcgis_agent.commands.data:register"
analysis = "arcgis_agent.commands.analysis:register"
project = "arcgis_agent.commands.project:register"
```

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| click | 8.1+ | CLI framework | Always -- primary CLI entry point |
| click-plugins | Latest | Plugin loading helpers | If needed for additional plugin ergonomics (optional) |
| mcp | 1.x+ | MCP server | Always -- MCP server entry point |
| rich | Latest | Terminal formatting | For CLI output formatting (tables, progress bars, colors) |
| pydantic | 2.x | Data validation / models | For service layer input/output models |
| logging | stdlib | Structured logging | Always -- use stdlib logging, not print |

**Optional / Phase-dependent:**

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| geopandas | Latest | DataFrame-based GIS | If converting between arcpy and pandas workflows |
| shapely | Latest | Geometry operations | If doing geometry manipulation outside arcpy |
| pytest | Latest | Testing | Always for development |
| pytest-click | Latest | Click CLI testing | Phase 1+ |

---

## Alternatives Considered

### CLI Framework

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Click 8.1+ | Typer | Adds abstraction over Click; plugin registration less direct; type-hint convenience does not offset architectural rigidity for dynamic command loading |
| Click 8.1+ | argparse (stdlib) | No built-in group/subcommand support, no plugin ecosystem, more boilerplate for complex CLIs |
| Click 8.1+ | Cement | Overkill for this use case, smaller community, less ecosystem support |

### MCP Implementation

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| mcp (FastMCP) | Low-level MCP SDK | FastMCP covers all our needs with less code; low-level API only needed for custom transports or protocol extensions |
| mcp (FastMCP) | Custom HTTP server | Reinventing the wheel; MCP is the standard protocol for AI agent tool integration |

### Package Management

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| conda + pip (inside arcgispro-py3) | uv | uv creates its own Python envs, bypasses ArcGIS conda, breaks arcpy |
| conda + pip (inside arcgispro-py3) | Poetry | Poetry manages its own venvs, same conflict as uv |
| conda + pip (inside arcgispro-py3) | pdm | Same venv conflict issue |
| hatchling (build backend) | setuptools | Hatchling is lighter, modern, well-supported |

### Data Validation

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Pydantic 2.x | attrs | Pydantic has better JSON schema generation (useful for MCP tool schemas) |
| Pydantic 2.x | dataclasses | No built-in validation, no JSON schema generation |
| Pydantic 2.x | marshmallow | Pydantic is faster (v2), better type hint integration |

---

## Installation

```bash
# 1. Open ArcGIS Python Command Prompt (Start Menu)
#    OR run: "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

# 2. Verify environment
python -c "import arcpy; print(arcpy.GetInstallInfo()['Version'])"

# 3. Install project dependencies (inside arcgispro-py3 env)
pip install click>=8.1 mcp>=1.0 rich pydantic

# 4. Install project in editable mode (after cloning)
cd path/to/arcgis-agent
pip install -e .

# 5. Verify CLI works
arcgis-agent --version
arcgis-agent --help

# 6. Verify MCP server works
python -m arcgis_agent.mcp_server
```

---

## Environment Detection Script

The CLI should detect and validate the ArcGIS Pro Python environment at startup:

```python
# arcgis_agent/env_check.py
import sys
import os

PRO_PYTHON_PATHS = [
    r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
    # Add custom paths if Pro is installed elsewhere
]

def check_environment():
    """Validate we're running in the ArcGIS Pro Python environment."""
    try:
        import arcpy
        version = arcpy.GetInstallInfo()['Version']
        return True, f"ArcGIS Pro {version} (arcpy OK)"
    except ImportError:
        return False, (
            "arcpy not found. This tool must run inside the ArcGIS Pro Python environment.\n"
            "Activate it with: proenv.bat\n"
            "Or use: conda activate arcgispro-py3"
        )
    except Exception as e:
        return False, f"arcpy error: {e}"
```

---

## Version Matrix

| Component | Minimum | Recommended | Maximum |
|-----------|---------|-------------|---------|
| ArcGIS Pro | 3.0 | 3.3+ | Latest |
| Python | 3.9 | 3.11 (matches Pro 3.3+) | 3.11 |
| Click | 8.1.0 | 8.1.x | < 9.0 |
| mcp | 1.0.0 | Latest 1.x | < 2.0 |
| Pydantic | 2.0 | 2.x latest | < 3.0 |

---

## Sources

- [ArcGIS Pro Python Environment Docs](https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/installing-python-for-arcgis-pro.htm) -- official Esri docs on conda env setup
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk) -- official Anthropic MCP SDK, includes FastMCP
- [MCP Documentation](https://modelcontextprotocol.io) -- protocol specification and quickstart guides
- [Click Documentation](https://click.palletsprojects.com/) -- official Click docs
- [Typer Documentation](https://typer.tiangolo.com/) -- for comparison reference
- [PEP 621](https://peps.python.org/pep-0621/) -- pyproject.toml project metadata standard
