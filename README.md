# arcgis-agent

AI Agent for ArcGIS Pro — 让 AI 通过标准化接口操控 ArcGIS Pro，实现 GIS 工作流的自动化。

[![PyPI version](https://img.shields.io/pypi/v/arcgis-agent)](https://pypi.org/project/arcgis-agent/)
[![Python](https://img.shields.io/pypi/pyversions/arcgis-agent)](https://pypi.org/project/arcgis-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 功能特性

- **CLI 工具** — 31 个 GIS 命令，覆盖数据发现、地理处理、地图生产
- **MCP Server** — 31 个工具暴露给 Claude Desktop / Claude Code 直接调用
- **Web API** — FastAPI REST API + React 聊天界面
- **AI 集成** — LangChain 驱动的自然语言 GIS 对话

## 重要前提

> **arcpy 不可通过 pip 安装。** 本项目所有功能依赖 `arcpy`，它随 ArcGIS Pro 附带。

使用前需确保：
- Windows 10/11
- ArcGIS Pro 3.x（含有效许可证）
- ArcGIS Pro 自带的 Python conda 环境（3.9–3.11）

## 安装

### 方式一：pip 安装（推荐）

```bash
# 1. 激活 ArcGIS Pro 的 Python 环境
conda activate arcgispro-py3
# 或使用克隆的环境
conda activate arcgis-agent

# 2. 安装
pip install arcgis-agent

# 3. 验证
arcgis-agent --version
```

### 方式二：从源码安装

```bash
git clone https://github.com/lzw-cjs/arcgis-agent.git
cd arcgis-agent

# 在 ArcGIS Pro conda 环境中
pip install .
```

> **中文用户名注意:** 如果 Windows 用户名含中文，请使用 `pip install .` 而非 `pip install -e .`。

### 环境检测

```bash
python scripts/check-env.py
```

## 使用方法

### CLI 模式

```bash
arcgis-agent --help
arcgis-agent workspace set "C:\GIS\Projects"
arcgis-agent data list
arcgis-agent data describe "C:\GIS\Data\roads.shp"
arcgis-agent gp buffer input.shp output.shp --distance 500 --unit Meters
arcgis-agent map create "MyMap" --project "C:\GIS\project.aprx"
arcgis-agent map export "MyMap" "C:\output\map.png" --project "C:\GIS\project.aprx"
```

### MCP Server 模式

在 Claude Desktop 中配置（详见 [docs/mcp-setup.md](docs/mcp-setup.md)）：

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

### Web API 模式

```bash
# 启动服务
arcgis-agent-web
# 或指定端口
python -m arcgis_agent.api.main

# API 文档
# http://localhost:8000/docs
```

## 命令总览

| 命令组 | 命令 | 说明 |
|--------|------|------|
| workspace | set, get | 工作空间管理 |
| project | info | 工程信息 |
| data | list, describe, fields, extent, count | 数据发现 |
| data | copy, delete, rename, convert | 数据管理 |
| data | select, clip, buffer, intersect, union, dissolve, spatial-join, merge, project | 地理处理 |
| analysis | summary-stats | 汇总统计 |
| map | create, add-layer, remove-layer, list-layers, set-extent, export, symbolize, label | 地图操作 |
| layout | create, add-element, export | 布局出图 |

## 项目架构

```
src/arcgis_agent/
├── adapters/        # arcpy 封装（惰性导入）
├── commands/        # Click CLI 命令
├── models/          # Result 统一输出模型
├── services/        # 业务逻辑层
├── api/             # FastAPI REST API
├── mcp_server.py    # MCP Server（31 个工具）
└── cli.py           # CLI 入口
```

## 开发

```bash
conda activate arcgis-agent
pip install ".[dev]"
pytest tests/ -v
```

## 许可证

[MIT](LICENSE)