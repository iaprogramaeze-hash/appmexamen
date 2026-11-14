"""Servicio de catálogo (SDD-2 S7; CU-05 consulta, CU-06 mantenimiento).

Reglas:
- Sólo filas vigentes (soft delete §1.7) en lecturas.
- FK RESTRICT: la jerarquía orientación → curso → materia se valida al
  escribir (404 si la FK no existe o está borrada).
- Unicidad de `descripcion` en orientaciones y condiciones (§3.13/§3.16).
- PD-02: limite_materias editable desde SIGME; NULL = sin límite.
- PD-21: PATCH agregado a las 4 colecciones (renombre/corrección de carga).
- RB-11: renombrar catálogo NUNCA recalcula snapshots de mesas (acá no hay
  mesas todavía; queda como restricción vigente para SDD-3).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.features.catalogo.models import (
    EsCondicion,
    EsCurso,
    EsMateria,
    EsOrientacion,
)
from app.features.catalogo.schemas import (
    CondicionCreate,
    CondicionUpdate,
    CursoCreate,
    CursoUpdate,
    MateriaCreate,
    MateriaUpdate,
    OrientacionCreate,
    OrientacionUpdate,
)


def _ahora() -> datetime:
    return datetime.now(UTC)


async def _no_encontrado(db: AsyncSession, modelo, entidad_id: uuid.UUID, code: str,
                         detalle: str):
    fila = await db.get(modelo, entidad_id)
    if fila is None or fila.deleted_at is not None:
        raise NotFoundError(detalle, code=code)
    return fila


async def _aplicar(fila, cambios: dict) -> None:
    for campo, valor in cambios.items():
        setattr(fila, campo, valor)
    fila.updated_at = _ahora()


# ---------------------------------------------------------------------------
# Orientaciones
# ---------------------------------------------------------------------------
async def listar_orientaciones(db: AsyncSession) -> list[EsOrientacion]:
    return list(
        await db.scalars(
            select(EsOrientacion)
            .where(EsOrientacion.deleted_at.is_(None))
            .order_by(EsOrientacion.descripcion)
        )
    )


async def crear_orientacion(
    db: AsyncSession, payload: OrientacionCreate
) -> EsOrientacion:
    existe = await db.scalar(
        select(EsOrientacion.id).where(
            EsOrientacion.descripcion == payload.descripcion,
            EsOrientacion.deleted_at.is_(None),
        )
    )
    if existe is not None:
        raise ConflictError(
            "Ya existe una orientación con esa descripción",
            code="orientacion-existente",
        )
    fila = EsOrientacion(
        id=uuid.uuid4(), descripcion=payload.descripcion, activo=True,
        created_at=_ahora(),
    )
    db.add(fila)
    await db.flush()
    return fila


async def modificar_orientacion(
    db: AsyncSession, orientacion_id: uuid.UUID, payload: OrientacionUpdate
) -> EsOrientacion:
    fila = await _no_encontrado(
        db, EsOrientacion, orientacion_id,
        "orientacion-no-encontrada", "Orientación no encontrada",
    )
    await _aplicar(fila, payload.model_dump(exclude_unset=True))
    await db.flush()
    return fila


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------
async def listar_cursos(
    db: AsyncSession, *, orientacion_id: uuid.UUID | None = None
) -> list[EsCurso]:
    statement = (
        select(EsCurso).where(EsCurso.deleted_at.is_(None)).order_by(EsCurso.descripcion)
    )
    if orientacion_id is not None:
        statement = statement.where(EsCurso.orientacion_id == orientacion_id)
    return list(await db.scalars(statement))


async def crear_curso(db: AsyncSession, payload: CursoCreate) -> EsCurso:
    orientacion = await db.get(EsOrientacion, payload.orientacion_id)
    if orientacion is None or orientacion.deleted_at is not None:
        raise NotFoundError(
            "La orientación referenciada no existe",
            code="orientacion-no-encontrada",
        )
    fila = EsCurso(
        id=uuid.uuid4(), orientacion_id=payload.orientacion_id,
        descripcion=payload.descripcion, anio=payload.anio, activo=True,
        created_at=_ahora(),
    )
    db.add(fila)
    await db.flush()
    return fila


async def modificar_curso(
    db: AsyncSession, curso_id: uuid.UUID, payload: CursoUpdate
) -> EsCurso:
    fila = await _no_encontrado(
        db, EsCurso, curso_id, "curso-no-encontrado", "Curso no encontrado"
    )
    await _aplicar(fila, payload.model_dump(exclude_unset=True))
    await db.flush()
    return fila


# ---------------------------------------------------------------------------
# Materias
# ---------------------------------------------------------------------------
async def listar_materias(
    db: AsyncSession, *, curso_id: uuid.UUID | None = None
) -> list[EsMateria]:
    statement = (
        select(EsMateria).where(EsMateria.deleted_at.is_(None)).order_by(EsMateria.descripcion)
    )
    if curso_id is not None:
        statement = statement.where(EsMateria.curso_id == curso_id)
    return list(await db.scalars(statement))


async def crear_materia(db: AsyncSession, payload: MateriaCreate) -> EsMateria:
    curso = await db.get(EsCurso, payload.curso_id)
    if curso is None or curso.deleted_at is not None:
        raise NotFoundError(
            "El curso referenciado no existe", code="curso-no-encontrado"
        )
    fila = EsMateria(
        id=uuid.uuid4(), curso_id=payload.curso_id, codigo=payload.codigo,
        descripcion=payload.descripcion, es_taller=payload.es_taller,
        activo=True, created_at=_ahora(),
    )
    db.add(fila)
    await db.flush()
    return fila


async def modificar_materia(
    db: AsyncSession, materia_id: uuid.UUID, payload: MateriaUpdate
) -> EsMateria:
    fila = await _no_encontrado(
        db, EsMateria, materia_id, "materia-no-encontrada", "Materia no encontrada"
    )
    await _aplicar(fila, payload.model_dump(exclude_unset=True))
    await db.flush()
    return fila


# ---------------------------------------------------------------------------
# Condiciones
# ---------------------------------------------------------------------------
async def listar_condiciones(db: AsyncSession) -> list[EsCondicion]:
    return list(
        await db.scalars(
            select(EsCondicion)
            .where(EsCondicion.deleted_at.is_(None))
            .order_by(EsCondicion.descripcion)
        )
    )


async def crear_condicion(db: AsyncSession, payload: CondicionCreate) -> EsCondicion:
    existe = await db.scalar(
        select(EsCondicion.id).where(
            EsCondicion.descripcion == payload.descripcion,
            EsCondicion.deleted_at.is_(None),
        )
    )
    if existe is not None:
        raise ConflictError(
            "Ya existe una condición con esa descripción",
            code="condicion-existente",
        )
    fila = EsCondicion(
        id=uuid.uuid4(), descripcion=payload.descripcion,
        limite_materias=payload.limite_materias, activo=True, created_at=_ahora(),
    )
    db.add(fila)
    await db.flush()
    return fila


async def modificar_condicion(
    db: AsyncSession, condicion_id: uuid.UUID, payload: CondicionUpdate
) -> EsCondicion:
    fila = await _no_encontrado(
        db, EsCondicion, condicion_id,
        "condicion-no-encontrada", "Condición no encontrada",
    )
    await _aplicar(fila, payload.model_dump(exclude_unset=True))
    await db.flush()
    return fila
