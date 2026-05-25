# Phase 1: CLI 基础框架 & 核心基础设施 - Research

**Researched:** 2026-05-25
**Domain:** Click CLI 框架 + Adapter 模式 + 日志/编码基础设施
**Confidence:** HIGH

## Summary

Phase 1 是整个项目的技术基础层。它需要交付：(1) 一个完整的 Click CLI 主命令组，支持 `--help`、`--version`、`--json`、`--verbose`、`--quiet`；(2) 通过 `entry_points("arcgis_agent.commands")` 实现的插件加载机制；(3) 统一的 Result 数据模型（Pydantic），所有命令的 JSON 输出都通过它序列化；(4) 明确的退出码语义（0/1/2/3）；(5) 强制 UTF-8 的 stdout/stderr 和 pathlib 路径处理；(6) 基于 stdlib logging 的日志系统，`--verbose`/`--quiet` 控制级别，输出到 stderr；(7) arcpy 适配器接口（IGeoProcessor、IMapDocument、IDataAccessor）及真实/Mock 两种实现；(8) 带依赖注入的 BaseService 基类；(9) 环境检测模块（arcpy 可用性和许可证检查）。

Phase 1 不实现任何业务命令（那是 Phase 2+ 的事）。它只搭建框架骨架，让后续阶段的开发者能 "填空" —— 写一个 adapter 方法、一个 service 方法、一个 command 函数，就能跑起来。

**Primary recommendation:** 先实现 Result 模型和 CLI 框架（CLI-01~06），再实现 Adapter 接口（ADP-01~04），最后实现环境检测（ENV-04）。这种顺序让每个 wave 都能独立测试。

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI 参数解析与分发 | CLI Entry | — | Click group 是唯一入口 |
| 插件发现与注册 | CLI Entry | Command Registry | entry_points 在启动时由 CLI 调用 |
| 统一输出格式 | Core Layer | — | Result 模型被所有层共用 |
| 日志系统 | CLI Entry | — | --verbose/--quiet 是 CLI 选项，日志输出到 stderr |
| arcpy 适配器接口 | Adapter Layer | — | ABC 定义在 adapters/base.py |
| 真实 arcpy 实现 | Adapter Layer | — | ArcPy* 类在 adapters/arcpy_adapter.py |
| Mock 实现 | Adapter Layer | — | Mock* 类在 adapters/mock_adapter.py，供测试用 |
| 依赖注入 | Service Layer | — | BaseService 接受 adapter 实例 |
| 环境检测 | CLI Entry | Adapter Layer | 启动时检测，失败时给出清晰错误 |
| 退出码语义 | CLI Entry | — | CLI 入口处统一处理异常到退出码 |
| UTF-8 编码 | CLI Entry | — | CLI 入口处 reconfigure stdout/stderr |

## Standard Stack

### Core

| Package | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.1.7 | CLI 框架 | 已预装；plugin 生态成熟；`Group.add_command()` 直接支持插件模式 [VERIFIED: Phase 0 RESEARCH.md] |
| pydantic | 2.13.4 | 数据验证 / Result 模型 | 已预装（mcp 安装后升级）；JSON Schema 生成对 MCP 工具类型注解有直接价值 [VERIFIED: Phase 0 RESEARCH.md] |
| rich | 15.0.0 | 终端格式化 | 已确认待安装；用于 --verbose 模式下的彩色日志和表格输出 [VERIFIED: Phase 0 RESEARCH.md] |
| logging | stdlib | 日志系统 | Python 标准库；无需额外安装；stderr 输出与 stdout JSON 严格分离 |
| pathlib | stdlib | 路径处理 | Python 标准库；自动处理 Windows/Unix 路径差异；支持中文路径 |

### Supporting

| Package | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | latest | 测试框架 | 所有单元测试 |
| pytest-click | latest | Click CLI 测试辅助 | CLI 命令的集成测试 |
| importlib.metadata | stdlib | entry_points API | 插件加载器 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Click | Typer | Typer 是 Click 的封装，插件注册不如 Click 的 `add_command()` 直接；类型提示便利性不抵消架构刚性 [CITED: STACK.md] |
| Pydantic Result | dataclasses | dataclasses 无内置验证、无 JSON Schema 生成；对 MCP 工具类型注解无价值 |
| stdlib logging | loguru | loguru 功能更强但增加依赖；stdlib logging 够用且零依赖 |

**Installation:**
```bash
pip install click>=8.1 pydantic>=2.11 rich pytest pytest-click
```

**Version verification:** Phase 0 RESEARCH.md 已确认 click 8.1.7 预装、pydantic 2.4.2 将被 mcp 升级到 2.13.4、rich 15.0.0 待安装。

## Architecture Patterns

### 系统架构图（Phase 1 范围）

```
User Input (命令行)
    │
    ▼
┌─────────────────────────────────────────┐
│  cli.py: Click Group                    │
│  --help / --version / --json            │
│  --verbose / --quiet                    │
│  UTF-8 reconfigure                      │
│  Exit code mapping                      │
│  ┌─────────────────────────────────┐    │
│  │  plugins.py: Plugin Loader      │    │
│  │  entry_points("arcgis_agent.    │    │
│  │    commands")                   │    │
│  │  ┌────────┐ ┌────────┐         │    │
│  │  │ data   │ │ map    │  ...    │    │
│  │  │commands│ │commands│         │    │
│  │  └───┬────┘ └───┬────┘         │    │
│  └──────┼──────────┼──────────────┘    │
└─────────┼──────────┼───────────────────┘
          │          │
          ▼          ▼
    ┌─────────────────────┐
    │  Service Layer      │
    │  BaseService (DI)   │
    │  ┌───────────────┐  │
    │  │ MapService     │  │
    │  │ DataService    │  │
    │  └───────┬───────┘  │
    └──────────┼──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  Adapter Layer      │
    │  ┌───────────────┐  │
    │  │ IGeoProcessor  │  │ (ABC 接口)
    │  │ IMapDocument   │  │
    │  │ IDataAccessor  │  │
    │  └───────┬───────┘  │
    └──────────┼──────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
  ArcPy*Impl    Mock*Impl
  (lazy import) (测试用)
```

### 推荐项目结构（Phase 1 新增/修改的文件标 *）

```
src/arcgis_agent/
├── __init__.py              # (已有) __version__
├── __main__.py              # (已有) python -m arcgis_agent
├── cli.py                   # * 重写：完整 Click group + 选项
├── plugins.py               # * 新建：插件加载器
├── exceptions.py            # * 新建：自定义异常体系
├── logging_config.py        # * 新建：日志配置
├── env_check.py             # * 重写：环境检测模块
├── models/
│   ├── __init__.py
│   └── result.py            # * 新建：统一 Result 模型
├── adapters/
│   ├── __init__.py
│   ├── base.py              # * 新建：ABC 接口
│   ├── arcpy_adapter.py     # * 新建：真实 ArcPy 实现
│   └── mock_adapter.py      # * 新建：Mock 实现
├── services/
│   ├── __init__.py
│   └── base.py              # * 新建：BaseService (DI)
├── commands/
│   └── __init__.py          # (已有) 空包
└── mcp_server.py            # (已有) Phase 5 实现

tests/
├── conftest.py              # * 新建：共享 fixtures
├── unit/
│   ├── test_cli.py          # * 新建：CLI 选项测试
│   ├── test_plugins.py      # * 新建：插件加载测试
│   ├── test_result.py       # * 新建：Result 模型测试
│   ├── test_adapters.py     # * 新建：Mock adapter 测试
│   ├── test_services.py     # * 新建：BaseService DI 测试
│   └── test_env_check.py    # * 新建：环境检测测试
└── integration/             # Phase 2+ 填充
```

### Pattern 1: Click Group + 全局选项

**What:** Click 主命令组，所有全局选项（`--json`、`--verbose`、`--quiet`）在 group 级别定义，通过 `click.pass_context` 传递给子命令。

**When to use:** 所有 CLI 入口点。

**Example:**
```python
# Source: https://click.palletsprojects.com/en/stable/commands/
import click
from arcgis_agent import __version__

@click.group()
@click.version_option(version=__version__, prog_name="arcgis-agent")
@click.option("--json", "output_json", is_flag=True, default=False,
              help="Output in JSON format.")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Enable verbose logging (DEBUG level).")
@click.option("--quiet", "-q", is_flag=True, default=False,
              help="Suppress non-error output.")
@click.pass_context
def cli(ctx, output_json, verbose, quiet):
    """AI Agent CLI for ArcGIS Pro automation."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    # Configure logging based on flags
    from arcgis_agent.logging_config import setup_logging
    setup_logging(verbose=verbose, quiet=quiet)
```

**关键点：**
- `--json` 存入 `ctx.obj`，子命令通过 `@click.pass_context` 读取
- `--verbose` 和 `--quiet` 互斥，CLI 入口处做冲突检测
- `click.version_option` 从 `__init__.__version__` 读取版本号

### Pattern 2: Plugin Loader（entry_points）

**What:** 启动时通过 `importlib.metadata.entry_points(group="arcgis_agent.commands")` 发现所有已注册的命令模块，调用其 `register(cli_group)` 函数。

**When to use:** CLI 启动时自动执行。

**Example:**
```python
# Source: https://docs.python.org/3.11/library/importlib.metadata.html
import logging
import click
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)

def load_plugins(cli_group: click.Group) -> None:
    """Discover and register all command plugins."""
    eps = entry_points(group="arcgis_agent.commands")
    for ep in sorted(eps, key=lambda e: e.name):
        try:
            register_fn = ep.load()
            register_fn(cli_group)
            logger.debug("Loaded plugin: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load plugin '%s': %s", ep.name, e)
```

**关键点：**
- 使用 `entry_points(group=...)` 关键字参数，这是 Python 3.9+ 的跨版本兼容 API [VERIFIED: Python docs]
- 不要用 `entry_points().get("group")` 字典风格访问，在 Python 3.12 中已废弃
- 插件加载失败只 warning 不 crash —— 一个坏插件不应毁掉整个 CLI
- `sorted()` 保证加载顺序稳定（便于调试和测试）

### Pattern 3: Result 模型（Pydantic）

**What:** 所有命令的统一输出格式。success/code/message/data/warnings 五个字段，Pydantic BaseModel 实现，内置 `to_json()` 方法。

**When to use:** 所有 service 方法返回值；CLI 命令输出；MCP 工具返回值。

**Example:**
```python
# Source: Pydantic v2 docs + ARCHITECTURE.md
from pydantic import BaseModel, Field
from typing import Any, Optional
import json

class Result(BaseModel):
    success: bool
    code: str = "OK"
    message: str = ""
    data: Optional[dict[str, Any]] = None
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def ok(cls, data: dict[str, Any] | None = None,
           message: str = "OK") -> "Result":
        return cls(success=True, code="OK", message=message, data=data)

    @classmethod
    def error(cls, code: str, message: str,
              data: dict[str, Any] | None = None) -> "Result":
        return cls(success=False, code=code, message=message, data=data)

    @classmethod
    def from_exception(cls, exc: Exception) -> "Result":
        from arcgis_agent.exceptions import map_exception_to_code
        code = map_exception_to_code(exc)
        return cls(success=False, code=code, message=str(exc))

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)
```

**关键点：**
- 用 Pydantic `BaseModel` 而不是 `dataclasses`，因为：(1) 内置 JSON Schema 生成对 MCP 工具有价值；(2) 字段验证自动执行；(3) `model_dump_json()` 处理序列化细节
- `warnings: list[str]` 用 `Field(default_factory=list)` 避免可变默认值陷阱
- `from_exception()` 是异常到 Result 的桥接，配合退出码映射使用

### Pattern 4: Adapter 接口 + 真实/Mock 实现

**What:** ABC 定义三个接口（IGeoProcessor、IMapDocument、IDataAccessor），真实实现在构造函数中 lazy import arcpy，Mock 实现用于无 ArcGIS 许可证的单元测试。

**When to use:** 所有需要调用 arcpy 的操作都必须通过 adapter。

**Example:**
```python
# Source: ARCHITECTURE.md
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class IGeoProcessor(ABC):
    """arcpy 地理处理操作接口。"""

    @abstractmethod
    def buffer(self, input_fc: str, output_fc: str,
               distance: float, unit: str) -> Path:
        ...

    @abstractmethod
    def clip(self, input_fc: str, clip_fc: str,
             output_fc: str) -> Path:
        ...

class ArcPyGeoProcessor(IGeoProcessor):
    """真实 arcpy 实现 — 构造函数内 lazy import。"""

    def __init__(self):
        import arcpy  # 关键：在构造函数中 import，不是模块顶层
        self._arcpy = arcpy

    def buffer(self, input_fc, output_fc, distance, unit):
        try:
            self._arcpy.analysis.Buffer(
                input_fc, output_fc, f"{distance} {unit}"
            )
            return Path(output_fc)
        except self._arcpy.ExecuteError as e:
            from arcgis_agent.exceptions import ArcGISError
            raise ArcGISError(
                code="GP_BUFFER_FAILED",
                message=str(e),
                arcpy_messages=self._arcpy.GetMessages()
            )

class MockGeoProcessor(IGeoProcessor):
    """Mock 实现 — 用于单元测试，不需要 arcpy。"""

    def __init__(self):
        self.calls: list[tuple] = []

    def buffer(self, input_fc, output_fc, distance, unit):
        self.calls.append(("buffer", input_fc, output_fc, distance, unit))
        Path(output_fc).touch()  # 创建空文件验证路径
        return Path(output_fc)
```

**关键点：**
- `import arcpy` 必须在 `__init__()` 中，不能在模块顶层 —— 否则没有 ArcGIS 许可证时整个模块无法导入 [CITED: PITFALLS.md #14]
- Mock 实现记录 `self.calls` 用于测试断言
- 真实实现捕获 `arcpy.ExecuteError` 并转换为 `ArcGISError`

### Pattern 5: BaseService（依赖注入）

**What:** 基类接受 adapter 实例注入；未注入时 lazy 创建真实 adapter。

**Example:**
```python
from arcgis_agent.adapters.base import IGeoProcessor, IMapDocument, IDataAccessor

class BaseService:
    def __init__(self,
                 gp: IGeoProcessor | None = None,
                 map_doc: IMapDocument | None = None,
                 data: IDataAccessor | None = None):
        self._gp = gp or self._make_gp()
        self._map = map_doc or self._make_map()
        self._data = data or self._make_data()

    @staticmethod
    def _make_gp() -> IGeoProcessor:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyGeoProcessor
        return ArcPyGeoProcessor()

    @staticmethod
    def _make_map() -> IMapDocument:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyMapDocument
        return ArcPyMapDocument()

    @staticmethod
    def _make_data() -> IDataAccessor:
        from arcgis_agent.adapters.arcpy_adapter import ArcPyDataAccessor
        return ArcPyDataAccessor()
```

**关键点：**
- `_make_*()` 方法中 lazy import 真实 adapter —— 同样避免模块级 arcpy 导入
- 测试时注入 Mock adapter：`Service(gp=MockGeoProcessor())`
- 子类 service 只需 `super().__init__()` 然后用 `self._gp` 等

### Anti-Patterns to Avoid

- **模块顶层 import arcpy:** 导致无 ArcGIS 许可证时整个包无法导入。所有 arcpy 导入必须在函数/方法内部。
- **一个巨大的 adapter 类:** 按领域拆分为 IGeoProcessor / IMapDocument / IDataAccessor。
- **CLI 命令直接调用 arcpy:** 必须通过 Service -> Adapter 链路。
- **print() 输出到 stdout:** stdout 只能输出 JSON；日志/进度/警告全部 stderr。
- **用 `entry_points().get("group")` 字典风格:** Python 3.12 已废弃；用 `entry_points(group="...")` 关键字参数。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI 参数解析 | sys.argv 手动解析 | Click group | 成熟框架，内置帮助、补全、类型转换 |
| JSON 序列化 | json.dumps 手动构造 | Pydantic `model_dump_json()` | 自动处理 None、日期、嵌套；JSON Schema 生成 |
| 插件发现 | 目录扫描 / importlib 遍历 | `entry_points(group=...)` | Python 标准机制；pip 安装即注册；无需运行时扫描 |
| 日志配置 | print() + 手动级别判断 | stdlib logging + handler 配置 | 级别控制、格式化、stderr 输出一体化 |
| 路径处理 | os.path.join / 字符串拼接 | pathlib.Path | 跨平台、中文路径安全、链式操作 |
| 异常体系 | 每个模块自定义 Exception | 统一 exceptions.py + 错误码映射 | 退出码语义一致、错误信息可机器解析 |
| 测试中的 arcpy 模拟 | mock.patch 整个 arcpy 模块 | Mock adapter 类 | 接口隔离；测试更稳定；不依赖 mock 的内部实现 |

## Common Pitfalls

### Pitfall 1: Windows 控制台 GBK 编码导致 JSON 输出崩溃

**What goes wrong:** JSON 中包含中文字符时 `UnicodeEncodeError: 'gbk' codec can't encode character`。
**Why it happens:** Windows 控制台默认编码是 CP936/GBK，Python 的 `sys.stdout` 继承此编码。
**How to avoid:** CLI 入口处强制 UTF-8：
```python
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```
同时在 wrapper .bat 中设置 `PYTHONUTF8=1` 和 `PYTHONIOENCODING=utf-8`。
**Warning signs:** 任何包含中文路径或中文消息的命令在 CMD.exe 中崩溃。[CITED: PITFALLS.md #7]

### Pitfall 2: entry_points 在 editable install 后不生效

**What goes wrong:** `pip install -e .` 后 `arcgis-agent` 命令找不到新注册的插件。
**Why it happens:** editable install 的 entry_points 注册可能需要重新激活 conda 环境。
**How to avoid:** 安装后验证 `python -c "from importlib.metadata import entry_points; print(list(entry_points(group='arcgis_agent.commands')))"`。如为空，重新激活环境。
**Warning signs:** `arcgis-agent --help` 不显示子命令。[CITED: Phase 0 RESEARCH.md]

### Pitfall 3: Plugin 模块顶层 import arcpy

**What goes wrong:** 动态加载的插件模块在顶层 `import arcpy`，导致无 ArcGIS 许可证时 `load_plugins()` 崩溃。
**Why it happens:** `importlib.metadata.entry_points.load()` 执行模块顶层代码。
**How to avoid:** 所有 plugin 的 `register()` 函数内部不应导入 arcpy；arcpy 导入推迟到 service/adapter 层的构造函数中。
**Warning signs:** Mock 测试环境（无 arcpy）下 `load_plugins()` 抛出 ImportError。[CITED: PITFALLS.md #14]

### Pitfall 4: --verbose 和 --quiet 同时指定

**What goes wrong:** 用户同时传 `--verbose --quiet`，日志级别不确定。
**Why it happens:** 没有互斥检测。
**How to avoid:** 在 CLI group 的 callback 中检测冲突并报错：
```python
if verbose and quiet:
    click.echo("Error: --verbose and --quiet are mutually exclusive.", err=True)
    sys.exit(1)
```
**Warning signs:** 测试中同时传两个标志时行为不一致。

### Pitfall 5: Pydantic model_dump() vs model_dump_json() 混淆

**What goes wrong:** 用 `model_dump()` 返回 dict 然后 `json.dumps()`，遇到 datetime 等非 JSON 类型时 `TypeError`。
**Why it happens:** `model_dump()` 返回 Python 对象（可能含 datetime），`json.dumps()` 不知道如何序列化。
**How to avoid:** 统一使用 `model_dump_json()`，它内部调用 Pydantic 的自定义 JSON 编码器。
**Warning signs:** Result.data 中包含非基本类型时序列化失败。

### Pitfall 6: exit code 语义不一致

**What goes wrong:** 有的异常返回 exit 1，有的返回 exit 2，agent 无法区分用户错误和系统错误。
**Why it happens:** 没有统一的异常到退出码映射。
**How to avoid:** 在 `exceptions.py` 中定义异常层级，CLI 入口处用 `except` 块映射：
```python
try:
    cli()
except UserError:
    sys.exit(1)
except SystemError_:
    sys.exit(2)
except ArcGISError:
    sys.exit(3)
```
**Warning signs:** 不同命令对相同类型的错误返回不同退出码。[CITED: PITFALLS.md #17]

## Code Examples

### CLI 完整入口（cli.py 重写）

```python
"""Click main entry point for arcgis-agent CLI."""
import sys
import click
from arcgis_agent import __version__
from arcgis_agent.logging_config import setup_logging

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@click.group()
@click.version_option(version=__version__, prog_name="arcgis-agent")
@click.option("--json", "output_json", is_flag=True, default=False,
              help="Output results as JSON.")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging (DEBUG level to stderr).")
@click.option("--quiet", "-q", is_flag=True, default=False,
              help="Suppress non-error output.")
@click.pass_context
def cli(ctx, output_json, verbose, quiet):
    """AI Agent CLI for ArcGIS Pro automation."""
    if verbose and quiet:
        click.echo("Error: --verbose and --quiet are mutually exclusive.",
                    err=True)
        sys.exit(1)
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    setup_logging(verbose=verbose, quiet=quiet)
    from arcgis_agent.plugins import load_plugins
    load_plugins(cli)


# Source: https://click.palletsprojects.com/en/stable/commands/
```

### 插件加载器（plugins.py）

```python
"""Plugin loader via importlib.metadata entry_points."""
import logging
import click
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


def load_plugins(cli_group: click.Group) -> None:
    """Discover and register all command plugins."""
    eps = entry_points(group="arcgis_agent.commands")
    for ep in sorted(eps, key=lambda e: e.name):
        try:
            register_fn = ep.load()
            register_fn(cli_group)
            logger.debug("Loaded plugin: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load plugin '%s': %s", ep.name, e)

# Source: https://docs.python.org/3.11/library/importlib.metadata.html
# 关键：用 group= 关键字参数，不用字典风格访问
```

### 日志配置（logging_config.py）

```python
"""Logging configuration with --verbose / --quiet control."""
import logging
import sys


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging to stderr with level based on flags."""
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    ))
    root = logging.getLogger("arcgis_agent")
    root.setLevel(level)
    root.addHandler(handler)
```

### 自定义异常体系（exceptions.py）

```python
"""Custom exception hierarchy with exit code mapping."""


class AgentError(Exception):
    """Base exception for arcgis-agent."""
    code: str = "UNKNOWN_ERROR"
    exit_code: int = 2


class UserError(AgentError):
    """User input errors (exit code 1)."""
    code = "USER_ERROR"
    exit_code = 1


class FileNotFoundError_(UserError):
    code = "FILE_NOT_FOUND"


class InvalidFormatError(UserError):
    code = "INVALID_FORMAT"


class SystemError_(AgentError):
    """System/environment errors (exit code 2)."""
    code = "SYSTEM_ERROR"
    exit_code = 2


class ArcGISError(AgentError):
    """arcpy/license errors (exit code 3)."""
    code = "ARCGIS_ERROR"
    exit_code = 3

    def __init__(self, code: str = "ARCGIS_ERROR", message: str = "",
                 arcpy_messages: str = ""):
        super().__init__(message)
        self.code = code
        self.arcpy_messages = arcpy_messages


def map_exception_to_code(exc: Exception) -> str:
    """Map exception type to error code string."""
    if isinstance(exc, AgentError):
        return exc.code
    return "UNKNOWN_ERROR"
```

### 环境检测模块（env_check.py 重写）

```python
"""Environment detection: arcpy availability and license check."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentStatus:
    available: bool
    message: str
    arcpy_version: str | None = None
    license_level: str | None = None


def check_environment() -> EnvironmentStatus:
    """Check if arcpy is available and license is valid."""
    try:
        import arcpy
        info = arcpy.GetInstallInfo()
        version = info.get("Version", "unknown")
        license_level = info.get("LicenseLevel", "unknown")
        return EnvironmentStatus(
            available=True,
            message=f"ArcGIS Pro {version} ({license_level})",
            arcpy_version=version,
            license_level=license_level,
        )
    except ImportError:
        return EnvironmentStatus(
            available=False,
            message=(
                "arcpy not found. Run inside ArcGIS Pro Python environment.\n"
                "Activate with: proenv.bat  or  conda activate arcgispro-py3"
            ),
        )
    except Exception as e:
        return EnvironmentStatus(
            available=False,
            message=f"arcpy error: {e}",
        )

# Source: STACK.md + PITFALLS.md #1/#2
```

## State of the Art

| Item | Current State | Impact |
|------|--------------|--------|
| Click | 8.1.7 (预装) | `group.add_command()` 和 `version_option` API 稳定 |
| Pydantic | 2.4.2 → 2.13.4 (mcp 升级后) | 用 `model_dump_json()` 不用旧的 `.json()` |
| importlib.metadata | Python 3.11 标准库 | `entry_points(group=...)` 关键字参数可用 |
| Python | 3.11.10 | `list[str]` 类型注解原生支持（无需 `from __future__`） |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `entry_points(group="arcgis_agent.commands")` 在 Python 3.11 中返回 `list[EntryPoint]` | Plugin Loader | 如果返回 SelectableGroups 需要额外 `.entries` 访问 |
| A2 | Pydantic 2.13 的 `model_dump_json()` 可正确处理 `Optional[dict]` 和 `list[str]` | Result Model | 如果有序列化问题需要自定义 encoder |
| A3 | `sys.stdout.reconfigure(encoding="utf-8")` 在 ArcGIS Pro conda 环境中生效 | CLI Entry | 如果不生效需要用 `io.TextIOWrapper` 重新包装 |
| A4 | click.testing.CliRunner 可正确测试带 `@click.pass_context` 的 group | Validation | 如果不行需要手动构造 Context |
| A5 | editable install (`pip install -e .`) 后 entry_points 立即可用 | Plugin Loader | 如果需要重新激活环境，测试流程要调整 |

## Open Questions

1. **entry_points 在 editable install 后的刷新行为**
   - What we know: Python 3.11 的 importlib.metadata 支持 editable install 的 entry_points
   - What's unclear: hatchling 的 editable install 是否立即注册 entry_points 还是需要重新激活
   - Recommendation: 测试时先 `pip install -e .`，然后验证 `entry_points(group="arcgis_agent.commands")` 是否有值

2. **pytest-click 的版本兼容性**
   - What we know: pytest-click 提供 `CliRunner` fixture
   - What's unclear: 最新版是否兼容 Click 8.1.7
   - Recommendation: 如不兼容，直接用 `click.testing.CliRunner`（stdlib 提供）

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | 所有 | ✓ | 3.11.10 | — |
| click | CLI-01 | ✓ | 8.1.7 | — |
| pydantic | CLI-03 (Result) | ✓ | 2.13.4 (升级后) | dataclasses (降级方案) |
| rich | CLI-06 (日志格式化) | 待安装 | 15.0.0 | 不用 rich，用纯 logging |
| logging | CLI-06 | ✓ (stdlib) | — | — |
| pathlib | CLI-05 | ✓ (stdlib) | — | — |
| importlib.metadata | CLI-02 | ✓ (stdlib) | — | — |
| pytest | 测试 | 待安装 | latest | unittest (stdlib) |
| arcpy | ADP-02, ENV-04 | ✓ | 3.4.3 | Mock adapter (ADP-03) |

**Missing dependencies with no fallback:**
- 无 — 所有关键依赖已就绪或有待安装的明确版本

**Missing dependencies with fallback:**
- rich（如安装失败可不使用，日志输出退化为纯文本）

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (待安装: `pip install pytest pytest-click`) |
| Config file | none — Wave 0 创建 `tests/conftest.py` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `arcgis-agent --help` 显示帮助信息 | unit | `pytest tests/unit/test_cli.py::test_help -x` | ❌ Wave 0 |
| CLI-01 | `arcgis-agent --version` 显示版本号 | unit | `pytest tests/unit/test_cli.py::test_version -x` | ❌ Wave 0 |
| CLI-01 | `arcgis-agent --json` 设置 JSON 输出标志 | unit | `pytest tests/unit/test_cli.py::test_json_flag -x` | ❌ Wave 0 |
| CLI-01 | `--verbose --quiet` 冲突时报错退出 | unit | `pytest tests/unit/test_cli.py::test_verbose_quiet_conflict -x` | ❌ Wave 0 |
| CLI-02 | 插件加载器发现并注册 mock 插件 | unit | `pytest tests/unit/test_plugins.py::test_load_plugins -x` | ❌ Wave 0 |
| CLI-02 | 插件加载失败时 warning 不 crash | unit | `pytest tests/unit/test_plugins.py::test_plugin_failure_no_crash -x` | ❌ Wave 0 |
| CLI-03 | `Result.ok()` 生成正确 JSON | unit | `pytest tests/unit/test_result.py::test_result_ok -x` | ❌ Wave 0 |
| CLI-03 | `Result.error()` 生成正确 JSON | unit | `pytest tests/unit/test_result.py::test_result_error -x` | ❌ Wave 0 |
| CLI-03 | `Result.from_exception()` 映射正确 | unit | `pytest tests/unit/test_result.py::test_result_from_exception -x` | ❌ Wave 0 |
| CLI-04 | UserError → exit 1 | unit | `pytest tests/unit/test_cli.py::test_exit_code_user_error -x` | ❌ Wave 0 |
| CLI-04 | SystemError → exit 2 | unit | `pytest tests/unit/test_cli.py::test_exit_code_system_error -x` | ❌ Wave 0 |
| CLI-04 | ArcGISError → exit 3 | unit | `pytest tests/unit/test_cli.py::test_exit_code_arcgis_error -x` | ❌ Wave 0 |
| CLI-05 | stdout 输出为 UTF-8 | unit | `pytest tests/unit/test_cli.py::test_utf8_output -x` | ❌ Wave 0 |
| CLI-06 | `--verbose` 启用 DEBUG 级别 | unit | `pytest tests/unit/test_cli.py::test_verbose_logging -x` | ❌ Wave 0 |
| CLI-06 | `--quiet` 只输出 ERROR | unit | `pytest tests/unit/test_cli.py::test_quiet_logging -x` | ❌ Wave 0 |
| CLI-06 | 日志输出到 stderr 不污染 stdout | unit | `pytest tests/unit/test_cli.py::test_logging_to_stderr -x` | ❌ Wave 0 |
| ADP-01 | IGeoProcessor 接口可被实现 | unit | `pytest tests/unit/test_adapters.py::test_interface_instantiation -x` | ❌ Wave 0 |
| ADP-02 | ArcPy* 在构造函数中 import arcpy | unit | `pytest tests/unit/test_adapters.py::test_lazy_import -x` | ❌ Wave 0 |
| ADP-03 | Mock* 记录调用并返回有效路径 | unit | `pytest tests/unit/test_adapters.py::test_mock_adapter -x` | ❌ Wave 0 |
| ADP-04 | BaseService 接受注入的 adapter | unit | `pytest tests/unit/test_services.py::test_di_injection -x` | ❌ Wave 0 |
| ADP-04 | BaseService 未注入时 lazy 创建真实 adapter | unit | `pytest tests/unit/test_services.py::test_lazy_creation -x` | ❌ Wave 0 |
| ENV-04 | 有 arcpy 时返回 available=True | unit | `pytest tests/unit/test_env_check.py::test_env_available -x` | ❌ Wave 0 |
| ENV-04 | 无 arcpy 时返回 available=False + 清晰消息 | unit | `pytest tests/unit/test_env_check.py::test_env_unavailable -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`（快速验证不回归）
- **Per wave merge:** `pytest tests/ -v`（完整输出确认）
- **Phase gate:** 全部 22 个测试用例绿色

### Wave 0 Gaps

- [ ] `tests/conftest.py` — 共享 fixtures（mock adapter、CliRunner）
- [ ] `tests/unit/test_cli.py` — CLI 选项和退出码测试
- [ ] `tests/unit/test_plugins.py` — 插件加载测试
- [ ] `tests/unit/test_result.py` — Result 模型测试
- [ ] `tests/unit/test_adapters.py` — Adapter 接口和 Mock 测试
- [ ] `tests/unit/test_services.py` — BaseService DI 测试
- [ ] `tests/unit/test_env_check.py` — 环境检测测试
- [ ] pytest 安装: `pip install pytest pytest-click`

## Sources

### Primary (HIGH confidence)
- [Click Documentation - Commands and Groups](https://click.palletsprojects.com/en/stable/commands/) — group.add_command() 模式
- [Click Documentation - Testing](https://click.palletsprojects.com/en/stable/testing/) — CliRunner 测试模式
- [Python 3.11 importlib.metadata](https://docs.python.org/3.11/library/importlib.metadata.html) — entry_points(group=...) API
- Phase 0 RESEARCH.md — 本机验证的包版本和环境信息

### Secondary (MEDIUM confidence)
- ARCHITECTURE.md — 分层架构、adapter 模式、Result 模型设计
- STACK.md — Click vs Typer 选型理由、pyproject.toml 配置
- PITFALLS.md — 编码问题、arcpy 导入陷阱、插件加载副作用

### Tertiary (LOW confidence)
- WebSearch: importlib.metadata entry_points API 变更历史（Python 3.9 → 3.12）

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 所有包版本已通过 Phase 0 本机验证
- Architecture: HIGH — 分层架构和 adapter 模式基于已验证的 ARCHITECTURE.md
- Pitfalls: HIGH — 编码/arcpy/entry_points 陷阱基于 PITFALLS.md 和已知模式
- Code examples: MEDIUM — 基于 Click/Pydantic 官方文档，但未经本机运行验证

**Research date:** 2026-05-25
**Valid until:** 2026-06-25 (30 天 — 依赖版本已锁定，架构模式稳定)
