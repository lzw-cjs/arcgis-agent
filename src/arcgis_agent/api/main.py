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
        title="arcgis-agent REST API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )

    # CORS — allow the Vite dev server on localhost:5173
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

        # Shutdown — clear all sessions
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
