"""Endpoints /api/v1/sigme del catálogo (SDD-2 S7; CU-05/CU-06).

RBAC: lectura por módulo sigme_web (A4: CU-05 "cualquier rol sigme_web");
escritura (POST/PATCH) por usuario.gestionar (A1: la matriz §2.4 no define
código de permiso para catálogo — hueco declarado en doc 05).
PD-21 resuelto: PATCH agregado a las 4 colecciones.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_modulo, require_permiso
from app.features.auth.tokens import Principal
from app.features.catalogo import service
from app.features.catalogo.schemas import (
    CondicionCreate,
    CondicionResponse,
    CondicionUpdate,
    CursoCreate,
    CursoResponse,
    CursoUpdate,
    MateriaCreate,
    MateriaResponse,
    MateriaUpdate,
    OrientacionCreate,
    OrientacionResponse,
    OrientacionUpdate,
)

router = APIRouter(tags=["sigme-catalogo"])

_LEER = Depends(require_modulo("sigme_web"))
_GESTIONAR = Depends(require_permiso("usuario.gestionar"))


# ---------------------------------------------------------------------------
# Orientaciones
# ---------------------------------------------------------------------------
@router.get("/orientaciones", response_model=list[OrientacionResponse])
async def listar_orientaciones(
    _: Principal = _LEER, db: AsyncSession = Depends(get_db)
) -> list[OrientacionResponse]:
    filas = await service.listar_orientaciones(db)
    return [OrientacionResponse.model_validate(f) for f in filas]


@router.post(
    "/orientaciones", response_model=OrientacionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_orientacion(
    payload: OrientacionCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> OrientacionResponse:
    fila = await service.crear_orientacion(db, payload)
    await db.commit()
    return OrientacionResponse.model_validate(fila)


@router.patch("/orientaciones/{orientacion_id}", response_model=OrientacionResponse)
async def modificar_orientacion(
    orientacion_id: uuid.UUID,
    payload: OrientacionUpdate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> OrientacionResponse:
    fila = await service.modificar_orientacion(db, orientacion_id, payload)
    await db.commit()
    return OrientacionResponse.model_validate(fila)


# ---------------------------------------------------------------------------
# Cursos
# ---------------------------------------------------------------------------
@router.get("/cursos", response_model=list[CursoResponse])
async def listar_cursos(
    orientacion_id: uuid.UUID | None = Query(default=None),
    _: Principal = _LEER,
    db: AsyncSession = Depends(get_db),
) -> list[CursoResponse]:
    filas = await service.listar_cursos(db, orientacion_id=orientacion_id)
    return [CursoResponse.model_validate(f) for f in filas]


@router.post("/cursos", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
async def crear_curso(
    payload: CursoCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> CursoResponse:
    fila = await service.crear_curso(db, payload)
    await db.commit()
    return CursoResponse.model_validate(fila)


@router.patch("/cursos/{curso_id}", response_model=CursoResponse)
async def modificar_curso(
    curso_id: uuid.UUID,
    payload: CursoUpdate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> CursoResponse:
    fila = await service.modificar_curso(db, curso_id, payload)
    await db.commit()
    return CursoResponse.model_validate(fila)


# ---------------------------------------------------------------------------
# Materias
# ---------------------------------------------------------------------------
@router.get("/materias", response_model=list[MateriaResponse])
async def listar_materias(
    curso_id: uuid.UUID | None = Query(default=None),
    _: Principal = _LEER,
    db: AsyncSession = Depends(get_db),
) -> list[MateriaResponse]:
    filas = await service.listar_materias(db, curso_id=curso_id)
    return [MateriaResponse.model_validate(f) for f in filas]


@router.post("/materias", response_model=MateriaResponse, status_code=status.HTTP_201_CREATED)
async def crear_materia(
    payload: MateriaCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    fila = await service.crear_materia(db, payload)
    await db.commit()
    return MateriaResponse.model_validate(fila)


@router.patch("/materias/{materia_id}", response_model=MateriaResponse)
async def modificar_materia(
    materia_id: uuid.UUID,
    payload: MateriaUpdate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    fila = await service.modificar_materia(db, materia_id, payload)
    await db.commit()
    return MateriaResponse.model_validate(fila)


# ---------------------------------------------------------------------------
# Condiciones
# ---------------------------------------------------------------------------
@router.get("/condiciones", response_model=list[CondicionResponse])
async def listar_condiciones(
    _: Principal = _LEER, db: AsyncSession = Depends(get_db)
) -> list[CondicionResponse]:
    filas = await service.listar_condiciones(db)
    return [CondicionResponse.model_validate(f) for f in filas]


@router.post(
    "/condiciones", response_model=CondicionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_condicion(
    payload: CondicionCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> CondicionResponse:
    fila = await service.crear_condicion(db, payload)
    await db.commit()
    return CondicionResponse.model_validate(fila)


@router.patch("/condiciones/{condicion_id}", response_model=CondicionResponse)
async def modificar_condicion(
    condicion_id: uuid.UUID,
    payload: CondicionUpdate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> CondicionResponse:
    fila = await service.modificar_condicion(db, condicion_id, payload)
    await db.commit()
    return CondicionResponse.model_validate(fila)
