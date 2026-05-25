---
phase: 01-cli
plan: 02
subsystem: cli
tags: [click, entry-points, logging, utf-8, plugins]

# Dependency graph
requires:
  - phase: 01-cli/01
    provides: "Result model (from_exception, to_json) and exception hierarchy (UserError, SystemError_, ArcGISError)"
provides:
  - "Click CLI group with --help/--version/--json/--verbose/--quiet global options"
  - "Plugin loader via importlib.metadata entry_points(group='arcgis_agent.commands')"
  - "Logging configuration with verbose/quiet level control, output to stderr"
  - "main() entry point with exception-to-exit-code mapping (1/2/3)"
  - "UTF-8 stdout/stderr reconfigure at CLI entry"
affects: [01-cli/03, 01-cli/04, 01-cli/05, phase-02, phase-03, phase-04, phase-05]

# Tech tracking
tech-stack:
  added: [importlib.metadata]
  patterns: [plugin-loader-entry-points, invoke-without-command, lazy-import-in-callback, exception-exit-code-mapping]

key-files:
  created:
    - src/arcgis_agent/logging_config.py
    - src/arcgis_agent/plugins.py
  modified:
    - src/arcgis_agent/cli.py
    - src/arcgis_agent/__main__.py
    - pyproject.toml

key-decisions:
  - "invoke_without_command=True so --verbose/--quiet conflict check runs even without a subcommand"
  - "Lazy imports of logging_config and plugins inside cli() callback (after UTF-8 reconfigure)"
  - "main() catches Exception and uses isinstance checks for exit code mapping (not except chain)"

patterns-established:
  - "Plugin loader: entry_points(group='arcgis_agent.commands'), sorted load order, warning on failure, never crash"
  - "Logging: all output to stderr, root.handlers.clear() prevents duplicates"
  - "CLI entry: sys.stdout/stderr.reconfigure(encoding='utf-8', errors='replace') at module level"

requirements-completed: [CLI-01, CLI-02, CLI-04, CLI-05, CLI-06]

# Metrics
duration: 7min
completed: 2026-05-25
---

# Phase 1 Plan 02: CLI Framework Summary

**Click group with --help/--version/--json/--verbose/--quiet, plugin loader via entry_points, logging to stderr, and exit code mapping via main()**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-25T14:48:10Z
- **Completed:** 2026-05-25T14:55:17Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Full Click CLI group with 5 global options (--help, --version, --json, --verbose, --quiet)
- Plugin loader discovers commands via importlib.metadata entry_points, catches failures gracefully
- Logging system outputs to stderr only, level controlled by --verbose (DEBUG) / --quiet (ERROR) / default (WARNING)
- main() entry point maps UserError/SystemError_/ArcGISError to exit codes 1/2/3 with JSON output
- UTF-8 forced on stdout/stderr at module level to prevent Windows GBK encoding crashes

## Task Commits

Each task was committed atomically:

1. **Task 1: Create logging_config.py and plugins.py** - `b95f9ed` (feat)
2. **Task 2: Rewrite cli.py with Click group and exit code mapping** - `be0d0c5` (feat)

## Files Created/Modified
- `src/arcgis_agent/logging_config.py` - Logging setup with verbose/quiet level control, output to stderr
- `src/arcgis_agent/plugins.py` - Plugin loader via importlib.metadata entry_points, catches failures
- `src/arcgis_agent/cli.py` - Click group with all global options, main() with exit code mapping, UTF-8 reconfigure
- `src/arcgis_agent/__main__.py` - Updated to import main() instead of cli()
- `pyproject.toml` - Entry point changed from cli:cli to cli:main

## Decisions Made
- Used `invoke_without_command=True` on the Click group so that `--verbose`/`--quiet` conflict detection works even when no subcommand is given (without this, Click raises "Missing command" before the callback runs)
- Used lazy imports of `logging_config` and `plugins` inside the `cli()` callback to ensure UTF-8 reconfigure happens first
- Used `isinstance` chain in `main()` instead of multiple `except` blocks to avoid Python's exception ordering issues with inheritance

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Click group callback not invoked without subcommand**
- **Found during:** Task 2 (CLI verification)
- **Issue:** Default `@click.group()` only invokes the callback when a subcommand is present. The `--verbose --quiet` conflict check never ran without a subcommand, causing Click to show "Missing command" instead of the mutual exclusivity error.
- **Fix:** Changed to `@click.group(invoke_without_command=True)` and added `if ctx.invoked_subcommand is None: click.echo(ctx.get_help())` to preserve the default "show help when no subcommand" behavior.
- **Files modified:** src/arcgis_agent/cli.py
- **Verification:** `--verbose --quiet` now correctly exits with code 1 and "mutually exclusive" message; no subcommand shows help.
- **Committed in:** be0d0c5

**2. [Note] Commit be0d0c5 included pre-staged adapter files**
- **Found during:** Post-commit review
- **Issue:** The commit included `adapters/arcpy_adapter.py` and `adapters/mock_adapter.py` which were pre-staged from a prior plan (01-03) execution context. These files are valid code but not part of this plan's scope.
- **Fix:** No action needed - the adapter files are correct and will be used by plan 01-03.
- **Impact:** None - no functional impact, just slightly larger commit than expected.

---

**Total deviations:** 1 auto-fixed (blocking), 1 note
**Impact on plan:** The invoke_without_command fix is essential for correct CLI behavior. The pre-staged files have no impact.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CLI framework complete, ready for subcommand registration
- Plugin loader in place for future command modules
- Plan 01-03 (Adapter interfaces) can proceed
- Plan 01-04 (BaseService + env check) can proceed

## Self-Check: PASSED

- All 5 created/modified files verified present
- Both commit hashes (b95f9ed, be0d0c5) verified in git log

---
*Phase: 01-cli*
*Completed: 2026-05-25*
