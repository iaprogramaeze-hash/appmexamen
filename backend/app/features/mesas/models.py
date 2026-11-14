"""Modelos del dominio mesas de exámenes: §3.17, §3.18, §3.19 y §3.22.

FK hacia catálogo y usuarios en forma de string: §5 prohíbe que un dominio
importe a otro. `es_grupo_horario` (§3.22) se crea ANTES que `es_mesa_examen`
en la migración (el orden lo resuelve el grafo de FK).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Time,
    Uuid,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EsConvocatoria(Base):
    """§3.17 [CORREGIDO — reemplaza a es_apertura_inscripcion].

    PD-14 RESUELTO: la convocatoria NO declara fechas de exámenes — cada
    grupo declara su fecha y hora (RB-27) y la mesa copia ese par de su grupo
    (RB-29). La ventana de inscripción sólo depende de sus dos fechas.
    """

    __tablename__ = "es_convocatoria"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    descripcion: Mapped[str] = mapped_column(String(100))  # "1er Cuatrimestre 2026"
    fecha_inicio_inscripcion: Mapped[date] = mapped_column(Date)
    fecha_fin_inscripcion: Mapped[date] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "fecha_inicio_inscripcion <= fecha_fin_inscripcion",
            name="ck_convocatoria_ventana",
        ),
    )


class EsMesaExamen(Base):
    """§3.18 [CORREGIDO — snapshot con política explícita].

    fecha/hora son una COPIA SINCRONIZADA del grupo (RB-29). Los 4 `_nombre`
    son snapshot inmutable: política RB-11 — se recalculan SOLO al editar la
    asignación de la mesa (cambiar materia/condición), nunca por un renombre
    de la tabla origen.
    """

    __tablename__ = "es_mesa_examen"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    convocatoria_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_convocatoria.id", ondelete="RESTRICT")
    )
    condicion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_condicion.id", ondelete="RESTRICT")
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_materia.id", ondelete="RESTRICT")
    )
    grupo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_grupo_horario.id", ondelete="RESTRICT")
    )
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[time | None] = mapped_column(Time)  # copia del grupo (RB-29)
    estado: Mapped[str] = mapped_column(String(20), server_default="planificada")

    # SNAPSHOT (copia inmutable de la asignación) — RB-11.
    orientacion_nombre: Mapped[str] = mapped_column(
        String(150),
        comment="Snapshot al crear/editar la mesa. "
        "Inmutable ante renombres de es_orientacion.",
    )
    curso_nombre: Mapped[str] = mapped_column(
        String(100),
        comment="Snapshot al crear/editar la mesa. Inmutable ante renombres de es_curso.",
    )
    materia_nombre: Mapped[str] = mapped_column(
        String(150),
        comment="Snapshot al crear/editar la mesa. Inmutable ante renombres de es_materia.",
    )
    condicion_nombre: Mapped[str] = mapped_column(
        String(50),
        comment="Snapshot al crear/editar la mesa. Inmutable ante renombres de es_condicion.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # El DDL no nombra este CHECK -> §1.2 ck_{tabla}_{regla}.
        CheckConstraint(
            "estado IN ('planificada','cerrada','realizada')",
            name="ck_es_mesa_examen_estado",
        ),
        # PD-13 [CERRADO — 2026-10-06]: convocatoria_id incluida; `hora` NO
        # participa (RN-031, EX-18).
        Index(
            "uq_mesa_unica",
            "convocatoria_id",
            "materia_id",
            "condicion_id",
            "fecha",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index("idx_mesa_fecha", "fecha"),
        Index("idx_mesa_convocatoria", "convocatoria_id"),
        Index("idx_mesa_materia", "materia_id"),
    )


class EsMesaInscripcion(Base):
    """§3.19 [CORREGIDO — unicidad y trazabilidad].

    RB-08: la unicidad es por MATERIA × CONVOCATORIA (no por mesa); un
    registro 'anulado' no ocupa cupo, por eso el índice lo excluye. No hay
    estados de asistencia ni de resultado (RB-18, RB-21).
    """

    __tablename__ = "es_mesa_inscripcion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="RESTRICT")
    )
    mesa_examen_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_mesa_examen.id", ondelete="RESTRICT")
    )
    convocatoria_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_convocatoria.id", ondelete="RESTRICT")
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_materia.id", ondelete="RESTRICT")
    )
    condicion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_condicion.id", ondelete="RESTRICT")
    )
    estado: Mapped[str] = mapped_column(String(20), server_default="inscripto")
    inscripto_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "estado IN ('inscripto','anulado')",
            name="ck_es_mesa_inscripcion_estado",
        ),
        Index(
            "uq_inscripcion_unica",
            "convocatoria_id",
            "usuario_id",
            "materia_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND estado <> 'anulado'"),
            sqlite_where=text("deleted_at IS NULL AND estado <> 'anulado'"),
        ),
        Index("idx_inscripcion_usuario", "usuario_id"),
        Index("idx_inscripcion_mesa", "mesa_examen_id"),
        Index("idx_inscripcion_conv", "convocatoria_id"),
    )


class EsGrupoHorario(Base):
    """§3.22 [NUEVA — grupo de mesas: fecha + hora].

    RB-27: el grupo es SÓLO fecha + hora compartidas por todas sus mesas; no
    hay aula ni profesor (fuera de alcance, confirmado 2026-10-01). PD-16:
    misma convocatoria + fecha + hora = SIEMPRE el mismo bloque (uq_grupo_unico).
    PD-18: borrar un grupo es borrado lógico en cascada transaccional.
    """

    __tablename__ = "es_grupo_horario"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    convocatoria_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("es_convocatoria.id", ondelete="RESTRICT")
    )
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[time] = mapped_column(Time)
    nombre: Mapped[str | None] = mapped_column(String(100))  # "Mañana", "Tarde"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_grupo_convocatoria", "convocatoria_id"),
        Index(
            "idx_grupo_activa",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_grupo_unico",
            "convocatoria_id",
            "fecha",
            "hora",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )
