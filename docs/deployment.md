# ArcGIS Agent 部署指南

本文档详细说明如何在不同环境中部署 arcgis-agent Web API。

## 前提条件

| 条件 | 说明 |
|------|------|
| 操作系统 | Windows 10/11（arcpy 限制） |
| ArcGIS Pro | 3.x + 有效许可证（需登录一次） |
| Python | 3.9–3.11（ArcGIS Pro conda 环境） |
| 内存 | 建议 8GB+（arcpy 导入占用约 200MB） |
| 磁盘 | ArcGIS Pro 约 4GB + conda 环境约 2GB |

## 方式一：conda 环境直接部署（推荐）

这是最可靠的部署方式，因为 arcpy 需要运行在 ArcGIS Pro 的 conda 环境中。

### 1. 安装

```bash
# 创建或激活 conda 环境
conda activate arcgis-agent

# 安装（含 Web 和 AI 依赖）
pip install ".[web,ai]"

# 或从 PyPI 安装后补装可选依赖
pip install arcgis-agent
pip install arcgis-agent[web,ai]
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，至少配置以下项：
# OPENAI_API_KEY=sk-xxx          # LLM API 密钥（AI 对话必需）
# OPENAI_BASE_URL=https://api.openai.com/v1  # 或 DeepSeek/Qwen 等兼容 API
# OPENAI_MODEL=gpt-4o            # 使用的模型
# API_PORT=8000                   # 监听端口
```

### 3. 启动

```bash
# 方式一：使用 entry point
arcgis-agent-web

# 方式二：使用 uvicorn（更多控制）
uvicorn arcgis_agent.api.main:app --host 0.0.0.0 --port 8000 --workers 1

# 方式三：开发模式（自动重载）
uvicorn arcgis_agent.api.main:app --host 0.0.0.0 --port 8000 --reload
```

> **workers 必须为 1：** arcpy 是 COM 组件，非线程安全。多 worker 会导致并发崩溃。arcgis-agent 通过全局 `threading.Lock` + `asyncio.to_thread()` 串行化所有 arcpy 调用。

### 4. 验证

```bash
# 健康检查
curl http://localhost:8000/api/v1/health
# {"status":"ok"}

# Swagger API 文档
# 浏览器打开 http://localhost:8000/docs

# 测试 GIS 工具（需要 arcpy 环境）
curl http://localhost:8000/api/v1/tools/workspace/get
# {"success":true,"code":"OK","message":"Workspace: ...","data":null,"warnings":[]}
```

## 方式二：Windows 服务（开机自启）

使用 NSSM（Non-Sucking Service Manager）将 API 注册为 Windows 服务，实现开机自启和崩溃自动重启。

### 1. 安装 NSSM

```powershell
choco install nssm
# 或从 https://nssm.cc/download 下载
```

### 2. 注册服务

```powershell
# 以管理员身份运行 PowerShell

# 查找 Python 路径
conda activate arcgis-agent
python -c "import sys; print(sys.executable)"
# 输出类似: C:\conda-envs\arcgis-agent\python.exe

# 注册服务
nssm install arcgis-agent "C:\conda-envs\arcgis-agent\python.exe" "-m" "arcgis_agent.api.main"

# 设置工作目录
nssm set arcgis-agent AppDirectory "C:\path\to\arcgis-agent"

# 设置环境变量
nssm set arcgis-agent AppEnvironment PYTHONUTF8=1 APP_ENV=production API_PORT=8000

# 设置日志输出
mkdir C:\path\to\logs
nssm set arcgis-agent AppStdout "C:\path\to\logs\arcgis-agent-stdout.log"
nssm set arcgis-agent AppStderr "C:\path\to\logs\arcgis-agent-stderr.log"

# 设置日志轮转（防止单个日志文件过大）
nssm set arcgis-agent AppRotateFiles 1
nssm set arcgis-agent AppRotateBytes 10485760

# 设置开机自启
nssm set arcgis-agent Start SERVICE_AUTO_START

# 设置崩溃重启策略
nssm set arcgis-agent AppRestartDelay 5000
```

### 3. 管理服务

```powershell
nssm start arcgis-agent       # 启动
nssm status arcgis-agent      # 查看状态
nssm stop arcgis-agent        # 停止
nssm restart arcgis-agent     # 重启
nssm remove arcgis-agent confirm  # 删除服务
```

### 4. 使用脚本一键安装

```powershell
# 使用项目自带的安装脚本
powershell -ExecutionPolicy Bypass -File scripts\install-windows-service.ps1
```

脚本参数：

```powershell
.\scripts\install-windows-service.ps1 -CondaEnv arcgis-agent -InstallDir "C:\arcgis-agent" -Port 8000
```

## 方式三：Docker 部署

> **重要限制：** arcpy 无法在标准 Linux Docker 容器中运行。Docker 部署仅适用于以下场景：
> - 不需要 arcpy 的纯 API/聊天模式（GIS 工具调用会返回错误）
> - 开发和测试
> - 使用 Windows Server 容器 + ArcGIS Pro（复杂，不推荐）

### 标准 Docker（功能受限，无 arcpy）

```bash
# 构建镜像
docker build -t arcgis-agent .

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

docker-compose.yml 会自动加载 `.env` 文件中的环境变量。

### Windows 容器 + ArcGIS Pro（完整功能）

如需完整 arcpy 功能，需使用 Windows Server 容器并安装 ArcGIS Pro：

```dockerfile
# 示例 Dockerfile（需自行准备 ArcGIS Pro 安装包）
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# 安装 ArcGIS Pro（静默安装）
COPY ArcGISPro_3x.msi C:\install\
RUN msiexec /i C:\install\ArcGISPro_3x.msi /qn ACCEPTEULA=1

# 安装 Python 依赖
RUN "C:\Program Files\ArcGIS\Pro\bin\Python\Scripts\proenv.bat" && pip install arcgis-agent

EXPOSE 8000
CMD ["C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe", "-m", "arcgis_agent.api.main"]
```

> 此方式需要 Windows Server 容器运行时和 ArcGIS Pro 许可证，部署复杂度较高。建议优先使用方式一或方式二。

## 方式四：Linux 部署（无 arcpy）

在 Linux 上可运行 Web API 的聊天和 UI 功能，但所有 arcpy 工具调用会返回 `ArcGISError`。

```bash
# 安装
pip install ".[web,ai]"

# 启动
uvicorn arcgis_agent.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> Linux 无 arcpy 限制，可以使用多 worker。

### Systemd 服务

```bash
# 复制服务文件
sudo cp scripts/arcgis-agent.service /etc/systemd/system/

# 编辑服务文件中的路径
sudo nano /etc/systemd/system/arcgis-agent.service
# 修改 User、WorkingDirectory、ExecStart 为实际路径

# 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable arcgis-agent
sudo systemctl start arcgis-agent

# 查看状态
sudo systemctl status arcgis-agent

# 查看日志
sudo journalctl -u arcgis-agent -f
```

### Nginx 反向代理（生产环境）

```nginx
server {
    listen 80;
    server_name gis-api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

## API 端点参考

### 同步端点（立即返回结果）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/tools/workspace/set` | 设置工作空间 |
| GET | `/api/v1/tools/workspace/get` | 获取工作空间 |
| GET | `/api/v1/tools/project/info` | 工程信息 |
| POST | `/api/v1/tools/data/list` | 列出数据集 |
| POST | `/api/v1/tools/data/describe` | 描述数据集 |
| POST | `/api/v1/tools/data/fields` | 字段信息 |
| POST | `/api/v1/tools/data/extent` | 空间范围 |
| POST | `/api/v1/tools/data/count` | 要素数量 |
| POST | `/api/v1/tools/data/copy` | 复制数据 |
| POST | `/api/v1/tools/data/delete` | 删除数据 |
| POST | `/api/v1/tools/data/rename` | 重命名 |
| POST | `/api/v1/tools/data/convert` | 格式转换 |
| POST | `/api/v1/tools/analysis/summary-stats` | 汇总统计 |
| POST | `/api/v1/tools/map/create` | 创建地图 |
| POST | `/api/v1/tools/map/add-layer` | 添加图层 |
| POST | `/api/v1/tools/map/list-layers` | 列出图层 |
| POST | `/api/v1/tools/map/set-extent` | 缩放图层 |
| GET | `/api/v1/chat/providers` | 查看可用 LLM |
| GET | `/api/v1/tasks` | 列出最近任务 |

### 异步端点（返回 task_id，需轮询）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tools/gp/select` | 属性选择 |
| POST | `/api/v1/tools/gp/clip` | 裁剪 |
| POST | `/api/v1/tools/gp/buffer` | 缓冲区 |
| POST | `/api/v1/tools/gp/intersect` | 叠加求交 |
| POST | `/api/v1/tools/gp/union` | 叠加求并 |
| POST | `/api/v1/tools/gp/dissolve` | 融合 |
| POST | `/api/v1/tools/gp/spatial-join` | 空间连接 |
| POST | `/api/v1/tools/gp/merge` | 合并 |
| POST | `/api/v1/tools/gp/project` | 投影变换 |
| POST | `/api/v1/tools/map/export` | 导出地图 |
| POST | `/api/v1/tools/layout/create` | 创建布局 |
| POST | `/api/v1/tools/layout/add-element` | 添加元素 |
| POST | `/api/v1/tools/layout/export` | 导出布局 |
| POST | `/api/v1/tasks` | 创建自定义任务 |
| GET | `/api/v1/tasks/{task_id}` | 查询任务状态 |

### SSE 流式端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat` | AI 对话（SSE 流式返回） |
| DELETE | `/api/v1/chat/{session_id}` | 清除会话 |

### 文件上传

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/upload` | 上传 GIS 数据（.shp/.zip/.gdb） |

## 环境变量参考

| 变量 | 默认值 | 必需 | 说明 |
|------|--------|------|------|
| `APP_ENV` | development | 否 | 环境模式（development/production） |
| `DEBUG` | false | 否 | 调试模式（启用详细日志） |
| `API_HOST` | 0.0.0.0 | 否 | 监听地址 |
| `API_PORT` | 8000 | 否 | 监听端口 |
| `OPENAI_API_KEY` | — | 是 | LLM API 密钥（AI 对话必需） |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | 否 | LLM API 地址（可改为 DeepSeek/Qwen） |
| `OPENAI_MODEL` | gpt-4o | 否 | 使用的模型名称 |
| `PYTHONUTF8` | — | 推荐 | 强制 UTF-8 编码（Windows 中文环境必设） |

### 支持的 LLM 提供商

| 提供商 | `OPENAI_BASE_URL` | `OPENAI_MODEL` | 说明 |
|--------|-------------------|----------------|------|
| OpenAI | https://api.openai.com/v1 | gpt-4o | 默认 |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat | 性价比高 |
| Qwen (通义千问) | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus | 国内访问快 |
| Azure OpenAI | https://{resource}.openai.azure.com/ | gpt-4o | 企业用户 |

## 故障排除

### "arcpy not found"

Web API 可启动，但 GIS 工具调用会失败。

**解决：** 确保在 ArcGIS Pro conda 环境中运行。运行 `python scripts/check-env.py` 验证。

### 中文路径乱码

**解决：** 设置环境变量 `PYTHONUTF8=1`。在 `.env` 文件、NSSM 环境变量或 Systemd Environment 中添加。

### 端口被占用

```bash
# 修改端口
# 方式一：修改 .env 中的 API_PORT
# 方式二：启动时指定
uvicorn arcgis_agent.api.main:app --port 8001

# Windows 查看端口占用
netstat -ano | findstr :8000

# Linux 查看端口占用
ss -tlnp | grep 8000
```

### 服务启动后立即退出

**常见原因：**
- ArcGIS 许可证不可用 → 先打开 ArcGIS Pro 登录一次
- 端口冲突 → 更换端口
- Python 环境错误 → 检查 `which python` 是否指向正确环境

**查看错误日志：**
- NSSM 服务：查看 `AppStdout`/`AppStderr` 指定的日志文件
- Systemd：`journalctl -u arcgis-agent -n 50`
- 直接运行：在终端中执行 `arcgis-agent-web` 查看输出

### .aprx 文件被锁定

ArcGIS Pro 打开 .aprx 文件时会加锁，导致 API 无法修改。

**解决：** 关闭 ArcGIS Pro，或使用 .aprx 的副本进行操作。

### 性能问题

- **首次请求慢：** arcpy 首次导入需 3-5 秒（加载 COM 组件），后续请求正常
- **地理处理超时：** 大数据集操作可能需要数分钟，使用异步端点（返回 task_id）
- **内存占用高：** arcpy 常驻内存约 200MB，大数据处理可能更高

### 安全建议

- 生产环境不要暴露 `0.0.0.0`，使用 Nginx 反向代理并限制访问
- `OPENAI_API_KEY` 不要提交到 git，使用 `.env` 文件
- 定期更新依赖：`pip install --upgrade arcgis-agent`