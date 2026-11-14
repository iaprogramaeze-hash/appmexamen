"""Primitivas de seguridad: Argon2id y JWT ES256 (analisis.txt 2.1 y 2.5).

Sólo funciones puras: hash/verify de contraseñas, generación de keysets y
emisión/verificación de access tokens. El flujo de login, rotación y reuse
detection vive en el dominio auth (T2/T3 de SDD-1) y usa estas piezas.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# Argon2id con los parámetros de analisis.txt 2.5 (OWASP): m=19456 (19 MiB), t=2, p=1.
_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

#: analisis.txt 2.1: firma asimétrica; ES256 (supuesto A1 del feature doc SDD-1).
JWT_ALGORITHM = "ES256"

#: Claims obligatorios de analisis.txt 2.1; decode_token los exige todos.
_REQUIRED_CLAIMS = ["iss", "aud", "exp", "nbf", "iat", "jti", "sid", "ver", "sub"]


def hash_password(password: str) -> str:
    """Hashea con Argon2id; cada llamada produce un hash distinto (salt propio)."""
    return _hasher.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """True si coincide. Cualquier hash inválido o roto devuelve False, no excepción."""
    try:
        return _hasher.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_keypair() -> tuple[str, str]:
    """Genera un keyset ES256 (SECP256R1); devuelve (private_pem, public_pem).

    Sólo para dev/test: en producción las claves vienen del entorno (config).
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


def create_access_token(
    *,
    subject: str,
    sid: str,
    token_version: int,
    roles: list[str],
    permisos: list[str],
    modulos: list[str],
    private_key: str,
    kid: str,
    issuer: str,
    audience: str,
    expires_delta: timedelta,
    jti: str | None = None,
) -> str:
    """Access token ES256 con los claims obligatorios de analisis.txt 2.1.

    El refresh token NO es un JWT (analisis.txt 2.2): es opaco aleatorio y su
    lógica vive en el dominio de sesiones (T2 de SDD-1).
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "sid": sid,
        "ver": token_version,
        "jti": jti or str(uuid.uuid4()),
        "roles": roles,
        "permisos": permisos,
        "modulos": modulos,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM, headers={"kid": kid})


def decode_token(token: str, *, public_key: str, issuer: str, audience: str) -> dict[str, Any]:
    """Verifica firma ES256, issuer, audiencia, expiración y claims obligatorios.

    Lanza ``jwt.ExpiredSignatureError`` o ``jwt.InvalidTokenError``; el caller
    decide la respuesta HTTP. La invalidación por token_version (analisis.txt
    2.6) la valida el dominio auth contra la base, no aquí.
    """
    return jwt.decode(
        token,
        public_key,
        algorithms=[JWT_ALGORITHM],
        issuer=issuer,
        audience=audience,
        options={"require": _REQUIRED_CLAIMS},
    )
