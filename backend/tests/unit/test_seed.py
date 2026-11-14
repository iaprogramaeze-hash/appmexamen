"""Seed base de seguridad: permisos, módulos, roles (matriz doc02 §2.4) y
condiciones (PD-02)."""
from __future__ import annotations

from sqlalchemy import func, select

from app.features.catalogo.models import EsCondicion
from app.features.catalogo.seed import seed_condiciones
from app.features.usuarios.models import UsModulo, UsPermiso, UsRol, UsRolPermiso
from app.features.usuarios.seed import (
    MODULOS,
    PERMISOS,
    ROLES,
    seed_modulos,
    seed_permisos,
    seed_roles,
)

#: §2.7 (líneas 163–166 de analisis.txt), verbatim.
_CODIGOS_287 = {
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
    "preinscripcion.crear",
    "preinscripcion.listar",
}


def test_permission_catalog_matches_analisis_verbatim():
    assert len(PERMISOS) == 13
    assert {codigo for codigo, _ in PERMISOS} == _CODIGOS_287


def test_module_catalog_matches_analisis_verbatim():
    assert {codigo for codigo, _ in MODULOS} == {"landing", "sigme_web", "sigme_mobile"}


async def test_seed_permisos_is_idempotent(db_session):
    assert await seed_permisos(db_session) == 13
    assert await db_session.scalar(select(func.count()).select_from(UsPermiso)) == 13
    assert await seed_permisos(db_session) == 0


async def test_seed_modulos_is_idempotent(db_session):
    assert await seed_modulos(db_session) == 3
    assert await db_session.scalar(select(func.count()).select_from(UsModulo)) == 3
    assert await seed_modulos(db_session) == 0


#: Matriz rol × permiso de analisis/02-actores-y-consumidores.md §2.4
#: (DEFINITIVA — fuente de la semilla, PD-03). Celda S = asigna;
#: — o PENDIENTE = NO asigna (denegar por defecto: un hueco nunca otorga).
_MATRIZ_24: dict[str, set[str]] = {
    "alumno": {
        "mesa.listar",
        "inscripcion.listar",
        "inscripcion.crear",
        "inscripcion.anular",
    },
    "secretario": {
        "mesa.listar",
        "mesa.crear",
        "mesa.modificar",
        "inscripcion.listar",
        "inscripcion.anular",
        "persona.listar",
        "persona.modificar",
        "reporte.exportar",
        "preinscripcion.listar",
    },
    "director": {
        "mesa.listar",
        "inscripcion.listar",
        "persona.listar",
        "reporte.exportar",
        "preinscripcion.listar",
    },
    "administrador": {
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
    },
    "superadmin": {
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
    },
}


def test_role_catalog_matches_matrix_24_verbatim():
    assert {codigo for codigo, _, _ in ROLES} == {
        "alumno",
        "secretario",
        "director",
        "administrador",
        "superadmin",
    }
    for codigo, _, permisos in ROLES:
        assert set(permisos) == _MATRIZ_24[codigo], f"reparto de {codigo} difiere de §2.4"


def test_preinscripcion_crear_belongs_to_nobody():
    # doc02 §2.4: "La landing escribe sin JWT (§2.9): el permiso no puede
    # aplicarse allí. Dueño dentro de SIGME no determinado — PENDIENTE (G-02)".
    for _, _, permisos in ROLES:
        assert "preinscripcion.crear" not in permisos


async def test_seed_roles_is_idempotent_and_assigns_matrix(db_session):
    assert await seed_roles(db_session) == 5
    assert await db_session.scalar(select(func.count()).select_from(UsRol)) == 5

    # Toda asignación debe reflejar exactamente la matriz §2.4.
    filas = await db_session.execute(
        select(UsRol.codigo, UsPermiso.codigo).join(
            UsRolPermiso, UsRolPermiso.rol_id == UsRol.id
        ).join(UsPermiso, UsPermiso.id == UsRolPermiso.permiso_id)
    )
    obtenidos: dict[str, set[str]] = {}
    for rol_codigo, permiso_codigo in filas:
        obtenidos.setdefault(rol_codigo, set()).add(permiso_codigo)
    assert obtenidos == _MATRIZ_24

    assert await seed_roles(db_session) == 0  # idempotente


async def test_seed_condiciones_is_idempotent(db_session):
    assert await seed_condiciones(db_session) == 3
    filas = {
        desc: limite
        for desc, limite in await db_session.execute(
            select(EsCondicion.descripcion, EsCondicion.limite_materias)
        )
    }
    # PD-02: "Previa 3, Regular 8, Libre NULL".
    assert filas == {"Previa": 3, "Regular": 8, "Libre": None}
    assert await seed_condiciones(db_session) == 0  # idempotente
