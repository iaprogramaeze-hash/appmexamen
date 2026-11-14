"""Service de dispositivos (SDD-4 T6, S6).

Upsert por (usuario_id, device_id) — idempotente. Soft delete en DELETE.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.features.dispositivos.models import EsDispositivo


async def registrar_dispositivo(
    db: AsyncSession, *, usuario_id: uuid.UUID, device_id: str,
    plataforma: str, push_token: str | None,
) -> EsDispositivo:
    """Upsert idempotente: si existe (usuario_id, device_id) vivo, actualiza;
    si no, crea. Maneja carrera con IntegrityError."""
    # Intento de actualización primero (patrón upsert sin ON CONFLICT en SQLite)
    existente = await db.scalar(
        select(EsDispositivo).where(
            EsDispositivo.usuario_id == usuario_id,
            EsDispositivo.device_id == device_id,
            EsDispositivo.deleted_at.is_(None),
        )
    )
    if existente:
        existente.plataforma = plataforma
        existente.push_token = push_token
        existente.activo = True
        existente.updated_at = datetime.now(UTC)
        await db.commit()
        return existente

    # Creación
    ahora = datetime.now(UTC)
    dispositivo = EsDispositivo(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        device_id=device_id,
        plataforma=plataforma,
        push_token=push_token,
        activo=True,
        created_at=ahora,
        updated_at=ahora,
    )
    db.add(dispositivo)
    try:
        await db.commit()
    except IntegrityError:
        # Carrera: otro request lo creó entre el select y el insert
        await db.rollback()
        existente = await db.scalar(
            select(EsDispositivo).where(
                EsDispositivo.usuario_id == usuario_id,
                EsDispositivo.device_id == device_id,
                EsDispositivo.deleted_at.is_(None),
            )
        )
        if existente:
            existente.plataforma = plataforma
            existente.push_token = push_token
            existente.activo = True
            existente.updated_at = datetime.now(UTC)
            await db.commit()
            return existente
        raise
    return dispositivo


async def listar_dispositivos(
    db: AsyncSession, *, usuario_id: uuid.UUID,
) -> list[EsDispositivo]:
    """Lista los dispositivos vivos del usuario."""
    resultado = await db.execute(
        select(EsDispositivo).where(
            EsDispositivo.usuario_id == usuario_id,
            EsDispositivo.deleted_at.is_(None),
        ).order_by(EsDispositivo.created_at.desc())
    )
    return list(resultado.scalars().all())


async def dar_de_baja_dispositivo(
    db: AsyncSession, *, usuario_id: uuid.UUID, dispositivo_id: uuid.UUID,
) -> None:
    """Soft delete: marca deleted_at y activo=false. Idempotente (PD-25):
    repetir devuelve 204 sin error aunque ya esté borrado."""
    dispositivo = await db.scalar(
        select(EsDispositivo).where(
            EsDispositivo.id == dispositivo_id,
            EsDispositivo.usuario_id == usuario_id,
        )
    )
    if dispositivo is None:
        raise NotFoundError("Dispositivo no encontrado", code="dispositivo-no-encontrado")
    if dispositivo.deleted_at is not None:
        return  # ya borrado -> idempotente
    ahora = datetime.now(UTC)
    dispositivo.deleted_at = ahora
    dispositivo.activo = False
    dispositivo.updated_at = ahora
    await db.commit()