"""Endpoints de dispositivos (SDD-4 T6, S6).

Rutas a raíz bajo /api/v1/ SIN prefijo de dispositivo (L2). Gate por SESIÓN
VÁLIDA (`get_current_principal`) — el usuario gestiona SUS dispositivos.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import get_current_principal
from app.features.auth.tokens import Principal
from app.features.dispositivos import service
from app.features.dispositivos.schemas import (
    DispositivoCrear,
    DispositivoLectura,
)

router = APIRouter(tags=["dispositivos"])


@router.post(
    "/dispositivos", response_model=DispositivoLectura, status_code=201
)
async def registrar_dispositivo(
    datos: DispositivoCrear,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> DispositivoLectura:
    """Registra o actualiza (upsert) un dispositivo del usuario autenticado.

    Idempotente por `device_id` del usuario. No requiere permiso extra:
    el usuario gestiona sus propios dispositivos.
    """
    fila = await service.registrar_dispositivo(
        db,
        usuario_id=principal.sub,
        device_id=datos.device_id,
        plataforma=datos.plataforma.value,
        push_token=datos.push_token,
    )
    return DispositivoLectura.model_validate(fila)


@router.get("/dispositivos", response_model=list[DispositivoLectura])
async def listar_dispositivos(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> list[DispositivoLectura]:
    """Lista los dispositivos del usuario autenticado."""
    filas = await service.listar_dispositivos(db, usuario_id=principal.sub)
    return [DispositivoLectura.model_validate(fila) for fila in filas]


@router.delete("/dispositivos/{dispositivo_id}", status_code=204)
async def dar_de_baja_dispositivo(
    dispositivo_id: UUID,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Da de baja (soft delete) un dispositivo propio.

    Idempotente: repetir devuelve 204.
    """
    await service.dar_de_baja_dispositivo(
        db, usuario_id=principal.sub, dispositivo_id=dispositivo_id
    )