"""Tablas planeadas PD-04 (us_password_reset) y PD-05 (aud_evento).

Verifican la estructura de las tablas que agregó la migración 0002:

- PD-04 [CERRADO 2026-10-06]: reset de clave por email desde v1. Sólo se
  persiste el hash SHA-256 del token opaco, nunca el token en claro; la fila
  se consume una única vez (usado_en) y expira (expira_en).
- PD-05 [CERRADO 2026-10-06]: bitácora append-only con snapshot JSONB. Sin
  updated_at ni deleted_at: la fila no se modifica (el trigger de la
  migración bloquea UPDATE/DELETE en Postgres). El snapshot no puede contener
  password_hash, refresh tokens ni hashes de sesión — regla de quien escribe
  el evento, fuera del alcance de estas tablas.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.auditoria.models import AudEvento
from app.features.usuarios.models import UsPasswordReset


def _sha256(valor: str) -> str:
    return hashlib.sha256(valor.encode()).hexdigest()


# ---------------------------------------------------------------------------
# PD-04 — us_password_reset
# ---------------------------------------------------------------------------
def test_password_reset_estructura_pd04() -> None:
    columnas = {c.name: c for c in UsPasswordReset.__table__.columns}
    assert set(columnas) == {
        "id",
        "usuario_id",
        "token_hash",
        "ip",
        "user_agent",
        "expira_en",
        "usado_en",
        "created_at",
    }
    # Un token se consume, no se edita: sin updated_at ni deleted_at (§3.12).
    assert "updated_at" not in columnas and "deleted_at" not in columnas
    assert columnas["token_hash"].unique
    assert columnas["token_hash"].nullable is False
    assert columnas["expira_en"].nullable is False
    assert columnas["usado_en"].nullable is True


async def test_password_reset_persiste_hash_y_se_consume(db_session) -> None:
    token = "opaco-que-nunca-se-persiste-en-claro"
    fila = UsPasswordReset(
        id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        token_hash=_sha256(token),
        ip="192.0.2.10",
        user_agent="Mozilla/5.0",
        expira_en=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )
    db_session.add(fila)
    await db_session.commit()

    guardado = await db_session.get(UsPasswordReset, fila.id)
    assert guardado is not None
    assert guardado.token_hash == _sha256(token)
    assert token not in guardado.token_hash  # jamás el valor en claro
    assert guardado.usado_en is None

    guardado.usado_en = datetime.now(UTC)
    await db_session.commit()
    releido = await db_session.get(UsPasswordReset, fila.id)
    assert releido.usado_en is not None


async def test_password_reset_token_hash_es_unico(db_session) -> None:
    hash_dup = _sha256("mismo-token")
    base = dict(
        usuario_id=uuid.uuid4(),
        token_hash=hash_dup,
        expira_en=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )
    db_session.add(UsPasswordReset(id=uuid.uuid4(), **base))
    db_session.add(UsPasswordReset(id=uuid.uuid4(), **base))
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ---------------------------------------------------------------------------
# PD-05 — aud_evento
# ---------------------------------------------------------------------------
def test_aud_evento_estructura_pd05() -> None:
    columnas = {c.name: c for c in AudEvento.__table__.columns}
    assert set(columnas) == {
        "id",
        "created_at",
        "usuario_id",
        "username",
        "modulo",
        "accion",
        "entidad",
        "entidad_id",
        "resultado",
        "ip",
        "user_agent",
        "snapshot",
    }
    # Append-only: la bitácora no tiene columnas de modificación (PD-05).
    assert "updated_at" not in columnas and "deleted_at" not in columnas
    for obligatoria in ("accion", "entidad", "resultado", "created_at"):
        assert columnas[obligatoria].nullable is False
    # Intentos denegados anónimos: usuario_id y username pueden ser NULL.
    assert columnas["usuario_id"].nullable is True
    assert columnas["snapshot"].nullable is True


async def test_aud_evento_admite_intento_denegado_anonimo(db_session) -> None:
    evento = AudEvento(
        id=uuid.uuid4(),
        accion="auth-login",
        entidad="us_usuario",
        resultado="denegado",
        ip="198.51.100.7",
        user_agent="curl/8.5",
        snapshot={"motivo": "credenciales-invalidas"},
        created_at=datetime.now(UTC),
    )
    db_session.add(evento)
    await db_session.commit()

    guardado = await db_session.get(AudEvento, evento.id)
    assert guardado is not None
    assert guardado.usuario_id is None and guardado.username is None
    assert guardado.snapshot == {"motivo": "credenciales-invalidas"}


async def test_aud_evento_registra_escritura_exitosa(db_session) -> None:
    mesa_id = uuid.uuid4()
    evento = AudEvento(
        id=uuid.uuid4(),
        usuario_id=uuid.uuid4(),
        username="colega.sigme",
        modulo="sigme_web",
        accion="mesa-examen-crear",
        entidad="es_mesa_examen",
        entidad_id=str(mesa_id),
        resultado="ok",
        snapshot={"antes": None, "despues": {"id": str(mesa_id), "estado": "borrador"}},
        created_at=datetime.now(UTC),
    )
    db_session.add(evento)
    await db_session.commit()

    guardado = await db_session.get(AudEvento, evento.id)
    assert guardado.modulo == "sigme_web"
    assert guardado.entidad_id == str(mesa_id)
    assert guardado.snapshot["despues"]["estado"] == "borrador"


async def test_aud_evento_resultado_restringido_a_ok_o_denegado(db_session) -> None:
    db_session.add(
        AudEvento(
            id=uuid.uuid4(),
            accion="auth-login",
            entidad="us_usuario",
            resultado="cualquiera",
            created_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
