"""Engine y sesiones async (analisis.txt 5, db/session.py).

Regla operativa de analisis.txt 0 (PD-06 cerrado 2026-10-06): en producción
(Vercel serverless) NO hay proceso persistente, así que se RETIRA el pool TCP
de SQLAlchemy: desaparecen pool_pre_ping y pool_recycle. En desarrollo/local
sí se configuran. El engine se construye bajo demanda: sin DATABASE_URL no hay
engine y la app sigue viva (healthz degrada).
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_engines: dict[tuple[str, bool], AsyncEngine] = {}


def get_engine(database_url: str, *, production: bool) -> AsyncEngine:
    """Engine cacheado por (url, modo). Sólo desarrollo/local usa pool con
    pre_ping/recycle; producción arranca con la configuración por defecto (sin
    esos parámetros)."""
    key = (database_url, production)
    engine = _engines.get(key)
    if engine is None:
        kwargs: dict[str, Any] = {}
        if not production:
            kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
        engine = create_async_engine(database_url, **kwargs)
        _engines[key] = engine
    return engine


async def dispose_engines() -> None:
    """Cierra todos los engines (lifespan shutdown y tests)."""
    for engine in list(_engines.values()):
        await engine.dispose()
    _engines.clear()


def has_engine_configured() -> bool:
    """True sólo si el Settings trae DATABASE_URL."""
    return bool(get_settings().database_url)


async def ping(settings: Settings, timeout: float = 2.0) -> bool:
    """SELECT 1 con tope de tiempo. Sin URL o con cualquier fallo devuelve
    False: el health check informa, nunca se tumba (S6)."""
    if not settings.database_url:
        return False
    try:
        engine = get_engine(settings.database_url, production=settings.is_production)
        async with asyncio.timeout(timeout):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except TimeoutError:
        logger.warning("ping de base de datos expiró tras %ss", timeout)
        return False
    except Exception as exc:  # noqa: BLE001 - degradar es el contrato del healthz
        logger.warning("ping de base de datos falló: %s", exc.__class__.__name__)
        return False


async def get_session() -> AsyncIterator[AsyncSession]:
    """Sesión por petición (la usa get_db de core/dependencies)."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL no está configurada")
    engine = get_engine(settings.database_url, production=settings.is_production)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
