# MCP Server 安装指南

本文档说明如何配置 arcgis-agent MCP Server，让各种 AI 工具可以调用 31 个 GIS 工具。

支持的客户端：Claude Desktop、Claude Code、OpenClaw、Trae IDE/SOLO。

## 前提条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 |
| ArcGIS Pro | 3.x（含有效许可证） |
| Python | 3.9–3.11（ArcGIS Pro 自带） |
| conda | Miniconda 或 ArcGIS Pro 自带 |

## 安装步骤

### 1. 克隆 ArcGIS Pro conda 环境

```cmd
:: 打开 ArcGIS Python Command Prompt（开始菜单搜索）
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

:: 克隆环境
conda create -n arcgis-agent --clone arcgispro-py3
conda activate arcgis-agent
```

> **注意:** 如果 `--clone` 因 404 失败，参考项目 README 中的手动复制方法。

### 2. 安装 arcgis-agent

```bash
pip install .
```

> **中文用户名注意:** 不要使用 `pip install -e .`（editable 模式），会因路径编码问题失败。

### 3. 验证环境

```bash
python scripts/check-env.py
```

所有检查项应显示 `[OK]`。

### 4. 测试 MCP Server

```bash
arcgis-agent-mcp
```

应无报错，等待 stdio 输入（Ctrl+C 退出）。

## 配置 Claude Desktop

### 方法一：使用 entry point（推荐）

编辑 Claude Desktop 配置文件：

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

添加以下内容：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "arcgis-agent-mcp",
      "env": {
        "PYTHONUTF8": "1",
        "CONDA_DEFAULT_ENV": "arcgis-agent"
      }
    }
  }
}
```

### 方法二：使用 conda run

如果 entry point 不在 PATH 中，使用 conda run：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "conda",
      "args": ["run", "-n", "arcgis-agent", "arcgis-agent-mcp"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### 方法三：使用完整 Python 路径

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
      "args": ["-m", "arcgis_agent.mcp_server"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

## 配置 OpenClaw

OpenClaw（原名 Clawdbot/Moltbot）是 GitHub 上增长最快的开源 AI 智能体（375k+ stars）。它支持通过 MCP 连接外部工具。

### 方法一：使用 `openclaw mcp set` 命令

```bash
openclaw mcp set arcgis-agent '{"command":"C:\\conda-envs\\arcgis-agent\\python.exe","args":["-m","arcgis_agent.mcp_server"],"env":{"PYTHONUTF8":"1"},"transport":"stdio"}'
```

### 方法二：编辑 openclaw.json 配置文件

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "mcp": {
    "servers": {
      "arcgis-agent": {
        "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
        "args": ["-m", "arcgis_agent.mcp_server"],
        "env": {
          "PYTHONUTF8": "1"
        },
        "transport": "stdio"
      }
    }
  }
}
```

> **注意：** OpenClaw 的 MCP client 支持 stdio、SSE 和 streamable-http 三种传输方式。arcgis-agent 使用 stdio 传输。

### 方法三：使用 MCP Bridge 插件

如果 OpenClaw 原生 MCP client 有问题，可以使用社区插件：

```bash
openclaw plugins install @aiwerk/openclaw-mcp-bridge
```

然后在 `openclaw.json` 的 `plugins.entries` 中配置：

```json
{
  "openclaw-mcp-bridge": {
    "enabled": true,
    "config": {
      "mode": "router",
      "servers": {
        "arcgis-agent": {
          "transport": "stdio",
          "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
          "args": ["-m", "arcgis_agent.mcp_server"],
          "env": {
            "PYTHONUTF8": "1"
          }
        }
      },
      "connectionTimeoutMs": 15000
    }
  }
}
```

## 配置 Trae IDE / Trae SOLO

Trae 是字节跳动推出的 AI IDE，支持 MCP Server 集成。

### 方法一：通过 UI 添加（推荐）

1. 打开 Trae IDE，点击右上角 Settings 图标
2. 在左侧导航栏选择 **MCP**
3. 点击 **Add > Add Manually**
4. 输入以下 JSON 配置：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
      "args": ["-m", "arcgis_agent.mcp_server"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

5. 点击 Confirm

### 方法二：项目级 MCP 配置

在项目根目录创建 `.trae/mcp.json`：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
      "args": ["-m", "arcgis_agent.mcp_server"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

然后在 Settings > MCP 中启用 **Enable Project MCP** 开关。

### 方法三：在自定义 Agent 中使用

创建自定义 Trae Agent 后，在 Agent 配置中选择要使用的 MCP Server（arcgis-agent），Agent 就能直接调用 31 个 GIS 工具。

## 验证连接

1. 重启对应 AI 工具
2. 在对话中输入：`请列出可用的 MCP 工具` 或 `使用 arcgis-agent 的 workspace_set 工具设置工作空间`
3. 应看到 31 个 arcgis-agent 工具

## 可用工具列表

| 类别 | 工具 | 数量 |
|------|------|------|
| 工作区 | workspace_set, workspace_get | 2 |
| 工程 | project_info | 1 |
| 数据发现 | data_list, data_describe, data_fields, data_extent, data_count | 5 |
| 数据管理 | data_copy, data_delete, data_rename, data_convert | 4 |
| 地理处理 | gp_select, gp_clip, gp_buffer, gp_intersect, gp_union, gp_dissolve, gp_spatial_join, gp_merge, gp_project | 9 |
| 分析 | analysis_summary_stats | 1 |
| 地图 | map_create, map_add_layer, map_remove_layer, map_list_layers, map_set_extent, map_export, map_symbolize, map_label | 8 |
| 布局 | layout_create, layout_add_element, layout_export | 3 |

## 故障排除

### "arcpy not found"

MCP Server 启动时找不到 arcpy。确保：
- 使用 `conda run -n arcgis-agent` 或在 arcgis-agent 环境中运行
- ArcGIS Pro 已安装

### "License not available"

ArcGIS Pro 许可证未登录。打开 ArcGIS Pro 并登录一次即可。

### "Broken pipe" 或连接断开

Claude Desktop 关闭时正常现象，Server 会自动退出。

### 中文路径乱码

确保环境变量中设置了 `PYTHONUTF8=1`。

### Claude Desktop 看不到工具

1. 检查 JSON 配置语法是否正确
2. 重启 Claude Desktop
3. 查看 Claude Desktop 日志（Help → View Logs）
