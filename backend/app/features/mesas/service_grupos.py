"""Reglas de grupos de mesas (§3.22, RB-27/28/29, PD-12, ME-01/GR-01).

RB-28: el secretario elige materias[] y condiciones[]; el backend crea el
grupo y N = materias ×-condiciones mesas de una, todas con `grupo_id` y con
`fecha`/`hora` COPIADAS del grupo. RB-29: al mover el grupo, la copia se
sincroniza en la MISMA transacción. Las mesas nacen `planificada` con los 4
snapshots rellenos desde el catálogo (inmutables ante renombres, RB-11).

PD-12 (CERRADO 2026-10-22): crear con ventana de inscripción abierta está
PERMITIDO (alta aditiva); mover con ventana abierta responde
409 ventana-abierta hasta que cierre (RB-17: las fechas nunca cambian bajo
alumnos ya inscriptos). La ventana se evalúa POR CONVOCATORIA, no por
`pr_ventana` (esa es la del landing).
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.features.catalogo.models import (
    EsCondicion,
    EsCurso,
    EsMateria,
    EsOrientacion,
)
from app.features.mesas.models import EsGrupoHorario, EsMesaExamen
from app.features.mesas.schemas_grupo import GrupoCrear, GrupoMover
from app.features.mesas.service_convocatoria import (
    obtener_convocatoria,
    ventana_inscripcion_abierta,
)

__all__ = ["crear_grupo", "listar_grupos", "mover_grupo"]


async def _cargar_materias(
    db: AsyncSession, materias: list[UUID]
) -> list[tuple[EsMateria, EsCurso, EsOrientacion]]:
    """Materias activas con su curso y orientación (para los snapshots).

    Una ID inexistente, borrada o inactiva responde 404
    materia-no-encontrada: no existe para poder crearle mesas.
    """
    ids = list(dict.fromkeys(materias))  # dedup preserva orden; N pares únicos
    resultado = await db.execute(
        select(EsMateria, EsCurso, EsOrientacion)
        .join(EsCurso, EsMateria.curso_id == EsCurso.id)
        .join(EsOrientacion, EsCurso.orientacion_id == EsOrientacion.id)
        .where(
            EsMateria.id.in_(ids),
            EsMateria.activo.is_(True),
            EsMateria.deleted_at.is_(None),
        )
    )
    filas = resultado.all()
    if len(filas) != len(ids):
        raise NotFoundError(
            "Materia no encontrada", code="materia-no-encontrada"
        )
    return filas


async def _cargar_condiciones(
    db: AsyncSession, condiciones: list[UUID]
) -> list[EsCondicion]:
    """Condiciones activas — manejo simétrico al de materias (404)."""
    ids = list(dict.fromkeys(condiciones))
    resultado = await db.execute(
        select(EsCondicion).where(
            EsCondicion.id.in_(ids),
            EsCondicion.activo.is_(True),
            EsCondicion.deleted_at.is_(None),
        )
    )
    filas = list(resultado.scalars().all())
    if len(filas) != len(ids):
        raise NotFoundError(
            "Condición no encontrada", code="condicion-no-encontrada"
        )
    return filas


async def _existe_grupo_en(
    db: AsyncSession,
    convocatoria_id: UUID,
    fecha,
    hora,
    excluir_id: UUID | None = None,
) -> bool:
    """uq_grupo_unico (convocatoria, fecha, hora) sin borradas (PD-16)."""
    consulta = select(EsGrupoHorario.id).where(
        EsGrupoHorario.convocatoria_id == convocatoria_id,
        EsGrupoHorario.fecha == fecha,
        EsGrupoHorario.hora == hora,
        EsGrupoHorario.deleted_at.is_(None),
    )
    if excluir_id is not None:
        consulta = consulta.where(EsGrupoHorario.id != excluir_id)
    return await db.scalar(consulta) is not None


async def _mesas_en_colision(
    db: AsyncSession,
    convocatoria_id: UUID,
    fecha,
    pares: set[tuple[UUID, UUID]],
    excluir_grupo_id: UUID | None = None,
) -> bool:
    """uq_mesa_unica (convocatoria, materia, condición, fecha) — PD-13: la
    hora NO participa, por eso una franja horaria distinta choca igual."""
    if not pares:
        return False
    materias_ids = {m for m, _ in pares}
    condiciones_ids = {c for _, c in pares}
    consulta = select(EsMesaExamen.materia_id, EsMesaExamen.condicion_id).where(
        EsMesaExamen.convocatoria_id == convocatoria_id,
        EsMesaExamen.fecha == fecha,
        EsMesaExamen.materia_id.in_(materias_ids),
        EsMesaExamen.condicion_id.in_(condiciones_ids),
        EsMesaExamen.deleted_at.is_(None),
    )
    if excluir_grupo_id is not None:
        consulta = consulta.where(EsMesaExamen.grupo_id != excluir_grupo_id)
    existentes = {(fila.materia_id, fila.condicion_id) for fila in await db.execute(consulta)}
    return bool(existentes & pares)


async def crear_grupo(
    db: AsyncSession, datos: GrupoCrear
) -> tuple[EsGrupoHorario, int]:
    """RB-28: crea el grupo y N = materias × condiciones mesas de una.

    Todas las mesas nacen `planificada` con `grupo_id` y fecha/hora copiadas
    del grupo (RB-29) y los 4 snapshots rellenados desde el catálogo
    (ME-01/GR-01). El check de ventana NO aplica aquí (PD-12: crear sí).
    """
    convocatoria = await obtener_convocatoria(db, datos.convocatoria_id)
    materias = await _cargar_materias(db, datos.materias)
    condiciones = await _cargar_condiciones(db, datos.condiciones)

    if await _existe_grupo_en(db, convocatoria.id, datos.fecha, datos.hora):
        raise ConflictError(
            "Ya existe un grupo en esa fecha y hora para la convocatoria",
            code="grupo-duplicado",
        )
    pares = {(m.id, c.id) for m, _, _ in materias for c in condiciones}
    if await _mesas_en_colision(db, convocatoria.id, datos.fecha, pares):
        raise ConflictError(
            "Ya existe una mesa para alguna materia y condición "
            "de ese grupo en la convocatoria",
            code="mesa-duplicada",
        )

    ahora = datetime.now(UTC)
    grupo = EsGrupoHorario(
        id=uuid4(),
        convocatoria_id=convocatoria.id,
        fecha=datos.fecha,
        hora=datos.hora,
        nombre=datos.nombre,
        created_at=ahora,
    )
    db.add(grupo)
    await db.flush()
    for materia, curso, orientacion in materias:
        for condicion in condiciones:
            db.add(
                EsMesaExamen(
                    id=uuid4(),
                    convocatoria_id=convocatoria.id,
                    condicion_id=condicion.id,
                    materia_id=materia.id,
                    grupo_id=grupo.id,
                    fecha=grupo.fecha,
                    hora=grupo.hora,
                    estado="planificada",
                    orientacion_nombre=orientacion.descripcion,
                    curso_nombre=curso.descripcion,
                    materia_nombre=materia.descripcion,
                    condicion_nombre=condicion.descripcion,
                    created_at=ahora,
                )
            )
    try:
        await db.commit()
    except IntegrityError:
        # Cierre de carrera (NFR-029, patrón landing): dos altas simultáneas
        # pasan el pre-chequeo y pegan el índice — se relee y se responde el
        # 409 que corresponde, nunca un 500.
        await db.rollback()
        if await _existe_grupo_en(db, convocatoria.id, datos.fecha, datos.hora):
            raise ConflictError(
                "Ya existe un grupo en esa fecha y hora para la convocatoria",
                code="grupo-duplicado",
            ) from None
        raise ConflictError(
            "Ya existe una mesa para alguna materia y condición "
            "de ese grupo en la convocatoria",
            code="mesa-duplicada",
        ) from None
    await db.refresh(grupo)
    return grupo, len(pares)


async def mover_grupo(
    db: AsyncSession, grupo_id: UUID, datos: GrupoMover
) -> EsGrupoHorario:
    """RB-29/CU-16: mueve el grupo y TODAS sus mesas en la misma transacción.

    PD-12: con la ventana de inscripción de la convocatoria ABIERTA no se
    mueve — 409 ventana-abierta hasta que cierre (RB-17).
    """
    grupo = await db.scalar(
        select(EsGrupoHorario).where(
            EsGrupoHorario.id == grupo_id,
            EsGrupoHorario.deleted_at.is_(None),
        )
    )
    if grupo is None:
        raise NotFoundError("Grupo no encontrado", code="grupo-no-encontrado")

    convocatoria = await obtener_convocatoria(db, grupo.convocatoria_id)
    if ventana_inscripcion_abierta(convocatoria):
        raise ConflictError(
            "No se puede mover el grupo con la ventana de inscripción "
            "abierta",
            code="ventana-abierta",
        )

    if await _existe_grupo_en(
        db, grupo.convocatoria_id, datos.fecha, datos.hora, excluir_id=grupo.id
    ):
        raise ConflictError(
            "Ya existe un grupo en esa fecha y hora para la convocatoria",
            code="grupo-duplicado",
        )
    mesas = list(
        (
            await db.execute(
                select(EsMesaExamen).where(
                    EsMesaExamen.grupo_id == grupo.id,
                    EsMesaExamen.deleted_at.is_(None),
                )
            )
        ).scalars()
    )
    pares = {(m.materia_id, m.condicion_id) for m in mesas}
    if await _mesas_en_colision(
        db,
        grupo.convocatoria_id,
        datos.fecha,
        pares,
        excluir_grupo_id=grupo.id,
    ):
        raise ConflictError(
            "Ya existe una mesa para alguna materia y condición "
            "de ese grupo en la fecha destino",
            code="mesa-duplicada",
        )

    # RB-29: grupo y mesas se mueven juntos — una sola transacción.
    grupo.fecha = datos.fecha
    grupo.hora = datos.hora
    grupo.updated_at = datetime.now(UTC)
    for mesa in mesas:
        mesa.fecha = datos.fecha
        mesa.hora = datos.hora
        mesa.updated_at = datetime.now(UTC)
    try:
        await db.commit()
    except IntegrityError:
        # Mismo cierre de carrera que en la creación (NFR-029).
        await db.rollback()
        if await _existe_grupo_en(
            db, grupo.convocatoria_id, datos.fecha, datos.hora, excluir_id=grupo.id
        ):
            raise ConflictError(
                "Ya existe un grupo en esa fecha y hora para la convocatoria",
                code="grupo-duplicado",
            ) from None
        raise ConflictError(
            "Ya existe una mesa para alguna materia y condición "
            "de ese grupo en la fecha destino",
            code="mesa-duplicada",
        ) from None
    await db.refresh(grupo)
    return grupo


async def listar_grupos(
    db: AsyncSession, convocatoria_id: UUID
) -> list[EsGrupoHorario]:
    """CU-17/RB-27: grupos de la convocatoria, ordenados por fecha y hora."""
    await obtener_convocatoria(db, convocatoria_id)
    resultado = await db.execute(
        select(EsGrupoHorario)
        .where(
            EsGrupoHorario.convocatoria_id == convocatoria_id,
            EsGrupoHorario.deleted_at.is_(None),
        )
        .order_by(EsGrupoHorario.fecha, EsGrupoHorario.hora)
    )
    return list(resultado.scalars().all())
