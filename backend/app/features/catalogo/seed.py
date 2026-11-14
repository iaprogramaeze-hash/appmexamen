"""Seed del catálogo de condiciones (PD-02, cerrado 2026-10-06).

"los valores de es_condicion.limite_materias se siembran como default
(Previa 3, Regular 8, Libre NULL) y quedan editables desde SIGME"
— analisis.txt PD-02. Idempotente por descripción (única, §3.16).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.catalogo.models import EsCondicion

#: (descripcion, limite_materias) — NULL = sin límite (Libre).
CONDICIONES: tuple[tuple[str, int | None], ...] = (
    ("Previa", 3),
    ("Regular", 8),
    ("Libre", None),
)


async def seed_condiciones(db: AsyncSession) -> int:
    """Crea las condiciones faltantes; devuelve cuántas insertó (0 si ya estaban)."""
    existing = set(await db.scalars(select(EsCondicion.descripcion)))
    moment = datetime.now(UTC)
    created = 0
    for descripcion, limite in CONDICIONES:
        if descripcion in existing:
            continue
        db.add(
            EsCondicion(
                id=uuid.uuid4(),
                descripcion=descripcion,
                limite_materias=limite,
                activo=True,
                created_at=moment,
            )
        )
        created += 1
    await db.flush()
    return created
