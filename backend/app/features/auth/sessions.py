"""Sesiones de refresh: token opaco, rotación y reuse detection (analisis.txt 2.2).

El refresh NUNCA es un JWT: es un valor aleatorio de 32 bytes y en us_sesion se
persiste sólo su hash SHA-256 (2.2). La rotación mantiene la familia y el reuse
detection revoca la familia completa. Estas funciones no hacen commit: la
transacción la cierra quien las invoca (los endpoints de T3).
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.errors import InvalidRefreshTokenError, RefreshReuseDetectedError
from app.features.usuarios.models import UsSesion

#: analisis.txt 2.2: refresh opaco de 32 bytes aleatorios, TTL 7 días.
REFRESH_TOKEN_BYTES = 32
REFRESH_TOKEN_TTL = timedelta(days=7)

ESTADO_ACTIVO = "activo"
ESTADO_REVOCADO = "revocado"


def new_refresh_token() -> tuple[str, str]:
    """Genera el par (token opaco, hash SHA-256 hex): se persiste sólo el hash."""
    raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256 hex del refresh; es lo único que se guarda en us_sesion (2.2)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Normaliza datetimes sin tzinfo (SQLite en tests) a UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def create_session(
    db: AsyncSession,
    *,
    usuario_id: uuid.UUID,
    modulo_id: uuid.UUID,
    ip: str | None = None,
    user_agent: str | None = None,
    now: datetime | None = None,
) -> tuple[UsSesion, str]:
    """Crea una sesión nueva con su propia familia; devuelve (fila, refresh crudo)."""
    moment = _now(now)
    raw, digest = new_refresh_token()
    row = UsSesion(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        modulo_id=modulo_id,
        refresh_token_hash=digest,
        familia_id=uuid.uuid4(),
        estado=ESTADO_ACTIVO,
        ip=ip,
        user_agent=user_agent,
        expires_at=moment + REFRESH_TOKEN_TTL,
        created_at=moment,
    )
    db.add(row)
    await db.flush()
    return row, raw


async def _find_by_token(db: AsyncSession, raw_refresh: str) -> UsSesion | None:
    return await db.scalar(
        select(UsSesion).where(UsSesion.refresh_token_hash == hash_refresh_token(raw_refresh))
    )


async def rotate_session(
    db: AsyncSession,
    *,
    raw_refresh: str,
    ip: str | None = None,
    user_agent: str | None = None,
    now: datetime | None = None,
) -> tuple[UsSesion, str]:
    """Rota el par dentro de la familia (2.2); devuelve (sesión nueva, refresh crudo).

    Reuse detection: si el token ya estaba revocado, revoca TODA la familia y se
    exige login nuevo. Un token vencido es simplemente inválido.
    """
    moment = _now(now)
    current = await _find_by_token(db, raw_refresh)
    if current is None:
        raise InvalidRefreshTokenError("refresh token desconocido")
    if current.estado != ESTADO_ACTIVO:
        await revoke_family(db, familia_id=current.familia_id)
        raise RefreshReuseDetectedError("refresh token ya usado: familia revocada")
    if as_utc(current.expires_at) <= moment:
        raise InvalidRefreshTokenError("refresh token expirado")
    current.estado = ESTADO_REVOCADO
    current.rotated_at = moment
    new_row, raw = await create_session(
        db,
        usuario_id=current.usuario_id,
        modulo_id=current.modulo_id,
        ip=ip,
        user_agent=user_agent,
        now=moment,
    )
    new_row.familia_id = current.familia_id  # la rotación no cambia de familia (2.2)
    await db.flush()
    return new_row, raw


async def revoke_family(db: AsyncSession, *, familia_id: uuid.UUID) -> int:
    """Revoca todas las sesiones activas de la familia; devuelve cuántas cambió."""
    result = await db.execute(
        update(UsSesion)
        .where(UsSesion.familia_id == familia_id, UsSesion.estado == ESTADO_ACTIVO)
        .values(estado=ESTADO_REVOCADO)
    )
    await db.flush()
    return result.rowcount or 0


async def revoke_session(db: AsyncSession, *, sid: uuid.UUID) -> bool:
    """Logout (2.4): revoca la sesión del sid. False si no existe o ya estaba revocada."""
    row = await db.get(UsSesion, sid)
    if row is None or row.estado != ESTADO_ACTIVO:
        return False
    row.estado = ESTADO_REVOCADO
    await db.flush()
    return True


async def revoke_all_sessions(db: AsyncSession, *, usuario_id: uuid.UUID) -> int:
    """Logout-all (2.4): revoca las sesiones activas del usuario; devuelve cuántas."""
    result = await db.execute(
        update(UsSesion)
        .where(UsSesion.usuario_id == usuario_id, UsSesion.estado == ESTADO_ACTIVO)
        .values(estado=ESTADO_REVOCADO)
    )
    await db.flush()
    return result.rowcount or 0
