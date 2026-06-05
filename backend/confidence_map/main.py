"""FastAPI application entry point."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from confidence_map.api.analysis import router as analysis_router
from confidence_map.api.chat import router as chat_router
from confidence_map.core.settings import get_settings


def _app_version() -> str:
    try:
        return pkg_version("confidence-map")
    except PackageNotFoundError:
        return "dev"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    _version = _app_version()

    app = FastAPI(
        title="Confidence Map API",
        description="AI Architecture & Delivery Intelligence Platform",
        version=_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.include_router(analysis_router)
    app.include_router(chat_router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "version": _version,
            "mode": "demo" if settings.demo_mode else "live",
        }

    return app


app = create_app()
