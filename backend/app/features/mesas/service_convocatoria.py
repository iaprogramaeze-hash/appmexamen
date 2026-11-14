"""Reglas de convocatorias (§3.17, doc 04 §4.1 C-01/C-05, RB-16/17/23).

El estado es DERIVADO: nunca se guarda. `activa=false` => borrador; con
`activa=true`, `hoy` dentro de la ventana (límite inclusive, RB-23, fecha de
calendario en America/Argentina/Buenos_Aires) => abierta; si `hoy` superó
`fecha_fin_inscripcion` => cerrada.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainValidationError, NotFoundError
from app.core.fechas import hoy_buenos_aires
from app.features.mesas.models import EsConvocatoria
from app.features.mesas.schemas_convocatoria import (
    ConvocatoriaActualizar,
    ConvocatoriaCrear,
)

__all__ = ["hoy_buenos_aires"]  # re-export: los routers de mesas lo usan vía service


def estado_convocatoria(convocatoria: EsConvocatoria, hoy: date) -> str:
    """Estado derivado doc 04 §4.1 sin escritura (CU-22)."""
    if not convocatoria.activa:
        return "borrador"
    if hoy < convocatoria.fecha_inicio_inscripcion:
        return "borrador"
    if hoy > convocatoria.fecha_fin_inscripcion:
        return "cerrada"
    return "abierta"


def ventana_inscripcion_abierta(
    convocatoria: EsConvocatoria, hoy: date | None = None
) -> bool:
    """`activa` y `hoy` dentro de la ventana, límite inclusive (RB-23).

    Es la ventana de inscripción POR CONVOCATORIA que usa la guarda PD-12 de
    grupos (T3), no `pr_ventana` (esa es la del landing).
    """
    hoy = hoy or hoy_buenos_aires()
    if not convocatoria.activa:
        return False
    return (
        convocatoria.fecha_inicio_inscripcion
        <= hoy
        <= convocatoria.fecha_fin_inscripcion
    )


async def listar_convocatorias(db: AsyncSession) -> list[EsConvocatoria]:
    resultado = await db.execute(
        select(EsConvocatoria)
        .where(EsConvocatoria.deleted_at.is_(None))
        .order_by(EsConvocatoria.fecha_inicio_inscripcion.desc())
    )
    return list(resultado.scalars().all())


async def obtener_convocatoria(
    db: AsyncSession, convocatoria_id: UUID
) -> EsConvocatoria:
    resultado = await db.execute(
        select(EsConvocatoria).where(
            EsConvocatoria.id == convocatoria_id,
            EsConvocatoria.deleted_at.is_(None),
        )
    )
    fila = resultado.scalar_one_or_none()
    if fila is None:
        raise NotFoundError(
            "Convocatoria no encontrada", code="convocatoria-no-encontrada"
        )
    return fila


async def crear_convocatoria(
    db: AsyncSession, datos: ConvocatoriaCrear
) -> EsConvocatoria:
    """C-01: la convocatoria nace en su estado derivado; sólo se persisten
    las columnas de negocio (`activa` por defecto en true)."""
    convocatoria = EsConvocatoria(
        id=uuid4(),
        descripcion=datos.descripcion,
        fecha_inicio_inscripcion=datos.fecha_inicio_inscripcion,
        fecha_fin_inscripcion=datos.fecha_fin_inscripcion,
        activa=datos.activa,
    )
    convocatoria.created_at = datetime.now(UTC)
    db.add(convocatoria)
    await db.commit()
    await db.refresh(convocatoria)
    return convocatoria


async def actualizar_convocatoria(
    db: AsyncSession,
    convocatoria: EsConvocatoria,
    datos: ConvocatoriaActualizar,
) -> EsConvocatoria:
    cambios = datos.model_dump(exclude_unset=True)
    # El CHECK §3.17 se evalúa sobre los valores RESULTANTES, no sólo los
    # enviados: una mitad de la ventana también puede invertirla.
    inicio = cambios.get(
        "fecha_inicio_inscripcion", convocatoria.fecha_inicio_inscripcion
    )
    fin = cambios.get("fecha_fin_inscripcion", convocatoria.fecha_fin_inscripcion)
    if inicio > fin:
        raise DomainValidationError(
            "Solicitud inválida",
            code="validacion",
            errors=[
                {
                    "field": "fecha_fin_inscripcion",
                    "message": (
                        "fecha_fin_inscripcion no puede ser anterior a "
                        "fecha_inicio_inscripcion"
                    ),
                }
            ],
        )
    for campo, valor in cambios.items():
        setattr(convocatoria, campo, valor)
    await db.commit()
    await db.refresh(convocatoria)
    return convocatoria
