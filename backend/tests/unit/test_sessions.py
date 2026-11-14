"""Sesiones de refresh: token opaco, rotación y reuse detection (analisis.txt 2.2)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.features.auth.errors import InvalidRefreshTokenError, RefreshReuseDetectedError
from app.features.auth.sessions import (
    REFRESH_TOKEN_TTL,
    create_session,
    hash_refresh_token,
    new_refresh_token,
    revoke_all_sessions,
    revoke_session,
    rotate_session,
)


def test_new_refresh_token_is_opaque_and_sha256():
    raw, digest = new_refresh_token()
    assert len(raw) >= 32  # 32 bytes aleatorios (2.2)
    assert digest == hash_refresh_token(raw)
    assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


async def test_create_session_persists_only_the_hash(db_session):
    usuario_id, modulo_id = uuid.uuid4(), uuid.uuid4()
    row, raw = await create_session(db_session, usuario_id=usuario_id, modulo_id=modulo_id)
    assert row.refresh_token_hash == hash_refresh_token(raw)
    assert row.refresh_token_hash != raw  # jamás se persiste el token tal cual (2.2)
    assert row.estado == "activo"
    assert row.familia_id is not None
    assert row.expires_at - row.created_at == REFRESH_TOKEN_TTL  # TTL 7 días (2.2)


async def test_rotate_revokes_old_and_keeps_family(db_session):
    usuario_id, modulo_id = uuid.uuid4(), uuid.uuid4()
    first, raw1 = await create_session(db_session, usuario_id=usuario_id, modulo_id=modulo_id)
    second, raw2 = await rotate_session(db_session, raw_refresh=raw1)
    assert raw2 != raw1
    assert first.estado == "revocado" and first.rotated_at is not None
    assert second.estado == "activo"
    assert second.familia_id == first.familia_id  # rotación dentro de la familia (2.2)
    assert second.refresh_token_hash == hash_refresh_token(raw2)


async def test_reuse_detection_revokes_whole_family(db_session):
    usuario_id, modulo_id = uuid.uuid4(), uuid.uuid4()
    _, raw1 = await create_session(db_session, usuario_id=usuario_id, modulo_id=modulo_id)
    second, raw2 = await rotate_session(db_session, raw_refresh=raw1)
    with pytest.raises(RefreshReuseDetectedError):
        await rotate_session(db_session, raw_refresh=raw1)  # token ya usado (2.2)
    assert second.estado == "revocado"  # la familia entera murió
    with pytest.raises(RefreshReuseDetectedError):
        await rotate_session(db_session, raw_refresh=raw2)


async def test_expired_refresh_rejected(db_session):
    past = datetime.now(UTC) - REFRESH_TOKEN_TTL - timedelta(minutes=1)
    _, raw = await create_session(
        db_session, usuario_id=uuid.uuid4(), modulo_id=uuid.uuid4(), now=past
    )
    with pytest.raises(InvalidRefreshTokenError):
        await rotate_session(db_session, raw_refresh=raw)


async def test_unknown_refresh_rejected(db_session):
    with pytest.raises(InvalidRefreshTokenError):
        await rotate_session(db_session, raw_refresh="token-inexistente")


async def test_logout_and_logout_all(db_session):
    usuario_id, modulo_id = uuid.uuid4(), uuid.uuid4()
    one, _ = await create_session(db_session, usuario_id=usuario_id, modulo_id=modulo_id)
    two, _ = await create_session(db_session, usuario_id=usuario_id, modulo_id=modulo_id)
    other, _ = await create_session(
        db_session, usuario_id=uuid.uuid4(), modulo_id=modulo_id
    )

    assert await revoke_session(db_session, sid=one.id) is True  # logout (2.4)
    assert one.estado == "revocado"
    assert await revoke_session(db_session, sid=one.id) is False  # ya revocada

    assert await revoke_all_sessions(db_session, usuario_id=usuario_id) == 1  # logout-all
    assert two.estado == "revocado"
    assert other.estado == "activo"  # otra familia/usuario no se toca
