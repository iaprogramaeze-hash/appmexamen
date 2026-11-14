"""Reglas de mesas SIGME (S4: CU-19/20, RB-11/22/23, ME-03/04, PD-13).

RB-22: las 3 lecturas de CU-19 devuelven SÓLO mesas con al menos una
inscripción activa (`estado='inscripto'`, `deleted_at IS NULL`); las
recién creadas no aparecen pero tampoco se borran (S-03). Las mesas
VENCIDAS dejan de listarse en SIGME (7 fuentes, L11a): `GET /mesas` y
`por-fecha` las excluyen; el detalle por id sí las muestra con estado
DERIVADO — vencida → `cerrada` (A-SDD3-6; ME-03/ME-04 constatan al LEER,
la columna `estado` nunca se escribe). `por-fecha` (RB-23) exige
desde/hasta con rango INCLUSIVE sobre la fecha de la mesa.

CU-20: el PATCH recalcula los 4 snapshots (RB-11) en la MISMA transacción,
respeta `uq_mesa_unica` — PD-13: la hora NO participa — y NO tiene gate
temporal (CU-20 no declara ventana) ni filtro RB-22 (es escritura sobre
fila existente).
"""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import and_, exists, or_, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
)
from app.features.catalogo.models import (
    EsCondicion,
    EsCurso,
    EsMateria,
    EsOrientacion,
)
from app.features.mesas.models import EsMesaExamen, EsMesaInscripcion
from app.features.mesas.schemas_mesas import MesaAsignar
from app.features.mesas.service_convocatoria import obtener_convocatoria

# Reutiliza la carga de catálogo de T3: 404 materia/condicion-no-encontrada
# para IDs inexistentes, borrados o inactivos.
from app.features.mesas.service_grupos import (
    _cargar_condiciones,
    _cargar_materias,
)

__all__ = [
    "cobertura_mesas",
    "estado_derivado",
    "listar_mesas",
    "mesas_por_fecha",
    "obtener_mesa",
    "reasignar_mesa",
]


def _ahora_ba() -> datetime:
    """Buenos Aires es UTC-3 fijo (sin DST desde 2009): la vencimiento se
    lee en hora local del colegio (L11a)."""
    return datetime.now(UTC) - timedelta(hours=3)


def _vencida(fecha: date, hora: time | None, ahora_ba: datetime) -> bool:
    """vencida = su fecha/hora YA pasó en Buenos Aires."""
    if fecha < ahora_ba.date():
        return True
    if fecha > ahora_ba.date():
        return False
    return hora is not None and hora < ahora_ba.time()


def _no_vencida(ahora_ba: datetime):
    """Filtro SQL simétrico a `_vencida` (misma frontera, sin hora → hoy)."""
    return or_(
        EsMesaExamen.fecha > ahora_ba.date(),
        and_(
            EsMesaExamen.fecha == ahora_ba.date(),
            or_(
                EsMesaExamen.hora.is_(None),
                EsMesaExamen.hora >= ahora_ba.time(),
            ),
        ),
    )


def _con_vida():
    """RB-22: al menos UNA inscripción activa ('inscripto', sin borrar)."""
    return exists(
        select(EsMesaInscripcion.id).where(
            EsMesaInscripcion.mesa_examen_id == EsMesaExamen.id,
            EsMesaInscripcion.estado == "inscripto",
            EsMesaInscripcion.deleted_at.is_(None),
        )
    )


async def _mesas_visibles(
    db: AsyncSession,
    *,
    convocatoria_id: UUID | None = None,
    materia_id: UUID | None = None,
    condicion_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[EsMesaExamen]:
    """Base de las lecturas de CU-19: con vida (RB-22), sin vencer (L11a),
    sin borradas, con filtros opcionales y rango inclusive (RB-23)."""
    if convocatoria_id is not None:
        await obtener_convocatoria(db, convocatoria_id)
    consulta = select(EsMesaExamen).where(
        EsMesaExamen.deleted_at.is_(None),
        _con_vida(),
        _no_vencida(_ahora_ba()),
    )
    if convocatoria_id is not None:
        consulta = consulta.where(
            EsMesaExamen.convocatoria_id == convocatoria_id
        )
    if materia_id is not None:
        consulta = consulta.where(EsMesaExamen.materia_id == materia_id)
    if condicion_id is not None:
        consulta = consulta.where(EsMesaExamen.condicion_id == condicion_id)
    if desde is not None:
        consulta = consulta.where(EsMesaExamen.fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(EsMesaExamen.fecha <= hasta)
    consulta = consulta.order_by(EsMesaExamen.fecha, EsMesaExamen.hora)
    return list((await db.execute(consulta)).scalars().all())


async def listar_mesas(
    db: AsyncSession,
    *,
    convocatoria_id: UUID | None = None,
    materia_id: UUID | None = None,
    condicion_id: UUID | None = None,
) -> list[EsMesaExamen]:
    """CU-19: mesas visibles en SIGME (vida + calendario)."""
    return await _mesas_visibles(
        db,
        convocatoria_id=convocatoria_id,
        materia_id=materia_id,
        condicion_id=condicion_id,
    )


async def mesas_por_fecha(
    db: AsyncSession,
    desde: date,
    hasta: date,
    *,
    convocatoria_id: UUID | None = None,
) -> list[EsMesaExamen]:
    """RB-23: rango INCLUSIVE desde/hasta sobre la fecha de la mesa."""
    if desde > hasta:
        raise DomainValidationError(
            "El rango de fechas es inválido: desde no puede ser "
            "posterior a hasta",
            errors=[
                {
                    "field": "desde",
                    "message": "desde no puede ser posterior a hasta",
                }
            ],
        )
    return await _mesas_visibles(
        db, convocatoria_id=convocatoria_id, desde=desde, hasta=hasta
    )


async def obtener_mesa(db: AsyncSession, mesa_id: UUID) -> EsMesaExamen:
    """CU-19: el detalle también exige vida (RB-22 → 404 sin ella) y NO
    filtra vencidas: el estado derivado las hace visibles (A-SDD3-6)."""
    mesa = await db.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.id == mesa_id,
            EsMesaExamen.deleted_at.is_(None),
        )
    )
    if mesa is None:
        raise NotFoundError("Mesa no encontrada", code="mesa-no-encontrada")
    inscripcion = await db.scalar(
        select(EsMesaInscripcion.id)
        .where(
            EsMesaInscripcion.mesa_examen_id == mesa.id,
            EsMesaInscripcion.estado == "inscripto",
            EsMesaInscripcion.deleted_at.is_(None),
        )
        .limit(1)
    )
    if inscripcion is None:
        raise NotFoundError("Mesa no encontrada", code="mesa-no-encontrada")
    return mesa


def estado_derivado(mesa: EsMesaExamen) -> str:
    """A-SDD3-6 (L11c): vencida → `cerrada` al LEER; la columna no cambia
    (ME-03/ME-04 constatan, CU-22). `realizada` no se deriva en v1."""
    if _vencida(mesa.fecha, mesa.hora, _ahora_ba()):
        return "cerrada"
    return mesa.estado


async def _ocupada(
    db: AsyncSession,
    convocatoria_id: UUID,
    materia_id: UUID,
    condicion_id: UUID,
    fecha: date,
    excluir_id: UUID,
) -> bool:
    """uq_mesa_unica (PD-13: convocatoria+materia+condición+fecha; la
    hora NO participa, por eso otra franja horaria choca igual)."""
    return (
        await db.scalar(
            select(EsMesaExamen.id).where(
                EsMesaExamen.convocatoria_id == convocatoria_id,
                EsMesaExamen.materia_id == materia_id,
                EsMesaExamen.condicion_id == condicion_id,
                EsMesaExamen.fecha == fecha,
                EsMesaExamen.deleted_at.is_(None),
                EsMesaExamen.id != excluir_id,
            )
        )
        is not None
    )


async def reasignar_mesa(
    db: AsyncSession, mesa_id: UUID, datos: MesaAsignar
) -> EsMesaExamen:
    """CU-20/RB-11: cambia materia y/o condición recalculando los 4
    snapshots en la MISMA transacción; el estado no cambia."""
    mesa = await db.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.id == mesa_id,
            EsMesaExamen.deleted_at.is_(None),
        )
    )
    if mesa is None:
        raise NotFoundError("Mesa no encontrada", code="mesa-no-encontrada")

    nueva_materia = mesa.materia_id
    nueva_condicion = mesa.condicion_id
    snapshots_materia: tuple[str, str, str] | None = None
    if datos.materia_id is not None:
        materia, curso, orientacion = (
            await _cargar_materias(db, [datos.materia_id])
        )[0]
        nueva_materia = materia.id
        snapshots_materia = (
            materia.descripcion,
            curso.descripcion,
            orientacion.descripcion,
        )
    condicion = None
    if datos.condicion_id is not None:
        condicion = (await _cargar_condiciones(db, [datos.condicion_id]))[0]
        nueva_condicion = condicion.id

    if await _ocupada(
        db,
        mesa.convocatoria_id,
        nueva_materia,
        nueva_condicion,
        mesa.fecha,
        excluir_id=mesa.id,
    ):
        raise ConflictError(
            "Ya existe una mesa para esa materia y condición "
            "en la fecha de la convocatoria",
            code="mesa-duplicada",
        )

    if snapshots_materia is not None:
        mesa.materia_id = nueva_materia
        (
            mesa.materia_nombre,
            mesa.curso_nombre,
            mesa.orientacion_nombre,
        ) = snapshots_materia
    if condicion is not None:
        mesa.condicion_id = condicion.id
        mesa.condicion_nombre = condicion.descripcion
    mesa.updated_at = datetime.now(UTC)
    try:
        await db.commit()
    except IntegrityError:
        # Cierre de carrera (NFR-029): dos reasignaciones simultáneas
        # pasan el pre-chequeo y pegan el índice — se responde el 409 que
        # corresponde, nunca un 500.
        await db.rollback()
        raise ConflictError(
            "Ya existe una mesa para esa materia y condición "
            "en la fecha de la convocatoria",
            code="mesa-duplicada",
        ) from None
    await db.refresh(mesa)
    return mesa


async def cobertura_mesas(
    db: AsyncSession, convocatoria_id: UUID
) -> list[tuple[EsMateria, EsCurso, EsOrientacion, EsCondicion]]:
    """RB-31/CU-21: pares materia × condición del catálogo ACTIVO completo
    SIN mesa en la convocatoria (PD-15/A-SDD3-1).

    Reporte de consulta (advisory), no un gate: cuenta cualquier mesa con
    `deleted_at IS NULL` — cualquier grupo y cualquier fecha — como cubierta.
    """
    await obtener_convocatoria(db, convocatoria_id)
    mesa_creada = (
        select(EsMesaExamen.id)
        .where(
            EsMesaExamen.convocatoria_id == convocatoria_id,
            EsMesaExamen.deleted_at.is_(None),
            EsMesaExamen.materia_id == EsMateria.id,
            EsMesaExamen.condicion_id == EsCondicion.id,
        )
        .exists()
    )
    resultado = await db.execute(
        select(EsMateria, EsCurso, EsOrientacion, EsCondicion)
        .join(EsCurso, EsMateria.curso_id == EsCurso.id)
        .join(EsOrientacion, EsCurso.orientacion_id == EsOrientacion.id)
        .join(EsCondicion, true())  # catálogo × catálogo: cross join (PD-15)
        .where(
            EsMateria.activo.is_(True),
            EsMateria.deleted_at.is_(None),
            EsCondicion.activo.is_(True),
            EsCondicion.deleted_at.is_(None),
            ~mesa_creada,  # sólo los pares SIN mesa
        )
        .order_by(EsMateria.descripcion, EsCondicion.descripcion)
    )
    return list(resultado.all())
