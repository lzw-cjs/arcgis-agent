---
phase: 0
slug: setup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-25
---

# Phase 0 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | 手动 smoke test（环境操作不适合自动化） |
| **Config file** | none — Phase 1 搭建 pytest |
| **Quick run command** | `python -c "import arcpy; print(arcpy.GetInstallInfo()['Version'])"` |
| **Full suite command** | 手动验证全部 4 个成功标准 |
| **Estimated runtime** | ~60 秒（含 conda clone） |

---

## Sampling Rate

- **After every task commit:** 手动验证当前任务的 smoke test
- **After every plan wave:** 运行 full suite 命令
- **Before `/gsd-verify-work`:** 全部成功标准必须通过
- **Max feedback latency:** 60 秒

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 00-01-01 | 01 | 1 | ENV-01 | smoke | `python -c "import arcpy"` | N/A | ⬜ pending |
| 00-01-02 | 01 | 1 | ENV-01 | smoke | `python -c "from mcp.server.fastmcp import FastMCP"` | N/A | ⬜ pending |
| 00-02-01 | 02 | 1 | ENV-02 | smoke | `pip install -e . && arcgis-agent --version` | N/A | ⬜ pending |
| 00-03-01 | 03 | 1 | ENV-03 | smoke | `arcgis-agent.bat --version` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- 无 — Phase 0 的验证是手动 smoke test，不需要测试框架

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| conda 环境克隆后 arcpy 可导入 | ENV-01 | 需要 conda 环境激活 | `conda activate arcgis-agent && python -c "import arcpy"` |
| pip install -e . 成功 | ENV-02 | 需要 conda 环境激活 | `pip install -e . && arcgis-agent --version` |
| wrapper .bat 从干净 CMD 可运行 | ENV-03 | 需要干净 CMD 窗口 | 打开新 CMD，运行 `arcgis-agent.bat --version` |

---

## Validation Sign-Off

- [ ] 所有任务有 smoke test 验证
- [ ] 采样连续性：每个任务完成后立即验证
- [ ] Wave 0 无需求（手动验证）
- [ ] 无 watch-mode 标志
- [ ] 反馈延迟 < 60s
- [ ] `nyquist_compliant: true` 设置在 frontmatter

**Approval:** pending
