"""Cola de email (RB-25 / NFR-033): encolar después de responder y entregar.

Contrato que este módulo cumple:

- RN-051: la notificación se encola DESPUÉS de responder. Por eso
  `encolar_y_entregar` corre como BackgroundTask de Starlette, con sesión
  propia: la sesión de la request ya se cerró cuando el task se ejecuta.
- NFR-034 / EX-21: un fallo del proveedor ocurre después de la respuesta y
  NO modifica la respuesta HTTP ni ninguna fila de negocio. Por eso el
  transport se envuelve y cualquier excepción queda registrada en la cola
  (`estado='fallido'`, `reintentos`, `ultimo_error`) sin propagarse: el task
  jamás revienta el ciclo ASGI de la respuesta.
- Sin SMTP configurado (dev/test) el envío queda `pendiente` en la cola, no
  falla. El reintento programado está fuera de alcance: el contrato de
  reintento sigue ABIERTO (PD-04 / 0005) y lo dará el worker.
- Al pasar a un estado terminal (`enviado` o `fallido`) se purga `cuerpo`:
  el token de recuperación no debe quedar legible en la BD (RIESGO-1).
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.session import get_engine, has_engine_configured
from app.features.notificaciones.models import (
    ESTADO_ENVIADO,
    ESTADO_FALLIDO,
    ESTADO_PENDIENTE,
    NtfEnvio,
)

logger = logging.getLogger(__name__)

#: Segundos por intento de conexión SMTP (el backoff de reintentos es NFR-032
#: y pertenece al contrato de reintento, todavía abierto).
SMTP_TIMEOUT = 10


@asynccontextmanager
async def _sesion_propia() -> AsyncIterator[AsyncSession]:
    """Sesión aparte de la de la request (el background corre tras el cierre)."""
    settings = get_settings()
    engine = get_engine(settings.database_url or "", production=settings.is_production)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def encolar_y_entregar(
    *, destinatario: str, asunto: str, cuerpo: str
) -> None:
    """Encola el email y hace UN intento de entrega; nunca lanza excepción.

    Se invoca desde el router como BackgroundTask, después de enviar la
    respuesta (RN-051). Sin DATABASE_URL no hay dónde registrar la cola
    (entorno de test): se omite con un log, sin romper la respuesta.
    """
    try:
        if not has_engine_configured():
            logger.warning(
                "ntf_envio: sin DATABASE_URL; el email a %s no quedó encolado",
                destinatario,
            )
            return
        async with _sesion_propia() as db:
            envio = NtfEnvio(
                id=uuid.uuid4(),
                created_at=datetime.now(UTC),
                destinatario=destinatario,
                asunto=asunto,
                cuerpo=cuerpo,
                estado=ESTADO_PENDIENTE,
                reintentos=0,
            )
            db.add(envio)
            await db.flush()

            settings = get_settings()
            if not settings.smtp_host:
                # Sin transporte (dev/test): queda visible como pendiente.
                await db.commit()
                logger.info(
                    "ntf_envio: SMTP sin configurar; el email a %s queda pendiente",
                    destinatario,
                )
                return

            try:
                await asyncio.to_thread(_enviar_smtp, destinatario, asunto, cuerpo)
            except Exception as exc:  # noqa: BLE001 - EX-21: el fallo va a la cola
                envio.estado = ESTADO_FALLIDO
                envio.reintentos += 1
                envio.ultimo_error = f"{exc.__class__.__name__}: {exc}"[:500]
                envio.cuerpo = ""  # terminal: purga el token (nunca se entregó)
                await db.commit()
                logger.warning(
                    "ntf_envio: entrega a %s fallida (reintento %d): %s",
                    destinatario,
                    envio.reintentos,
                    exc,
                )
                return
            envio.estado = ESTADO_ENVIADO
            envio.cuerpo = ""  # terminal: purga el token tras entregarlo
            await db.commit()
    except Exception as exc:  # noqa: BLE001 - un task nunca debe tumbar la respuesta
        logger.exception("ntf_envio: fallo inesperado del envío a %s: %s", destinatario, exc)


def _enviar_smtp(destinatario: str, asunto: str, cuerpo: str) -> None:
    """Transporte SMTP síncrono (se llama vía asyncio.to_thread)."""
    settings = get_settings()
    origen = settings.smtp_from or settings.smtp_user or "no-reply@localhost"
    mensaje = EmailMessage()
    mensaje["From"] = origen
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    if settings.smtp_starttls:
        cliente = smtplib.SMTP(
            settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT
        )
    else:
        cliente = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT
        )
    with cliente:
        if settings.smtp_starttls:
            cliente.starttls()
        if settings.smtp_user and settings.smtp_password:
            cliente.login(
                settings.smtp_user, settings.smtp_password.get_secret_value()
            )
        cliente.send_message(mensaje)
