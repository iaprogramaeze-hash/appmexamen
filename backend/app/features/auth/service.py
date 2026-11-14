"""Flujo de login, cambio de clave y recuperación (analisis.txt 2.4-2.6; PD-27)."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppError,
    DomainValidationError,
    ForbiddenError,
    UnauthorizedError,
)
from app.core.security import hash_password, verify_password
from app.features.auth.sessions import (
    as_utc,
    create_session,
    revoke_all_sessions,
)
from app.features.auth.tokens import Principal
from app.features.usuarios.models import (
    UsModulo,
    UsPasswordReset,
    UsUsuario,
    UsUsuarioModulo,
)

#: PD-27 (§2.4): 5 fallos en 15 minutos -> 429 + cuenta bloqueada 15 minutos.
LOGIN_MAX_INTENTOS = 5
LOGIN_BLOQUEO = timedelta(minutes=15)

#: Validez del token de recuperación que viaja por correo (PD-04 / decisión
#: 2026-11-12: flujo automático con verificación por correo). 24 h es el
#: supuesto desde v1 y queda ajustable sin tocar esquema.
SOLICITUD_EXPIRA = timedelta(hours=24)



class CuentaBloqueadaError(AppError):
    """429 con Retry-After: bloqueo temporal de login (PD-27)."""

    status_code = 429
    code = "cuenta-bloqueada"


def _credenciales_invalidas() -> UnauthorizedError:
    return UnauthorizedError("Usuario o clave incorrectos", code="credenciales-invalidas")


def _bloqueada(restante: int) -> CuentaBloqueadaError:
    return CuentaBloqueadaError(
        "Cuenta bloqueada temporalmente por intentos fallidos",
        headers={"Retry-After": str(restante)},
    )


async def login(
    db: AsyncSession,
    *,
    username: str,
    password: str,
    modulo: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[UsUsuario, uuid.UUID, str]:
    """Verifica credenciales con rate limit en base (PD-27, supuesto A4).

    Devuelve (usuario, sid, refresh_crudo). No hace commit: el router
    persiste contadores incluso cuando la respuesta es un error.
    """
    now = datetime.now(UTC)
    usuario = await db.scalar(
        select(UsUsuario).where(
            UsUsuario.username == username, UsUsuario.deleted_at.is_(None)
        )
    )

    if usuario is not None and usuario.bloqueado_hasta is not None:
        bloqueado_hasta = as_utc(usuario.bloqueado_hasta)
        if bloqueado_hasta > now:
            restante = max(1, int((bloqueado_hasta - now).total_seconds()))
            raise _bloqueada(restante)
        # El bloqueo venció: intentos_fallidos -> 0 (PD-27)
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None

    if usuario is None or not verify_password(usuario.password_hash, password):
        if usuario is not None:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= LOGIN_MAX_INTENTOS:
                usuario.bloqueado_hasta = now + LOGIN_BLOQUEO
                usuario.token_version += 1  # §2.6: bloquear sube token_version
                raise _bloqueada(max(1, int(LOGIN_BLOQUEO.total_seconds())))
        raise _credenciales_invalidas()

    if usuario.bloqueado:
        raise ForbiddenError("La cuenta está suspendida", code="cuenta-suspendida")

    modulo_row = await db.scalar(select(UsModulo).where(UsModulo.codigo == modulo))
    if modulo_row is None:
        raise DomainValidationError(
            "Solicitud inválida",
            code="validacion",
            errors=[{"field": "modulo", "message": "módulo inexistente"}],
        )

    # §2.8: el usuario sólo puede OPERAR en los módulos que tiene asignados;
    # entrar a una app sin asignación es 403, no un fallo de credenciales
    # (no suma intentos_fallidos del rate limit de PD-27).
    asignado = await db.scalar(
        select(UsUsuarioModulo.usuario_id).where(
            UsUsuarioModulo.usuario_id == usuario.id,
            UsUsuarioModulo.modulo_id == modulo_row.id,
        )
    )
    if asignado is None:
        raise ForbiddenError(
            "El usuario no tiene asignado este módulo", code="modulo-no-asignado"
        )

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_ingreso = now
    sesion, refresh = await create_session(
        db,
        usuario_id=usuario.id,
        modulo_id=modulo_row.id,
        ip=ip,
        user_agent=user_agent,
        now=now,
    )
    return usuario, sesion.id, refresh


def verificar_cuenta_operativa(usuario: UsUsuario) -> None:
    """§2.6/PD-27: una cuenta suspendida o bloqueada no opera por request.

    Se usa en autorización (get_current_principal) y en refresh: el access y
    el refresh previos al bloqueo no renuevan API mientras dure la suspensión
    (bloqueado) o el bloqueo temporal (bloqueado_hasta vigente).
    """
    if usuario.bloqueado:
        raise ForbiddenError("La cuenta está suspendida", code="cuenta-suspendida")
    if usuario.bloqueado_hasta is not None:
        bloqueado_hasta = as_utc(usuario.bloqueado_hasta)
        ahora = datetime.now(UTC)
        if bloqueado_hasta > ahora:
            restante = max(1, int((bloqueado_hasta - ahora).total_seconds()))
            raise CuentaBloqueadaError(
                "Cuenta bloqueada temporalmente por intentos fallidos",
                headers={"Retry-After": str(restante)},
            )


async def cambiar_clave(
    db: AsyncSession, *, principal: Principal, clave_actual: str, clave_nueva: str
) -> UsUsuario:
    """§2.6: cambia la clave y sube token_version; el access nuevo lo emite el router."""
    usuario = await db.get(UsUsuario, principal.sub)
    if usuario is None or not verify_password(usuario.password_hash, clave_actual):
        raise UnauthorizedError("La clave actual no es correcta", code="clave-invalida")
    usuario.password_hash = hash_password(clave_nueva)
    usuario.password_changed_at = datetime.now(UTC)
    usuario.token_version += 1
    await db.flush()
    return usuario


class CorreoRecuperacion(NamedTuple):
    """Email de recuperación listo para encolar (RB-25, lo encola el router)."""

    destinatario: str
    asunto: str
    cuerpo: str


_ASUNTO_RECUPERACION = "Restablecimiento de clave"


def _correo_recuperacion(
    *, destinatario: str, username: str, token: str
) -> CorreoRecuperacion:
    """Cuerpo del email: el token en claro viaja SÓLO por este correo (RB-25)."""
    horas = int(SOLICITUD_EXPIRA.total_seconds() // 3600)
    cuerpo = (
        f"Hola {username}:\n\n"
        "Recibimos un pedido para restablecer la clave de tu cuenta.\n\n"
        "Tu token de recuperación es:\n\n"
        f"    {token}\n\n"
        f"Vence en {horas} horas y solo puede usarse una vez. "
        "Ingrese el token en la app junto con su nueva clave.\n\n"
        "Si no pidió este cambio, ignore este mensaje: su clave no cambió.\n"
    )
    return CorreoRecuperacion(
        destinatario=destinatario, asunto=_ASUNTO_RECUPERACION, cuerpo=cuerpo
    )


async def solicitar_recuperacion(
    db: AsyncSession,
    *,
    identificador: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> CorreoRecuperacion | None:
    """Registra el pedido de blanqueo y devuelve el correo a encolar.

    El identificador coincide con username o email. La fila queda pendiente
    (usado_en IS NULL, expira_en vigente) en `us_password_reset` con el HASH
    SHA-256 de un token opaco: el token en claro jamás se persiste y sólo
    viaja por el correo devuelto, que el router encola DESPUÉS de responder
    (RN-051; decisión 2026-11-12: el usuario blanquea su clave él mismo
    verificando el correo, sin intervención del admin).

    Un reenvío regenera el token y invalida el del correo anterior (un solo
    pedido vigente por usuario). Si la cuenta no existe, o existe sin correo
    registrado, no hay correo que devolver: la respuesta del router a la
    red es idéntica en todos los casos (anti-enumeración). No hace commit.
    """
    now = datetime.now(UTC)
    usuario = await db.scalar(
        select(UsUsuario).where(
            or_(
                UsUsuario.username == identificador,
                func.lower(UsUsuario.email) == identificador.lower(),
            ),
            UsUsuario.deleted_at.is_(None),
        )
    )
    if usuario is None:
        return None

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    pendiente = await db.scalar(
        select(UsPasswordReset).where(
            UsPasswordReset.usuario_id == usuario.id,
            UsPasswordReset.usado_en.is_(None),
            UsPasswordReset.expira_en > now,
        )
    )
    if pendiente is not None:
        # Reenvío: se conserva UNA sola fila por usuario y el token nuevo
        # invalida al del correo anterior.
        pendiente.token_hash = token_hash
        pendiente.expira_en = now + SOLICITUD_EXPIRA
        pendiente.ip = ip
        pendiente.user_agent = user_agent
    else:
        db.add(
            UsPasswordReset(
                id=uuid.uuid4(),
                usuario_id=usuario.id,
                token_hash=token_hash,
                ip=ip,
                user_agent=user_agent,
                expira_en=now + SOLICITUD_EXPIRA,
                created_at=now,
            )
        )

    if not usuario.email:
        return None  # sin correo registrado no hay a quién enviarle el token
    return _correo_recuperacion(
        destinatario=usuario.email, username=usuario.username, token=token
    )


def _recuperacion_invalida() -> UnauthorizedError:
    return UnauthorizedError(
        "El token de recuperación no es válido o expiró",
        code="recuperacion-invalida",
    )


async def restablecer_clave(
    db: AsyncSession, *, token: str, clave_nueva: str
) -> UsUsuario:
    """Blanquea la clave con el token del correo (PD-04; §2.5 y §2.6).

    - El token se busca por su hash SHA-256: jamás se consulta en claro.
    - Debe estar sin usar (`usado_en IS NULL`) y vigente (`expira_en > now`);
      un token desconocido, vencido o ya consumido devuelve SIEMPRE el mismo
      error (no se revela cuál de los tres casos falló).
    - Al blanquear: sube `token_version` (invalida los access vigentes),
      revoca todas las sesiones (el blanqueo es autónomo: no hay sesión que
      preservar), limpia los intentos fallidos del rate limit (PD-27) y marca
      el token como usado (un solo uso). La suspensión (`bloqueado`) NO se
      toca: sólo un admin la levanta.
    No hace commit: el router persiste.
    """
    ahora = datetime.now(UTC)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    fila = await db.scalar(
        select(UsPasswordReset).where(
            UsPasswordReset.token_hash == token_hash,
            UsPasswordReset.usado_en.is_(None),
            UsPasswordReset.expira_en > ahora,
        )
    )
    if fila is None:
        raise _recuperacion_invalida()

    usuario = await db.get(UsUsuario, fila.usuario_id)
    if usuario is None or usuario.deleted_at is not None:
        raise _recuperacion_invalida()

    usuario.password_hash = hash_password(clave_nueva)
    usuario.password_changed_at = ahora
    usuario.token_version += 1
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    fila.usado_en = ahora
    await revoke_all_sessions(db, usuario_id=usuario.id)
    await db.flush()
    return usuario

