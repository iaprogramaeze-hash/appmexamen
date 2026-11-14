"""Endpoints de consultas de alumno y de gestión (SDD-4, CU-23/34..CU-42).

Rutas a raíz bajo /api/v1/ SIN prefijo de dispositivo (feature doc L2): el
contrato es el mismo para web, móvil o webhook. Gate por SESIÓN VÁLIDA
(`get_current_principal`) o permiso — nunca por módulo/dispositivo.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import get_current_principal, require_permiso
from app.features.auth.tokens import Principal
from app.features.inscripciones import service_inscripciones as service
from app.features.inscripciones.schemas_inscripciones import (
    InscripcionCrear,
    InscripcionGestion,
    InscripcionLectura,
    MesaDisponible,
    MisInscripcionLectura,
)
from app.features.mesas.schemas_convocatoria import ConvocatoriaLectura
from app.features.mesas.service_convocatoria import (
    estado_convocatoria,
    hoy_buenos_aires,
)

router = APIRouter(tags=["inscripciones"])


@router.get("/convocatoria-vigente", response_model=ConvocatoriaLectura)
async def convocatoria_vigente(
    _: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> ConvocatoriaLectura:
    """CU-34: la convocatoria vigente con estado derivado (A-SDD4-1).

    Sólo sesión válida: el catálogo §2.7 no tiene código de lectura de
    convocatoria (hueco declarado en CU-34) y el endpoint es la fuente para
    saber si hay ventana abierta — no puede exigir permiso de la ventana.
    """
    fila = await service.convocatoria_vigente(db)
    # Misma construcción que _a_lectura (mesas/router.py): el estado es
    # DERIVADO y la fila ORM no lo trae, por eso no sirve model_validate.
    return ConvocatoriaLectura(
        id=fila.id,
        descripcion=fila.descripcion,
        fecha_inicio_inscripcion=fila.fecha_inicio_inscripcion,
        fecha_fin_inscripcion=fila.fecha_fin_inscripcion,
        activa=fila.activa,
        estado=estado_convocatoria(fila, hoy_buenos_aires()),
    )


@router.get("/mesas-disponibles", response_model=list[MesaDisponible])
async def mesas_disponibles(
    _: Principal = Depends(require_permiso("mesa.listar")),
    db: AsyncSession = Depends(get_db),
) -> list[MesaDisponible]:
    """CU-35 (S2): mesas vivas de la convocatoria vigente, en ventana.

    Permiso `mesa.listar` (agnóstico de dispositivo, L2). Fuera de la
    ventana -> 409 `ventana-cerrada`; RB-22 no aplica (A-SDD4-2): las mesas
    sin inscripciones también se listan. RN-019: sin `grupo_id` ni campos
    del grupo. La cascada G-04 (orientación -> curso -> materia -> condición)
    se deriva de las combinaciones únicas de esta respuesta.
    """
    filas = await service.mesas_disponibles(db)
    return [MesaDisponible.model_validate(fila) for fila in filas]


@router.post(
    "/inscripciones", response_model=InscripcionLectura, status_code=201
)
async def inscribirse(
    datos: InscripcionCrear,
    principal: Principal = Depends(require_permiso("inscripcion.crear")),
    db: AsyncSession = Depends(get_db),
) -> InscripcionLectura:
    """CU-37/CU-40 (S3): inscribirse a la materia y condición elegidas.

    Permiso `inscripcion.crear` (agnóstico de dispositivo, L2). El cuerpo
    sólo admite `materia_id` + `condicion_id` (RB-30); la convocatoria es
    SIEMPRE la vigente (A-SDD4-4) y la mesa se elige por el backend
    (A-SDD4-6: la de fecha más próxima del combo). Valida en orden (spec S3)
    y crea la fila `inscripto`. CU-40: reinscribir tras anular crea una fila
    NUEVA.
    """
    fila = await service.inscribirse(
        db,
        usuario_id=principal.sub,
        materia_id=datos.materia_id,
        condicion_id=datos.condicion_id,
    )
    return InscripcionLectura.model_validate(fila)


@router.get("/inscripciones", response_model=list[InscripcionGestion])
async def inscripciones_gestion(
    mesa_id: UUID | None = Query(default=None),
    convocatoria_id: UUID | None = Query(default=None),
    _: Principal = Depends(require_permiso("inscripcion.listar")),
    db: AsyncSession = Depends(get_db),
) -> list[InscripcionGestion]:
    """CU-23 (S4): listado de gestión con filtros opcionales.

    Permiso `inscripcion.listar` (agnóstico de dispositivo, L2). RB-22 NO
    aplica (lista inscripciones, no mesas). Un filtro que referencia un ID
    inexistente -> 404 `mesa-no-encontrada` / `convocatoria-no-encontrada`.
    Orden `inscripto_en` desc. La anulación por secretaría (INS-03) queda
    FUERA de SDD-4.
    """
    filas = await service.inscripciones_gestion(
        db, mesa_id=mesa_id, convocatoria_id=convocatoria_id
    )
    return [InscripcionGestion.model_validate(fila) for fila in filas]


@router.get("/mis-inscripciones", response_model=list[MisInscripcionLectura])
async def mis_inscripciones(
    principal: Principal = Depends(require_permiso("inscripcion.listar")),
    db: AsyncSession = Depends(get_db),
) -> list[MisInscripcionLectura]:
    """CU-38 (S5): las inscripciones del usuario autenticado.

    Permiso `inscripcion.listar` (agnóstico de dispositivo, L2). Sólo las
    filas PROPIAS, cada una con estado, nombres de materia/condición y
    `fecha`/`hora` de la mesa; nunca grupo (RN-019). Sin paginación
    (A-SDD4-9) y sin exigir ventana: la lectura sigue disponible con la
    ventana cerrada (RB-07).
    """
    filas = await service.mis_inscripciones(db, usuario_id=principal.sub)
    return [
        MisInscripcionLectura(
            id=inscripcion.id,
            mesa_examen_id=mesa.id,
            materia_id=inscripcion.materia_id,
            condicion_id=inscripcion.condicion_id,
            estado=inscripcion.estado,
            materia_nombre=mesa.materia_nombre,
            condicion_nombre=mesa.condicion_nombre,
            fecha=mesa.fecha,
            hora=mesa.hora,
            inscripto_en=inscripcion.inscripto_en,
        )
        for inscripcion, mesa in filas
    ]


@router.delete(
    "/mis-inscripciones/{inscripcion_id}", status_code=204
)
async def anular_inscripcion(
    inscripcion_id: UUID,
    principal: Principal = Depends(require_permiso("inscripcion.anular")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """CU-39/INS-02 (S5): anula la inscripción propia dentro de la ventana.

    Permiso `inscripcion.anular`. Sólo la propia (otro alumno o inexistente
    -> 404, sin filtrar existencia ajena); sólo dentro de la ventana de ESA
    convocatoria (RB-08b) -> fuera, 409 `ventana-cerrada`; `inscripto` ->
    `anulado` (fila conservada, libera la unicidad); ya `anulado` -> 204
    idempotente sin cuerpo (PD-25).
    """
    await service.anular_inscripcion(
        db, usuario_id=principal.sub, inscripcion_id=inscripcion_id
    )
