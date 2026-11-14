"""Bitácora de auditoría (analisis.txt PD-05): aud_evento, append-only.

PD-05 [CERRADO 2026-10-06]: SÍ desde v1. ALCANCE: escrituras exitosas de
cualquier usuario, intentos denegados (401/403) y descargas o impresiones de
reportes. Se EXCLUYEN las lecturas corrientes: un GET masivo no aporta quién
hizo qué y sólo llena la tabla.

La tabla es inmutable: sin updated_at ni deleted_at y con trigger en Postgres
que bloquea UPDATE/DELETE (migración 0002). El snapshot JSONB no puede contener
password_hash, refresh tokens ni hashes de sesión — regla de quien escribe el
evento; su validación vive en el servicio de auditoría (SDD aparte).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AudEvento(Base):
    """PD-05 — un evento por acción relevante del alcance.

    username y modulo se denormalizan para que el evento sobreviva a cambios
    o borrado lógico del actor. usuario_id es NULL en intentos anónimos
    (login con usuario inexistente); FK ON DELETE RESTRICT porque la bitácora
    es inmutable y no admite que un borrado físico la reescriba.
    """

    __tablename__ = "aud_evento"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="RESTRICT")
    )
    username: Mapped[str | None] = mapped_column(String(50))
    modulo: Mapped[str | None] = mapped_column(String(30))
    accion: Mapped[str] = mapped_column(String(60))  # kebab-case, convención PD-24
    entidad: Mapped[str] = mapped_column(String(100))  # tabla o recurso afectado
    entidad_id: Mapped[str | None] = mapped_column(String(36))
    resultado: Mapped[str] = mapped_column(String(20))
    ip: Mapped[str | None] = mapped_column(
        String(45).with_variant(postgresql.INET(), "postgresql")
    )
    user_agent: Mapped[str | None] = mapped_column(String(300))
    snapshot: Mapped[dict | None] = mapped_column(
        JSON().with_variant(postgresql.JSONB(), "postgresql")
    )

    __table_args__ = (
        # PD-05: el resultado sólo admite los dos estados del alcance.
        CheckConstraint(
            "resultado IN ('ok','denegado')", name="ck_aud_evento_resultado"
        ),
        Index("idx_aud_evento_created_at", "created_at"),
        Index("idx_aud_evento_usuario_id", "usuario_id"),
        Index("idx_aud_evento_accion", "accion"),
        Index("idx_aud_evento_entidad", "entidad", "entidad_id"),
    )
