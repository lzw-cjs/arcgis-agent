"""FastAPI application factory (Phase 7).

Creates and configures the FastAPI app with all route modules.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns a fully configured app with all routes registered,
    CORS enabled for local development, and health check endpoint.
    """
    app = FastAPI(
        title="arcgis-agent API",
        description="AI-powered ArcGIS Pro automation API",
        version="1.0.0",
    )

    # CORS: allow local development origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check ──

    @app.get("/api/v1/health")
    def health_check():
        return {"status": "ok"}

    # ── Register route modules ──

    from arcgis_agent.api.routes.chat import router as chat_router
    from arcgis_agent.api.routes.tasks import router as tasks_router
    from arcgis_agent.api.routes.tools import router as tools_router
    from arcgis_agent.api.routes.upload import router as upload_router

    app.include_router(chat_router)
    app.include_router(tasks_router)
    app.include_router(tools_router)
    app.include_router(upload_router)

    return app


def main():
    """Entry point for uvicorn server."""
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
