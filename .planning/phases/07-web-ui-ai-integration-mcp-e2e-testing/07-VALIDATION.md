---
phase: 7
slug: web-ui-ai-integration-mcp-e2e-testing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend) + vitest (frontend) |
| **Config file** | pyproject.toml (pytest), vitest.config.ts (frontend) |
| **Quick run command** | `pytest tests/unit/ -x -q` |
| **Full suite command** | `pytest tests/ -v --cov=src/arcgis_agent` |
| **E2E command** | `pytest tests/e2e/ -v` |
| **Frontend test command** | `cd web && npx vitest run` |
| **Estimated runtime** | ~30s (unit), ~120s (full), ~180s (E2E) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/ -x -q`
- **After every plan wave:** Run full suite + frontend tests
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | D-01~08 | T-07-01 | arcpy 串行化锁复用，localhost only 无认证 | unit | `pytest tests/unit/api/ -q` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | D-23~27 | T-07-02 | API Key 后端保存，LLM 代理不泄露 | unit | `pytest tests/unit/adapters/test_llm.py -q` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 3 | D-16~22 | T-07-03 | API Key 前端环境变量，不提交到仓库 | vitest | `cd web && npx vitest run` | ❌ W0 | ⬜ pending |
| 07-04-01 | 04 | 4 | D-28~31 | N/A | E2E 测试隔离，不操作生产数据 | e2e | `pytest tests/e2e/ -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/api/` — REST API 单元测试目录
- [ ] `tests/unit/adapters/test_llm.py` — LLM Adapter 单元测试
- [ ] `tests/e2e/` — MCP E2E 测试目录
- [ ] `tests/e2e/conftest.py` — MCP ClientSession fixtures
- [ ] `web/vitest.config.ts` — 前端测试配置
- [ ] `web/src/__tests__/` — 前端测试目录

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ArcGIS 地图渲染 | D-18, D-19 | 需要真实 API Key + 浏览器环境 | 启动前端，验证地图组件加载，确认可折叠面板交互 |
| Claude Code MCP 集成 | D-30 | 需要 Claude Code 客户端 | 按手动测试清单逐项验证，记录结果 |
| SSE 进度推送 | D-13 | 需要浏览器 EventSource | 触发长时操作（buffer/export），观察进度更新 |
| 中文路径 arcpy.mp | D-02 | 已知 bug，需实际环境验证 | 使用中文用户名系统测试 Map/Layout 操作 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
