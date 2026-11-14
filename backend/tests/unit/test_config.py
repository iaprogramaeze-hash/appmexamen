"""Config: enumerados, defaults y las guardas de producción de analisis.txt 0 y 2.1."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_DB = "postgresql+asyncpg://user:pass@host/db"
_PRIVATE_PEM = "-----BEGIN PRIVATE KEY-----\n(test)\n-----END PRIVATE KEY-----"
_PUBLIC_PEM = "-----BEGIN PUBLIC KEY-----\n(test)\n-----END PUBLIC KEY-----"


def _prod(**overrides):
    kwargs: dict = {
        "_env_file": None,
        "environment": "production",
        "database_url": _DB,
        "jwt_private_key": _PRIVATE_PEM,
        "jwt_public_key": _PUBLIC_PEM,
        "cors_origins": ["https://landing.example.com"],
    }
    kwargs.update(overrides)
    return Settings(**kwargs)


def test_defaults():
    s = Settings(_env_file=None)
    assert s.environment == "test"
    assert s.database_url is None
    assert s.cors_origins == []
    assert s.access_token_expire_minutes == 15
    assert s.refresh_token_expire_days == 7
    assert not s.is_production
    # analisis.txt 2.1: firma asimétrica; las claves son opcionales fuera de producción.
    assert s.jwt_algorithm == "ES256"
    assert s.jwt_private_key is None
    assert s.jwt_public_key is None


def test_environment_enum_rejects_unknown():
    with pytest.raises(ValidationError, match="environment"):
        Settings(_env_file=None, environment="prod")


def test_production_requires_database_url():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(
            _env_file=None,
            environment="production",
            jwt_private_key=_PRIVATE_PEM,
            jwt_public_key=_PUBLIC_PEM,
        )


def test_production_requires_signing_keys():
    """analisis.txt 2.1: producción sin claves de firma asimétrica no arranca."""
    with pytest.raises(ValidationError, match="JWT_PRIVATE_KEY"):
        Settings(_env_file=None, environment="production", database_url=_DB)


def test_production_rejects_symmetric_algorithm():
    """analisis.txt 2.1: RS256 o ES256; jamás simétrico (HS256)."""
    with pytest.raises(ValidationError, match="ES256"):
        _prod(jwt_algorithm="HS256")


def test_production_rejects_wildcard_cors():
    """analisis.txt 0: nunca allow_origins=["*"] en producción."""
    with pytest.raises(ValidationError, match="CORS"):
        _prod(cors_origins=["*"])


def test_production_accepts_real_config():
    s = _prod()
    assert s.is_production
    assert s.cors_origins == ["https://landing.example.com"]


def test_pem_keys_are_unescaped():
    """env.example pide PEM en una línea con \\n literal: Settings los convierte."""
    s = Settings(_env_file=None, jwt_private_key="-----BEGIN X-----\\nabc\\n-----END X-----")
    assert "\\n" not in s.jwt_private_key.get_secret_value()
    assert "\n" in s.jwt_private_key.get_secret_value()
