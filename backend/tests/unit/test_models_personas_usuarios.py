"""T2 — modelos §3.1–§3.12: create_all en SQLite y cobertura 12/12.

La suite no inserta filas: `now()`/`gen_random_uuid()` son defaults de
PostgreSQL (verificado empíricamente que SQLite los acepta en el DDL y sólo
los rechazaría al insertar).
"""
from __future__ import annotations

from sqlalchemy import create_engine

import app.features.personas.models  # noqa: F401 - registra las 4 tablas
import app.features.usuarios.models  # noqa: F401 - registra las 8 tablas
from app.db.base import Base

ESPERADAS = {
    "pe_documento_tipo",
    "pe_persona",
    "pe_contacto_tipo",
    "pe_contacto",
    "us_usuario",
    "us_rol",
    "us_permiso",
    "us_usuario_rol",
    "us_rol_permiso",
    "us_modulo",
    "us_usuario_modulo",
    "us_sesion",
}


def test_create_all_sqlite_sin_errores():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)  # no debe lanzar
    assert len(ESPERADAS) == 12
    assert ESPERADAS <= set(Base.metadata.tables)


def test_us_usuario_rol_pk_compuesta_sin_auditoria():
    tabla = Base.metadata.tables["us_usuario_rol"]
    assert [c.name for c in tabla.primary_key.columns] == ["usuario_id", "rol_id"]
    columnas = set(tabla.columns)
    assert not {"created_at", "updated_at", "deleted_at"} & columnas


def test_us_sesion_indice_compuesto_de_estado():
    nombres = {i.name for i in Base.metadata.tables["us_sesion"].indexes}
    assert {"idx_sesion_usuario", "idx_sesion_familia", "idx_sesion_expira"} <= nombres
    # §1.9: las intermedias no tienen auditoría; §3.12 sólo created_at.
    assert "updated_at" not in Base.metadata.tables["us_sesion"].columns
