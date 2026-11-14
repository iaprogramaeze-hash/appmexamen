"""Entorno de Alembic: async sobre asyncpg + metadata de todos los modelos.

§0 (PD-06): las migraciones corren desde CI/local sobre la conexión DIRECTA —
el host con sufijo `-pooler` se omite porque PgBouncer en modo transaction no
soporta DDL confiable. `MIGRATE_DATABASE_URL` (si existe) tiene prioridad y se
usa tal cual.
"""
from __future__ import annotations

import asyncio
import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.features.catalogo.models  # noqa: F401
import app.features.mesas.models  # noqa: F401
import app.features.personas.models  # noqa: F401
import app.features.preinscripcion.models  # noqa: F401
import app.features.usuarios.models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

logger = logging.getLogger("alembic.env")


def _database_url() -> str:
    """URL de migración: MIGRATE_DATABASE_URL > DATABASE_URL sin `-pooler`."""
    explicit = os.environ.get("MIGRATE_DATABASE_URL")
    if explicit:
        return explicit
    url = Settings().database_url
    if not url:
        raise RuntimeError(
            "Falta la base: definí MIGRATE_DATABASE_URL o DATABASE_URL (.env) para las migraciones"
        )
    if "-pooler." in url:
        logger.info("migraciones: se omite '-pooler' -> conexión directa (analisis.txt 0)")
        url = url.replace("-pooler.", ".", 1)
    return url


def run_migrations_offline() -> None:
    """Modo offline: renderiza el SQL sin conexión (usado por la verificación)."""
    # Elección de dialecto = postgresql; el driver concreto no importa acá.
    url = _database_url().replace("postgresql://", "postgresql+asyncpg://", 1)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = async_engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Modo online: requiere conexión (CI/local sobre el host directo, §0)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
