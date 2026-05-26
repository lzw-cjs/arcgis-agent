# arcgis-agent

AI Agent CLI for ArcGIS Pro automation. 让 AI Agent 通过标准化 CLI 接口操控 ArcGIS Pro，实现 GIS 工作流的自动化和智能化。

## 前置条件

- Windows 10/11
- ArcGIS Pro 3.x（含有效许可证）
- ArcGIS Pro 自带的 Python conda 环境

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/arcgis-agent.git
cd arcgis-agent
```

### 2. 创建 conda 环境

打开 **ArcGIS Python Command Prompt**（开始菜单搜索），或运行：

```cmd
"C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"
```

然后克隆环境并安装依赖：

```bash
conda create -n arcgis-agent --clone arcgispro-py3
conda activate arcgis-agent
pip install -e .
```

### 3. 验证安装

```bash
arcgis-agent --version
```

## 使用方法

### CLI 模式

```bash
# 使用 wrapper 脚本（无需手动激活 conda）
arcgis-agent.bat --version
arcgis-agent.bat --help
```

### MCP Server 模式（供 AI Agent 调用）

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "arcgis-agent": {
      "command": "C:\\path\\to\\arcgis-agent\\arcgis-agent.bat",
      "args": ["mcp-server"]
    }
  }
}
```

## 开发

```bash
conda activate arcgis-agent
pip install -e ".[dev]"
pytest tests/ -v
```

## 许可证

MIT License
