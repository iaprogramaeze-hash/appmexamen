"""Endpoints SIGME de la ventana de preinscripción (§6, CU-14).

§6 declara SÓLO `GET|POST /ventanas-preinscripcion` (gestiona `pr_ventana`):
el POST es un upsert por `anio_lectivo`. La landing es anónima — quien
gestiona la ventana lo hace SÓLO desde acá (§3.21).

RBAC temporal patrón SDD-2: lectura por módulo sigme_web; escritura por
usuario.gestionar. Los códigos `ventana.*` siguen PENDIENTE en los docs
(CU-14 los deja sin definir) — se reemplazan apenas el cliente confirme.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.fechas import hoy_buenos_aires
from app.features.auth.dependencies import require_modulo, require_permiso
from app.features.auth.tokens import Principal
from app.features.preinscripcion import service_ventana as service
from app.features.preinscripcion.schemas_ventana import (
    VentanaLectura,
    VentanaUpsert,
)

router = APIRouter(tags=["sigme-ventanas"])

_LEER = Depends(require_modulo("sigme_web"))
_GESTIONAR = Depends(require_permiso("usuario.gestionar"))


def _a_lectura(ventana) -> VentanaLectura:
    """Adjunta la vigencia DERIVADA (doc 11 §11.5) — nunca se persiste."""
    return VentanaLectura(
        id=ventana.id,
        anio_lectivo=ventana.anio_lectivo,
        descripcion=ventana.descripcion,
        fecha_desde=ventana.fecha_desde,
        fecha_hasta=ventana.fecha_hasta,
        activa=ventana.activa,
        vigente=service.ventana_vigente(ventana, hoy_buenos_aires()),
    )


@router.get(
    "/ventanas-preinscripcion",
    response_model=list[VentanaLectura],
)
async def listar_ventanas(
    _: Principal = _LEER, db: AsyncSession = Depends(get_db)
) -> list[VentanaLectura]:
    filas = await service.listar_ventanas(db)
    return [_a_lectura(f) for f in filas]


@router.post(
    "/ventanas-preinscripcion",
    response_model=VentanaLectura,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_ventana(
    payload: VentanaUpsert,
    response: Response,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> VentanaLectura:
    """Crea o actualiza la ventana del año (CU-14: abrir o cerrar).

    Upsert por `anio_lectivo` (la única clave natural de `pr_ventana`):
    201 al crear, 200 al actualizar. RN-035: no acepta un resultado que
    deje dos ventanas activas con rangos solapados.
    """
    fila, creada = await service.upsert_ventana(db, payload)
    if not creada:
        response.status_code = status.HTTP_200_OK
    return _a_lectura(fila)
