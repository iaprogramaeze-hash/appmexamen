"""Servicio de usuarios (SDD-2 S5; CU-09).

Reglas:
- Alta sobre persona existente y no borrada (404 persona-no-encontrada).
- username único entre no borrados → 409 username-existente; email único
  (parcial, sólo si no nulo) → 409 email-existente (§3.5).
- password_hash con el mismo algoritmo que auth (§2.5); jamás se expone.
- Asignación de roles/módulos: fuera de alcance (A3, §6 no la declara).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.features.personas.models import PePersona
from app.features.usuarios.models import UsRol, UsUsuario, UsUsuarioRol
from app.features.usuarios.schemas import UsuarioCreate


async def crear_usuario(db: AsyncSession, payload: UsuarioCreate) -> UsUsuario:
    """Alta de usuario con validaciones §3.5 y hash §2.5."""
    persona = await db.get(PePersona, payload.persona_id)
    if persona is None or persona.deleted_at is not None:
        raise NotFoundError(
            "La persona referenciada no existe", code="persona-no-encontrada"
        )

    existe = await db.scalar(
        select(UsUsuario.id).where(
            UsUsuario.username == payload.username,
            UsUsuario.deleted_at.is_(None),
        )
    )
    if existe is not None:
        raise ConflictError(
            "Ya existe un usuario con ese username", code="username-existente"
        )

    if payload.email is not None:
        email_usado = await db.scalar(
            select(UsUsuario.id).where(
                UsUsuario.email == payload.email,
                UsUsuario.deleted_at.is_(None),
            )
        )
        if email_usado is not None:
            raise ConflictError(
                "Ya existe un usuario con ese email", code="email-existente"
            )

    momento = datetime.now(UTC)
    usuario = UsUsuario(
        id=uuid.uuid4(),
        persona_id=payload.persona_id,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        activo=True,
        bloqueado=False,
        intentos_fallidos=0,
        password_changed_at=momento,
        token_version=1,
        created_at=momento,
    )
    db.add(usuario)
    await db.flush()
    return usuario


async def listar_usuarios(db: AsyncSession) -> list[tuple[UsUsuario, list[str]]]:
    """Usuarios vigentes con sus roles por código (nunca password_hash)."""
    usuarios = list(
        await db.scalars(
            select(UsUsuario)
            .where(UsUsuario.deleted_at.is_(None))
            .order_by(UsUsuario.username)
        )
    )
    roles = await cargar_roles_por_usuario(db, [u.id for u in usuarios])
    return [(usuario, roles.get(usuario.id, [])) for usuario in usuarios]


async def cargar_roles_por_usuario(
    db: AsyncSession, usuario_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[str]]:
    """Mapa usuario_id → códigos de rol ordenados (§2.7)."""
    if not usuario_ids:
        return {}
    filas = await db.execute(
        select(UsUsuarioRol.usuario_id, UsRol.codigo)
        .join(UsRol, UsRol.id == UsUsuarioRol.rol_id)
        .where(UsUsuarioRol.usuario_id.in_(usuario_ids))
        .order_by(UsRol.codigo)
    )
    resultado: dict[uuid.UUID, list[str]] = {}
    for usuario_id, codigo in filas:
        resultado.setdefault(usuario_id, []).append(codigo)
    return resultado
