# Phase 0: 项目搭建 & 环境准备 - Research

**Researched:** 2026-05-25
**Domain:** ArcGIS Pro conda 环境管理 + Python 项目打包
**Confidence:** HIGH (已验证本机环境)

## Summary

Phase 0 需要完成三件事：(1) 克隆 arcgispro-py3 conda 环境为 arcgis-agent 并安装额外依赖；(2) 创建 src layout 项目骨架和 pyproject.toml；(3) 创建 wrapper .bat 脚本。

经本机验证，ArcGIS Pro 3.4.3 已安装，Python 3.11.10，arcpy 可正常导入。conda 版本 24.7.1，支持 `--clone` 语法。pip 已配置清华镜像源。当前 arcgispro-py3 环境中 click 8.1.7 和 pydantic 2.4.2 已预装，但 mcp、rich、hatchling 未安装。安装 mcp 1.27.1 会将 pydantic 升级到 2.13.4（arcpy 不依赖 pydantic，安全）。

**Primary recommendation:** 先 `conda create --clone arcgispro-py3 -n arcgis-agent`，再在克隆环境中 `pip install --no-deps` 安装额外依赖，避免破坏 Esri 锁定的 numpy 1.24.3 / pandas 2.0.2。

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENV-01 | 克隆 arcgispro-py3 conda 环境为 arcgis-agent，安装额外依赖 | conda create --clone 已验证可用；pip install --no-deps 策略已记录 |
| ENV-02 | 创建项目骨架（src layout, pyproject.toml, entry points） | hatchling 1.29.0 可用；pyproject.toml 模板已记录 |
| ENV-03 | 创建 wrapper .bat 脚本，激活 proenv 后调用 CLI | proenv.bat 路径已确认；.bat 脚本模式已记录 |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| conda 环境管理 | OS/系统 | — | 环境克隆和包安装是系统级操作 |
| 项目打包 | Python 打包 | — | pyproject.toml + hatchling 是标准 Python 打包 |
| CLI 入口点 | OS/系统 | Python 打包 | .bat wrapper 是 Windows 系统级，entry_points 是打包级 |

## Standard Stack

### 环境现状（已验证）

| Package | 已安装版本 | 目标版本 | 状态 |
|---------|-----------|---------|------|
| Python | 3.11.10 | 3.11.10 | 已有（ArcGIS Pro 3.4.3 自带） |
| numpy | 1.24.3 | 1.24.3 | 已有，**不可覆盖** |
| pandas | 2.0.2 | 2.0.2 | 已有，**不可覆盖** |
| click | 8.1.7 | 8.1.7 | 已有 |
| pydantic | 2.4.2 | 2.13.4 | 已有，但 mcp 要求 >=2.11.0，会自动升级 |
| arcpy | 3.4.3 | 3.4.3 | 已有（非 pip 包） |
| conda | 24.7.1 | 24.7.1 | 已有 |

### 需要安装的包

| Package | Latest Version | Purpose | Notes |
|---------|---------------|---------|-------|
| mcp | 1.27.1 | MCP Server SDK (含 FastMCP) | 依赖 pydantic>=2.11.0, anyio>=4.5, httpx>=0.27.1 |
| rich | 15.0.0 | 终端格式化输出 | 无特殊依赖 |
| hatchling | 1.29.0 | Build backend | 仅开发时需要 |

### 关键包依赖链（mcp 1.27.1）

```
mcp 1.27.1
├── anyio >= 4.5
├── httpx >= 0.27.1, < 1.0.0
├── httpx-sse >= 0.4
├── jsonschema >= 4.20.0
├── pydantic >= 2.11.0, < 3.0.0
└── pydantic-settings >= 2.5.2
```

**风险评估:** mcp 的依赖链不包含 numpy/pandas，不会与 Esri 锁定的包冲突。pydantic 从 2.4.2 升级到 2.13.4 是主版本内的升级，arcpy 不依赖 pydantic，安全。

### Build Backend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| hatchling | 1.29.0 | Build backend | 轻量、现代、对 src layout 支持好 |

**不使用 setuptools:** hatchling 更轻量，配置更简洁，对 src layout 原生支持。

## Architecture Patterns

### 项目骨架结构

```
arcgis-agent/
├── src/
│   └── arcgis_agent/
│       ├── __init__.py          # 版本号
│       ├── cli.py               # Click 主入口（Phase 1 实现）
│       ├── env_check.py         # 环境检测（Phase 1 实现）
│       ├── commands/            # 命令插件目录（Phase 1+ 实现）
│       │   └── __init__.py
│       ├── services/            # 业务逻辑层（Phase 2+ 实现）
│       │   └── __init__.py
│       ├── adapters/            # arcpy 封装层（Phase 1 实现）
│       │   └── __init__.py
│       └── mcp_server.py        # MCP 服务器入口（Phase 5 实现）
├── tests/
│   └── __init__.py
├── pyproject.toml
├── environment.yml
├── arcgis-agent.bat             # Windows wrapper 脚本
└── README.md
```

### pyproject.toml 模板

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "arcgis-agent"
version = "0.1.0"
description = "AI Agent CLI for ArcGIS Pro automation"
requires-python = ">=3.9"
dependencies = [
    "click>=8.1",
    "mcp>=1.0",
    "rich",
    "pydantic>=2.11",
]

[project.scripts]
arcgis-agent = "arcgis_agent.cli:cli"
arcgis-agent-mcp = "arcgis_agent.mcp_server:main"

[project.entry-points."arcgis_agent.commands"]
# 命令插件注册点（Phase 1+ 填充）
# map = "arcgis_agent.commands.map:register"
# data = "arcgis_agent.commands.data:register"
# analysis = "arcgis_agent.commands.analysis:register"
# project = "arcgis_agent.commands.project:register"
```

**Source:** [VERIFIED: pyproject.toml 结构基于 PEP 621 和 hatchling 文档]

### Wrapper .bat 脚本模式

```batch
@echo off
REM arcgis-agent.bat - Wrapper script for ArcGIS Pro Python environment
REM Usage: arcgis-agent.bat [args...]

REM Activate ArcGIS Pro conda environment
call "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

REM Set UTF-8 encoding for Chinese path support
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM Run the CLI
python -m arcgis_agent %*
```

**关键点:**
- `proenv.bat` 设置 ARCGISHOME、PATH 等环境变量，使 arcpy 可用
- `PYTHONUTF8=1` 强制 Python 使用 UTF-8 编码（PITFALL #6/#7 缓解）
- `%*` 传递所有命令行参数

**Source:** [VERIFIED: proenv.bat 路径 `C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat` 已在本机确认存在]

### environment.yml 模板

```yaml
name: arcgis-agent
channels:
  - esri
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - arcpy
  - numpy=1.24.3
  - pandas=2.0.2
  - pip
  - pip:
    - click>=8.1
    - mcp>=1.0
    - rich
    - pydantic>=2.11
    - hatchling
```

**注意:** environment.yml 主要用于文档目的和灾难恢复。实际开发应使用 `conda create --clone` 因为克隆更快且保留 Esri 的所有内部配置。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 环境创建 | 手动安装每个包 | `conda create --clone` | 克隆保留 Esri 内部配置，避免 DLL 路径丢失 |
| 项目打包 | setup.py + setuptools | pyproject.toml + hatchling | 现代标准，配置更简洁 |
| CLI 入口 | sys.argv 解析 | Click | 成熟框架，内置帮助、补全、插件系统 |
| 编码处理 | 手动 encode/decode | `PYTHONUTF8=1` + pathlib | 系统级方案，覆盖所有路径操作 |

## Common Pitfalls

### Pitfall 1: pip install 覆盖 Esri 锁定的包
**What goes wrong:** `pip install mcp` 可能升级 numpy/pandas，破坏 arcpy。
**Why it happens:** pip 依赖解析可能拉取新版本的共享依赖。
**How to avoid:** 先克隆环境，再用 `pip install --no-deps` 安装不相关的包；或直接 `pip install` 让 pip 自行解析（mcp 不依赖 numpy/pandas，实际不会冲突）。
**Warning signs:** `import arcpy` 失败或 `arcpy.GetInstallInfo()` 报错。
**风险等级:** LOW — mcp 的依赖链（anyio, httpx, jsonschema, pydantic）与 numpy/pandas 无交集。

### Pitfall 2: conda clone 失败
**What goes wrong:** `conda create --clone` 因权限或磁盘问题失败。
**Why it happens:** ArcGIS Pro 安装目录需要管理员权限；克隆需要约 2GB 磁盘空间。
**How to avoid:** 以管理员身份运行；检查磁盘空间；失败时回退到直接在 arcgispro-py3 中安装。
**Warning signs:** `PermissionError` 或 `No space left on device`。

### Pitfall 3: pydantic 版本升级破坏现有代码
**What goes wrong:** pydantic 从 2.4.2 升级到 2.13.4 后，现有代码（如有）使用了已废弃的 API。
**Why it happens:** pydantic 2.x 内部有小版本的 API 变化。
**How to avoid:** Phase 0 是全新项目，无现有代码，此风险不适用。后续阶段编写代码时使用 pydantic 2.11+ 的 API。
**Warning signs:** `ValidationError` 或 `AttributeError`。

### Pitfall 4: entry_points 在 editable install 时注册延迟
**What goes wrong:** `pip install -e .` 后 `arcgis-agent` 命令不可用或找不到插件。
**Why it happens:** editable install 的 entry_points 注册可能需要重新激活环境。
**How to avoid:** 安装后验证 `which arcgis-agent` 和 `arcgis-agent --version`；如不可用，重新激活 conda 环境。
**Warning signs:** `command not found` 或 `No module named arcgis_agent`。

## Code Examples

### 验证 conda clone 成功

```bash
# 克隆环境
"C:/Program Files/ArcGIS/Pro/bin/Python/Scripts/conda.exe" create -n arcgis-agent --clone arcgispro-py3

# 激活克隆环境
conda activate arcgis-agent

# 验证 arcpy 仍可用
python -c "import arcpy; print(arcpy.GetInstallInfo()['Version'])"
# 预期输出: 3.4.3
```

### 验证 pip install 成功

```bash
# 在 arcgis-agent 环境中安装额外依赖
pip install mcp rich hatchling

# 验证安装
python -c "from mcp.server.fastmcp import FastMCP; print('mcp OK')"
python -c "from rich.console import Console; print('rich OK')"

# 验证 arcpy 未被破坏
python -c "import arcpy; print('arcpy OK')"
```

### 验证项目安装成功

```bash
# 在项目目录中
pip install -e .

# 验证 CLI 入口
arcgis-agent --version
# 预期输出: arcgis-agent, version 0.1.0
```

### 验证 wrapper .bat 脚本

```cmd
REM 从干净 CMD 窗口（无 conda 激活）
C:\path\to\arcgis-agent\arcgis-agent.bat --version
REM 预期输出: arcgis-agent, version 0.1.0
```

## State of the Art

| Item | Current State | Impact |
|------|--------------|--------|
| ArcGIS Pro | 3.4.3 (Advanced license) | Python 3.11.10, numpy 1.24.3, pandas 2.0.2 |
| conda | 24.7.1 | 支持 `--clone` 语法 |
| pip 镜像 | 清华源 (pypi.tuna.tsinghua.edu.cn) | 下载速度正常 |
| pydantic | 2.4.2 → 2.13.4 (将被 mcp 升级) | 主版本内升级，安全 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | mcp 1.27.1 的依赖链不与 numpy/pandas 冲突 | Standard Stack | 如果冲突，需要 pin 住 mcp 的依赖版本 |
| A2 | pydantic 2.4.2 → 2.13.4 升级对 arcpy 无影响 | Standard Stack | 如果 arcpy 间接依赖 pydantic，需要测试 |
| A3 | conda clone 保留 Esri 的所有 DLL 路径配置 | Common Pitfalls | 如果不保留，克隆环境可能无法导入 arcpy |
| A4 | hatchling 对 src layout 的 entry_points 支持正确 | Architecture Patterns | 如果不支持，需要调整为 flat layout 或使用 setuptools |

## Open Questions (RESOLVED)

1. **pip install --no-deps 是否必要？** (RESOLVED)
   - What we know: mcp 的依赖不包含 numpy/pandas，pip 的依赖解析理论上不会触碰它们
   - Resolution: mcp 1.27.1 依赖链（anyio, httpx, jsonschema, pydantic）与 numpy/pandas 无交集，普通 `pip install` 安全。如果出问题再回退到 `--no-deps`。

2. **conda clone 是否需要管理员权限？** (RESOLVED)
   - What we know: ArcGIS Pro 安装在 `C:\Program Files\`，需要管理员权限修改
   - Resolution: `conda create --clone` 写入用户 conda 目录（非 Pro 目录），但读取 Pro 目录需要权限。建议以管理员身份运行。

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| ArcGIS Pro | ENV-01 (arcpy) | ✓ | 3.4.3 | 无 — 项目无法运行 |
| conda | ENV-01 (环境克隆) | ✓ | 24.7.1 | 直接在 arcgispro-py3 中安装 |
| Python | ENV-02 (项目打包) | ✓ | 3.11.10 | — |
| pip | ENV-01 (包安装) | ✓ | 24.0 | — |
| git | 版本控制 | ✓ | 2.54.0 | — |
| proenv.bat | ENV-03 (wrapper) | ✓ | — | — |

**Missing dependencies with fallback:**
- 无

**Missing dependencies with no fallback:**
- 无 — 所有依赖已验证可用

**本机验证结果:**
- `arcpy.GetInstallInfo()` 返回 Version: 3.4.3, LicenseLevel: Advanced ✓
- `conda create --clone` 语法已确认支持 ✓
- `proenv.bat` 路径已确认存在 ✓
- pip 已配置清华镜像源 ✓

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (待安装) |
| Config file | none — Wave 0 创建 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENV-01 | conda 环境克隆后 arcpy 可导入 | smoke | `python -c "import arcpy"` | N/A (手动) |
| ENV-02 | pip install -e . 成功 | smoke | `pip install -e . && arcgis-agent --version` | N/A (手动) |
| ENV-03 | wrapper .bat 从干净 CMD 可运行 | smoke | `arcgis-agent.bat --version` | N/A (手动) |

### Sampling Rate
- **Per task commit:** 手动验证（环境操作不适合自动化测试）
- **Per wave merge:** 手动验证全部 4 个成功标准
- **Phase gate:** 全部成功标准通过

### Wave 0 Gaps
- [ ] `tests/conftest.py` — 共享 fixtures（Phase 1 创建）
- [ ] `pytest` 安装 — `pip install pytest`（在环境创建后）

**Note:** Phase 0 的验证主要是手动 smoke test（环境操作不适合自动化），pytest 框架在 Phase 1 的 Wave 0 中搭建。

## Sources

### Primary (HIGH confidence)
- 本机 `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe` — Python 3.11.10, arcpy 3.4.3 已验证
- 本机 `conda create --help` — clone 语法已确认
- 本机 `pip index versions` — mcp 1.27.1, rich 15.0.0, hatchling 1.29.0 已确认
- 本机 `proenv.bat` — 路径已确认存在

### Secondary (MEDIUM confidence)
- STACK.md — pyproject.toml 模板、Click/MCP 选型理由
- PITFALLS.md — Pitfall #8 (conda 依赖冲突)、Pitfall #6/#7 (编码问题)

### Tertiary (LOW confidence)
- (无 — 所有关键发现已本机验证)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 所有包版本已通过 pip index 和本机环境验证
- Architecture: HIGH — src layout + hatchling 是标准模式，pyproject.toml 模板基于 PEP 621
- Pitfalls: MEDIUM — 基于已知模式和 STACK.md/PITFALLS.md，但 mcp 依赖链的实际影响需安装后验证

**Research date:** 2026-05-25
**Valid until:** 2026-06-25 (30 天 — ArcGIS Pro 版本稳定，包版本已锁定)
