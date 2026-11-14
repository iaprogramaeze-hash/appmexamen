"""Endpoints SIGME de grupos de mesas (§6: POST|PATCH|GET /grupos).

A diferencia de convocatorias (T1) y ventanas (T2), los códigos de permiso
SÍ existen — §2.7 y §6 (`analisis.txt:1101-1112`): crear un grupo exige
`mesa.crear`; mover la fecha/hora exige `mesa.modificar`; listar exige
`mesa.listar`. Sin permisos nuevos.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.auth.tokens import Principal
from app.features.mesas import service_grupos as service
from app.features.mesas.schemas_grupo import (
    GrupoCreado,
    GrupoCrear,
    GrupoLectura,
    GrupoMover,
)

router = APIRouter(tags=["sigme-mesas"])

_CREAR = Depends(require_permiso("mesa.crear"))
_MODIFICAR = Depends(require_permiso("mesa.modificar"))
_LISTAR = Depends(require_permiso("mesa.listar"))


def _a_lectura(grupo) -> GrupoLectura:
    return GrupoLectura.model_validate(grupo)


@router.post(
    "/grupos",
    response_model=GrupoCreado,
    status_code=status.HTTP_201_CREATED,
)
async def crear_grupo(
    payload: GrupoCrear,
    _: Principal = _CREAR,
    db: AsyncSession = Depends(get_db),
) -> GrupoCreado:
    """RB-28: crea el grupo y N = materias × condiciones mesas de una."""
    fila, mesas_creadas = await service.crear_grupo(db, payload)
    return GrupoCreado(
        **_a_lectura(fila).model_dump(), mesas_creadas=mesas_creadas
    )


@router.patch(
    "/grupos/{grupo_id}",
    response_model=GrupoLectura,
)
async def mover_grupo(
    grupo_id: uuid.UUID,
    payload: GrupoMover,
    _: Principal = _MODIFICAR,
    db: AsyncSession = Depends(get_db),
) -> GrupoLectura:
    """RB-29/CU-16: mueve el grupo y todas sus mesas en la misma
    transacción; con ventana de inscripción abierta responde 409 (PD-12)."""
    fila = await service.mover_grupo(db, grupo_id, payload)
    return _a_lectura(fila)


@router.get(
    "/grupos",
    response_model=list[GrupoLectura],
)
async def listar_grupos(
    convocatoria_id: uuid.UUID,
    _: Principal = _LISTAR,
    db: AsyncSession = Depends(get_db),
) -> list[GrupoLectura]:
    """CU-17/RB-27: lista los grupos de una convocatoria."""
    filas = await service.listar_grupos(db, convocatoria_id)
    return [_a_lectura(f) for f in filas]
