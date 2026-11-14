"""Seguridad: Argon2id (analisis.txt 2.5) y claims/validez del JWT ES256 (2.1, 2.6)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    generate_keypair,
    hash_password,
    verify_password,
)

_PRIVATE, _PUBLIC = generate_keypair()
_ISSUER = "backend-epet-n36"
_AUDIENCE = "epet36-api"


def _token(**overrides):
    kwargs: dict = {
        "subject": "usuario-1",
        "sid": "sesion-1",
        "token_version": 3,
        "roles": ["director"],
        "permisos": ["mesa.listar"],
        "modulos": ["sigme_web"],
        "private_key": _PRIVATE,
        "kid": "kid-test",
        "issuer": _ISSUER,
        "audience": _AUDIENCE,
        "expires_delta": timedelta(minutes=15),
    }
    kwargs.update(overrides)
    return create_access_token(**kwargs)


def test_password_roundtrip():
    hashed = hash_password("clave-secreta-123")
    assert hashed != "clave-secreta-123"
    assert verify_password(hashed, "clave-secreta-123")


def test_wrong_password_rejected():
    hashed = hash_password("clave-secreta-123")
    assert not verify_password(hashed, "otra-clave")


def test_broken_hash_rejected_without_exception():
    assert not verify_password("no-es-un-hash", "lo-que-sea")


def test_hashes_are_salted():
    assert hash_password("misma-clave") != hash_password("misma-clave")


def test_argon2_parameters_match_spec():
    """analisis.txt 2.5: Argon2id, m=19456 (19 MiB), t=2, p=1 (OWASP)."""
    hashed = hash_password("clave-secreta-123")
    assert hashed.startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_access_token_full_claims():
    """analisis.txt 2.1: claims obligatorios iss, aud, exp, nbf, iat, jti, sid,
    ver y sub; roles/permisos/módulos en el payload; kid en el header."""
    token = _token()
    header = jwt.get_unverified_header(token)
    assert header["kid"] == "kid-test"
    claims = decode_token(token, public_key=_PUBLIC, issuer=_ISSUER, audience=_AUDIENCE)
    assert claims["sub"] == "usuario-1"
    assert claims["ver"] == 3  # token_version: invalidación global (2.6)
    assert claims["sid"] == "sesion-1"
    assert claims["iss"] == _ISSUER
    assert claims["aud"] == _AUDIENCE
    assert claims["roles"] == ["director"]
    assert claims["permisos"] == ["mesa.listar"]
    assert claims["modulos"] == ["sigme_web"]
    for required in ("exp", "nbf", "iat", "jti"):
        assert required in claims
    assert claims["exp"] > claims["iat"]


def test_expired_token_raises():
    token = _token(expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, public_key=_PUBLIC, issuer=_ISSUER, audience=_AUDIENCE)


def test_wrong_public_key_rejected():
    """analisis.txt 2.1: firma asimétrica — otra clave pública no verifica."""
    _, other_public = generate_keypair()
    token = _token()
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, public_key=other_public, issuer=_ISSUER, audience=_AUDIENCE)


def test_missing_required_claim_rejected():
    """analisis.txt 2.1: sin un claim obligatorio (iss) el token no es válido."""
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": "usuario-1", "iat": now, "exp": now + timedelta(minutes=5)},
        _PRIVATE,
        algorithm="ES256",
        headers={"kid": "kid-test"},
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, public_key=_PUBLIC, issuer=_ISSUER, audience=_AUDIENCE)
