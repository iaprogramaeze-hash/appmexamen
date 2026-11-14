"""Keyset de firma y emisión de access tokens (analisis.txt 2.1; SDD-1 T3)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, generate_keypair
from app.features.usuarios.models import (
    UsModulo,
    UsPermiso,
    UsRol,
    UsRolPermiso,
    UsUsuarioModulo,
    UsUsuarioRol,
)


@dataclass(frozen=True, slots=True)
class Principal:
    """Identidad verificada del access token (claims ya validados)."""

    sub: uuid.UUID
    sid: uuid.UUID
    ver: int
    roles: list[str]
    permisos: list[str]
    modulos: list[str]


@lru_cache(maxsize=1)
def get_signing_keypair() -> tuple[str, str]:
    """(private_pem, public_pem): del Settings; en dev/test, efímero (A2)."""
    settings = get_settings()
    private = settings.jwt_private_key.get_secret_value() if settings.jwt_private_key else None
    public = settings.jwt_public_key.get_secret_value() if settings.jwt_public_key else None
    if private and public:
        return private, public
    return generate_keypair()


async def load_claims(
    db: AsyncSession, *, usuario_id: uuid.UUID
) -> tuple[list[str], list[str], list[str]]:
    """roles, permisos y módulos del usuario (§2.1: viajan en el payload)."""
    roles = list(
        await db.scalars(
            select(UsRol.codigo)
            .join(UsUsuarioRol, UsUsuarioRol.rol_id == UsRol.id)
            .where(UsUsuarioRol.usuario_id == usuario_id)
        )
    )
    permisos = sorted(
        set(
            await db.scalars(
                select(UsPermiso.codigo)
                .join(UsRolPermiso, UsRolPermiso.permiso_id == UsPermiso.id)
                .join(UsUsuarioRol, UsUsuarioRol.rol_id == UsRolPermiso.rol_id)
                .where(UsUsuarioRol.usuario_id == usuario_id)
            )
        )
    )
    modulos = list(
        await db.scalars(
            select(UsModulo.codigo)
            .join(UsUsuarioModulo, UsUsuarioModulo.modulo_id == UsModulo.id)
            .where(UsUsuarioModulo.usuario_id == usuario_id)
        )
    )
    return roles, permisos, modulos


async def issue_access_token(
    db: AsyncSession, *, usuario_id: uuid.UUID, sid: uuid.UUID, token_version: int
) -> str:
    """Firma el access token ES256 con los claims completos de §2.1."""
    settings = get_settings()
    private, _public = get_signing_keypair()
    roles, permisos, modulos = await load_claims(db, usuario_id=usuario_id)
    return create_access_token(
        subject=str(usuario_id),
        sid=str(sid),
        token_version=token_version,
        roles=roles,
        permisos=permisos,
        modulos=modulos,
        private_key=private,
        kid=settings.jwt_kid,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
