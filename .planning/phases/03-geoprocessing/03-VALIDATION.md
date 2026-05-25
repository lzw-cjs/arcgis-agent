---
phase: 3
slug: geoprocessing
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | conftest.py (shared fixtures) |
| **Quick run command** | `python -m pytest tests/unit/test_geoprocessing.py -x` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit/test_geoprocessing.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | GEO-01 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_select -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | GEO-02 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_clip -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | GEO-03 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_buffer -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | GEO-04 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_intersect -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 1 | GEO-05 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_union -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 1 | GEO-06 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_dissolve -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 1 | GEO-07 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_spatial_join -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 1 | GEO-08 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_merge -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 1 | GEO-09 | — | N/A | unit | `pytest tests/unit/test_geoprocessing.py::test_project -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 1 | GEO-10 | — | N/A | unit | `pytest tests/unit/test_analysis.py::test_summary_stats -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> **Nyquist deviation:** Test files are created in Plan 04 (Wave 3), not Wave 0.
> Waves 1-2 verify via import checks and grep for method/function definitions.
> This is acceptable for infrastructure phases where adapter/service/CLI layers
> are built before tests. Plan 04 provides full pytest coverage.

- [x] Framework: pytest already available in conda env
- [ ] `tests/unit/test_geoprocessing.py` — created in Plan 04 (Wave 3)
- [ ] `tests/unit/test_analysis.py` — created in Plan 04 (Wave 3)
- [ ] `tests/unit/test_adapters.py` — extended in Plan 04 (Wave 3)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CRS mismatch error message clarity | GEO-04/05 | Error message quality is subjective | Run `data intersect` with mismatched CRS inputs, verify error message names the CRS values |
| Large dataset performance | GEO-01~09 | Performance thresholds are environment-dependent | Run buffer on 100K+ features, verify completes within 60s |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (Waves 1-2 use import/grep checks)
- [x] Sampling continuity: Waves 1-2 verify via import/grep; Wave 3 adds pytest
- [x] Wave 0 covers all MISSING references (pytest already installed)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-26
