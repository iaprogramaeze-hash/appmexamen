"""Aislamiento de entorno para todos los tests: sin .env ni variables reales de la máquina."""
from __future__ import annotations

import os

# El proceso de test no debe leer el .env local ni variables reales de la máquina.
for _key in (
    "ENVIRONMENT",
    "DATABASE_URL",
    "JWT_SECRET",
    "JWT_PRIVATE_KEY",
    "JWT_PUBLIC_KEY",
    "CORS_ORIGINS",
    "LOG_LEVEL",
):
    os.environ.pop(_key, None)

# Aislamiento del .env FILE: pydantic-settings lo lee aunque la variable de
# entorno no exista, y el .env local trae una DATABASE_URL real (Neon). Sin
# este guard, cualquier código que consulte has_engine_configured() en un test
# (p. ej. la entrega en background de ntf_envio) intentaría tocar la BD real.
# "" es falsy: get_session, ping y has_engine_configured tratan "" como "sin
# base", igual que None.
os.environ["DATABASE_URL"] = ""

os.environ["ENVIRONMENT"] = "test"
# Aislamiento JWT: aunque exista un .env local con claves reales, los tests
# firman con un keyset efímero (supuesto A2). El string vacío hace que
# get_signing_keypair genere el par efímero sin tocar las claves del usuario.
os.environ["JWT_PRIVATE_KEY"] = ""
os.environ["JWT_PUBLIC_KEY"] = ""

import pytest  # noqa: E402

from app.core.config import clear_settings_cache  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import dispose_engines  # noqa: E402

# Todas las tablas deben estar en el metadata antes de cualquier create_all:
# los FK cruzan dominios (us_usuario.persona_id -> pe_persona) y correr un
# solo archivo de tests no importa los demás modelos.
from app.features.auditoria import models as _auditoria_models  # noqa: E402,F401
from app.features.catalogo import models as _catalogo_models  # noqa: E402,F401
from app.features.dispositivos import models as _dispositivos_models  # noqa: E402,F401
from app.features.mesas import models as _mesas_models  # noqa: E402,F401
from app.features.notificaciones import models as _notificaciones_models  # noqa: E402,F401
from app.features.personas import models as _personas_models  # noqa: E402,F401
from app.features.preinscripcion import models as _preinscripcion_models  # noqa: E402,F401
from app.features.reportes import models as _reportes_models  # noqa: E402,F401
from app.features.usuarios import models as _usuarios_models  # noqa: E402,F401


@pytest.fixture(autouse=True)
def _clean_state():
    """Cache de settings y engines limpios entre tests."""
    clear_settings_cache()
    yield
    clear_settings_cache()
    import asyncio

    asyncio.run(dispose_engines())


@pytest.fixture
async def db_session():
    """Sesión async sobre SQLite en memoria usando el metadata real.

    Los ``server_default`` de Postgres (gen_random_uuid(), now()) se quitan
    sólo durante la creación del esquema de test y se restauran al final: los
    servicios siempre escriben id/created_at/expires_at explícitos.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    saved: dict[tuple[str, str], object] = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                saved[(table.name, column.name)] = column.server_default
                column.server_default = None
    engine = create_async_engine("sqlite+aiosqlite://")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        maker = async_sessionmaker(engine, expire_on_commit=False)
        async with maker() as session:
            yield session
    finally:
        for (table_name, column_name), default in saved.items():
            Base.metadata.tables[table_name].columns[column_name].server_default = default
        await engine.dispose()
