"""Health check operativo (S6)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.db.session import ping

logger = logging.getLogger(__name__)

router = APIRouter(tags=["salud"])


@router.get("/healthz", summary="Estado de la aplicación y de la base")
async def healthz(request: Request) -> dict[str, str]:
    """200 siempre: informa estado y degrada a db=unavailable sin tumbarse.

    Lee los settings de la app (app.state), no el singleton: cada aplicación
    creada con create_app(settings) responde con su propia configuración.
    """
    settings = request.app.state.settings
    db_ok = await ping(settings)
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "db": "ok" if db_ok else "unavailable",
    }
