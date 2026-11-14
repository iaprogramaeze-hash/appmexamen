"""Endpoints /api/v1/sigme/usuarios (SDD-2 S5; CU-09, analisis.txt §6).

RBAC: ambos endpoints exigen usuario.gestionar (matriz doc02 §2.4).
GET /usuarios/{id} no está en §6 → no se implementa.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.auth.tokens import Principal
from app.features.usuarios import service_usuarios
from app.features.usuarios.schemas import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioResponse])
async def listar_usuarios(
    _: Principal = Depends(require_permiso("usuario.gestionar")),
    db: AsyncSession = Depends(get_db),
) -> list[UsuarioResponse]:
    """GET /sigme/usuarios: lista con roles por código (CU-09)."""
    filas = await service_usuarios.listar_usuarios(db)
    return [
        UsuarioResponse(
            id=usuario.id,
            persona_id=usuario.persona_id,
            username=usuario.username,
            email=usuario.email,
            activo=usuario.activo,
            bloqueado=usuario.bloqueado,
            roles=roles,
        )
        for usuario, roles in filas
    ]


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    payload: UsuarioCreate,
    _: Principal = Depends(require_permiso("usuario.gestionar")),
    db: AsyncSession = Depends(get_db),
) -> UsuarioResponse:
    """POST /sigme/usuarios: alta sobre persona existente (CU-09, §2.5)."""
    usuario = await service_usuarios.crear_usuario(db, payload)
    await db.commit()
    return UsuarioResponse(
        id=usuario.id,
        persona_id=usuario.persona_id,
        username=usuario.username,
        email=usuario.email,
        activo=usuario.activo,
        bloqueado=usuario.bloqueado,
        roles=[],
    )
