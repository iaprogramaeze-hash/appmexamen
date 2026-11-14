"""Configuracion central: pydantic-settings + variables de entorno (analisis.txt 5)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENVIRONMENTS = ("development", "test", "staging", "production")

#: analisis.txt 2.1: firma asimétrica; sólo ES256 (supuesto A1 del feature doc SDD-1).
_JWT_ALGORITHMS = ("ES256",)


class Settings(BaseSettings):
    """Entorno cargado de variables reales o de un archivo .env local."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "backend-epet-n36"
    app_version: str = "0.1.0"
    # development | test | staging | production
    environment: str = "development"
    log_level: str = "INFO"

    # None -> la app arranca sin base y /healthz degrada a db=unavailable.
    database_url: str | None = None

    # analisis.txt 2.1: keyset asimétrico ES256 (PEM; en la variable de entorno
    # se escriben con \n literal). None en dev/test: se genera un keyset efímero.
    jwt_private_key: SecretStr | None = None
    jwt_public_key: SecretStr | None = None
    jwt_kid: str = "epet36-key-1"
    jwt_algorithm: str = "ES256"
    jwt_issuer: str = "backend-epet-n36"
    jwt_audience: str = "epet36-api"
    access_token_expire_minutes: int = 15  # analisis.txt 2.1: 15 min, max 30
    refresh_token_expire_days: int = 7  # analisis.txt 2.2: refresh de 7 dias

    # [] -> CORS deshabilitado. Nunca "*" en produccion (analisis.txt 0).
    cors_origins: list[str] = []

    # SMTP de la cola de email (RB-25 / NFR-033). Sin smtp_host la app arranca
    # igual: los envios quedan 'pendientes' en ntf_envio (dev/test); con host
    # configurado se intenta la entrega tras responder. Nunca es requisito de
    # arranque en produccion (la cola registra el estado, NFR-033).
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    #: Remitente (From); si se omite se usa smtp_user.
    smtp_from: str | None = None
    smtp_starttls: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("environment")
    @classmethod
    def _known_environment(cls, value: str) -> str:
        if value not in _ENVIRONMENTS:
            raise ValueError(f"environment debe ser uno de {_ENVIRONMENTS}, no {value!r}")
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def _asymmetric_only(cls, value: str) -> str:
        if value not in _JWT_ALGORITHMS:
            raise ValueError(f"jwt_algorithm debe ser ES256 (analisis.txt 2.1), no {value!r}")
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _vacia_es_ninguna(cls, value: object) -> object:
        """Vacío (env o .env) == sin base: '' y None significan lo mismo.

        Los consumidores (get_session, ping, has_engine_configured) chequean
        por truthiness; este validador unifica la señal y permite que el
        conftest pise con "" una DATABASE_URL real del .env local.
        """
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("jwt_private_key", "jwt_public_key", mode="before")
    @classmethod
    def _normalize_pem(cls, value: object) -> object:
        """Clave vacía -> None; los PEM viajan en una línea con \\n literal
        (env.example) y se cargan con saltos reales."""
        if isinstance(value, str):
            if not value.strip():
                return None
            if "\\n" in value:
                return value.replace("\\n", "\n")
        return value

    @model_validator(mode="after")
    def _validate_production(self) -> Settings:
        """Fallar temprano si produccion llega con la configuracion de ejemplo.

        Reglas de analisis.txt 0: secretos nunca en el repo; CORS sin "*".
        Regla de 2.1: el keyset de firma asimétrica es obligatorio en producción.
        """
        if not self.is_production:
            return self
        if not self.database_url:
            raise ValueError("DATABASE_URL es obligatoria en produccion")
        private = self.jwt_private_key.get_secret_value() if self.jwt_private_key else ""
        public = self.jwt_public_key.get_secret_value() if self.jwt_public_key else ""
        if not private.strip() or not public.strip():
            raise ValueError(
                "JWT_PRIVATE_KEY y JWT_PUBLIC_KEY (PEM ES256) son obligatorios "
                "en produccion (analisis.txt 2.1)"
            )
        if "*" in self.cors_origins:
            raise ValueError("CORS: nunca allow_origins=[\"*\"] en produccion (analisis.txt 0)")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Instancia singleton; los tests limpian la cache con clear_settings_cache()."""
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
