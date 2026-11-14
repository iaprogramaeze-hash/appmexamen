"""Rutas públicas de preinscripción (landing).

La preinscripción es una anotación a la escuela para futuros alumnos:
NO requiere autenticación y NO tiene relación con las mesas de examen
(PD-01, §3.20). Sólo hay UNA ventana vigente; fuera de ella el POST
responde 409 ventana-cerrada (§3.21).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import ConflictError
from app.core.fechas import hoy_buenos_aires
from app.features.preinscripcion.models import PrPreinscripcion, PrVentana
from app.features.preinscripcion.pydantic import PreInscripcionAccion, PreInscripcionCreate

router = APIRouter(prefix="/preinscripcion", tags=["preinscripción"])


async def _ventana_activa(db: AsyncSession) -> PrVentana | None:
    """Ventana vigente: activa, sin deleted_at y cuyo rango contiene hoy.

    RB-23: `hoy` es la fecha de calendario en America/Argentina/Buenos_Aires,
    no la del servidor.
    """
    hoy = hoy_buenos_aires()
    return await db.scalar(
        select(PrVentana)
        .where(
            PrVentana.activa == true(),
            PrVentana.deleted_at.is_(None),
            PrVentana.fecha_desde <= hoy,
            PrVentana.fecha_hasta >= hoy,
        )
        .limit(1)
    )


@router.post("/", status_code=201, response_model=PreInscripcionAccion)
async def crear_preinscripcion(
    payload: PreInscripcionCreate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> PreInscripcionAccion:
    """Upsert de preinscripción sin login (RB-13, §6, doc 11 §11.4).

    - 201 { accion: "creada" }: identidad nueva → INSERT.
    - 200 { accion: "actualizada" }: identidad existente → UPDATE de campos
      mutables (reenviar el formulario no es error, RB-13).
    - 409 ventana-cerrada: SÓLO por ventana cerrada (§3.21). Un documento
      repetido JAMÁS devuelve 409 (§6).
    - Guarda metadata de servidor: ip, user_agent y utm_*.
    """
    ventana = await _ventana_activa(db)
    if ventana is None:
        raise ConflictError("La ventana de preinscripción está cerrada", code="ventana-cerrada")

    identidad = (
        PrPreinscripcion.anio_lectivo == ventana.anio_lectivo,
        PrPreinscripcion.documento == payload.documento,
    )
    existente = await db.scalar(select(PrPreinscripcion).where(*identidad))
    if existente is not None:
        response.status_code = 200
        return await _actualizar_reenvio(db, existente, payload, request)

    nuevo = PrPreinscripcion(
        id=uuid.uuid4(),
        nombre_alumno=payload.nombre_alumno,
        documento=payload.documento,
        fecha_nacimiento=payload.fecha_nacimiento,
        orientacion=payload.orientacion,
        nombre_tutor=payload.nombre_tutor,
        email=payload.email,
        anio_lectivo=ventana.anio_lectivo,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        utm_source=request.query_params.get("utm_source"),
        utm_medium=request.query_params.get("utm_medium"),
        utm_campaign=request.query_params.get("utm_campaign"),
        estado="pendiente",
        created_at=datetime.now(UTC),
    )
    db.add(nuevo)
    try:
        await db.commit()
    except IntegrityError:
        # Concurrencia (NFR-029, doc 11 §11.4.1): dos envíos simultáneos con
        # la misma identidad; uq_preinscripcion_unica garantiza una sola fila.
        # El que pierde el INSERT vuelve como actualización → 200, nunca 500.
        await db.rollback()
        existente = await db.scalar(select(PrPreinscripcion).where(*identidad))
        if existente is None:
            raise  # no era el índice único: 500 honesto
        response.status_code = 200
        return await _actualizar_reenvio(db, existente, payload, request)

    response.status_code = 201
    return PreInscripcionAccion(accion="creada")


async def _actualizar_reenvio(
    db: AsyncSession,
    fila: PrPreinscripcion,
    payload: PreInscripcionCreate,
    request: Request,
) -> PreInscripcionAccion:
    """UPDATE del reenvío (doc 11 §11.4.1): campos mutables solamente.

    Cambian los 5 campos del cliente menos `documento` (identidad) y la
    metadata del último contacto (§3.20). NO se tocan: `anio_lectivo` y
    `documento` (identidad), `created_at` (conservado) y `estado` (fuera de
    la lista de mutables). `updated_at` lo refresca el trigger (§1.6).
    """
    fila.nombre_alumno = payload.nombre_alumno
    fila.fecha_nacimiento = payload.fecha_nacimiento
    fila.orientacion = payload.orientacion
    fila.nombre_tutor = payload.nombre_tutor
    fila.email = payload.email
    fila.ip = request.client.host if request.client else None
    fila.user_agent = request.headers.get("user-agent")
    fila.utm_source = request.query_params.get("utm_source")
    fila.utm_medium = request.query_params.get("utm_medium")
    fila.utm_campaign = request.query_params.get("utm_campaign")
    await db.commit()
    return PreInscripcionAccion(accion="actualizada")
