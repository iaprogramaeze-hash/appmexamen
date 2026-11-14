"""Endpoints /api/v1/sigme/roles, /permisos y /modulos (SDD-2 S6; CU-10).

RBAC: los 6 endpoints exigen usuario.gestionar (matriz doc02 §2.4).
Catálogo cerrado: la asignación permiso-rol no tiene endpoint (§6); vive
en la semilla T1/T2.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.auth.tokens import Principal
from app.features.usuarios import service_catalogo
from app.features.usuarios.schemas_catalogo import (
    CatalogoCreate,
    ModuloResponse,
    PermisoResponse,
    RolResponse,
)

router = APIRouter(tags=["sigme-catalogo-seguridad"])

_GESTIONAR = Depends(require_permiso("usuario.gestionar"))


@router.get("/roles", response_model=list[RolResponse])
async def listar_roles(
    _: Principal = _GESTIONAR, db: AsyncSession = Depends(get_db)
) -> list[RolResponse]:
    """GET /sigme/roles: catálogo con permisos por código (CU-10)."""
    filas = await service_catalogo.listar_roles(db)
    return [
        RolResponse(
            id=rol.id,
            codigo=rol.codigo,
            descripcion=rol.descripcion,
            activo=rol.activo,
            permisos=permisos,
        )
        for rol, permisos in filas
    ]


@router.post(
    "/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED
)
async def crear_rol(
    payload: CatalogoCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> RolResponse:
    """POST /sigme/roles: 201 / 409 codigo-existente (§3.6)."""
    rol = await service_catalogo.crear_rol(db, payload)
    await db.commit()
    return RolResponse(
        id=rol.id, codigo=rol.codigo, descripcion=rol.descripcion,
        activo=rol.activo, permisos=[],
    )


@router.get("/permisos", response_model=list[PermisoResponse])
async def listar_permisos(
    _: Principal = _GESTIONAR, db: AsyncSession = Depends(get_db)
) -> list[PermisoResponse]:
    """GET /sigme/permisos: catálogo cerrado de 13 (§2.7)."""
    permisos = await service_catalogo.listar_permisos(db)
    return [PermisoResponse.model_validate(p) for p in permisos]


@router.post(
    "/permisos", response_model=PermisoResponse, status_code=status.HTTP_201_CREATED
)
async def crear_permiso(
    payload: CatalogoCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> PermisoResponse:
    """POST /sigme/permisos: 201 / 409 codigo-existente (§3.7)."""
    permiso = await service_catalogo.crear_permiso(db, payload)
    await db.commit()
    return PermisoResponse.model_validate(permiso)


@router.get("/modulos", response_model=list[ModuloResponse])
async def listar_modulos(
    _: Principal = _GESTIONAR, db: AsyncSession = Depends(get_db)
) -> list[ModuloResponse]:
    """GET /sigme/modulos: catálogo de 3 módulos (§2.8)."""
    modulos = await service_catalogo.listar_modulos(db)
    return [ModuloResponse.model_validate(m) for m in modulos]


@router.post(
    "/modulos", response_model=ModuloResponse, status_code=status.HTTP_201_CREATED
)
async def crear_modulo(
    payload: CatalogoCreate,
    _: Principal = _GESTIONAR,
    db: AsyncSession = Depends(get_db),
) -> ModuloResponse:
    """POST /sigme/modulos: 201 / 409 codigo-existente (§3.10)."""
    modulo = await service_catalogo.crear_modulo(db, payload)
    await db.commit()
    return ModuloResponse.model_validate(modulo)
