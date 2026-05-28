# ArcGIS Agent 部署指南

本文档说明如何在不同环境中部署 arcgis-agent Web API。

## 前提条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11（arcpy 限制） |
| ArcGIS Pro | 3.x + 有效许可证 |
| Python | 3.9–3.11（ArcGIS Pro conda 环境） |

## 方式一：conda 环境直接部署（推荐）

这是最可靠的部署方式，因为 arcpy 需要 ArcGIS Pro 的 conda 环境。

### 1. 安装

```bash
conda activate arcgis-agent
pip install ".[web]"
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 填入 API 密钥等配置
```

### 3. 启动

```bash
arcgis-agent-web
# 或使用 uvicorn 获得更多控制
uvicorn arcgis_agent.api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> **注意：** 由于 arcpy 非线程安全，workers 必须为 1。

### 4. 验证

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok"}
```

## 方式二：Docker 部署

> **重要限制：** arcpy 无法在标准 Linux Docker 容器中运行。Docker 部署仅适用于
> 不需要 arcpy 的 API 模式，或使用 Windows 容器 + ArcGIS Pro 的场景。

### 标准 Docker（功能受限）

```bash
# 构建镜像
docker build -t arcgis-agent .

# 启动服务
docker compose up -d
```

### Windows 容器 + ArcGIS Pro

如需完整 arcpy 功能，需使用 Windows Server 容器并安装 ArcGIS Pro：

```dockerfile
FROM mcr.microsoft.com/windows/servercore:ltsc2022
# 安装 ArcGIS Pro（需自行准备安装包）
# 安装 Python + conda
# pip install arcgis-agent
```

详情参考 Esri 官方文档。

## 方式三：Windows 服务

使用 NSSM 将 API 注册为 Windows 服务，实现开机自启。

### 1. 安装 NSSM

```powershell
choco install nssm
```

### 2. 注册服务

```powershell
# 以管理员身份运行
nssm install arcgis-agent "C:\conda-envs\arcgis-agent\python.exe" "-m" "arcgis_agent.api.main"
nssm set arcgis-agent AppDirectory "C:\path\to\arcgis-agent"
nssm set arcgis-agent AppEnvironment PYTHONUTF8=1
nssm set arcgis-agent AppStdout "C:\path\to\logs\arcgis-agent-stdout.log"
nssm set arcgis-agent AppStderr "C:\path\to\logs\arcgis-agent-stderr.log"
```

### 3. 管理服务

```powershell
nssm start arcgis-agent
nssm status arcgis-agent
nssm stop arcgis-agent
nssm remove arcgis-agent
```

## 方式四：Linux 部署（无 arcpy）

在 Linux 上可运行 Web API 的聊天和 UI 功能，但所有 arcpy 工具调用会返回错误。

```bash
pip install ".[web,ai]"

# 使用 Systemd 服务
sudo cp scripts/arcgis-agent.service /etc/systemd/system/
sudo systemctl enable arcgis-agent
sudo systemctl start arcgis-agent
```

## 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | development | 环境（development/production） |
| `DEBUG` | false | 调试模式 |
| `API_HOST` | 0.0.0.0 | 监听地址 |
| `API_PORT` | 8000 | 监听端口 |
| `OPENAI_API_KEY` | — | LLM API 密钥 |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | LLM API 地址 |
| `OPENAI_MODEL` | gpt-4o | 使用的模型 |
| `PYTHONUTF8` | — | 强制 UTF-8（Windows 必设） |

## 故障排除

### "arcpy not found"

Web API 可启动，但 GIS 工具调用会失败。确保在 ArcGIS Pro conda 环境中运行。

### 中文路径乱码

设置环境变量 `PYTHONUTF8=1`。

### 端口被占用

修改 `.env` 中的 `API_PORT`，或启动时指定：

```bash
uvicorn arcgis_agent.api.main:app --port 8001
```

### 服务启动后立即退出

检查日志文件中的错误信息。常见原因：许可证不可用、端口冲突。