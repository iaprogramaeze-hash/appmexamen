"""Seed base de seguridad: permisos (§2.7), módulos (§2.8) y roles (matriz
doc02 §2.4) de analisis.txt.

Idempotente por código: inserta sólo lo que falta. Los valores se escriben
explícitos (id, created_at) para no depender de server_default de Postgres.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.usuarios.models import UsModulo, UsPermiso, UsRol, UsRolPermiso

#: §2.7 (líneas 163–166), verbatim: los 13 códigos granulares de permiso.
PERMISOS: tuple[tuple[str, str], ...] = (
    ("mesa.listar", "Listar mesas de examen"),
    ("mesa.crear", "Crear mesas de examen"),
    ("mesa.modificar", "Modificar mesas de examen"),
    ("mesa.eliminar", "Eliminar mesas de examen"),
    ("inscripcion.listar", "Listar inscripciones"),
    ("inscripcion.crear", "Crear inscripciones"),
    ("inscripcion.anular", "Anular inscripciones"),
    ("persona.listar", "Listar personas"),
    ("persona.modificar", "Modificar personas"),
    ("usuario.gestionar", "Gestionar usuarios, roles y permisos"),
    ("reporte.exportar", "Exportar reportes"),
    ("preinscripcion.crear", "Crear preinscripciones"),
    ("preinscripcion.listar", "Listar preinscripciones"),
)

#: §2.8: us_modulo contiene 'landing', 'sigme_web' y 'sigme_mobile'.
MODULOS: tuple[tuple[str, str], ...] = (
    ("landing", "Landing pública de preinscripción"),
    ("sigme_web", "SIGME web"),
    ("sigme_mobile", "SIGME mobile"),
)

#: Matriz rol × permiso de analisis/02-actores-y-consumidores.md §2.4
#: (DEFINITIVA — fuente de la semilla, PD-03). Celda `S` = asigna el permiso;
#: celda `—` o `PENDIENTE` = NO asigna: un hueco de la matriz nunca otorga
#: ("no se resuelven por silencio ni por suposición", §2.4).
#: `preinscripcion.crear` no se asigna a ningún rol: la landing escribe sin
#: JWT y el dueño dentro de SIGME sigue PENDIENTE (G-02).
ROLES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "alumno",
        "Alumno (SIGME-M)",
        ("mesa.listar", "inscripcion.listar", "inscripcion.crear", "inscripcion.anular"),
    ),
    (
        "secretario",
        "Secretario/a",
        (
            "mesa.listar",
            "mesa.crear",
            "mesa.modificar",
            "inscripcion.listar",
            "inscripcion.anular",
            "persona.listar",
            "persona.modificar",
            "reporte.exportar",
            "preinscripcion.listar",
        ),
    ),
    (
        "director",
        "Director",
        (
            "mesa.listar",
            "inscripcion.listar",
            "persona.listar",
            "reporte.exportar",
            "preinscripcion.listar",
        ),
    ),
    (
        "administrador",
        "Administrador",
        (
            "mesa.listar",
            "mesa.crear",
            "mesa.modificar",
            "mesa.eliminar",
            "inscripcion.listar",
            "inscripcion.crear",
            "inscripcion.anular",
            "persona.listar",
            "persona.modificar",
            "usuario.gestionar",
            "reporte.exportar",
            "preinscripcion.listar",
        ),
    ),
    (
        "superadmin",
        "Superadmin",
        (
            "mesa.listar",
            "mesa.crear",
            "mesa.modificar",
            "mesa.eliminar",
            "inscripcion.listar",
            "inscripcion.crear",
            "inscripcion.anular",
            "persona.listar",
            "persona.modificar",
            "usuario.gestionar",
            "reporte.exportar",
            "preinscripcion.listar",
        ),
    ),
)


async def seed_permisos(db: AsyncSession) -> int:
    """Crea los permisos faltantes; devuelve cuántos insertó (0 si ya estaban)."""
    existing = set(await db.scalars(select(UsPermiso.codigo)))
    moment = datetime.now(UTC)
    created = 0
    for codigo, descripcion in PERMISOS:
        if codigo in existing:
            continue
        db.add(
            UsPermiso(
                id=uuid.uuid4(),
                codigo=codigo,
                descripcion=descripcion,
                created_at=moment,
            )
        )
        created += 1
    await db.flush()
    return created


async def seed_modulos(db: AsyncSession) -> int:
    """Crea los módulos faltantes; devuelve cuántos insertó (0 si ya estaban)."""
    existing = set(await db.scalars(select(UsModulo.codigo)))
    moment = datetime.now(UTC)
    created = 0
    for codigo, descripcion in MODULOS:
        if codigo in existing:
            continue
        db.add(
            UsModulo(
                id=uuid.uuid4(),
                codigo=codigo,
                descripcion=descripcion,
                activo=True,
                created_at=moment,
            )
        )
        created += 1
    await db.flush()
    return created


async def seed_roles(db: AsyncSession) -> int:
    """Crea roles faltantes y su asignación de permisos según la matriz §2.4.

    Garantiza primero los permisos (los referencia por código). Devuelve
    cuántos roles insertó; la asignación permiso-rol se completa también para
    roles que ya existían pero estaban sin permisos (idempotente por par).
    """
    await seed_permisos(db)

    permiso_id_por_codigo = dict(
        (await db.execute(select(UsPermiso.codigo, UsPermiso.id))).all()
    )
    momento = datetime.now(UTC)

    existing_rol_ids = dict(
        (await db.execute(select(UsRol.codigo, UsRol.id))).all()
    )
    created = 0
    rol_id_por_codigo: dict[str, uuid.UUID] = dict(existing_rol_ids)
    for codigo, descripcion, _ in ROLES:
        if codigo in existing_rol_ids:
            continue
        rol_id = uuid.uuid4()
        rol_id_por_codigo[codigo] = rol_id
        db.add(
            UsRol(
                id=rol_id,
                codigo=codigo,
                descripcion=descripcion,
                activo=True,
                created_at=momento,
            )
        )
        created += 1
    await db.flush()

    # Asignación rol × permiso, idempotente por par (rol_id, permiso_id).
    pares_existentes = set(
        await db.execute(select(UsRolPermiso.rol_id, UsRolPermiso.permiso_id))
    )
    for codigo, _, permisos in ROLES:
        rol_id = rol_id_por_codigo[codigo]
        for permiso_codigo in permisos:
            par = (rol_id, permiso_id_por_codigo[permiso_codigo])
            if par in pares_existentes:
                continue
            db.add(
                UsRolPermiso(
                    rol_id=rol_id, permiso_id=permiso_id_por_codigo[permiso_codigo]
                )
            )
    await db.flush()
    return created
