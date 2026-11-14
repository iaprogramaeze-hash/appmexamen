"""Endpoints de reportes (SDD-5).

Rutas a raíz bajo /api/v1/ SIN prefijo de dispositivo (L2).
Gate por permiso `reporte.exportar` — roles: secretario, director, admin, superadmin.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.reportes import service
from app.features.reportes.schemas import (
    ActaVolanteResponse,
    MesaSnapshotResponse,
    PermisoExamenMasivoResponse,
    PermisoExamenResponse,
    PlanillaGruposResponse,
)

router = APIRouter(tags=["reportes"])


@router.get(
    "/reportes/permiso-examen/{usuario_id}",
    response_model=PermisoExamenResponse,
)
async def permiso_examen_individual(
    usuario_id: UUID,
    _: str = Depends(require_permiso("reporte.exportar")),
    db: AsyncSession = Depends(get_db),
) -> PermisoExamenResponse:
    """S1 (CU-27): Permiso de examen individual por alumno.

    Lista mesas donde el alumno tiene inscripción ACTIVA, con snapshots
    (RB-11). Orden fecha asc, hora asc. RB-22: solo mesas con inscripción
    activa del alumno.
    """
    data = await service.permiso_examen_individual(db, usuario_id=usuario_id)
    return PermisoExamenResponse(**data)


@router.get(
    "/reportes/permisos-examen",
    response_model=PermisoExamenMasivoResponse,
)
async def permisos_examen_masivo(
    convocatoria_id: UUID | None = Query(default=None),
    _: str = Depends(require_permiso("reporte.exportar")),
    db: AsyncSession = Depends(get_db),
) -> PermisoExamenMasivoResponse:
    """S2 (CU-27): Permisos de examen masivo, agrupados por mesa.

    Para cada mesa con inscriptos activos (RB-22), lista alumnos con sus
    materias/condiciones. `convocatoria_id` opcional (por defecto la vigente).
    """
    data = await service.permisos_examen_masivo(
        db, convocatoria_id=convocatoria_id
    )
    return PermisoExamenMasivoResponse(**data)


@router.get(
    "/reportes/acta-volante/{mesa_id}",
    response_model=ActaVolanteResponse,
)
async def acta_volante(
    mesa_id: UUID,
    _: str = Depends(require_permiso("reporte.exportar")),
    db: AsyncSession = Depends(get_db),
) -> ActaVolanteResponse:
    """S3 (CU-28): Acta volante por mesa.

    Alumnos inscriptos en esa mesa. RB-22: mesa debe tener ≥ 1 inscripción
    activa -> si no, 404 `mesa-sin-inscriptos`.
    """
    data = await service.acta_volante(db, mesa_id=mesa_id)
    return ActaVolanteResponse(**data)


@router.get(
    "/reportes/mesa/{mesa_id}",
    response_model=MesaSnapshotResponse,
)
async def mesa_snapshot(
    mesa_id: UUID,
    _: str = Depends(require_permiso("reporte.exportar")),
    db: AsyncSession = Depends(get_db),
) -> MesaSnapshotResponse:
    """S4 (CU-29): Snapshot de mesa.

    Lee columnas snapshot (RB-11/12) + estado derivado por fecha/hora BA.
    """
    data = await service.mesa_snapshot(db, mesa_id=mesa_id)
    return MesaSnapshotResponse(**data)


@router.get(
    "/reportes/planilla-grupos/{convocatoria_id}",
    response_model=PlanillaGruposResponse,
)
async def planilla_grupos(
    convocatoria_id: UUID,
    _: str = Depends(require_permiso("reporte.exportar")),
    db: AsyncSession = Depends(get_db),
) -> PlanillaGruposResponse:
    """S5 (CU-30, RB-32): Planilla de grupos por convocatoria.

    Cada grupo (fecha, hora) con sus mesas (materia, condición). Vista de
    horario, NO detalle de alumnos. RB-22: solo grupos con mesas que tengan
    inscriptos activos.
    """
    data = await service.planilla_grupos(db, convocatoria_id=convocatoria_id)
    return PlanillaGruposResponse(**data)