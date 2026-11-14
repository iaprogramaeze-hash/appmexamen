"""Regression: named table constraints in raw DDL must use the CONSTRAINT keyword.

Postgres rejects a bare ``ck_nombre CHECK (...)`` at table level: it parses the
name as a column and fails with ``syntax error at or near "CHECK"``. SQLite
silently accepts the same text as a typeless column, and offline
``alembic upgrade head --sql`` only prints SQL without parsing it, so neither
pytest-green nor the offline dump catches the defect — only executing the
migration against real Postgres does.

This lints both executable artifacts that carry the raw DDL:

- every file in ``alembic/versions/`` — the migrations that run against
  Postgres (linted as a set so a new revision inherits the same rules).
- ``analisis.txt`` — the source of truth future migrations are generated from.
"""

from __future__ import annotations

import re
from pathlib import Path

BARE_NAMED_TABLE_CONSTRAINT = re.compile(
    r"^\s+\w+\s+(?:CHECK|UNIQUE|PRIMARY KEY|FOREIGN KEY|EXCLUDE)\s*\(",
)

_ROOT = Path(__file__).resolve().parents[2]

#: Cada revisión nueva queda cubierta sin tocar este archivo.
_MIGRATIONS = tuple(
    sorted(
        f"alembic/versions/{path.name}"
        for path in (_ROOT / "alembic" / "versions").glob("*.py")
        if not path.name.startswith("_")
    )
)


def _defect_lines(relative_path: str) -> list[str]:
    path = _ROOT / relative_path
    hits = []
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if BARE_NAMED_TABLE_CONSTRAINT.match(line):
            hits.append(f"{relative_path}:{number}: {line.strip()}")
    return hits


def test_migration_named_table_constraints_use_constraint_keyword() -> None:
    defects = [
        defect
        for migration in _MIGRATIONS
        for defect in _defect_lines(migration)
    ]
    assert not defects, (
        "Table-level constraints with a name need the CONSTRAINT keyword:\n"
        + "\n".join(defects)
    )


def test_analysis_ddl_named_table_constraints_use_constraint_keyword() -> None:
    defects = _defect_lines("analisis.txt")
    assert not defects, (
        "Table-level constraints with a name need the CONSTRAINT keyword:\n"
        + "\n".join(defects)
    )


def _unnamed_unique_lines(relative_path: str) -> list[str]:
    """Inline ``NOT NULL UNIQUE`` shorthand makes Postgres autoname
    ``<tabla>_<col>_key``, while the SQLAlchemy models declare
    ``uq_<tabla>_<col>`` (§1.2 convention). Same logical constraint, different
    name → ``alembic check`` never converges. Prose, headings and comment-only
    lines mentioning UNIQUE are not column definitions and are skipped."""
    hits = []
    for number, line in enumerate(
        (_ROOT / relative_path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        if "NOT NULL UNIQUE" not in line:
            continue
        if "CONSTRAINT uq_" in line:
            continue
        hits.append(f"{relative_path}:{number}: {stripped}")
    return hits


def test_migration_unique_constraints_declare_explicit_uq_names() -> None:
    defects = [
        defect
        for migration in _MIGRATIONS
        for defect in _unnamed_unique_lines(migration)
    ]
    assert not defects, (
        "Unique constraints must be named uq_<tabla>_<columna>:\n"
        + "\n".join(defects)
    )


#: 0003 siembra roles/permisos (PD-03) y condiciones (PD-02) para prod.
_MIGRATION_0003 = _ROOT / "alembic" / "versions" / "0003_seed_roles_condiciones.py"


def _load_migration_0003():
    """Importa la revisión 0003 por ruta (el nombre de archivo no es
    identificador Python)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("mig_0003", _MIGRATION_0003)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_0003_seed_data_is_present_and_idempotent() -> None:
    text = _MIGRATION_0003.read_text(encoding="utf-8")
    # Encadenamiento de revisión.
    assert 'revision = "0003"' in text
    assert 'down_revision = "0002"' in text
    # Idempotencia: toda la data entra con ON CONFLICT DO NOTHING.
    assert "ON CONFLICT DO NOTHING" in text
    # La migración no importa código de app/ (data inline, PD-03).
    assert "from app" not in text


def test_migration_0003_matrix_equals_seed_matrix() -> None:
    """La migración debe transportar EXACTAMENTE la matriz del seed."""
    from app.features.catalogo.seed import CONDICIONES
    from app.features.usuarios.seed import ROLES

    mig = _load_migration_0003()

    # Roles: mismos códigos que el seed.
    assert {codigo for codigo, _ in mig._ROLES} == {
        codigo for codigo, _, _ in ROLES
    }

    # Matriz: mismos pares (rol, permiso) que el seed, ni más ni menos.
    matriz_seed = {
        (codigo, permiso)
        for codigo, _, permisos in ROLES
        for permiso in permisos
    }
    assert set(mig._MATRIZ) == matriz_seed
    # Sin duplicados (cada par asignado una sola vez).
    assert len(mig._MATRIZ) == len(matriz_seed)

    # Condiciones: mismo (descripcion, limite_materias) que el seed PD-02.
    assert mig._CONDICIONES == CONDICIONES


def test_analysis_unique_constraints_declare_explicit_uq_names() -> None:
    defects = _unnamed_unique_lines("analisis.txt")
    assert not defects, (
        "Unique constraints must be named uq_<tabla>_<columna>:\n"
        + "\n".join(defects)
    )
