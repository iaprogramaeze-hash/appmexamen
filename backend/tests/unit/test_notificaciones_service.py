"""Cola de email RB-25 / NFR-033: encolar en background y estados (EX-21).

`encolar_y_entregar` corre DESPUÉS de responder (RN-051) con sesión propia.
Estos tests cubren los tres caminos del transporte: sin base (test), sin SMTP
(dev, queda pendiente) y con SMTP (enviado / fallido sin propagar el error,
NFR-034).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.db.session import get_engine
from app.features.notificaciones.models import (
    ESTADO_ENVIADO,
    ESTADO_FALLIDO,
    ESTADO_PENDIENTE,
    NtfEnvio,
)
from app.features.notificaciones.service import encolar_y_entregar


async def _motor_tmp(tmp_path, monkeypatch, *, smtp_host: str | None) -> object:
    """Apunta los settings a un SQLite de archivo y crea `ntf_envio`.

    Devuelve el engine compartido: `get_engine` cachea por URL, así que el
    task y el test ven la MISMA base.
    """
    url = f"sqlite+aiosqlite:///{tmp_path / 'ntf.db'}"
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", url)
    monkeypatch.setattr(settings, "smtp_host", smtp_host)

    tabla = NtfEnvio.__table__
    engine = get_engine(url, production=settings.is_production)
    # Replica el strip de server_default del conftest: gen_random_uuid()/now()
    # son expresiones de Postgres que SQLite no evalúa.
    guardados = {
        col.name: col.server_default
        for col in tabla.columns
        if col.server_default is not None
    }
    for nombre in guardados:
        tabla.columns[nombre].server_default = None
    try:
        async with engine.begin() as conn:
            await conn.run_sync(tabla.create)
    finally:
        for nombre, default in guardados.items():
            tabla.columns[nombre].server_default = default
    return engine


async def _fila_unica(engine) -> NtfEnvio | None:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        return await session.scalar(select(NtfEnvio))


async def test_sin_base_no_revienta_ni_encola(monkeypatch):
    """Sin DATABASE_URL (test) el task se omite con log: nunca rompe (EX-21)."""
    monkeypatch.setattr(get_settings(), "database_url", "")
    assert not get_settings().database_url  # "" o None: ambos significan sin base
    await encolar_y_entregar(destinatario="a@b.c", asunto="s", cuerpo="c")
    # sin motor no hay fila posible; lo verificado es que no lanza excepción


async def test_sin_smtp_queda_pendiente(tmp_path, monkeypatch):
    """Sin transporte configurado (dev) el envío queda registrado como
    pendiente para el worker: no falla y no se pierde el pedido."""
    engine = await _motor_tmp(tmp_path, monkeypatch, smtp_host=None)

    await encolar_y_entregar(
        destinatario="alumno@correo.com",
        asunto="Restablecimiento de clave",
        cuerpo="token de prueba",
    )

    fila = await _fila_unica(engine)
    assert fila is not None
    assert fila.estado == ESTADO_PENDIENTE
    assert fila.destinatario == "alumno@correo.com"
    assert fila.reintentos == 0
    assert fila.ultimo_error is None
    assert fila.cuerpo == "token de prueba"  # pendiente conserva el cuerpo


async def test_entrega_exitosa_marca_enviado(tmp_path, monkeypatch):
    """Con SMTP configurado y transporte OK: estado 'enviado'."""
    engine = await _motor_tmp(tmp_path, monkeypatch, smtp_host="smtp.test")
    monkeypatch.setattr(
        "app.features.notificaciones.service._enviar_smtp", lambda *args: None
    )

    await encolar_y_entregar(destinatario="a@b.c", asunto="s", cuerpo="c")

    fila = await _fila_unica(engine)
    assert fila.estado == ESTADO_ENVIADO
    assert fila.reintentos == 0
    assert fila.ultimo_error is None
    assert fila.cuerpo == ""  # purga tras entregar: el token no queda en la BD


async def test_falla_del_proveedor_queda_en_la_cola(tmp_path, monkeypatch):
    """EX-21/NFR-034: el proveedor falla DESPUÉS de la respuesta; el error se
    registra en la cola (fallido + reintentos) y NUNCA se propaga."""
    engine = await _motor_tmp(tmp_path, monkeypatch, smtp_host="smtp.test")

    def _proveedor_caido(*_args, **_kwargs):
        raise RuntimeError("proveedor de email caído")

    monkeypatch.setattr(
        "app.features.notificaciones.service._enviar_smtp", _proveedor_caido
    )

    await encolar_y_entregar(destinatario="a@b.c", asunto="s", cuerpo="c")

    fila = await _fila_unica(engine)
    assert fila.estado == ESTADO_FALLIDO
    assert fila.reintentos == 1
    assert "proveedor de email caído" in (fila.ultimo_error or "")
    assert fila.cuerpo == ""  # purga también en fallo: nunca salió, no se reintentan
