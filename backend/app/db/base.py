"""Base declarativa y convención de nombres (analisis.txt 1.2 y 5, db/base.py)."""
from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

#: analisis.txt 1.2: índices idx_{tabla}_{columnas}, únicos uq_{tabla}_{columnas},
#: FK fk_{tabla}_{columna}_{tabla_referida}. Los CHECK son pass-through: §3 es
#: la fuente de verdad y sus nombres (ck_convocatoria_ventana, ck_ventana) se
#: conservan tal cual; el patrón ck_{tabla}_{regla} de §1.2 se aplica al ELEGIR
#: el nombre explícito cuando el DDL no lo trae.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Todas las tablas heredan de acá; Alembic genera a partir de este metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
