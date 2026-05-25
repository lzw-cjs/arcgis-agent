# arcgis-agent

## What This Is

一个基于 Python 的 CLI 工具，为 ArcGIS Pro 提供命令行接口，让 AI Agent（如 Claude Code）可以通过自然语言驱动 ArcGIS Pro 完成 GIS 任务。同时支持作为 MCP Server 运行，实现 Agent 与 ArcGIS Pro 的无缝集成。

目标用户：使用 AI Agent 辅助 GIS 工作的开发者和 GIS 分析师。

## Core Value

让 AI Agent 能够通过标准化 CLI 接口操控 ArcGIS Pro，实现 GIS 工作流的自动化和智能化。

## Architecture Principles

- **插件化设计**：每个功能模块（map/data/analysis/project）独立封装，新增模块不影响已有代码
- **命令注册机制**：新命令只需创建文件并注册，无需修改核心框架
- **统一接口层**：所有 arcpy 调用通过封装层隔离，业务逻辑与 ArcGIS API 解耦
- **输出标准化**：所有命令返回统一格式的 Result 对象，自动序列化为 JSON
- **测试隔离**：每个模块可独立测试，mock arcpy 不影响其他模块

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] CLI 基础框架：支持子命令结构，JSON 输出格式，插件化命令注册
- [ ] 地图生产自动化：创建/打开工程、添加图层、符号化、导出地图（PDF/PNG）
- [ ] GIS 数据处理：格式转换（shp/gdb/csv/geojson）、裁剪、合并、投影变换
- [ ] 空间分析：缓冲区分析、叠加分析（intersect/union/erase）、空间查询
- [ ] 项目管理：列出工程内容、管理图层、管理布局（Layout）
- [ ] MCP Server 模式：将 CLI 功能暴露为 MCP 工具，供 Agent 直接调用
- [ ] Agent 友好的输出：结构化 JSON 输出，包含操作结果、错误信息、元数据

### Out of Scope

- ArcGIS Server / Enterprise 远程服务管理 — 本工具聚焦本地 ArcGIS Pro 桌面操作
- 实时数据流处理 — ArcGIS Pro 不适合流处理场景
- 3D 分析（Scene） — 初期聚焦 2D 地图，3D 后续扩展
- 自定义 GP 工具开发 — 用户已有工具可通过 CLI 调用

## Context

- **技术环境**：Windows 11，ArcGIS Pro 本地安装，Python 3.x（ArcGIS Pro 自带的 conda 环境）
- **核心依赖**：arcpy（ArcGIS Pro Python 库）、click/typer（CLI 框架）、mcp（MCP SDK）
- **Agent 集成**：Claude Code 通过 Bash 工具调用 CLI，或通过 MCP 协议直接通信
- **输出格式**：所有命令默认 JSON 输出，便于 Agent 解析

## Constraints

- **平台**：仅支持 Windows — ArcGIS Pro 仅在 Windows 上运行
- **Python 版本**：必须兼容 ArcGIS Pro 自带的 Python 环境（通常是 3.9+）
- **依赖**：核心功能仅依赖 arcpy，额外依赖尽量最小化
- **许可证**：需要 ArcGIS Pro 有效许可证才能运行
- **扩展性**：新增功能必须通过插件/模块方式添加，不修改已有代码

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Click/Typer | ArcPy 原生 Python，CLI 框架成熟 | — Pending |
| JSON 输出格式 | Agent 解析最方便，结构化数据 | — Pending |
| CLI + MCP 双模式 | CLI 可独立使用，MCP 供 Agent 深度集成 | — Pending |
| 子命令按功能分组 | map/data/analysis/project 四大类，清晰易用 | — Pending |
| 插件化架构 | 新增功能不影响已有代码，模块独立可测试 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-25 after initialization*
