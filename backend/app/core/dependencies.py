"""Dependencias compartidas de FastAPI (analisis.txt 5, core/dependencies.py).

Sólo se declara lo que toda petición necesita. require_permiso() y
require_modulo() (§2.7/§2.8) NO viven acá: están con get_current_principal en
app/features/auth/dependencies.py (SDD-1 T4), porque construyen sobre Principal
y core no debe importar un dominio.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session


async def get_db() -> AsyncIterator[AsyncSession]:
    """Una sesión de SQLAlchemy por petición; el caller decide commit/rollback."""
    async for session in get_session():
        yield session
