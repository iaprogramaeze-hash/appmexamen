"""Endpoints /api/v1/auth (analisis.txt 2.4 y §6; PD-24 y PD-27)."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import AppError, UnauthorizedError
from app.features.auth import service
from app.features.auth.dependencies import get_current_principal
from app.features.auth.errors import InvalidRefreshTokenError, RefreshReuseDetectedError
from app.features.auth.schemas import (
    AccessOnly,
    CambiarClaveRequest,
    LoginRequest,
    OlvidoClaveRequest,
    OlvidoClaveResponse,
    RefreshRequest,
    RestablecerClaveRequest,
    RestablecerClaveResponse,
    TokenPair,
    YoResponse,
)
from app.features.auth.sessions import revoke_all_sessions, revoke_session, rotate_session
from app.features.auth.tokens import Principal, issue_access_token
from app.features.notificaciones.service import encolar_y_entregar
from app.features.usuarios.models import UsUsuario

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenPair:
    """POST /auth/login -> access + refresh (analisis.txt 2.4)."""
    try:
        usuario, sid, refresh = await service.login(
            db,
            username=payload.username,
            password=payload.password,
            modulo=payload.modulo,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        access = await issue_access_token(
            db, usuario_id=usuario.id, sid=sid, token_version=usuario.token_version
        )
        await db.commit()
        return TokenPair(access=access, refresh=refresh)
    except AppError:
        # Los contadores de intentos y bloqueos persisten aunque la
        # respuesta sea un error (PD-27); el rollback nunca debe borrarlos.
        await db.commit()
        raise


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> TokenPair:
    """POST /auth/refresh rota el par (§2.2); reuse detection revoca la familia."""
    try:
        sesion, refresh_nuevo = await rotate_session(
            db,
            raw_refresh=payload.refresh,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except InvalidRefreshTokenError as exc:
        await db.commit()
        raise UnauthorizedError(
            "Refresh token inválido o expirado", code="refresh-invalido"
        ) from exc
    except RefreshReuseDetectedError as exc:
        await db.commit()  # la revocación de la familia debe persistir (§2.2)
        raise UnauthorizedError(
            "Refresh token ya usado: inicie sesión de nuevo", code="refresh-reutilizado"
        ) from exc

    usuario = await db.get(UsUsuario, sesion.usuario_id)
    if usuario is None or usuario.deleted_at is not None or not usuario.activo:
        await db.commit()
        raise UnauthorizedError("El token de acceso no es válido", code="token-invalido")
    # §2.6/PD-27: una cuenta suspendida o bloqueada no renueva su par; la
    # rotación sin commitear se descarta y el refresh sigue vigente.
    service.verificar_cuenta_operativa(usuario)
    access = await issue_access_token(
        db, usuario_id=usuario.id, sid=sesion.id, token_version=usuario.token_version
    )
    await db.commit()
    return TokenPair(access=access, refresh=refresh_nuevo)


@router.post("/logout", status_code=204)
async def logout(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    """POST /auth/logout revoca la sesión del token presentado (2.4)."""
    await revoke_session(db, sid=principal.sid)
    await db.commit()


@router.post("/logout-all", status_code=204)
async def logout_all(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    """POST /auth/logout-all revoca todas las sesiones del usuario (2.4)."""
    await revoke_all_sessions(db, usuario_id=principal.sub)
    await db.commit()


@router.get("/yo", response_model=YoResponse)
async def yo(
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> YoResponse:
    """GET /auth/yo: identidad desde los claims (§2.1: autorizar sin consulta)."""
    usuario = await db.get(UsUsuario, principal.sub)
    return YoResponse(
        id=str(principal.sub),
        username=usuario.username,
        roles=principal.roles,
        permisos=principal.permisos,
        modulos=principal.modulos,
    )


@router.post("/cambiar-clave", response_model=AccessOnly)
async def cambiar_clave(
    payload: CambiarClaveRequest,
    principal: Principal = Depends(get_current_principal),
    db: AsyncSession = Depends(get_db),
) -> AccessOnly:
    """POST /auth/cambiar-clave: sube token_version y devuelve access nuevo (§2.6)."""
    usuario = await service.cambiar_clave(
        db,
        principal=principal,
        clave_actual=payload.clave_actual,
        clave_nueva=payload.clave_nueva,
    )
    access = await issue_access_token(
        db, usuario_id=usuario.id, sid=principal.sid, token_version=usuario.token_version
    )
    await db.commit()
    return AccessOnly(access=access)


@router.post("/olvido-clave", response_model=OlvidoClaveResponse, status_code=202)
async def olvido_clave(
    payload: OlvidoClaveRequest,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> OlvidoClaveResponse:
    """POST /auth/olvido-clave: registra el pedido y encola el email (202 siempre).

    Flujo automático con verificación por correo (decisión 2026-11-12): el
    usuario recibe un token opaco en su correo y blanquea su propia clave con
    POST /auth/restablecer-clave. La respuesta es idéntica exista o no la
    cuenta (anti-enumeración); el email se encola DESPUÉS de responder
    (RN-051) y su fallo nunca afecta esta respuesta (NFR-034 / EX-21).
    """
    correo = await service.solicitar_recuperacion(
        db,
        identificador=payload.identificador,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    if correo is not None:
        background.add_task(
            encolar_y_entregar,
            destinatario=correo.destinatario,
            asunto=correo.asunto,
            cuerpo=correo.cuerpo,
        )
    return OlvidoClaveResponse(status="solicitado")


@router.post("/restablecer-clave", response_model=RestablecerClaveResponse)
async def restablecer_clave(
    payload: RestablecerClaveRequest, db: AsyncSession = Depends(get_db)
) -> RestablecerClaveResponse:
    """POST /auth/restablecer-clave: blanquea la clave con el token del correo.

    Token de un solo uso, vencimiento y hash SHA-256 en `us_password_reset`
    (PD-04); al blanquear sube token_version y revoca las sesiones (§2.6).
    El error es único para token desconocido, vencido o ya usado.
    """
    try:
        await service.restablecer_clave(
            db, token=payload.token, clave_nueva=payload.clave_nueva
        )
        await db.commit()
    except AppError:
        await db.commit()  # no hay mutaciones que conservar; cierra limpio
        raise
    return RestablecerClaveResponse(status="restablecida")
