---
phase: 04
slug: map-production
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/conftest.py |
| **Quick run command** | `python -m pytest tests/unit/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | MAP-01~11 | N/A | N/A | unit | `python -m pytest tests/unit/test_map_service.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_map_service.py` — stubs for MAP-01~08 (map commands)
- [ ] `tests/unit/test_layout_service.py` — stubs for MAP-09~11 (layout commands)
- [ ] `tests/unit/test_map_commands.py` — CLI integration test stubs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ArcPy symbology visual output | MAP-07 | Requires ArcGIS Pro GUI to verify renderer output | Open exported PNG, verify colors and symbols match expected |
| Layout element positioning | MAP-10 | Requires visual inspection of layout output | Export layout to PDF, verify element positions on page |
| Map export DPI quality | MAP-06 | Requires visual inspection of output resolution | Export at 96/150/300/600 DPI, compare sharpness |

*Other behaviors are testable via Mock adapters (call recording and assertions).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
