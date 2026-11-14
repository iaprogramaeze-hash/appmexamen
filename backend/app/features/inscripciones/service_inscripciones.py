"""Consultas de alumno (SDD-4, CU-34/35): convocatoria vigente y mesas.

T1/CU-34 — `convocatoria_vigente`: A-SDD4-1 define "vigente" como la de
estado `abierta` si existe; si no, la `activa` con
`fecha_inicio_inscripcion` más reciente (responde `borrador`/`cerrada`);
sin ninguna convocatoria activa viva -> 404 `convocatoria-no-encontrada`.

T2/CU-35 — `mesas_disponibles`: sólo dentro de la ventana de inscripción
(RB-07/RB-23) -> fuera, 409 `ventana-cerrada`. Devuelve las mesas VIVAS
(`deleted_at IS NULL`) de la convocatoria vigente; RB-22 NO aplica
(A-SDD4-2/PD-23: las mesas sin inscripciones SÍ aparecen) y RN-019 prohíbe
exponer `grupo_id` ni campos del grupo (la cascada G-04 se deriva de los
nombres de esta misma respuesta).

T3/S3 (CU-37/CU-40) — `inscribirse`: valida en orden (spec S3): convocatoria
vigente -> ventana abierta -> materia/condición activas -> unicidad por
materia × convocatoria (RN-006) -> límite de la condición (RN-013/PD-02) ->
mesa viva del combo (A-SDD4-5/PD-19); crea la fila `inscripto` eligiendo la
mesa de fecha más próxima (A-SDD4-6, determinismo). Reutiliza
`convocatoria_vigente`/`ventana_inscripcion_abierta` (SDD-3 T1).

Ambas reutilizan `estado_convocatoria`/`ventana_inscripcion_abierta`
(SDD-3 T1): nunca se persiste el estado, se recalcula con `hoy` en
America/Argentina/Buenos_Aires.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.features.catalogo.models import EsCondicion, EsMateria
from app.features.mesas.models import EsConvocatoria, EsMesaExamen, EsMesaInscripcion
from app.features.mesas.service_convocatoria import (
    estado_convocatoria,
    hoy_buenos_aires,
    obtener_convocatoria,
    ventana_inscripcion_abierta,
)
from app.features.mesas.service_mesas import obtener_mesa


async def convocatoria_vigente(db: AsyncSession) -> EsConvocatoria:
    """La convocatoria vigente según A-SDD4-1 (orden determinístico)."""
    hoy = hoy_buenos_aires()
    resultado = await db.execute(
        select(EsConvocatoria)
        .where(
            EsConvocatoria.activa.is_(True),
            EsConvocatoria.deleted_at.is_(None),
        )
        .order_by(EsConvocatoria.fecha_inicio_inscripcion.desc())
    )
    candidatas = list(resultado.scalars().all())
    if not candidatas:
        raise NotFoundError(
            "Convocatoria no encontrada", code="convocatoria-no-encontrada"
        )
    for convocatoria in candidatas:
        if estado_convocatoria(convocatoria, hoy) == "abierta":
            return convocatoria
    return candidatas[0]


async def mesas_disponibles(db: AsyncSession) -> list[EsMesaExamen]:
    """CU-35 (S2): las mesas VIVAS de la convocatoria vigente.

    "Sólo dentro de la ventana de inscripción" (§6, RB-07/RB-23): la
    convocatoria vigente puede existir con la ventana cerrada (`borrador`
    antes del inicio, `cerrada` después del fin) — en ese caso el endpoint
    no participa y responde 409 `ventana-cerrada`. Orden determinístico
    (fecha, hora, id) para que el cliente cachee sin saltos (RB-26).
    """
    convocatoria = await convocatoria_vigente(db)
    if not ventana_inscripcion_abierta(convocatoria):
        raise ConflictError(
            "La ventana de inscripción está cerrada", code="ventana-cerrada"
        )
    resultado = await db.execute(
        select(EsMesaExamen)
        .where(
            EsMesaExamen.convocatoria_id == convocatoria.id,
            EsMesaExamen.deleted_at.is_(None),
        )
        .order_by(EsMesaExamen.fecha, EsMesaExamen.hora, EsMesaExamen.id)
    )
    return list(resultado.scalars().all())


async def inscribirse(
    db: AsyncSession, *, usuario_id: uuid.UUID, materia_id: uuid.UUID,
    condicion_id: uuid.UUID,
) -> EsMesaInscripcion:
    """CU-37/CU-40 (S3): alta de inscripción con las validaciones en orden.

    La convocatoria es SIEMPRE la vigente (A-SDD4-4: no viaja en el cuerpo).
    En orden: (1) convocatoria vigente -> 404; (2) ventana abierta -> 409;
    (3) materia/condición activas -> 404; (4) unicidad por materia ×
    convocatoria (RN-006) -> 409; (5) límite de la condición, NULL = sin
    límite (RN-013/PD-02) -> 409; (6) mesa viva del combo (A-SDD4-5/PD-19)
    -> 409, eligiendo la de `fecha` más próxima con `hora`/`id` de
    desempate (A-SDD4-6). Crea la fila `inscripto` (CU-40: reinscribir tras
    anular es un alta de fila NUEVA — `anulado` queda fuera de `uq_inscripcion_unica`).
    """
    convocatoria = await convocatoria_vigente(db)
    if not ventana_inscripcion_abierta(convocatoria):
        raise ConflictError(
            "La ventana de inscripción está cerrada", code="ventana-cerrada"
        )
    materia = await db.scalar(
        select(EsMateria).where(
            EsMateria.id == materia_id,
            EsMateria.activo.is_(True),
            EsMateria.deleted_at.is_(None),
        )
    )
    if materia is None:
        raise NotFoundError("Materia no encontrada", code="materia-no-encontrada")
    condicion = await db.scalar(
        select(EsCondicion).where(
            EsCondicion.id == condicion_id,
            EsCondicion.activo.is_(True),
            EsCondicion.deleted_at.is_(None),
        )
    )
    if condicion is None:
        raise NotFoundError("Condición no encontrada", code="condicion-no-encontrada")

    # RN-006/RB-08: unicidad por materia × convocatoria; un 'anulado' no ocupa.
    base = (
        EsMesaInscripcion.convocatoria_id == convocatoria.id,
        EsMesaInscripcion.usuario_id == usuario_id,
        EsMesaInscripcion.deleted_at.is_(None),
        EsMesaInscripcion.estado != "anulado",
    )
    duplicada = await db.scalar(
        select(EsMesaInscripcion.id).where(*base, EsMesaInscripcion.materia_id == materia_id)
    )
    if duplicada is not None:
        raise ConflictError(
            "Ya está inscripto a esta materia en esta convocatoria",
            code="inscripcion-duplicada",
        )

    # RN-013/PD-02: límite por condición, unidad POR CONVOCATORIA, sólo al crear.
    if condicion.limite_materias is not None:
        activas = await db.scalar(
            select(func.count()).select_from(EsMesaInscripcion).where(*base)
        )
        if activas >= condicion.limite_materias:
            raise ConflictError(
                f"La condición permite hasta {condicion.limite_materias} "
                "materias por convocatoria",
                code="limite-materias",
            )

    # A-SDD4-5/PD-19: sin mesa viva del combo -> 409; A-SDD4-6: la más próxima.
    mesa = await db.scalar(
        select(EsMesaExamen)
        .where(
            EsMesaExamen.convocatoria_id == convocatoria.id,
            EsMesaExamen.materia_id == materia_id,
            EsMesaExamen.condicion_id == condicion_id,
            EsMesaExamen.deleted_at.is_(None),
        )
        .order_by(EsMesaExamen.fecha, EsMesaExamen.hora, EsMesaExamen.id)
    )
    if mesa is None:
        raise ConflictError(
            "No hay mesa disponible para esa materia y condición",
            code="mesa-no-disponible",
        )

    ahora = datetime.now(UTC)
    inscripcion = EsMesaInscripcion(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        mesa_examen_id=mesa.id,
        convocatoria_id=convocatoria.id,
        materia_id=materia_id,
        condicion_id=condicion_id,
        estado="inscripto",
        inscripto_en=ahora,
        created_at=ahora,
    )
    db.add(inscripcion)
    try:
        await db.commit()
    except IntegrityError:
        # Carrera sobre uq_inscripcion_unica: misma respuesta, sin duplicar (E-13).
        await db.rollback()
        raise ConflictError(
            "Ya está inscripto a esta materia en esta convocatoria",
            code="inscripcion-duplicada",
        ) from None
    return inscripcion


async def inscripciones_gestion(
    db: AsyncSession, *, mesa_id: uuid.UUID | None = None,
    convocatoria_id: uuid.UUID | None = None,
) -> list[EsMesaInscripcion]:
    """CU-23 (S4): listado de gestión con filtros opcionales.

    RB-22 NO aplica (lista INSCRIPCIONES, no mesas). Un filtro que referencia
    un ID inexistente -> 404 (patrón T4, reuse `obtener_mesa`/
    `obtener_convocatoria`). Orden determinístico `inscripto_en` desc.
    """
    if mesa_id is not None:
        await obtener_mesa(db, mesa_id)  # 404 mesa-no-encontrada si no existe
    if convocatoria_id is not None:
        await obtener_convocatoria(db, convocatoria_id)  # 404 si no existe

    consulta = select(EsMesaInscripcion).where(
        EsMesaInscripcion.deleted_at.is_(None)
    )
    if mesa_id is not None:
        consulta = consulta.where(EsMesaInscripcion.mesa_examen_id == mesa_id)
    if convocatoria_id is not None:
        consulta = consulta.where(
            EsMesaInscripcion.convocatoria_id == convocatoria_id
        )
    resultado = await db.execute(
        consulta.order_by(
            EsMesaInscripcion.inscripto_en.desc(), EsMesaInscripcion.id
        )
    )
    return list(resultado.scalars().all())


async def mis_inscripciones(
    db: AsyncSession, *, usuario_id: uuid.UUID
) -> list[tuple[EsMesaInscripcion, EsMesaExamen]]:
    """CU-38 (S5): las filas del usuario autenticado + su mesa (para los
    nombres y la fecha/hora). RN-019: nunca el grupo. Sin paginación
    (A-SDD4-9) y sin exigir ventana (RB-07: la lectura sigue disponible)."""
    resultado = await db.execute(
        select(EsMesaInscripcion, EsMesaExamen)
        .join(
            EsMesaExamen,
            EsMesaExamen.id == EsMesaInscripcion.mesa_examen_id,
        )
        .where(
            EsMesaInscripcion.usuario_id == usuario_id,
            EsMesaInscripcion.deleted_at.is_(None),
            EsMesaExamen.deleted_at.is_(None),
        )
        .order_by(EsMesaInscripcion.inscripto_en.desc(), EsMesaInscripcion.id)
    )
    return list(resultado.all())


async def anular_inscripcion(
    db: AsyncSession, *, usuario_id: uuid.UUID, inscripcion_id: uuid.UUID
) -> EsMesaInscripcion:
    """CU-39/INS-02 (S5): anula la inscripción PROPIA dentro de la ventana.

    Sólo la propia (de otro alumno o inexistente -> 404
    `inscripcion-no-encontrada`, sin filtrar existencia ajena); sólo dentro
    de la ventana de ESA convocatoria (RB-08b/RB-07) -> fuera, 409
    `ventana-cerrada`; `inscripto` -> `anulado` (la fila se conserva para
    auditoría y libera la unicidad); ya `anulado` -> no-op idempotente
    (PD-25) — el router responde 204 sin cuerpo.
    """
    inscripcion = await db.scalar(
        select(EsMesaInscripcion).where(
            EsMesaInscripcion.id == inscripcion_id,
            EsMesaInscripcion.usuario_id == usuario_id,
            EsMesaInscripcion.deleted_at.is_(None),
        )
    )
    if inscripcion is None:
        raise NotFoundError(
            "Inscripción no encontrada", code="inscripcion-no-encontrada"
        )
    convocatoria = await obtener_convocatoria(db, inscripcion.convocatoria_id)
    if not ventana_inscripcion_abierta(convocatoria):
        raise ConflictError(
            "La ventana de inscripción está cerrada", code="ventana-cerrada"
        )
    if inscripcion.estado != "anulado":
        inscripcion.estado = "anulado"
        await db.commit()
    return inscripcion
