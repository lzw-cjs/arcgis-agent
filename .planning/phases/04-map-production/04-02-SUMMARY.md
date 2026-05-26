---
phase: 04-map-production
plan: 02
subsystem: map
tags: [mock, testing, dependency-injection, baselayoutdocument, basemapdocument]

requires:
  - phase: 04-01
    provides: IMapDocument extension + ILayoutDocument ABC
provides:
  - MockMapDocument extended with 5 call-recording stubs (remove_layer, list_layers, set_extent, symbolize_layer, set_label)
  - MockLayoutDocument with 3 call-recording stubs (create_layout, add_element, export_layout)
  - BaseService.layout_doc DI parameter and _make_layout factory
affects: [04-04, 04-05, 04-06]

tech-stack:
  added: []
  patterns:
    - "Call-recording mock pattern: self.calls.append(tuple(method_name, *args)) for every method"

key-files:
  created: []
  modified:
    - src/arcgis_agent/adapters/mock_adapter.py
    - src/arcgis_agent/services/base.py

key-decisions:
  - "MockMapDocument.list_layers returns 2 stub layer dicts with name/datasource/feature_count"
  - "MockLayoutDocument.export_layout touches output file when parent dir exists (same pattern as MockMapDocument.export_map)"
  - "BaseService._make_layout lazily imports ArcPyLayoutDocument (same pattern as _make_map/_make_data)"

requirements-completed:
  - MAP-03
  - MAP-04
  - MAP-05
  - MAP-07
  - MAP-08
  - MAP-09
  - MAP-10
  - MAP-11

duration: 8 min
completed: 2026-05-26
---

# Phase 04 Plan 02: Mock Adapters + BaseService DI Summary

**Extended MockMapDocument with 5 call-recording stubs, added MockLayoutDocument with 3 stubs, and extended BaseService with layout_doc dependency injection — enabling full unit testing of all Phase 04 services without ArcGIS Pro.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-26
- **Completed:** 2026-05-26
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- MockMapDocument extended from 4 to 9 methods with call-recording stubs
- MockLayoutDocument created with 3 methods, all recording calls for test assertions
- BaseService now accepts layout_doc parameter and has _make_layout factory
- All imports work without arcpy (mock-only environment)

## Task Commits

1. **Task 1: Extend MockMapDocument + add MockLayoutDocument** — `2a2f5ad` (feat)
2. **Task 2: Extend BaseService with layout_doc DI** — `2a2f5ad` (feat)

**Plan metadata:** `2a2f5ad`

## Files Created/Modified
- `src/arcgis_agent/adapters/mock_adapter.py` — 5 new MockMapDocument stubs, new MockLayoutDocument class
- `src/arcgis_agent/services/base.py` — layout_doc parameter, _make_layout factory, updated docstring

## Decisions Made
None — followed plan as specified.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- Mock adapters ready for Plan 04-04 (Service layer) and Plan 04-06 (unit tests)
- BaseService.layout_doc DI ready for LayoutService to use

---
*Phase: 04-map-production*
*Completed: 2026-05-26*
