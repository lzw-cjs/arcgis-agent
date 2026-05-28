# MCP Server 安装与配置指南

本文档详细说明如何配置 arcgis-agent MCP Server，让 AI 工具可以直接调用 33 个 GIS 工具。

支持的客户端：Claude Desktop、Claude Code (VS Code)、OpenClaw、Trae IDE/SOLO。

## 前提条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11 |
| ArcGIS Pro | 3.x（含有效许可证，需登录一次） |
| Python | 3.9–3.11（ArcGIS Pro 自带 conda 环境） |
| conda | Miniconda 或 ArcGIS Pro 自带 |

## 安装步骤

### 1. 创建 conda 环境

ArcGIS Pro 自带的 `arcgispro-py3` 环境包含 arcpy，但为了不影响 Pro 本身，建议克隆一个独立环境：

```cmd
:: 打开 ArcGIS Python Command Prompt（开始菜单搜索 "ArcGIS Python"）
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"

:: 克隆环境
conda create -n arcgis-agent --clone arcgispro-py3
conda activate arcgis-agent
```

> **如果 `--clone` 因 404 失败：** 这是 Esri conda 渠道偶尔的问题。解决方法：
> 1. 直接使用 `arcgispro-py3` 环境：`conda activate arcgispro-py3`
> 2. 或手动复制环境目录：找到 `arcgispro-py3` 的路径，复制到新位置并在 `conda config` 中注册

### 2. 安装 arcgis-agent

**从 PyPI 安装（推荐）：**

```bash
pip install arcgis-agent
```

**从源码安装：**

```bash
git clone https://github.com/lzw-cjs/arcgis-agent.git
cd arcgis-agent
pip install .
```

> **中文用户名注意：** 不要使用 `pip install -e .`（editable 模式），会因中文路径编码问题失败。始终使用 `pip install .`。

### 3. 验证环境

```bash
python scripts/check-env.py
```

应全部显示 `[OK]`：

```
  [OK] Python version: Python 3.11.10
  [OK] arcpy: arcpy importable
  [OK] ArcGIS license: ArcGIS Pro license: ArcInfo
  [OK] arcgis-agent package: arcgis-agent 0.1.0 installed

All checks passed. arcgis-agent is ready to use.
```

### 4. 测试 MCP Server

```bash
arcgis-agent-mcp
```

启动后应无报错，等待 stdio 输入。按 Ctrl+C 退出。

## 配置 Claude Desktop

### 方法一：使用 entry point（推荐）

编辑 Claude Desktop 配置文件：

- **Windows：** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS：** `~/Library/Application Support/Claude/claude_desktop_config.json`

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

**适用场景：** `arcgis-agent-mcp` 已在 PATH 中（pip install 后自动注册）。

### 方法二：使用 conda run

如果 entry point 不在 PATH 中（常见于非默认 conda 安装）：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "conda",
      "args": ["run", "-n", "arcgis-agent", "--no-banner", "arcgis-agent-mcp"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**适用场景：** 需要确保在正确的 conda 环境中运行。

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

**适用场景：** 最可靠的方式，直接指向包含 arcpy 的 Python 解释器。

> **如何找到 Python 路径：** 在 arcgis-agent 环境中运行 `where python` 或 `python -c "import sys; print(sys.executable)"`。

## 配置 Claude Code (VS Code)

Claude Code 通过 VS Code 的 MCP 配置连接。在 Settings 中搜索 `mcp`，添加以下配置：

```json
{
  "mcp": {
    "servers": {
      "arcgis-agent": {
        "command": "C:\\conda-envs\\arcgis-agent\\python.exe",
        "args": ["-m", "arcgis_agent.mcp_server"],
        "env": {
          "PYTHONUTF8": "1"
        }
      }
    }
  }
}
```

或编辑 `%APPDATA%\Code\User\mcp.json` 添加相同配置。

## 配置 OpenClaw

OpenClaw（原名 Clawdbot/Moltbot）是 GitHub 上增长最快的开源 AI 智能体（375k+ stars），支持三种 MCP 传输方式（stdio、SSE、streamable-http）。

### 方法一：使用 `openclaw mcp set` 命令

```bash
openclaw mcp set arcgis-agent '{"command":"C:\\conda-envs\\arcgis-agent\\python.exe","args":["-m","arcgis_agent.mcp_server"],"env":{"PYTHONUTF8":"1"},"transport":"stdio"}'
```

**验证：** 运行 `openclaw mcp list`，应看到 `arcgis-agent` 在列表中。

### 方法二：编辑 openclaw.json 配置文件

在 `~/.openclaw/openclaw.json` 的 `mcp.servers` 中添加：

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

添加后需重启 Gateway：

```bash
openclaw gateway restart
```

### 方法三：使用 MCP Bridge 插件

如果 OpenClaw 原生 MCP client 不稳定，可使用社区插件 `@aiwerk/openclaw-mcp-bridge`：

```bash
openclaw plugins install @aiwerk/openclaw-mcp-bridge
```

在 `openclaw.json` 的 `plugins.entries` 中配置：

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

> **关键提示：** `connectionTimeoutMs: 15000` — 默认 5000ms 对 arcpy 操作可能太短（首次导入 arcpy 需数秒）。使用完整二进制路径而非 `npx`，避免冷启动延迟。

## 配置 Trae IDE / Trae SOLO

Trae 是字节跳动推出的 AI IDE，原生支持 MCP Server 集成，并提供 Marketplace 和手动添加两种方式。

### 方法一：通过 UI 添加（推荐）

1. 打开 Trae IDE，点击右上角 **Settings** 图标
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

5. 点击 **Confirm**

### 方法二：项目级 MCP 配置

在项目根目录创建 `.trae/mcp.json`（本项目已包含此文件）：

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

> **注意：** 项目级 MCP 仅在打开对应项目时生效。如果切换到其他项目，需要在该项目中也创建 `.trae/mcp.json`。

### 方法三：全局配置文件

编辑 Trae 的全局 MCP 配置：

- **Trae SOLO CN：** `%APPDATA%\TRAE SOLO CN\User\mcp.json`
- **Trae IDE：** `%APPDATA%\Trae CN\User\mcp.json`

添加 `arcgis-agent` 条目即可，全局生效。

### 方法四：在自定义 Trae Agent 中使用

1. 创建自定义 Trae Agent
2. 在 Agent 配置中勾选要使用的 MCP Server（arcgis-agent）
3. Agent 会自动发现并调用 33 个 GIS 工具

## 可用工具列表

MCP Server 暴露 33 个工具（与 CLI 的 31 个命令对应，外加 2 个 workspace 工具）：

| 类别 | 工具名 | 说明 | 参数 |
|------|--------|------|------|
| **工作区** | `workspace_set` | 设置工作空间目录 | `path: str` |
| | `workspace_get` | 获取当前工作空间路径 | 无参数 |
| **工程** | `project_info` | 获取工程信息（地图、GDB） | `project_path: str` |
| **数据发现** | `data_list` | 列出数据集 | `workspace?, dataset_type?, name_pattern?` |
| | `data_describe` | 描述数据集元数据 | `path: str` |
| | `data_fields` | 列出字段信息 | `path: str` |
| | `data_extent` | 获取空间范围 | `path: str` |
| | `data_count` | 获取要素数量 | `path: str` |
| **数据管理** | `data_copy` | 复制数据集 | `source, destination, no_overwrite?` |
| | `data_delete` | 删除数据集 | `path: str` |
| | `data_rename` | 重命名数据集 | `old_path, new_name` |
| | `data_convert` | 格式转换（shp/gdb/csv/geojson） | `source, destination, output_format, no_overwrite?` |
| **地理处理** | `gp_select` | 按属性选择 | `input_fc, output_fc, where_clause, no_overwrite?` |
| | `gp_clip` | 裁剪 | `input_fc, clip_features, output_fc, no_overwrite?` |
| | `gp_buffer` | 缓冲区 | `input_fc, output_fc, distance, unit?, dissolve_field?, no_overwrite?` |
| | `gp_intersect` | 叠加求交 | `inputs: list, output_fc, no_overwrite?` |
| | `gp_union` | 叠加求并 | `inputs: list, output_fc, no_overwrite?` |
| | `gp_dissolve` | 融合 | `input_fc, output_fc, dissolve_field, no_overwrite?` |
| | `gp_spatial_join` | 空间连接 | `target_fc, join_fc, output_fc, no_overwrite?` |
| | `gp_merge` | 合并 | `inputs: list, output_fc, no_overwrite?` |
| | `gp_project` | 投影变换 | `input_fc, output_fc, spatial_ref_wkid, no_overwrite?` |
| **分析** | `analysis_summary_stats` | 汇总统计 | `input_fc, field_spec, case_field?, output_table?` |
| **地图** | `map_create` | 创建地图 | `map_name, project_path?` |
| | `map_add_layer` | 添加图层 | `map_name, data_path, project_path` |
| | `map_remove_layer` | 移除图层 | `map_name, project_path, layer_name?, layer_index?` |
| | `map_list_layers` | 列出图层 | `map_name, project_path` |
| | `map_set_extent` | 缩放到图层 | `map_name, zoom_to_layer, project_path` |
| | `map_export` | 导出地图（PNG/PDF） | `map_name, output_path, project_path, format?, dpi?, transparent?` |
| | `map_symbolize` | 符号化图层 | `map_name, layer_name, project_path, symbology_type?, field?, color?, ...` |
| | `map_label` | 设置标注 | `map_name, layer_name, field, project_path, font_size?, color?, bold?` |
| **布局** | `layout_create` | 创建布局 | `layout_name, project_path, page_size?, orientation?` |
| | `layout_add_element` | 添加元素（6种类型） | `layout_name, element_type, project_path, position?, params?` |
| | `layout_export` | 导出布局（PNG/PDF） | `layout_name, output_path, project_path, format?, dpi?, transparent?` |

### 使用示例（在 AI 对话中）

```
用户: 请帮我列出当前工作区有哪些数据
AI → 调用 workspace_set 设置路径 → 调用 data_list 列出数据集 → 返回结果

用户: 对道路数据做 500 米缓冲区分析
AI → 调用 gp_buffer(input_fc="roads", output_fc="roads_buffer", distance=500, unit="Meters")

用户: 创建一张包含道路和缓冲区的地图，导出为 PNG
AI → 调用 map_create → map_add_layer(roads) → map_add_layer(buffer) → map_export(format="PNG", dpi=300)
```

## 验证连接

配置完成后，验证步骤：

1. **重启 AI 工具**（Claude Desktop / Trae / OpenClaw gateway）
2. **在对话中测试：** `请列出可用的 MCP 工具` 或 `使用 workspace_set 设置工作空间为 C:\GIS\Projects`
3. **检查工具发现：** 应看到 33 个 arcgis-agent 工具
4. **检查工具调用：** 尝试调用 `data_count` 等简单工具验证执行

## 故障排除

### "arcpy not found"

MCP Server 启动时找不到 arcpy。

**原因：** MCP Server 的 Python 环境中没有 arcpy。

**解决：**
- 确保 `command` 指向 ArcGIS Pro conda 环境中的 Python（如 `C:\conda-envs\arcgis-agent\python.exe`）
- 使用 `conda run -n arcgis-agent` 包装命令
- 运行 `python scripts/check-env.py` 验证环境

### "License not available"

ArcGIS Pro 许可证不可用。

**原因：** ArcGIS Pro 未登录或许可证过期。

**解决：** 打开 ArcGIS Pro GUI，登录 Esri 账户。许可证会在后台刷新。无需每次都打开 Pro，只需确保曾登录过。

### "Broken pipe" 或连接断开

**原因：** AI 工具关闭时正常现象。MCP Server 通过 stdio 通信，客户端断开后 Server 自动退出。

**无需处理。** 这是 MCP stdio 协议的正常行为。

### 中文路径乱码

**原因：** Windows 默认使用 GBK 编码，arcpy 和 MCP 通信需要 UTF-8。

**解决：** 确保所有配置中的 `env` 字段包含 `PYTHONUTF8=1`：

```json
"env": { "PYTHONUTF8": "1" }
```

### AI 工具看不到 arcgis-agent

**排查步骤：**
1. 检查 JSON 配置语法是否正确（特别注意转义字符 `\\`）
2. 检查 `command` 路径是否正确（文件是否存在）
3. 重启 AI 工具
4. 查看 AI 工具的 MCP 日志：
   - Claude Desktop：Help → View Logs
   - Trae：Settings > MCP > 查看服务器状态
   - OpenClaw：`openclaw mcp list` + `openclaw gateway logs`

### 工具调用返回错误

**常见原因：**
- 工作空间未设置（先调用 `workspace_set`）
- 文件路径不存在或格式不对（使用绝对路径）
- .aprx 文件被 ArcGIS Pro GUI 锁定（关闭 Pro 或另存副本）
- CRS 不一致（叠加操作前检查坐标系）

### MCP Server 启动超时

**原因：** arcpy 首次导入需数秒（加载 COM 组件）。

**解决：**
- Trae SOLO：在 `env` 中添加 `START_MCP_TIMEOUT_MS: "60000"`
- OpenClaw：设置 `connectionTimeoutMs: 15000`

### Windows 中文用户名的特殊问题

arcpy.mp 在中文用户名系统上存在已知 bug（`aprx.save()` 会崩溃）。

**影响范围：** 仅影响 Map 和 Layout 的保存操作。数据发现、地理处理等其他功能正常。

**解决：** 在纯英文用户名的 Windows 系统上运行 Map/Layout 操作，或使用 Web API 模式由服务器端处理。