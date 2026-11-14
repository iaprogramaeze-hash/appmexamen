"""Modelos del dominio catálogo escolar: §3.13–§3.16 de analisis.txt.

Tablas de referencia compartidas por mesas e inscripciones. Traducción fiel
del DDL; los índices conservan los nombres exactos de §3.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EsOrientacion(Base):
    """§3.13 — orientaciones (Tec. Gestión y Administración, Tec. Alimentos)."""

    __tablename__ = "es_orientacion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    descripcion: Mapped[str] = mapped_column(String(150), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EsCurso(Base):
    """§3.14 — AÑO dentro de la orientación.

    [RB-15] NO existe división de curso (A, B, D, G...) ni turno: todas las
    divisiones y turnos comparten las mismas materias, así que `anio`
    identifica únicamente el año dentro de la orientación.
    """

    __tablename__ = "es_curso"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    orientacion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_orientacion.id", ondelete="RESTRICT")
    )
    descripcion: Mapped[str] = mapped_column(String(100))  # "1er Año", "2do Año"...
    anio: Mapped[int | None] = mapped_column(Integer)  # 1, 2, 3 (sin letra)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("idx_curso_orientacion", "orientacion_id"),)


class EsMateria(Base):
    """§3.15 — materias.

    [DECISIÓN DEL USUARIO] Los talleres NO son entidad aparte: se cargan como
    materia normal con `es_taller = true`; el sistema no distingue su
    comportamiento.
    """

    __tablename__ = "es_materia"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    curso_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_curso.id", ondelete="RESTRICT")
    )
    codigo: Mapped[str | None] = mapped_column(String(20))
    descripcion: Mapped[str] = mapped_column(String(150))
    es_taller: Mapped[bool] = mapped_column(Boolean, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("idx_materia_curso", "curso_id"),)


class EsCondicion(Base):
    """§3.16 [CORREGIDO — agrega límite diferido] condiciones de rendición.

    [DECISIÓN DEL USUARIO] `limite_materias` queda previsto pero inactivo
    hasta definirlo (Previa = 3, Regular = 8); mientras sea NULL no se valida
    nada.
    """

    __tablename__ = "es_condicion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    descripcion: Mapped[str] = mapped_column(String(50), unique=True)
    limite_materias: Mapped[int | None] = mapped_column(Integer)  # NULL = sin límite
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
