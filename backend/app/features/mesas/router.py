"""Endpoints SIGME de convocatorias (§6: GET|POST /convocatorias, PATCH /{id}).

RBAC temporal patrón SDD-2: lectura por módulo sigme_web; escritura por
usuario.gestionar. Los códigos `convocatoria.*` siguen PENDIENTE en los docs
(CU-11 propone `convocatoria.gestionar`) — se reemplazan apenas el cliente
confirme el código (feature doc SDD-3, L4).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_modulo, require_permiso
from app.features.auth.tokens import Principal
from app.features.mesas import service_convocatoria as service
from app.features.mesas.schemas_convocatoria import (
    ConvocatoriaActualizar,
    ConvocatoriaCrear,
    ConvocatoriaLectura,
)

router = APIRouter(tags=["sigme-mesas"])

_LEER = Depends(require_modulo("sigme_web"))
_GESTIONAR = Depends(require_permiso("usuario.gestionar"))


def _a_lectura(convocatoria) -> ConvocatoriaLectura:
    """Adjunta el estado DERIVADO (doc 04 §4.1) — nunca se persiste."""
    hoy = service.hoy_buenos_aires()
    return ConvocatoriaLectura(
        id=convocatoria.id,
        descripcion=convocatoria.descripcion,
        fecha_inicio_inscripcion=convocatoria.fecha_inicio_inscripcion,
        fecha_fin_inscripcion=convocatoria.fecha_fin_inscripcion,
        activa=convocatoria.activa,
        estado=service.estado_convocatoria(convocatoria, hoy),
    )


@router.get(
    "/convocatorias",
    response_model=list[ConvocatoriaLectura],
)
async def listar_convocatorias(
    _: Principal = _LEER, db: AsyncSession = Depends(get_db)
) -> list[ConvocatoriaLectura]:
    filas = await service.listar_convocatorias(db)
    return [_a_lectura(f) for f in filas]


@router.post(
    "/convocatorias",
    response_model=ConvocatoriaLectura,
    status_code=status.HTTP_201_CREATED,
)
async def crear_convocatoria(
    payload: ConvocatoriaCrear,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> ConvocatoriaLectura:
    fila = await service.crear_convocatoria(db, payload)
    return _a_lectura(fila)


@router.patch(
    "/convocatorias/{convocatoria_id}",
    response_model=ConvocatoriaLectura,
)
async def modificar_convocatoria(
    convocatoria_id: uuid.UUID,
    payload: ConvocatoriaActualizar,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> ConvocatoriaLectura:
    actual = await service.obtener_convocatoria(db, convocatoria_id)
    fila = await service.actualizar_convocatoria(db, actual, payload)
    return _a_lectura(fila)
