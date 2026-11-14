"""Endpoints SIGME de mesas (§6: GET|PATCH /mesas — CU-19 y CU-20).

Los códigos de permiso existen (§2.7/§6): las lecturas exigen
`mesa.listar`; la reasignación exige `mesa.modificar`. El ORDEN de
declaración importa: `/mesas/por-fecha` va ANTES de `/mesas/{mesa_id}`
para que el literal no caiga en el parámetro UUID.
"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.auth.tokens import Principal
from app.features.mesas import service_mesas as service
from app.features.mesas.schemas_mesas import CoberturaPar, MesaAsignar, MesaLectura

router = APIRouter(tags=["sigme-mesas"])

_LISTAR = Depends(require_permiso("mesa.listar"))
_MODIFICAR = Depends(require_permiso("mesa.modificar"))


@router.get("/mesas", response_model=list[MesaLectura])
async def listar_mesas(
    convocatoria_id: uuid.UUID | None = None,
    materia_id: uuid.UUID | None = None,
    condicion_id: uuid.UUID | None = None,
    _: Principal = _LISTAR,
    db: AsyncSession = Depends(get_db),
) -> list[MesaLectura]:
    """CU-19/RB-22: sólo mesas con inscripción activa y sin vencer."""
    filas = await service.listar_mesas(
        db,
        convocatoria_id=convocatoria_id,
        materia_id=materia_id,
        condicion_id=condicion_id,
    )
    return [MesaLectura.model_validate(f) for f in filas]


@router.get("/mesas/por-fecha", response_model=list[MesaLectura])
async def mesas_por_fecha(
    desde: date,
    hasta: date,
    convocatoria_id: uuid.UUID | None = None,
    _: Principal = _LISTAR,
    db: AsyncSession = Depends(get_db),
) -> list[MesaLectura]:
    """RB-23: rango inclusive sobre la fecha de la mesa; desde/hasta
    obligatorios (422 validacion si faltan o el rango está invertido)."""
    filas = await service.mesas_por_fecha(
        db, desde, hasta, convocatoria_id=convocatoria_id
    )
    return [MesaLectura.model_validate(f) for f in filas]


@router.get("/mesas/{mesa_id}", response_model=MesaLectura)
async def obtener_mesa(
    mesa_id: uuid.UUID,
    _: Principal = _LISTAR,
    db: AsyncSession = Depends(get_db),
) -> MesaLectura:
    """CU-19: detalle con estado DERIVADO (vencida → cerrada, A-SDD3-6)."""
    fila = await service.obtener_mesa(db, mesa_id)
    lectura = MesaLectura.model_validate(fila)
    return lectura.model_copy(update={"estado": service.estado_derivado(fila)})


@router.patch("/mesas/{mesa_id}", response_model=MesaLectura)
async def reasignar_mesa(
    mesa_id: uuid.UUID,
    payload: MesaAsignar,
    _: Principal = _MODIFICAR,
    db: AsyncSession = Depends(get_db),
) -> MesaLectura:
    """CU-20/RB-11: reasigna materia/condición y recalcula los snapshots."""
    fila = await service.reasignar_mesa(db, mesa_id, payload)
    return MesaLectura.model_validate(fila)


@router.get("/cobertura-mesas", response_model=list[CoberturaPar])
async def cobertura_mesas(
    convocatoria_id: uuid.UUID,
    _: Principal = _LISTAR,
    db: AsyncSession = Depends(get_db),
) -> list[CoberturaPar]:
    """RB-31/CU-21: materias × condiciones SIN mesa (advisory, PD-15) — se
    consulta ANTES de abrir la ventana de inscripción."""
    filas = await service.cobertura_mesas(db, convocatoria_id)
    return [
        CoberturaPar(
            materia_id=materia.id,
            orientacion_nombre=orientacion.descripcion,
            curso_nombre=curso.descripcion,
            materia_nombre=materia.descripcion,
            condicion_id=condicion.id,
            condicion_nombre=condicion.descripcion,
        )
        for materia, curso, orientacion, condicion in filas
    ]
