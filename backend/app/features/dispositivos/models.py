"""Modelo de dispositivo para push notifications (SDD-4 T6, S6).

Tabla `es_dispositivo`: un usuario puede tener varios dispositivos registrados.
Upsert por `(usuario_id, device_id)` — el mismo device_id no se duplica para
el mismo usuario. Soft delete (`deleted_at`) y campo `activo` para baja lógica.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlataformaDispositivo(enum.StrEnum):
    """Plataforma del dispositivo."""

    ios = "ios"
    android = "android"
    web = "web"


class EsDispositivo(Base):
    """Dispositivo registrado para notificaciones push (SDD-4 T6)."""

    __tablename__ = "es_dispositivo"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # token FCM/APNS/web push
    plataforma: Mapped[PlataformaDispositivo] = mapped_column(
        Enum(PlataformaDispositivo, name="plataforma_dispositivo",
             create_constraint=True, validate_strings=True),
        nullable=False,
    )
    push_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    activo: Mapped[bool] = mapped_column(
        default=True, server_default=text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # Unicidad por usuario + device_id (upsert idempotente)
        Index("uq_dispositivo_usuario_device", "usuario_id", "device_id",
              unique=True, postgresql_where=text("deleted_at IS NULL")),
    )