# Phase 3: 地理处理操作 - Research

**Researched:** 2026-05-26
**Domain:** ArcPy geoprocessing tools (analysis + management)
**Confidence:** MEDIUM

## Summary

Phase 3 implements 10 geoprocessing commands (GEO-01~10) covering buffer, clip, intersect, union, dissolve, spatial join, merge, project, select-by-attribute, and summary statistics. All commands follow the established four-layer architecture (CLI -> Service -> Adapter -> ArcPy) and return structured JSON via Result.ok()/Result.error().

The IGeoProcessor interface already defines buffer/clip/intersect from Phase 1. Phase 3 extends it with 7 new methods. The ArcPyGeoProcessor and MockGeoProcessor must be updated in parallel. Two new CLI command files are needed: `geoprocessing.py` (GEO-01~09 under `data` group) and `analysis.py` (GEO-10 under `analysis` group), plus a shared `data_group.py` to resolve Click group conflicts.

**Primary recommendation:** Follow the DataManagementService pattern (Pattern A: full BaseService inheritance) for the new GeoprocessingService. Extend IGeoProcessor with all 7 new method signatures before implementing any adapter code.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Geoprocessing operations | Adapter (arcpy) | Service (validation) | ArcPy tools do the actual spatial work; service layer adds input validation and Result wrapping |
| CRS consistency check | Service | Adapter | Service layer performs pre-flight check before calling adapter; adapter raises ArcGISError if arcpy check fails |
| CLI argument parsing | Command (click) | — | Click handles all argument/option parsing, comma-splitting, field:STAT syntax |
| Output formatting | CLI (_run helper) | Service (Result) | Service returns Result object; CLI serializes to JSON via to_json() |
| License extension checkout | Adapter | Service | Adapter wraps arcpy.CheckOutExtension in try/finally; service does not manage licenses |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| arcpy | 3.4.3 (Pro install) | All geoprocessing operations | Only option for ArcGIS Pro geoprocessing |
| click | >=8.1 | CLI framework | Already used in Phase 1-2, entry_points plugin system |
| pydantic | >=2.11 | Result model | Already used for Result.ok()/Result.error() |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path handling | All path operations (Pitfall #6) |
| time | stdlib | Performance timing | Track processing time in Result.data |
| logging | stdlib | stderr logging | Verbose/debug output (never to stdout) |

### Installation

No new packages needed. All dependencies already declared in pyproject.toml. ArcPy is available via the conda environment.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct arcpy.analysis.* calls | arcpy.gp.* (geoprocessing) | analysis.* is the modern Python API; gp.* is legacy |

## Architecture Patterns

### System Architecture Diagram

```
User/Agent
    |
    v
[CLI Entry Point] -- click.argument / click.option parsing
    |
    v
[Command Layer] -- geoprocessing.py / analysis.py
    |  - parse comma-separated inputs
    |  - parse field:STAT syntax
    |  - create service instance
    v
[Service Layer] -- GeoprocessingService(BaseService)
    |  - input validation (file exists, CRS check)
    |  - Result.ok() / Result.error() wrapping
    |  - timing measurement
    v
[Adapter Layer] -- IGeoProcessor / ArcPyGeoProcessor
    |  - arcpy.analysis.* / arcpy.management.* calls
    |  - license checkout (try/finally)
    |  - ArcGISError on arcpy failure
    v
[ArcPy Runtime]
```

### Recommended Project Structure

```
src/arcgis_agent/
├── adapters/
│   ├── base.py              # IGeoProcessor: add 7 new abstract methods
│   ├── arcpy_adapter.py     # ArcPyGeoProcessor: implement 7 new methods
│   └── mock_adapter.py      # MockGeoProcessor: implement 7 new methods
├── services/
│   ├── base.py              # (unchanged) BaseService with DI
│   ├── geoprocessing.py     # NEW: GeoprocessingService (GEO-01~09)
│   └── analysis_service.py  # NEW: AnalysisService (GEO-10)
├── commands/
│   ├── data.py              # MODIFY: remove @cli_group.group("data"), use shared group
│   ├── data_group.py        # NEW: shared Click "data" subgroup
│   ├── geoprocessing.py     # NEW: GEO-01~09 commands under "data" group
│   └── analysis.py          # NEW: GEO-10 command under "analysis" group
└── models/
    └── result.py            # (unchanged) Result model
```

### Pattern A: Full BaseService (GeoprocessingService)

Follows DataManagementService pattern. Used for GEO-01~09.

```python
# Source: existing pattern from data_management.py
class GeoprocessingService(BaseService):
    """Geoprocessing operations (GEO-01 through GEO-09)."""

    def __init__(self, gp=None):
        super().__init__(gp=gp)
        # self._gp is the IGeoProcessor adapter

    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str,
               dissolve_field: str | None = None,
               no_overwrite: bool = False) -> Result:
        p_in = Path(input_fc)
        if not p_in.exists():
            return Result.error(code="FILE_NOT_FOUND",
                                message=f"Input not found: {input_fc}")
        if no_overwrite and Path(output_fc).exists():
            return Result.error(code="FILE_EXISTS",
                                message=f"Output exists: {output_fc}")
        import time
        t0 = time.perf_counter()
        try:
            result_path = self._gp.buffer(input_fc, output_fc, distance, unit,
                                          dissolve_field=dissolve_field)
            elapsed = time.perf_counter() - t0
            count = self._gp.get_count(str(result_path))
            return Result.ok(
                data={"output": str(result_path), "feature_count": count,
                      "elapsed_seconds": round(elapsed, 2)},
                message=f"Buffer created: {result_path.name}"
            )
        except Exception as e:
            return Result.from_exception(e)
```

### Pattern B: Shared Click Subgroup (data_group.py)

Resolves the conflict where both data.py and geoprocessing.py need to register under the "data" group.

```python
# Source: CONTEXT.md D-03
# data_group.py
import click

# Shared subgroup that both data.py and geoprocessing.py register into
_data_group = None

def get_data_group(cli_group: click.Group) -> click.Group:
    """Get or create the shared 'data' subgroup."""
    global _data_group
    if _data_group is None:
        @cli_group.group("data")
        def data_group():
            """Discover, inspect, and process workspace data."""
            pass
        _data_group = data_group
    return _data_group
```

### Pattern C: CLI Command with Comma-Separated Inputs

```python
# Source: CONTEXT.md D-09
@data_group.command("intersect")
@click.argument("inputs")
@click.argument("output")
@click.option("--no-overwrite", is_flag=True, default=False)
@click.pass_context
def data_intersect(ctx, inputs, output, no_overwrite):
    """Intersect multiple feature classes (GEO-04).

    INPUTS is a comma-separated list of feature class paths.
    Example: data intersect a.shp,b.shp,c.shp out.shp
    """
    input_list = [i.strip() for i in inputs.split(",")]
    from arcgis_agent.services.geoprocessing import GeoprocessingService
    svc = GeoprocessingService()
    result = svc.intersect(input_list, output, no_overwrite=no_overwrite)
    click.echo(result.to_json())
```

### Pattern D: Field:STAT Syntax Parsing

```python
# Source: CONTEXT.md D-14
def parse_stat_fields(field_spec: str) -> list[list[str]]:
    """Parse 'pop:SUM,area:MEAN' into [['pop','SUM'],['area','MEAN']]."""
    result = []
    for item in field_spec.split(","):
        parts = item.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid field:STAT syntax: '{item}'. Expected 'field:STAT'.")
        field, stat = parts[0].strip(), parts[1].strip().upper()
        valid_stats = {"SUM", "MEAN", "MIN", "MAX", "COUNT", "STD", "MEDIAN"}
        if stat not in valid_stats:
            raise ValueError(f"Invalid stat type: '{stat}'. Valid: {', '.join(sorted(valid_stats))}")
        result.append([field, stat])
    return result
```

### Anti-Patterns to Avoid

- **Top-level arcpy import:** Never import arcpy at module level. Always lazy import inside constructor or method.
- **Bare except:** Always catch specific exceptions (arcpy.ExecuteError, not bare Exception).
- **Missing try/finally for license checkout:** Extensions MUST be checked in even on failure.
- **String path concatenation:** Always use pathlib.Path for path construction.
- **Ignoring CRS mismatch:** Never silently reproject; always fail with clear error (D-10, D-16).

## ArcPy Tool Reference

### GEO-01: Select by Attribute

**ArcPy function:** `arcpy.management.SelectLayerByAttribute(in_layer_or_view, selection_type, where_clause)`

**Key details:**
- Requires a feature layer, not a feature class. Must call `arcpy.management.MakeFeatureLayer` first, then select, then `arcpy.management.CopyFeatures` to write output.
- `selection_type`: "NEW_SELECTION" (default), "ADD_TO_SELECTION", "REMOVE_FROM_SELECTION", "SUBSET_SELECTION", "SWITCH_SELECTION", "CLEAR_SELECTION"
- `where_clause`: SQL WHERE clause (e.g., `"POPULATION > 50000"`)
- Two-step process: select + copy to output. The adapter method must handle this internally.

**Suggested adapter signature:**
```python
def select_by_attribute(self, input_fc: str, output_fc: str,
                        where_clause: str) -> Path:
```

**Error code:** `GP_SELECT_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.management.SelectLayerByAttribute API]

---

### GEO-02: Clip

**ArcPy function:** `arcpy.analysis.Clip(in_features, clip_features, out_feature_class, cluster_tolerance)`

**Key details:**
- `in_features`: Input point, line, or polygon features
- `clip_features`: Must be polygon features
- `cluster_tolerance`: Optional (usually leave as default)
- Already defined in IGeoProcessor interface

**Existing adapter signature:** `def clip(self, input_fc: str, clip_fc: str, output_fc: str) -> Path`

**Error code:** `GP_CLIP_FAILED` (already defined)

**Confidence:** HIGH [VERIFIED - existing code in arcpy_adapter.py]

---

### GEO-03: Buffer

**ArcPy function:** `arcpy.analysis.Buffer(in_features, out_feature_class, buffer_distance_or_field, line_side, line_end_type, dissolve_option, dissolve_field)`

**Key details:**
- `buffer_distance_or_field`: String like `"100 Meters"` or `"500 Feet"`. The adapter formats this as `f"{distance} {unit}"`.
- `line_side`: "FULL" (default), "LEFT", "RIGHT", "OUTSIDE_ONLY" -- per D-08, NOT exposed in CLI
- `line_end_type`: "ROUND" (default), "FLAT" -- per D-08, NOT exposed in CLI
- `dissolve_option`: "NONE" (default), "LIST", "ALL"
- `dissolve_field`: List of field names when dissolve_option="LIST". Per D-07, support single `--dissolve-field` parameter.
- Valid units (D-05): Meters, Kilometers, Feet, Miles, Yards, DecimalDegrees

**Suggested adapter signature (extended):**
```python
def buffer(self, input_fc: str, output_fc: str,
           distance: float, unit: str,
           dissolve_field: str | None = None) -> Path:
```

**Internal implementation:**
```python
dist_str = f"{distance} {unit}"
if dissolve_field:
    self._arcpy.analysis.Buffer(
        input_fc, output_fc, dist_str,
        dissolve_option="LIST", dissolve_field=[dissolve_field]
    )
else:
    self._arcpy.analysis.Buffer(input_fc, output_fc, dist_str)
```

**Error code:** `GP_BUFFER_FAILED` (already defined)

**Confidence:** HIGH [VERIFIED - existing code + training knowledge of full API]

---

### GEO-04: Intersect

**ArcPy function:** `arcpy.analysis.Intersect(in_features, out_feature_class, join_attributes, cluster_tolerance, output_type)`

**Key details:**
- `in_features`: List of feature classes (e.g., `["fc1", "fc2", "fc3"]`)
- `join_attributes`: "ALL" (default), "NO_FID", "ONLY_FID"
- `cluster_tolerance`: Optional
- `output_type`: "INPUT" (default), "LINE", "POINT"
- Per D-10: pre-check CRS consistency before calling
- Per D-12: minimum 2 inputs required

**Existing adapter signature:** `def intersect(self, inputs: list[str], output_fc: str) -> Path`

**Suggested extended signature:**
```python
def intersect(self, inputs: list[str], output_fc: str,
              join_attributes: str = "ALL") -> Path:
```

**Error code:** `GP_INTERSECT_FAILED` (already defined)

**Confidence:** HIGH [VERIFIED - existing code + training knowledge of full API]

---

### GEO-05: Union

**ArcPy function:** `arcpy.analysis.Union(in_features, out_feature_class, join_attributes, gaps, cluster_tolerance)`

**Key details:**
- `in_features`: List of feature classes (minimum 2, per D-12)
- `join_attributes`: "ALL" (default), "NO_FID", "ONLY_FID"
- `gaps`: "GAPS" (default) or "NO_GAPS"
- Per D-10: pre-check CRS consistency
- Union only works with polygon features

**Suggested adapter signature:**
```python
def union(self, inputs: list[str], output_fc: str) -> Path:
```

**Error code:** `GP_UNION_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.analysis.Union API]

---

### GEO-06: Dissolve

**ArcPy function:** `arcpy.management.Dissolve(in_features, out_feature_class, dissolve_field, statistics_fields, multi_part, unsplit_lines)`

**Key details:**
- `dissolve_field`: Field name or list of field names to dissolve on
- `statistics_fields`: Optional, list like `[["POP", "SUM"], ["AREA", "MEAN"]]`
- `multi_part`: "MULTI_PART" (default) or "SINGLE_PART"
- Not exposed in CLI (D-08 context): multi_part defaults to MULTI_PART

**Suggested adapter signature:**
```python
def dissolve(self, input_fc: str, output_fc: str,
             dissolve_field: str) -> Path:
```

**Error code:** `GP_DISSOLVE_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.management.Dissolve API]

---

### GEO-07: Spatial Join

**ArcPy function:** `arcpy.analysis.SpatialJoin(target_features, join_features, out_feature_class, join_type, match_option, search_radius, distance_field_name, match_fields)`

**Key details:**
- `target_features`: Input features to receive attributes
- `join_features`: Features to join from
- `join_type`: "JOIN_ALL" (default, like LEFT JOIN) or "JOIN_COMMON" (like INNER JOIN)
- `match_option`: "INTERSECT" (default), "CLOSEST", "WITHIN", "CONTAINS", "IDENTICAL", etc.
- `search_radius`: Optional distance for "WITHIN_A_DISTANCE" match
- Two inputs (target + join), not multi-input list

**Suggested adapter signature:**
```python
def spatial_join(self, target_fc: str, join_fc: str,
                 output_fc: str) -> Path:
```

**Error code:** `GP_SPATIAL_JOIN_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.analysis.SpatialJoin API]

---

### GEO-08: Merge

**ArcPy function:** `arcpy.management.Merge(inputs, output, field_mappings)`

**Key details:**
- `inputs`: List of input feature classes (minimum 2, per D-12)
- `output`: Output feature class path
- `field_mappings`: Optional FieldMappings object for schema alignment
- Per D-12: minimum 2 inputs required
- Merge combines features from multiple datasets into one (no spatial operation, just appending)

**Suggested adapter signature:**
```python
def merge(self, inputs: list[str], output_fc: str) -> Path:
```

**Error code:** `GP_MERGE_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.management.Merge API]

---

### GEO-09: Project (Coordinate Transformation)

**ArcPy function:** `arcpy.management.Project(in_dataset, out_dataset, out_coor_system, transform_method, in_coor_system)`

**Key details:**
- `in_dataset`: Input feature class
- `out_dataset`: Output feature class
- `out_coor_system`: Target spatial reference (e.g., `arcpy.SpatialReference(4326)`)
- `transform_method`: Geographic transformation name (optional but often needed for datum changes)
- `in_coor_system`: Input CRS (optional, auto-detected from data)
- Per D-16: when ArcPy unavailable, CRS check must fail (not skip)

**Suggested adapter signature:**
```python
def project(self, input_fc: str, output_fc: str,
            spatial_reference: str) -> Path:
```

Where `spatial_reference` is a string like "4326" (WKID) or a name like "WGS 1984". The adapter creates `arcpy.SpatialReference(spatial_reference)` internally.

**Error code:** `GP_PROJECT_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.management.Project API]

---

### GEO-10: Summary Statistics

**ArcPy function:** `arcpy.analysis.Statistics(in_table, out_table, statistics_fields, case_field)`

**Key details:**
- `in_table`: Input feature class or table
- `out_table`: Output table (not feature class)
- `statistics_fields`: List of `[field_name, statistic_type]` pairs
- `case_field`: Optional field(s) to group by
- Valid statistics types (D-13): SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN
- Also available but not in D-13: VARIANCE, FIRST, LAST, RANGE, COUNT_DISTINCT
- Output is a table (not feature class), so Result.data should reflect table structure

**Suggested adapter signature:**
```python
def summary_statistics(self, input_fc: str, output_table: str,
                       statistics_fields: list[list[str]],
                       case_field: str | None = None) -> Path:
```

**Error code:** `GP_STATISTICS_FAILED`

**Confidence:** HIGH [ASSUMED - based on training knowledge of arcpy.analysis.Statistics API]

---

## Pitfalls and Mitigations

### Pitfall A: Two-Step Select (GEO-01)

**What goes wrong:** `SelectLayerByAttribute` operates on a layer, not a feature class. Directly calling it on a feature class path fails.

**Why it happens:** The tool requires a feature layer or table view as input, not a catalog path.

**How to avoid:** The adapter must:
1. Create a feature layer: `arcpy.management.MakeFeatureLayer(input_fc, "temp_layer")`
2. Select: `arcpy.management.SelectLayerByAttribute("temp_layer", "NEW_SELECTION", where_clause)`
3. Copy: `arcpy.management.CopyFeatures("temp_layer", output_fc)`
4. Clean up: `arcpy.management.Delete("temp_layer")`

**Warning signs:** Error message mentions "invalid layer" or "dataset not found".

**Confidence:** HIGH [ASSUMED - standard arcpy pattern]

---

### Pitfall B: License Extension Requirements (PITFALL #2)

**What goes wrong:** Some geoprocessing tools require specific license levels or extensions. Buffer with advanced dissolve options may require Advanced (ArcInfo) license.

**Why it happens:** ArcGIS Pro has three license levels: Basic (ArcView), Standard (ArcEditor), Advanced (ArcInfo). Some tools are restricted.

**How to avoid:**
- Most tools in GEO-01~10 work with Standard license
- Buffer, Clip, Intersect, Union, Dissolve, Merge, Project work at all license levels
- Spatial Join works at all license levels
- Statistics works at all license levels
- Use `try/except arcpy.ExecuteError` to catch license errors and return structured Result.error()

**Confidence:** MEDIUM [ASSUMED - license requirements vary by tool version; user confirmed Advanced license]

---

### Pitfall C: CRS Mismatch in Overlay Operations (PITFALL #13)

**What goes wrong:** Intersect/Union produce wrong results or fail when input layers have different coordinate systems.

**Why it happens:** ArcPy does not auto-reproject for overlay analysis.

**How to avoid (per D-10):**
```python
def _check_crs_match(self, inputs: list[str]) -> None:
    """Verify all inputs share the same spatial reference."""
    srs = []
    for fc in inputs:
        desc = self._arcpy.Describe(fc)
        sr = desc.spatialReference
        srs.append((fc, sr.factoryCode, sr.name))
    codes = set(code for _, code, _ in srs)
    if len(codes) > 1:
        details = ", ".join(f"{fc} ({name}, {code})" for fc, code, name in srs)
        raise UserError(
            code="CRS_MISMATCH",
            message=f"Input layers have different coordinate systems: {details}. "
                    f"Use 'data project' to reproject first."
        )
```

**Confidence:** HIGH [VERIFIED - PITFALLS.md documents this pattern]

---

### Pitfall D: GDB Schema Locks (PITFALL #3)

**What goes wrong:** Write operations fail with "schema lock could not be acquired" when ArcGIS Pro is open.

**How to avoid:**
- Use context managers for cursors
- Call `arcpy.ClearWorkspaceCache_management()` after operations
- Document: "Close ArcGIS Pro before running write operations"

**Confidence:** HIGH [VERIFIED - PITFALLS.md]

---

### Pitfall E: Large Dataset Memory (PITFALL #12)

**What goes wrong:** Processing large feature classes causes MemoryError.

**How to avoid:**
- Use `arcpy.GetCount_management()` to check dataset size before operations
- Add a warning (not error) for datasets > 1M features
- Let ArcPy handle internal paging (it does for most tools)

**Confidence:** MEDIUM [ASSUMED - most arcpy analysis tools handle paging internally]

---

### Pitfall F: overwriteOutput Default (PITFALL #11)

**What goes wrong:** Re-running a command fails because output already exists.

**How to avoid:**
- Support `--no-overwrite` flag (consistent with Phase 2)
- Default behavior: overwrite (set `arcpy.env.overwriteOutput = True` in adapter)

**Confidence:** HIGH [VERIFIED - PITFALLS.md, Phase 2 pattern]

---

### Pitfall G: Multi-Input Validation

**What goes wrong:** User passes only 1 input to intersect/union/merge which requires 2+.

**How to avoid (per D-12):**
```python
if len(inputs) < 2:
    return Result.error(
        code="INVALID_INPUT",
        message="At least 2 input layers required for intersect/union/merge."
    )
```

**Confidence:** HIGH [VERIFIED - CONTEXT.md D-12]

---

## Testing Strategy

### Mock Adapter Pattern

All tests use MockGeoProcessor. No ArcGIS Pro license needed.

**Extension to MockGeoProcessor:** Add 7 new methods following the existing pattern (record call in `self.calls`, return stub Path).

```python
# mock_adapter.py additions
def union(self, inputs: list[str], output_fc: str) -> Path:
    self.calls.append(("union", inputs, output_fc))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def dissolve(self, input_fc: str, output_fc: str,
             dissolve_field: str) -> Path:
    self.calls.append(("dissolve", input_fc, output_fc, dissolve_field))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def spatial_join(self, target_fc: str, join_fc: str,
                 output_fc: str) -> Path:
    self.calls.append(("spatial_join", target_fc, join_fc, output_fc))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def merge(self, inputs: list[str], output_fc: str) -> Path:
    self.calls.append(("merge", inputs, output_fc))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def project(self, input_fc: str, output_fc: str,
            spatial_reference: str) -> Path:
    self.calls.append(("project", input_fc, output_fc, spatial_reference))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def select_by_attribute(self, input_fc: str, output_fc: str,
                        where_clause: str) -> Path:
    self.calls.append(("select_by_attribute", input_fc, output_fc, where_clause))
    p = Path(output_fc)
    if p.parent.exists():
        p.touch()
    return p

def summary_statistics(self, input_fc: str, output_table: str,
                       statistics_fields: list[list[str]],
                       case_field: str | None = None) -> Path:
    self.calls.append(("summary_statistics", input_fc, output_table,
                        statistics_fields, case_field))
    p = Path(output_table)
    if p.parent.exists():
        p.touch()
    return p
```

### Test Categories

| Category | What to Test | Example |
|----------|-------------|---------|
| Service success | Result.ok with correct data keys | `svc.buffer(...)` returns `data.output`, `data.feature_count`, `data.elapsed_seconds` |
| Service validation | Result.error for bad inputs | File not found, CRS mismatch, < 2 inputs |
| Service no-overwrite | Result.error when FILE_EXISTS | `no_overwrite=True` with existing output |
| CLI integration | Click CliRunner produces valid JSON | `runner.invoke(cli, ["data", "buffer", ...])` |
| Mock adapter call recording | Correct args passed to adapter | `mock_gp.calls[0] == ("buffer", ...)` |
| Interface compliance | Mock implements IGeoProcessor | `isinstance(mock_gp, IGeoProcessor)` |

### Edge Cases per Tool

| Tool | Edge Cases |
|------|-----------|
| select | Empty WHERE clause, SQL injection attempt, no features selected |
| clip | Clip features larger than input, non-polygon clip features |
| buffer | Zero distance, negative distance, invalid unit string |
| intersect | Single input (should fail), 3+ inputs, all-empty overlap |
| union | Non-polygon inputs, self-union |
| dissolve | Non-existent field, numeric vs string field |
| spatial-join | No spatial overlap, duplicate matches |
| merge | Different schemas (field name mismatch), single input (should fail) |
| project | Same CRS (no-op), invalid WKID, unknown transformation |
| summary-stats | Non-numeric field with SUM, empty table, case_field with many groups |

## Implementation Recommendations

### Adapter Method Signatures

The IGeoProcessor interface needs 7 new abstract methods:

```python
# base.py additions to IGeoProcessor
@abstractmethod
def select_by_attribute(self, input_fc: str, output_fc: str,
                        where_clause: str) -> Path: ...

@abstractmethod
def union(self, inputs: list[str], output_fc: str) -> Path: ...

@abstractmethod
def dissolve(self, input_fc: str, output_fc: str,
             dissolve_field: str) -> Path: ...

@abstractmethod
def spatial_join(self, target_fc: str, join_fc: str,
                 output_fc: str) -> Path: ...

@abstractmethod
def merge(self, inputs: list[str], output_fc: str) -> Path: ...

@abstractmethod
def project(self, input_fc: str, output_fc: str,
            spatial_reference: str) -> Path: ...

@abstractmethod
def summary_statistics(self, input_fc: str, output_table: str,
                       statistics_fields: list[list[str]],
                       case_field: str | None = None) -> Path: ...
```

**Note:** The existing `buffer` signature needs an optional `dissolve_field` parameter added:
```python
def buffer(self, input_fc: str, output_fc: str,
           distance: float, unit: str,
           dissolve_field: str | None = None) -> Path: ...
```

### Service Layer Design

Two services:

1. **GeoprocessingService** (GEO-01~09): Full BaseService, uses `self._gp` (IGeoProcessor) and `self._data` (IDataAccessor for CRS checks via Describe).
2. **AnalysisService** (GEO-10): Partial init (like DataDiscoveryService), only needs `self._gp`.

**GeoprocessingService needs both gp and data adapters** because CRS checking requires `arcpy.Describe()` which lives in IDataAccessor (or can be done through arcpy directly in the adapter). Actually, the CRS check should be done in the adapter layer since it requires arcpy.Describe. The service just calls `self._gp.intersect(inputs, output)` which internally checks CRS.

**Revised approach:** CRS checking is an adapter responsibility (inside intersect/union methods). The service does NOT need IDataAccessor for geoprocessing. GeoprocessingService only needs IGeoProcessor.

```python
class GeoprocessingService(BaseService):
    def __init__(self, gp=None):
        super().__init__(gp=gp)
        # Only self._gp is used; self._data and self._map are initialized but unused
```

Or follow the DataDiscoveryService pattern to avoid unnecessary adapter initialization:

```python
class GeoprocessingService(BaseService):
    def __init__(self, gp=None):
        self._gp = gp if gp is not None else self._make_gp()
        self._data = None
        self._map = None
```

### pyproject.toml Changes

```toml
[project.entry-points."arcgis_agent.commands"]
workspace = "arcgis_agent.commands.workspace:register"
project = "arcgis_agent.commands.project:register"
data = "arcgis_agent.commands.data:register"
geoprocessing = "arcgis_agent.commands.geoprocessing:register"
analysis = "arcgis_agent.commands.analysis:register"
# map = "arcgis_agent.commands.map:register"
```

### CLI Command Summary

| Requirement | Command | Group | Arguments | Options |
|-------------|---------|-------|-----------|---------|
| GEO-01 | `data select` | data | `<in> <out>` | `--where` (required), `--no-overwrite` |
| GEO-02 | `data clip` | data | `<in> <clip> <out>` | `--no-overwrite` |
| GEO-03 | `data buffer` | data | `<in> <out>` | `--distance` (required), `--unit` (default Meters), `--dissolve-field`, `--no-overwrite` |
| GEO-04 | `data intersect` | data | `<inputs> <out>` | `--no-overwrite` |
| GEO-05 | `data union` | data | `<inputs> <out>` | `--no-overwrite` |
| GEO-06 | `data dissolve` | data | `<in> <out>` | `--field` (required), `--no-overwrite` |
| GEO-07 | `data spatial-join` | data | `<target> <join> <out>` | `--no-overwrite` |
| GEO-08 | `data merge` | data | `<inputs> <out>` | `--no-overwrite` |
| GEO-09 | `data project` | data | `<in> <out>` | `--sr` (required), `--no-overwrite` |
| GEO-10 | `analysis summary-stats` | analysis | `<in>` | `--field` (required, field:STAT syntax), `--case-field` |

### Error Codes

| Code | Tool | Exit Code |
|------|------|-----------|
| GP_SELECT_FAILED | Select by Attribute | 3 |
| GP_BUFFER_FAILED | Buffer | 3 |
| GP_CLIP_FAILED | Clip | 3 |
| GP_INTERSECT_FAILED | Intersect | 3 |
| GP_UNION_FAILED | Union | 3 |
| GP_DISSOLVE_FAILED | Dissolve | 3 |
| GP_SPATIAL_JOIN_FAILED | Spatial Join | 3 |
| GP_MERGE_FAILED | Merge | 3 |
| GP_PROJECT_FAILED | Project | 3 |
| GP_STATISTICS_FAILED | Statistics | 3 |
| CRS_MISMATCH | CRS check | 1 |
| INVALID_INPUT | Multi-input validation | 1 |

## Runtime State Inventory

> Not applicable -- Phase 3 is greenfield implementation, not rename/refactor/migration. No runtime state to inventory.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| arcpy | All geoprocessing | MEDIUM | 3.4.3 (Pro install) | Mock adapter for testing |
| click | CLI framework | HIGH | >=8.1 (in pyproject.toml) | -- |
| pydantic | Result model | HIGH | >=2.11 (in pyproject.toml) | -- |
| pytest | Testing | MEDIUM | installed in conda env | -- |

**Note:** arcpy availability depends on running in the arcgis-agent conda environment. Tests use Mock adapter and do not require arcpy.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (installed in conda env) |
| Config file | conftest.py (shared fixtures) |
| Quick run command | `python -m pytest tests/unit/test_geoprocessing.py -x` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEO-01 | Select by attribute with WHERE clause | unit | `pytest tests/unit/test_geoprocessing.py::test_select -x` | Wave 0 |
| GEO-02 | Clip features to boundary | unit | `pytest tests/unit/test_geoprocessing.py::test_clip -x` | Wave 0 |
| GEO-03 | Buffer with distance + unit + dissolve | unit | `pytest tests/unit/test_geoprocessing.py::test_buffer -x` | Wave 0 |
| GEO-04 | Intersect multi-input with CRS check | unit | `pytest tests/unit/test_geoprocessing.py::test_intersect -x` | Wave 0 |
| GEO-05 | Union multi-input with CRS check | unit | `pytest tests/unit/test_geoprocessing.py::test_union -x` | Wave 0 |
| GEO-06 | Dissolve by field | unit | `pytest tests/unit/test_geoprocessing.py::test_dissolve -x` | Wave 0 |
| GEO-07 | Spatial join target + join | unit | `pytest tests/unit/test_geoprocessing.py::test_spatial_join -x` | Wave 0 |
| GEO-08 | Merge multi-input | unit | `pytest tests/unit/test_geoprocessing.py::test_merge -x` | Wave 0 |
| GEO-09 | Project to different CRS | unit | `pytest tests/unit/test_geoprocessing.py::test_project -x` | Wave 0 |
| GEO-10 | Summary statistics with field:STAT | unit | `pytest tests/unit/test_analysis.py::test_summary_stats -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/unit/test_geoprocessing.py -x`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/test_geoprocessing.py` -- covers GEO-01~09
- [ ] `tests/unit/test_analysis.py` -- covers GEO-10
- [ ] `tests/unit/test_adapters.py` -- extend with new mock adapter method tests
- [ ] Framework install: `pip install pytest` if not present in conda env

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | -- |
| V3 Session Management | no | -- |
| V4 Access Control | no | -- |
| V5 Input Validation | yes | Validate WHERE clause syntax (prevent SQL injection in Select by Attribute); validate file paths exist before processing |
| V6 Cryptography | no | -- |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via WHERE clause | Tampering | Validate/sanitize WHERE clause; use arcpy's built-in SQL parser |
| Path traversal via output path | Tampering | Use pathlib to resolve and validate paths |
| Denial of service via huge datasets | DoS | Warn on datasets > 1M features; rely on arcpy internal limits |

## Sources

### Primary (HIGH confidence)
- Existing codebase: `adapters/base.py`, `arcpy_adapter.py`, `mock_adapter.py`, `services/base.py`, `services/data_management.py`, `commands/data.py`
- `.planning/REQUIREMENTS.md` -- GEO-01~10 definitions
- `.planning/phases/03-geoprocessing/03-CONTEXT.md` -- locked decisions D-01~D-17
- `.planning/phases/02-data-operations/CONTEXT.md` -- Phase 2 patterns to follow

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` -- known pitfalls and mitigations
- WebSearch: arcpy.analysis.Buffer, Intersect, Union, Clip, SpatialJoin, Statistics parameters
- WebSearch: arcpy.management.SelectLayerByAttribute, Dissolve, Merge, Project parameters

### Tertiary (LOW confidence)
- Specific license requirements for each tool (user confirmed Advanced license, so this is low-risk)
- Exact parameter names for less-common options (e.g., cluster_tolerance)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `arcpy.analysis.Buffer` accepts `dissolve_option="LIST"` and `dissolve_field` as list of strings | Buffer tool ref | Buffer dissolve feature broken; need different parameter format |
| A2 | `arcpy.management.SelectLayerByAttribute` requires MakeFeatureLayer first | Select tool ref | Select command fails; need different approach |
| A3 | All GEO-01~10 tools work with Standard (ArcEditor) license | Pitfall B | Some tools fail on Basic license; user has Advanced so low risk |
| A4 | `arcpy.analysis.Statistics` `case_field` accepts a single string or list | Statistics tool ref | Group-by feature broken; need different parameter format |
| A5 | `arcpy.management.Project` accepts WKID integer or string for `out_coor_system` | Project tool ref | CRS specification broken; need arcpy.SpatialReference object |
| A6 | CRS check via `arcpy.Describe(fc).spatialReference.factoryCode` is reliable | CRS mismatch check | CRS detection fails; need different comparison method |
| A7 | `arcpy.management.Merge` works without FieldMappings for simple same-schema merges | Merge tool ref | Merge fails for simple cases; need explicit field mapping |

## Open Questions

1. **CRS check implementation location**
   - What we know: D-10 says "pre-check CRS consistency"; D-16 says "fail when ArcPy unavailable"
   - What's unclear: Should CRS check be in adapter (has arcpy) or service (no arcpy)?
   - Recommendation: Put in adapter (intersect/union methods) since it needs arcpy.Describe. Service just calls adapter and gets Result back.

2. **Buffer dissolve_field as single field vs list**
   - What we know: D-07 says support `--dissolve-field` (singular); ArcPy accepts list
   - What's unclear: Should we support multiple dissolve fields?
   - Recommendation: Single field only (D-07 says `--dissolve-field`, singular). Pass as `[dissolve_field]` list to ArcPy.

3. **Summary statistics output format**
   - What we know: D-11 says return "output path, feature count, processing time"
   - What's unclear: Statistics produces a table, not features. What count to return?
   - Recommendation: Return table row count as "feature_count" for consistency. Include the table path.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- ArcPy is the only option, already used in Phase 1-2
- Architecture: HIGH -- patterns established in Phase 2, clear extension points
- Pitfalls: MEDIUM -- based on training knowledge of ArcPy API, not live-tested
- ArcPy API details: MEDIUM -- parameter names and formats from training knowledge, not verified against current docs

**Research date:** 2026-05-26
**Valid until:** 2026-06-26 (30 days -- ArcPy API is stable across ArcGIS Pro versions)
