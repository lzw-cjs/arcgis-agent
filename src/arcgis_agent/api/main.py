"""FastAPI application factory and entry point.

Usage:
    python -m arcgis_agent.api.main   # start server on 127.0.0.1:8000
    arcgis-agent-web                  # via pyproject.toml entry point
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from arcgis_agent.api.dependencies import get_conversation_store
from arcgis_agent.api.middleware import metrics_middleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns a FastAPI instance with:
    - CORS middleware (localhost:5173 for Vite dev server)
    - metrics_middleware for request logging
    - Lifespan handler for ConversationStore init/shutdown
    - Health check at GET /api/v1/health
    """

    app = FastAPI(
        title="ArcGIS Agent - AI 驱动的 GIS 自动化平台",
        description="""
## 概述

基于 LLM 的 GIS 智能代理，支持自然语言驱动的 ArcGIS 操作。

### 核心功能
- **对话式 GIS**：通过自然语言聊天执行地理处理、数据分析、制图输出
- **工具调用**：33 个 GIS 操作 REST 端点（缓冲区、裁剪、相交、符号化、布局导出等）
- **异步任务**：长耗时操作支持后台执行与状态轮询
- **多模态交互**：SSE 流式响应、工具调用可视化、建议生成

### 快速开始
1. 配置 LLM API 密钥（环境变量或 `/api/v1/chat/providers` 查看状态）
2. 设置工作空间 `POST /api/v1/tools/workspace/set`
3. 开始对话 `POST /api/v1/chat`
        """.strip(),
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
        summary="ArcGIS Agent REST API ： AI 驱动的 GIS 自动化",
    )

    # ── OpenAPI Tags (中文) ──────────────────────────────────

    app.openapi_tags = [
        {"name": "Chat", "description": "**对话服务** ： 多轮对话、SSE 流式响应、会话管理、LLM 提供商配置"},
        {"name": "Tools", "description": "**GIS 工具集** ： 33 个地理处理与分析 REST 端点"},
        {"name": "Tasks", "description": "**异步任务** ： 长耗时 GIS 操作的后台执行与状态查询"},
        {"name": "Upload", "description": "**文件上传** ： GIS 数据文件导入（.shp, .zip, .gdb）"},
    ]

    # CORS ： allow the Vite dev server on localhost:5173
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request metrics middleware (raw ASGI middleware)
    app.middleware("http")(metrics_middleware)

    # ── Lifespan ──────────────────────────────────────────────

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Startup: init ConversationStore. Shutdown: cleanup."""
        # Startup
        store = get_conversation_store()
        logger.info("ConversationStore initialized (max_sessions=%d)", store._max_sessions)

        yield

        # Shutdown ： clear all sessions
        logger.info("Shutting down API server")

    app.router.lifespan_context = lifespan

    # ── Task Routes ──────────────────────────────────────────

    from arcgis_agent.api.routes.tasks import router as tasks_router
    app.include_router(tasks_router)

    # ── Tool Routes ──────────────────────────────────────────

    from arcgis_agent.api.routes.tools import router as tools_router
    app.include_router(tools_router)

    # ── Upload Routes ────────────────────────────────────────

    from arcgis_agent.api.routes.upload import router as upload_router
    app.include_router(upload_router)

    # ── Chat Routes ──────────────────────────────────────────

    from arcgis_agent.api.routes.chat import router as chat_router
    app.include_router(chat_router)

    # ── Health Check ──────────────────────────────────────────

    @app.get("/api/v1/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


# ── Module-level app instance (for uvicorn) ──────────────────

app = create_app()


def main() -> None:
    """Entry point for `arcgis-agent-web` CLI command."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
