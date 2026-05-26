---
phase: 03-geoprocessing
plan: 05
type: execute
subsystem: geoprocessing/adapters
tags:
  - crs-check
  - overlay-operations
  - gap-closure
  - spatial-reference
requires: []
provides:
  - CRS pre-check in ArcPyGeoProcessor for multi-input overlay operations
affects:
  - intersect
  - union
  - merge
tech-stack:
  added: []
  patterns:
    - Pre-check validation pattern: adapter-level CRS consistency gate before arcpy tool call
    - UserError with custom code for structured error propagation through Result.from_exception
key-files:
  created: []
  modified:
    - src/arcgis_agent/adapters/arcpy_adapter.py
decisions:
  - "CRS pre-check placed in adapter layer (ArcPyGeoProcessor) since it requires arcpy.Describe()"
  - "Use arcpy.Describe(fc).spatialReference.factoryCode for CRS comparison"
  - "Error message includes user guidance to use 'data project' command for reprojection"
  - "Service layer unchanged; CRS_MISMATCH propagates via existing Result.from_exception path"
metrics:
  duration_seconds: 322
  tasks_completed: 1
  tasks_total: 1
  completed_date: "2026-05-26T03:03:38Z"
---

# Phase 3 Plan 5: CRS Pre-Check for Overlay Operations (Gap 1 Closure)

Adds coordinate system consistency validation to `ArcPyGeoProcessor.intersect()`, `.union()`, and `.merge()` via a new `_check_crs_match()` private method, closing VERIFICATION.md Gap 1.

## What Was Built

A `_check_crs_match(self, inputs)` method on `ArcPyGeoProcessor` that uses `arcpy.Describe(fc).spatialReference.factoryCode` to verify all input feature classes share the same CRS before overlay operations. On mismatch, it raises `UserError(code="CRS_MISMATCH")` with each input's coordinate system details and guidance to use the `data project` command.

**Key changes in `arcpy_adapter.py`:**
- New method `_check_crs_match()` (lines 15-42): Iterates inputs, collects spatial reference codes, raises `CRS_MISMATCH` if codes differ
- `intersect()` now calls `self._check_crs_match(inputs)` before `arcpy.analysis.Intersect`
- `union()` now calls `self._check_crs_match(inputs)` before `arcpy.analysis.Union`
- `merge()` now calls `self._check_crs_match(inputs)` before `arcpy.management.Merge`

**Propagation path:** `_check_crs_match` raises `UserError(code="CRS_MISMATCH")` -> caught by service layer `except Exception as e` -> `Result.from_exception(e)` -> `Result.error(code="CRS_MISMATCH", message="...")`. No service-layer changes needed.

## Verification

- All 35 existing geoprocessing service-layer tests pass with zero regressions
- `_check_crs_match` appears 4 times: 1 definition + 3 calls (intersect, union, merge)
- `CRS_MISMATCH` appears in the raise statement
- User guidance string `Use 'data project' to reproject` present in error message

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Edited main repo file instead of worktree file (#3099 absolute-path safety)**
- **Found during:** Task 1 implementation
- **Issue:** Edit/Write calls used the main repo path instead of the worktree-specific path. Edits silently wrote to the main repo copy, leaving the worktree file unchanged.
- **Fix:** Reverted the main repo file (`git checkout --`), re-applied all three edits to the worktree path (`C:\Users\...\.claude\worktrees\agent-a0d3f25c48acae105\src\...`)
- **Files modified:** `src/arcgis_agent/adapters/arcpy_adapter.py` (worktree)
- **Commit:** `4de87b2`

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: mitigated | src/arcgis_agent/adapters/arcpy_adapter.py | T-03-10 (CRS mismatch silently producing wrong overlay results) mitigated by _check_crs_match pre-check gate |

## Commits

| Hash | Message |
|------|---------|
| 4de87b2 | feat(03-05): add CRS pre-check to intersect/union/merge in ArcPyGeoProcessor |

## Threat Model Compliance

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-03-10 | mitigate | Resolved by `_check_crs_match()` gate |
| T-03-11 | accept | arcpy.Describe() failure caught by outer try/except |

## Requirements Covered

| Requirement | Description | Status |
|-------------|-------------|--------|
| GEO-04 | Intersect with CRS check | SATISFIED |
| GEO-05 | Union with CRS check | SATISFIED |
| GEO-08 | Merge with CRS check | SATISFIED |
