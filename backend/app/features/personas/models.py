"""Modelos del dominio personas: §3.1–§3.4 de analisis.txt.

Traducción fiel del DDL (columnas, tipos, FK, restricciones e índices con sus
nombres exactos). Los índices parciales declaran también `sqlite_where` para
que el create_all de los tests unitarios los emita igual que PostgreSQL.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
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


class PeDocumentoTipo(Base):
    """§3.1 — tipos de documento (DNI, LC, LE, Pasaporte)."""

    __tablename__ = "pe_documento_tipo"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    descripcion: Mapped[str] = mapped_column(String(50), unique=True)
    orden: Mapped[int | None] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    # updated_at lo refresca el trigger trg_set_updated_at (§1.6), no un DEFAULT.
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PePersona(Base):
    """§3.2 — persona compartida entre SIGME, SIGME-M y la landing.

    razon_social/fecha_nacimiento/sexo/direccion/nacionalidad quedaron
    nullable a propósito: [CORREGIDO] un esquema compartido no puede exigir
    datos que la landing nunca pide.
    """

    __tablename__ = "pe_persona"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    documento_tipo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pe_documento_tipo.id", ondelete="RESTRICT")
    )
    documento: Mapped[str] = mapped_column(String(20))
    apellido: Mapped[str] = mapped_column(String(100))
    nombre: Mapped[str] = mapped_column(String(100))
    razon_social: Mapped[str | None] = mapped_column(String(150))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))
    direccion: Mapped[str | None] = mapped_column(String(150))
    nacionalidad: Mapped[str] = mapped_column(String(50), server_default="Argentino")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "uq_persona_documento",
            "documento_tipo_id",
            "documento",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index("idx_persona_apellido_nombre", "apellido", "nombre"),
        Index(
            "idx_persona_activa",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )


class PeContactoTipo(Base):
    """§3.3 — tipos de contacto (Email, Teléfono, Celular)."""

    __tablename__ = "pe_contacto_tipo"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    descripcion: Mapped[str] = mapped_column(String(50), unique=True)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PeContacto(Base):
    """§3.4 — contactos concretos de una persona."""

    __tablename__ = "pe_contacto"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pe_persona.id", ondelete="CASCADE")
    )
    contacto_tipo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pe_contacto_tipo.id", ondelete="RESTRICT")
    )
    descripcion: Mapped[str] = mapped_column(String(150))  # valor concreto
    predeterminado: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "idx_contacto_persona",
            "persona_id",
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )
