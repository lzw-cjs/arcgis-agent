# ArcGIS Agent — Dockerfile
#
# 注意: arcpy 仅在 ArcGIS Pro 环境中可用，无法通过 pip 安装。
# 此 Dockerfile 适用于以下场景:
#   1. 在已安装 ArcGIS Pro 的 Windows 容器中运行
#   2. 不需要 arcpy 的纯 API 模式（功能受限）
#   3. 开发/测试环境
#
# 生产部署建议参考 docs/deployment.md 中的手动部署方式。

FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY src/ ./src/
COPY README.md .
COPY LICENSE .
COPY CHANGELOG.md .

# 安装（不含 arcpy）
RUN pip install --no-cache-dir .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "arcgis_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
