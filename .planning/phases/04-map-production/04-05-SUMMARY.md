---
phase: 04-map-production
plan: 05
subsystem: cli
tags: [click, cli, commands, entry-points, map, layout]

requires:
  - phase: 04-04
    provides: MapService and LayoutService
provides:
  - commands/map.py with 8 map subcommands
  - commands/layout.py with 3 layout subcommands
  - pyproject.toml entry_points for map and layout
affects: [04-06]

tech-stack:
  added: []
  patterns:
    - "Click register pattern: register(cli_group) → @cli_group.group() → @group.command()"
    - "_run helper pattern: safe service init + Result.to_json() output"

key-files:
  created:
    - src/arcgis_agent/commands/map.py
    - src/arcgis_agent/commands/layout.py
  modified:
    - pyproject.toml

key-decisions:
  - "Map and layout are peer command groups at top level, not nested under another group (D-08)"
  - "Map create uses direct MapService instantiation (needs workspace auto-detect); other commands use _run helper"
  - "Layout export default format is PDF (map export default is PNG)"

requirements-completed:
  - MAP-01
  - MAP-02
  - MAP-03
  - MAP-04
  - MAP-05
  - MAP-06
  - MAP-07
  - MAP-08
  - MAP-09
  - MAP-10
  - MAP-11

duration: 8 min
completed: 2026-05-26
---

# Phase 04 Plan 05: CLI Commands Summary

**Created map and layout CLI command groups with 11 total subcommands, registered via pyproject.toml entry_points — exposing all Phase 04 capabilities to the AI Agent through the CLI.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-26
- **Completed:** 2026-05-26
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- commands/map.py: 8 subcommands (create, add-layer, remove-layer, list-layers, set-extent, export, symbolize, label)
- commands/layout.py: 3 subcommands (create, add-element, export)
- pyproject.toml: map entry uncommented, layout entry added (7 total entry_points)
- All commands use Click type validation (Choice types for enums) and output JSON via Result.to_json()
- Both modules export register(cli_group) for entry_points discovery

## Task Commits

1. **Task 1: commands/map.py** — `cd6f5d1` (feat)
2. **Task 2: commands/layout.py + pyproject.toml** — `cd6f5d1` (feat)

**Plan metadata:** `cd6f5d1`

## Files Created/Modified
- `src/arcgis_agent/commands/map.py` — 8 map subcommands with _run helper and register function
- `src/arcgis_agent/commands/layout.py` — 3 layout subcommands with _run helper and register function
- `pyproject.toml` — map and layout entry_points registered

## Decisions Made
None — followed plan as specified.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- CLI commands ready for Plan 04-06 (integration tests)
- All 11 commands discoverable via arcgis-agent CLI

---
*Phase: 04-map-production*
*Completed: 2026-05-26*
