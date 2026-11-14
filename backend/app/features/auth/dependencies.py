"""Autenticación y autorización por request (analisis.txt 2.6, 2.7, 2.8; SDD-1 T3/T4).

Valida el access token ES256 y, contra la base: ver == token_version vigente
(§2.6) y sesión aún activa (logout mata el access de inmediato). La
autorización (require_permiso / require_modulo, §2.7/§2.8) vive acá y no en
core/dependencies.py porque construye sobre Principal: core no importa un
dominio. Los checks leen los claims del token (§2.1: viajan "para autorizar
sin consulta"), no vuelven a tocar la base.
"""
from __future__ import annotations

import uuid

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.features.auth import service
from app.features.auth.tokens import Principal, get_signing_keypair
from app.features.usuarios.models import UsSesion, UsUsuario

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str, *, code: str) -> UnauthorizedError:
    return UnauthorizedError(detail, code=code)


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    """Access token válido + token_version vigente + sesión activa (§2.6)."""
    if credentials is None:
        raise _unauthorized("Falta el token de acceso", code="no-autenticado")
    _, public_key = get_signing_keypair()
    settings = get_settings()
    try:
        claims = decode_token(
            credentials.credentials,
            public_key=public_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except pyjwt.ExpiredSignatureError as exc:
        raise _unauthorized("El token de acceso expiró", code="token-expirado") from exc
    except pyjwt.InvalidTokenError as exc:
        raise _unauthorized("El token de acceso no es válido", code="token-invalido") from exc

    try:
        usuario_id = uuid.UUID(str(claims["sub"]))
        sid = uuid.UUID(str(claims["sid"]))
    except (KeyError, ValueError) as exc:
        raise _unauthorized("El token de acceso no es válido", code="token-invalido") from exc

    usuario = await db.get(UsUsuario, usuario_id)
    if (
        usuario is None
        or usuario.deleted_at is not None
        or not usuario.activo
        or usuario.token_version != claims["ver"]
    ):
        raise _unauthorized("El token de acceso no es válido", code="token-invalido")
    # §2.6/PD-27: la suspensión y el bloqueo temporal frenan toda request,
    # no sólo el login.
    service.verificar_cuenta_operativa(usuario)

    sesion = await db.get(UsSesion, sid)
    if sesion is None or sesion.estado != "activo":
        raise _unauthorized("La sesión fue revocada", code="sesion-revocada")

    return Principal(
        sub=usuario_id,
        sid=sid,
        ver=int(claims["ver"]),
        roles=list(claims["roles"]),
        permisos=list(claims["permisos"]),
        modulos=list(claims["modulos"]),
    )


def require_permiso(codigo: str):
    """§2.7: el endpoint exige este permiso; lo decide desde los claims (§2.1).

    Uso en un endpoint: ``principal: Principal = Depends(require_permiso("mesa.crear"))``.
    Sin el permiso -> 403 permiso-denegado (PD-24).
    """

    async def _verificar(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if codigo not in principal.permisos:
            raise ForbiddenError(
                "El usuario no tiene el permiso requerido", code="permiso-denegado"
            )
        return principal

    return _verificar


def require_modulo(codigo: str):
    """§2.8: el usuario sólo opera en los módulos que tiene asignados.

    "El prefijo de módulo no reemplaza el permiso: módulo = a qué app puede
    entrar; permiso = qué puede hacer adentro" — ambos se declaran juntos.
    Sin el módulo -> 403 modulo-no-asignado (PD-24).
    """

    async def _verificar(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if codigo not in principal.modulos:
            raise ForbiddenError(
                "El usuario no tiene asignado este módulo", code="modulo-no-asignado"
            )
        return principal

    return _verificar
