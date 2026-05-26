---
phase: 04-map-production
plan: 01
subsystem: map
tags: [abc, abstractmethod, interface, imapdocument, ilayoutdocument]

requires: []
provides:
  - IMapDocument extended with 5 new abstract methods (remove_layer, list_layers, set_extent, symbolize_layer, set_label)
  - ILayoutDocument ABC with 3 abstract methods (create_layout, add_element, export_layout)
affects: [04-02, 04-03, 04-04, 04-05, 04-06]

tech-stack:
  added: []
  patterns:
    - "ABC abstractmethod pattern: all adapter interfaces use Path params, explicit return types, ellipsis body"
    - "dict config pattern: symbology_config and label_config as dict bags for adapter methods"

key-files:
  created: []
  modified:
    - src/arcgis_agent/adapters/base.py

key-decisions:
  - "IMapDocument.symbolize_layer uses dict-based symbology_config for all 3 renderer types (Simple, UniqueValues, GraduatedColors)"
  - "ILayoutDocument.export_layout uses **kwargs for format-specific options (e.g., transparent_background for PNG)"
  - "ILayoutDocument separated from IMapDocument per D-01 decision"

requirements-completed:
  - MAP-03
  - MAP-04
  - MAP-05
  - MAP-07
  - MAP-08
  - MAP-09
  - MAP-10
  - MAP-11

duration: 5 min
completed: 2026-05-26
---

# Phase 04 Plan 01: Adapter Interface Contracts Summary

**Extended IMapDocument with 5 new abstract methods and created new ILayoutDocument ABC with 3 abstract methods — establishing the interface contracts all downstream Phase 04 implementations build against.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-26
- **Completed:** 2026-05-26
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- IMapDocument extended from 3 to 8 abstract methods: remove_layer, list_layers, set_extent, symbolize_layer, set_label
- ILayoutDocument ABC created with 3 abstract methods: create_layout, add_element, export_layout
- All methods have full type annotations following existing IGeoProcessor/IMapDocument patterns
- Both interfaces import successfully from installed package

## Task Commits

1. **Task 1: Extend IMapDocument with 5 methods** — `5a96162` (feat)
2. **Task 2: Add ILayoutDocument ABC** — `5a96162` (feat, same commit — both in base.py)

**Plan metadata:** `5a96162`

## Files Created/Modified
- `src/arcgis_agent/adapters/base.py` — IMapDocument: 5 new abstract methods (remove_layer, list_layers, set_extent, symbolize_layer, set_label); ILayoutDocument: new ABC with 3 abstract methods (create_layout, add_element, export_layout)

## Decisions Made
None — followed plan as specified.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- Interface contracts ready for Plan 04-02 (Mock adapters) and Plan 04-03 (ArcPy adapters)
- Both adapter implementations can now implement IMapDocument and ILayoutDocument against these ABCs

---
*Phase: 04-map-production*
*Completed: 2026-05-26*
