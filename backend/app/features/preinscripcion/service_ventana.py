"""Reglas de la ventana de preinscripción SIGME (§3.21, CU-14, RN-035).

El POST es un upsert por `anio_lectivo` (§6 sólo declara GET|POST): crea la
ventana si el año no existe y si existe la actualiza — "abrir o cerrar la
ventana vigente" (CU-14). `vigente` se deriva al leer, nunca se persiste
(doc 11 §11.5); el rango es inclusivo por fecha de calendario BA (RB-23).
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.features.preinscripcion.models import PrVentana
from app.features.preinscripcion.schemas_ventana import VentanaUpsert


def ventana_vigente(ventana: PrVentana, hoy: date) -> bool:
    """`activa AND deleted_at IS NULL AND hoy BETWEEN fechas` (vw_ventana_vigente)."""
    if not ventana.activa or ventana.deleted_at is not None:
        return False
    return ventana.fecha_desde <= hoy <= ventana.fecha_hasta


def _solapadas(a: PrVentana, b: PrVentana) -> bool:
    """Rangos inclusivos que se cruzan: [a.desde, a.hasta] ∩ [b.desde, b.hasta] ≠ ∅."""
    return a.fecha_desde <= b.fecha_hasta and b.fecha_desde <= a.fecha_hasta


async def listar_ventanas(db: AsyncSession) -> list[PrVentana]:
    resultado = await db.execute(
        select(PrVentana)
        .where(PrVentana.deleted_at.is_(None))
        .order_by(PrVentana.anio_lectivo.desc())
    )
    return list(resultado.scalars().all())


async def upsert_ventana(
    db: AsyncSession, datos: VentanaUpsert
) -> tuple[PrVentana, bool]:
    """Crea o actualiza la ventana del año (CU-14) con las guardas RN-035.

    Devuelve (fila, creada) para que el router responda 201 o 200.

    - Año en una fila soft-deleted → 409 ventana-anio-existente:
      `uq_ventana_anio` cuenta filas borradas, no se re-crea vía upsert.
    - Resultado `activa` con rango solapado contra OTRA ventana `activa`
      viva → 409 ventana-solapada (RN-035: nunca dos ventanas vigentes).
    """
    resultado = await db.execute(
        select(PrVentana).where(PrVentana.anio_lectivo == datos.anio_lectivo)
    )
    fila = resultado.scalar_one_or_none()

    if fila is not None and fila.deleted_at is not None:
        raise ConflictError(
            f"Ya existe una ventana registrada (y borrada) para el año "
            f"{datos.anio_lectivo}",
            code="ventana-anio-existente",
        )

    creada = fila is None
    if creada:
        fila = PrVentana(
            id=uuid4(),
            anio_lectivo=datos.anio_lectivo,
            created_at=datetime.now(UTC),
        )
        db.add(fila)
    fila.descripcion = datos.descripcion
    fila.fecha_desde = datos.fecha_desde
    fila.fecha_hasta = datos.fecha_hasta
    fila.activa = datos.activa

    if datos.activa:
        otras = await db.execute(
            select(PrVentana).where(
                PrVentana.deleted_at.is_(None),
                PrVentana.activa.is_(True),
                PrVentana.id != fila.id,  # la fila nueva aún no está en la BD
            )
        )
        for otra in otras.scalars():
            if _solapadas(fila, otra):
                raise ConflictError(
                    f"La ventana {otra.anio_lectivo} ya está activa con un "
                    f"rango de fechas que se solapa: RN-035 permite una sola "
                    f"ventana vigente a la vez",
                    code="ventana-solapada",
                )

    try:
        await db.commit()
    except IntegrityError as exc:
        # Carrera sobre uq_ventana_anio: otra transacción registró el año.
        await db.rollback()
        raise ConflictError(
            f"Ya existe una ventana para el año {datos.anio_lectivo}",
            code="ventana-anio-existente",
        ) from exc
    await db.refresh(fila)
    return fila, creada
