"""T3 - modelos §3.13-§3.22 + T6 (es_dispositivo): create_all, cobertura 26/26
y nombres del DDL."""
from __future__ import annotations

from sqlalchemy import create_engine

import app.features.catalogo.models  # noqa: F401 - registra las 4 tablas
import app.features.dispositivos.models  # noqa: F401 - registra es_dispositivo
import app.features.mesas.models  # noqa: F401 - registra las 4 tablas
import app.features.notificaciones.models  # noqa: F401 - registra ntf_envio
import app.features.preinscripcion.models  # noqa: F401 - registra las 2 tablas
from app.db.base import Base

ESPERADAS = {
    "es_orientacion",
    "es_curso",
    "es_materia",
    "es_condicion",
    "es_convocatoria",
    "es_mesa_examen",
    "es_mesa_inscripcion",
    "es_grupo_horario",
    "es_dispositivo",
    "pr_preinscripcion",
    "pr_ventana",
    "ntf_envio",
}


def test_create_all_sqlite_y_cobertura_total():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)  # no debe lanzar
    assert ESPERADAS <= set(Base.metadata.tables)
    # 22 del esquema inicial (T2 12 + T3 10) + us_password_reset y
    # aud_evento de la migración 0002 (PD-04/PD-05) + es_dispositivo (T6)
    # + ntf_envio de la migración 0005 (RB-25, cola de email).
    assert len(Base.metadata.tables) == 26


def test_unicos_con_nombre_exacto_del_ddl():
    def indices_unicos(tabla: str) -> set[str]:
        return {i.name for i in Base.metadata.tables[tabla].indexes if i.unique}

    assert "uq_mesa_unica" in indices_unicos("es_mesa_examen")
    assert "uq_inscripcion_unica" in indices_unicos("es_mesa_inscripcion")
    assert "uq_preinscripcion_unica" in indices_unicos("pr_preinscripcion")
    assert "uq_grupo_unico" in indices_unicos("es_grupo_horario")
    # uq_ventana_anio es UNIQUE CONSTRAINT (no índice) — §3.21.
    constraintes = {
        c.name
        for c in Base.metadata.tables["pr_ventana"].constraints
        if type(c).__name__ == "UniqueConstraint"
    }
    assert "uq_ventana_anio" in constraintes


def test_checks_con_nombre_exacto_del_ddl():
    def checks(tabla: str) -> set[str]:
        return {
            c.name
            for c in Base.metadata.tables[tabla].constraints
            if type(c).__name__ == "CheckConstraint"
        }

    assert "ck_convocatoria_ventana" in checks("es_convocatoria")
    assert "ck_ventana" in checks("pr_ventana")
    assert "ck_es_mesa_examen_estado" in checks("es_mesa_examen")


def test_preinscripcion_aislada_sin_fk():
    """§3.20: ninguna FK hacia pe_*/es_* — aislamiento explícito (PD-01)."""
    tabla = Base.metadata.tables["pr_preinscripcion"]
    referencias = {fk.column.table.name for col in tabla.columns for fk in col.foreign_keys}
    assert referencias == set()
