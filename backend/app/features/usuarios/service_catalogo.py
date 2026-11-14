"""Servicio de roles, permisos y módulos (SDD-2 S6; CU-10).

Catálogo cerrado: GET lista todo; POST crea por {codigo, descripcion} con
codigo único → 409 codigo-existente. La asignación permiso-rol vive en la
semilla (S1/T1), no se modifica por API (§6 no la declara).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.features.usuarios.models import UsModulo, UsPermiso, UsRol, UsRolPermiso
from app.features.usuarios.schemas_catalogo import CatalogoCreate


async def listar_roles(db: AsyncSession) -> list[tuple[UsRol, list[str]]]:
    """Roles vigentes con sus permisos por código ordenados."""
    roles = list(
        await db.scalars(
            select(UsRol).where(UsRol.deleted_at.is_(None)).order_by(UsRol.codigo)
        )
    )
    if not roles:
        return []
    filas = await db.execute(
        select(UsRolPermiso.rol_id, UsPermiso.codigo)
        .join(UsPermiso, UsPermiso.id == UsRolPermiso.permiso_id)
        .where(UsRolPermiso.rol_id.in_([r.id for r in roles]))
        .order_by(UsPermiso.codigo)
    )
    permisos: dict[uuid.UUID, list[str]] = {}
    for rol_id, codigo in filas:
        permisos.setdefault(rol_id, []).append(codigo)
    return [(rol, permisos.get(rol.id, [])) for rol in roles]


async def crear_rol(db: AsyncSession, payload: CatalogoCreate) -> UsRol:
    """Alta de rol; codigo único → 409 codigo-existente (§3.6)."""
    existe = await db.scalar(select(UsRol.id).where(UsRol.codigo == payload.codigo))
    if existe is not None:
        raise ConflictError(
            "Ya existe un rol con ese código", code="codigo-existente"
        )
    rol = UsRol(
        id=uuid.uuid4(),
        codigo=payload.codigo,
        descripcion=payload.descripcion,
        activo=True,
        created_at=datetime.now(UTC),
    )
    db.add(rol)
    await db.flush()
    return rol


async def listar_permisos(db: AsyncSession) -> list[UsPermiso]:
    """Catálogo cerrado de 13 permisos (§2.7), orden por código."""
    return list(
        await db.scalars(select(UsPermiso).order_by(UsPermiso.codigo))
    )


async def crear_permiso(db: AsyncSession, payload: CatalogoCreate) -> UsPermiso:
    """Alta de permiso; codigo único → 409 codigo-existente (§3.7)."""
    existe = await db.scalar(
        select(UsPermiso.id).where(UsPermiso.codigo == payload.codigo)
    )
    if existe is not None:
        raise ConflictError(
            "Ya existe un permiso con ese código", code="codigo-existente"
        )
    permiso = UsPermiso(
        id=uuid.uuid4(),
        codigo=payload.codigo,
        descripcion=payload.descripcion,
        created_at=datetime.now(UTC),
    )
    db.add(permiso)
    await db.flush()
    return permiso


async def listar_modulos(db: AsyncSession) -> list[UsModulo]:
    """Catálogo de 3 módulos (§2.8)."""
    return list(
        await db.scalars(select(UsModulo).order_by(UsModulo.codigo))
    )


async def crear_modulo(db: AsyncSession, payload: CatalogoCreate) -> UsModulo:
    """Alta de módulo; codigo único → 409 codigo-existente (§3.10)."""
    existe = await db.scalar(
        select(UsModulo.id).where(UsModulo.codigo == payload.codigo)
    )
    if existe is not None:
        raise ConflictError(
            "Ya existe un módulo con ese código", code="codigo-existente"
        )
    modulo = UsModulo(
        id=uuid.uuid4(),
        codigo=payload.codigo,
        descripcion=payload.descripcion,
        activo=True,
        created_at=datetime.now(UTC),
    )
    db.add(modulo)
    await db.flush()
    return modulo
