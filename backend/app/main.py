"""create_app() factory + lifespan (analisis.txt 5, app/main.py)."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_error_handlers
from app.core.logging import configure_logging
from app.db.session import dispose_engines
from app.features.health.router import router as health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    logger.info("arranque environment=%s version=%s", settings.environment, settings.app_version)
    yield
    await dispose_engines()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory: los routers de dominio cuelgan de /api/v1; /healthz queda en raíz
    por ser contrato operativo, no de negocio."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = settings

    # analisis.txt 0: servicio independiente -> CORS obligatorio, nunca "*".
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # PD-24: contrato de error único para TODA la API (§6).
    register_error_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
