# arcgis-agent

AI Agent for ArcGIS Pro — 让 AI 通过标准化接口操控 ArcGIS Pro，实现 GIS 工作流的自动化。

[![PyPI version](https://img.shields.io/pypi/v/arcgis-agent)](https://pypi.org/project/arcgis-agent/)
[![Python](https://img.shields.io/pypi/pyversions/arcgis-agent)](https://pypi.org/project/arcgis-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-lzw--cjs/arcgis--agent-blue)](https://github.com/lzw-cjs/arcgis-agent)

## 功能特性

- **CLI 工具** — 31 个 GIS 命令，覆盖数据发现、数据管理、地理处理、地图生产、布局出图
- **MCP Server** — 33 个工具暴露给 Claude Desktop / Claude Code / OpenClaw / Trae SOLO 直接调用
- **Web API** — FastAPI REST API + SSE 流式聊天 + 异步任务系统 + 文件上传
- **AI 集成** — LangChain 驱动的自然语言 GIS 对话，支持 OpenAI/DeepSeek/Qwen 等兼容 API
- **线程安全** — arcpy COM 组件非线程安全，通过 `threading.Lock` + `asyncio.to_thread` 串行化所有调用
- **Mock 适配** — 内置 Mock 适配器，无需 ArcGIS 许可证即可运行 248 个单元测试

## 重要前提

> **arcpy 不可通过 pip 安装。** 本项目所有功能依赖 `arcpy`，它随 ArcGIS Pro 附带，无法独立获取。

使用前需确保：

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11（arcpy 限制） |
| ArcGIS Pro | 3.x（含有效许可证，需登录一次） |
| Python | 3.9–3.11（ArcGIS Pro 自带 conda 环境） |

## 快速开始

### 1. 创建 conda 环境

```cmd
:: 打开 ArcGIS Python Command Prompt（开始菜单搜索）
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

:: 克隆 ArcGIS Pro 自带环境（保留 arcpy）
conda create -n arcgis-agent --clone arcgispro-py3
conda activate arcgis-agent
```

> **注意：** 如果 `--clone` 因 404 失败，可直接使用 `arcgispro-py3` 环境，或手动复制环境目录。

### 2. 安装 arcgis-agent

```bash
# 从 PyPI 安装（推荐）
pip install arcgis-agent

# 或从源码安装
git clone https://github.com/lzw-cjs/arcgis-agent.git
cd arcgis-agent
pip install .
```

> **中文用户名注意：** 如果 Windows 用户名含中文，请使用 `pip install .` 而非 `pip install -e .`（editable 模式会因中文路径编码问题失败）。

### 3. 验证环境

```bash
python scripts/check-env.py
```

输出应全部为 `[OK]`：

```
  [OK] Python version: Python 3.11.10
  [OK] arcpy: arcpy importable
  [OK] ArcGIS license: ArcGIS Pro license: ArcInfo
  [OK] arcgis-agent package: arcgis-agent 0.1.0 installed

All checks passed. arcgis-agent is ready to use.
```

### 4. 验证 CLI

```bash
arcgis-agent --version
arcgis-agent --help
```

## 使用方法

### CLI 模式

```bash
# 全局选项
arcgis-agent --json data list          # JSON 输出
arcgis-agent -v gp buffer ...          # 调试日志
arcgis-agent -q data list              # 静默模式

# 工作区管理
arcgis-agent workspace set "C:\GIS\Projects"
arcgis-agent workspace get

# 工程信息
arcgis-agent project info --project "C:\GIS\project.aprx"

# 数据发现
arcgis-agent data list                                    # 列出当前工作区所有数据集
arcgis-agent data list --type FeatureClass                # 按类型过滤
arcgis-agent data list --pattern "roads*"                 # 按名称模式过滤
arcgis-agent data describe "C:\GIS\Data\roads.shp"        # 描述数据集元数据
arcgis-agent data fields "C:\GIS\Data\roads.shp"           # 列出字段信息
arcgis-agent data extent "C:\GIS\Data\roads.shp"          # 获取空间范围
arcgis-agent data count "C:\GIS\Data\roads.shp"           # 获取要素数量

# 数据管理
arcgis-agent data copy source.shp dest.shp                 # 复制
arcgis-agent data delete "C:\GIS\Data\temp.shp"            # 删除
arcgis-agent data rename old.shp new_name                   # 重命名
arcgis-agent data convert input.shp output.gdb/output --format gdb  # 格式转换

# 地理处理
arcgis-agent data select input.shp output.shp --where "POP > 10000"  # 属性选择
arcgis-agent data clip input.shp boundary.shp output.shp            # 裁剪
arcgis-agent data buffer input.shp output.shp --distance 500 --unit Meters  # 缓冲区
arcgis-agent data intersect "a.shp;b.shp" output.shp      # 叠加求交
arcgis-agent data union "a.shp;b.shp" output.shp           # 叠加求并
arcgis-agent data dissolve input.shp output.shp --field TYPE  # 融合
arcgis-agent data spatial-join target.shp join.shp output.shp  # 空间连接
arcgis-agent data merge "a.shp;b.shp" output.shp           # 合并
arcgis-agent data project input.shp output.shp --sr 4326   # 投影变换

# 分析
arcgis-agent analysis summary-stats input.shp --field "pop:SUM,area:MEAN"  # 汇总统计

# 地图操作
arcgis-agent map create "MyMap" --project "C:\GIS\project.aprx"       # 创建地图
arcgis-agent map add-layer "MyMap" data.shp --project project.aprx    # 添加图层
arcgis-agent map list-layers "MyMap" --project project.aprx           # 列出图层
arcgis-agent map remove-layer "MyMap" layer_name --project project.aprx  # 移除图层
arcgis-agent map set-extent "MyMap" layer_name --project project.aprx # 缩放到图层
arcgis-agent map symbolize "MyMap" layer_name --project project.aprx \
    --type graduated_colors --field POP --ramp "Yellow to Red"         # 符号化
arcgis-agent map label "MyMap" layer_name --field NAME --project project.aprx  # 标注
arcgis-agent map export "MyMap" output.png --project project.aprx \
    --format PNG --dpi 300                                            # 导出地图

# 布局出图
arcgis-agent layout create "Layout1" --project project.aprx \
    --page-size A4 --orientation portrait                              # 创建布局
arcgis-agent layout add-element "Layout1" text --project project.aprx \
    --position "top-center" --params "text=My Map;font_size=18"        # 添加标题
arcgis-agent layout add-element "Layout1" legend --project project.aprx  # 添加图例
arcgis-agent layout add-element "Layout1" scale-bar --project project.aprx  # 添加比例尺
arcgis-agent layout add-element "Layout1" north-arrow --project project.aprx  # 添加指北针
arcgis-agent layout add-element "Layout1" map-frame --project project.aprx \
    --position "center" --params "map_name=MyMap"                     # 添加地图框
arcgis-agent layout export "Layout1" output.pdf --project project.aprx \
    --format PDF --dpi 300                                            # 导出布局
```

### MCP Server 模式

arcgis-agent 可作为 MCP Server 运行，让 Claude Desktop、Claude Code、OpenClaw、Trae SOLO 等支持 MCP 协议的 AI 工具直接调用 33 个 GIS 工具。

```bash
# 启动 MCP Server
arcgis-agent-mcp

# 或通过 Python 模块
python -m arcgis_agent.mcp_server
```

详细配置方法见 [docs/mcp-setup.md](docs/mcp-setup.md)，支持以下客户端：

| 客户端 | 配置方式 | 传输协议 |
|--------|---------|---------|
| Claude Desktop | 编辑 `claude_desktop_config.json` | stdio |
| Claude Code (VS Code) | settings.json 中 mcp 配置 | stdio |
| OpenClaw | `openclaw mcp set` 命令或编辑 `openclaw.json` | stdio / SSE / HTTP |
| Trae IDE / Trae SOLO | Settings > MCP > Add Manually | stdio / HTTP |

配置示例（Claude Desktop）：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "arcgis-agent-mcp",
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
```

配置示例（OpenClaw）：

```bash
openclaw mcp set arcgis-agent '{"command":"C:\\conda-envs\\arcgis-agent\\python.exe","args":["-m","arcgis_agent.mcp_server"],"env":{"PYTHONUTF8":"1"},"transport":"stdio"}'
```

配置示例（Trae SOLO，通过 UI 添加）：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
      "args": ["-m", "arcgis_agent.mcp_server"],
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
```

> **通用注意：** `command` 必须指向包含 arcpy 的 Python 解释器。如果 entry point 不在 PATH 中，请使用完整路径如 `C:\conda-envs\arcgis-agent\python.exe`。`PYTHONUTF8=1` 在 Windows 中文环境中必须设置。

### Web API 模式

```bash
# 安装 Web 依赖
pip install ".[web,ai]"

# 启动服务
arcgis-agent-web
# 或
uvicorn arcgis_agent.api.main:app --host 0.0.0.0 --port 8000 --workers 1

# API 文档（Swagger UI）
# http://localhost:8000/docs
```

> **workers 必须为 1**：arcpy 是 COM 组件，非线程安全，多 worker 会导致并发崩溃。

#### API 端点总览

| 分类 | 端点 | 方法 | 同步/异步 | 说明 |
|------|------|------|----------|------|
| Chat | `/api/v1/chat` | POST | SSE 流式 | AI 对话，支持工具调用 |
| Chat | `/api/v1/chat/{session_id}` | DELETE | 同步 | 清除会话 |
| Chat | `/api/v1/chat/providers` | GET | 同步 | 查看可用 LLM 提供商 |
| Tools | `/api/v1/tools/workspace/set` | POST | 同步 | 设置工作空间 |
| Tools | `/api/v1/tools/workspace/get` | GET | 同步 | 获取工作空间 |
| Tools | `/api/v1/tools/project/info` | GET | 同步 | 工程信息 |
| Tools | `/api/v1/tools/data/*` | POST | 同步 | 数据发现与管理（5+4个） |
| Tools | `/api/v1/tools/gp/*` | POST | **异步** | 地理处理（9个，返回 task_id） |
| Tools | `/api/v1/tools/map/*` | POST | 混合 | 地图操作（8个，export 异步） |
| Tools | `/api/v1/tools/layout/*` | POST | 混合 | 布局操作（3个，export 异步） |
| Tools | `/api/v1/tools/analysis/summary-stats` | POST | 同步 | 汇总统计 |
| Tasks | `/api/v1/tasks` | POST | 同步 | 创建异步任务 |
| Tasks | `/api/v1/tasks/{task_id}` | GET | 同步 | 查询任务状态 |
| Tasks | `/api/v1/tasks` | GET | 同步 | 列出最近任务 |
| Upload | `/api/v1/upload` | POST | 同步 | 上传 GIS 数据文件 |
| Health | `/api/v1/health` | GET | 同步 | 健康检查 |

#### SSE 流式聊天示例

```bash
# 流式聊天
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我分析当前工作区的数据"}'

# SSE 事件类型：
# token      — 文本片段（50字符切块）
# tool_start — 工具调用开始 {name, args}
# tool_end   — 工具调用结束 {name, success, result}
# suggestions — 建议列表
# done       — 完成 {tool_calls, message_id}
# error      — 错误 {code, message}
```

#### 异步任务示例

```bash
# 提交异步任务（地理处理等耗时操作）
curl -X POST http://localhost:8000/api/v1/tools/gp/buffer \
  -H "Content-Type: application/json" \
  -d '{"input_fc": "roads.shp", "output_fc": "roads_buffer.shp", "distance": 500, "unit": "Meters"}'
# 返回: {"task_id": "uuid-xxx", "status": "pending"}

# 轮询任务状态
curl http://localhost:8000/api/v1/tasks/uuid-xxx
# 返回: {"task_id": "uuid-xxx", "status": "completed", "result": {...}}
```

## 命令总览

| 命令组 | 命令 | 说明 |
|--------|------|------|
| workspace | `set <path>`, `get` | 工作空间管理（持久化到 `~/.arcgis-agent/config.json`） |
| project | `info --project <.aprx>` | 工程信息（路径、GDB、地图列表） |
| data | `list`, `describe`, `fields`, `extent`, `count` | 数据发现（支持 `--type` 和 `--pattern` 过滤） |
| data | `copy`, `delete`, `rename`, `convert` | 数据管理（支持 `--no-overwrite` 安全选项） |
| data | `select`, `clip`, `buffer`, `intersect`, `union`, `dissolve`, `spatial-join`, `merge`, `project` | 地理处理（叠加操作自动检查 CRS 一致性） |
| analysis | `summary-stats --field <spec>` | 汇总统计（字段规格：`field:STAT`，如 `pop:SUM,area:MEAN`） |
| map | `create`, `add-layer`, `remove-layer`, `list-layers`, `set-extent`, `export`, `symbolize`, `label` | 地图操作（PNG/PDF 导出，支持透明背景） |
| layout | `create`, `add-element`, `export` | 布局出图（A4/A3/Letter/Tabloid，6 种元素类型） |

## 项目架构

```
src/arcgis_agent/
├── adapters/
│   ├── base.py           # 4 个适配器接口 ABC（IGeoProcessor, IMapDocument, ILayoutDocument, IDataAccessor）
│   ├── arcpy_adapter.py  # 真实 arcpy 实现（惰性导入，构造函数内 import）
│   └── mock_adapter.py   # Mock 实现（记录调用，返回桩数据，用于单元测试）
├── commands/
│   ├── workspace.py      # workspace set/get
│   ├── project.py        # project info
│   ├── data.py           # data 发现 + 管理
│   ├── geoprocessing.py  # data 地理处理（注册到 data 子组）
│   ├── analysis.py       # analysis summary-stats
│   ├── map.py            # map 操作
│   └── layout.py         # layout 操作
├── models/
│   ├── result.py         # Result(success/code/message/data/warnings) 统一输出
│   └── exceptions.py     # 异常层级（UserError=1, SystemError=2, ArcGISError=3）
├── services/
│   ├── base.py           # BaseService（依赖注入适配器）
│   ├── workspace_service.py
│   ├── project_service.py
│   ├── data_discovery.py
│   ├── data_management.py
│   ├── geoprocessing.py  # VALID_UNITS = {Meters, Kilometers, Feet, Miles, Yards, DecimalDegrees}
│   ├── analysis_service.py  # VALID_STATS = {SUM, MEAN, MIN, MAX, COUNT, STD, MEDIAN}
│   ├── map_service.py   # ALLOWED_DPI={96,150,300,600}, ALLOWED_FORMATS={PNG,PDF}
│   ├── layout_service.py # PAGE_SIZES={A4,A3,Letter,Tabloid}, 6 种元素类型
│   ├── task_service.py   # SQLite 异步任务存储
│   └── chat_service.py   # LLM Agent 循环（最多 5 轮工具调用，80K token 上下文窗口）
├── api/
│   ├── main.py           # FastAPI app factory + CORS + middleware + 健康检查
│   ├── dependencies.py   # _ARC_LOCK, _run_in_thread(), ConversationStore
│   ├── config.py         # LLMConfig（qwen/deepseek/openai 三提供商）
│   ├── middleware.py      # metrics_middleware（请求耗时/状态码日志）
│   ├── llm.py            # OpenAICompatibleProvider（LangChain ChatOpenAI）
│   ├── gis_tools.py      # 33 个 LangChain StructuredTool 定义
│   ├── mock_llm.py       # MockLLMProvider
│   ├── routes/
│   │   ├── chat.py       # POST /chat（SSE 流式）、DELETE /chat/{id}、GET /providers
│   │   ├── tools.py      # 33 个工具 REST 端点（11 个异步，22 个同步）
│   │   ├── tasks.py      # POST/GET /tasks
│   │   └── upload.py     # POST /upload（.shp/.zip/.gdb）
│   └── schemas/
│       ├── chat.py       # ChatRequest, ToolCallEvent
│       ├── tasks.py      # TaskCreate, TaskResult, TaskStatus
│       └── events.py     # ProgressEvent, TokenEvent, ErrorEvent
├── mcp_server.py         # FastMCP Server（33 个 @mcp.tool()）
├── cli.py                # Click CLI 入口
├── config.py             # WorkspaceConfig（~/.arcgis-agent/config.json）
├── env_check.py          # 环境检测
├── exceptions.py         # 异常层级 + 错误码映射
├── logging_config.py     # 日志配置
└── plugins.py            # 插件发现系统
```

### 四层架构

```
┌─────────────────────────────────────────────┐
│              Entry Points                    │
│  CLI (Click)  │  MCP Server  │  REST API    │
├───────────────┼──────────────┼──────────────┤
│              Service Layer                    │
│  WorkspaceService  │  DataDiscoveryService  │
│  GeoprocessingService  │  MapService        │
│  AnalysisService  │  LayoutService          │
│  ChatService  │  TaskService                │
├──────────────────────────────────────────────┤
│              Adapter Layer                    │
│  IGeoProcessor  │  IMapDocument              │
│  ILayoutDocument  │  IDataAccessor           │
│  ILLMProvider                               │
├──────────────────────────────────────────────┤
│              Implementation                  │
│  ArcPyGeoProcessor  │  ArcPyMapDocument      │
│  ArcPyLayoutDocument  │  ArcPyDataAccessor  │
│  OpenAICompatibleProvider                   │
└─────────────────────────────────────────────┘
```

**设计要点：**
- **适配器隔离**：arcpy 仅在 `arcpy_adapter.py` 中被导入，所有上层代码通过接口 ABC 调用
- **Mock 支持**：`mock_adapter.py` 提供无 arcpy 的完整实现，使 248 个单元测试可在任何环境运行
- **线程安全**：`_ARC_LOCK`（全局 `threading.Lock`）+ `asyncio.to_thread()` 确保 arcpy 串行执行
- **依赖注入**：BaseService 构造函数接受可选适配器实例，未提供时自动创建真实适配器

## 统一输出模型

所有命令和 MCP 工具返回统一的 `Result` JSON：

```json
{
  "success": true,
  "code": "OK",
  "message": "Buffer created: 500m Meters",
  "data": {
    "output": "C:/GIS/Output/roads_buffer.shp",
    "count": 1234
  },
  "warnings": ["CRS mismatch detected between inputs"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 操作是否成功 |
| `code` | str | 状态码：`OK`、`USER_ERROR`、`SYSTEM_ERROR`、`ARCGIS_ERROR` |
| `message` | str | 人类可读的描述 |
| `data` | dict | 操作结果数据（可能为 null） |
| `warnings` | list[str] | 非致命警告列表 |

### 退出码映射（CLI 模式）

| 退出码 | 异常类型 | 说明 |
|--------|---------|------|
| 0 | — | 成功 |
| 1 | `UserError` | 用户输入错误（路径不存在、参数无效等） |
| 2 | `SystemError_` | 系统级错误（arcpy 初始化失败等） |
| 3 | `ArcGISError` | arcpy 工具执行错误（含 `arcpy_messages` 字段） |

## 部署

详细部署指南见 [docs/deployment.md](docs/deployment.md)，支持以下方式：

| 方式 | 适用场景 | arcpy 支持 |
|------|---------|-----------|
| conda 环境 | 开发/生产 | 完整支持 |
| Windows 服务 | 生产/自启动 | 完整支持 |
| Docker | 无 arcpy 场景 | 不支持 |
| Linux (Systemd) | 纯 API/聊天 | 不支持 |

## 开发

```bash
conda activate arcgis-agent
pip install ".[dev]"
pytest tests/ -v
```

### 可选依赖组

```bash
pip install ".[web]"     # FastAPI + Uvicorn（Web API）
pip install ".[mcp]"     # MCP SDK（MCP Server）
pip install ".[ai]"      # LangChain（AI 对话）
pip install ".[dev]"     # pytest + build + twine
```

## 许可证

[MIT](LICENSE)