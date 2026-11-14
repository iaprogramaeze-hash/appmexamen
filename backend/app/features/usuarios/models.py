"""Modelos del dominio usuarios/seguridad: §3.5–§3.12 de analisis.txt.

FK hacia otros dominios (pe_persona) en forma de string: §5 prohíbe que un
dominio importe a otro. Las tablas intermedias (§1.9) llevan PK compuesta y
NO llevan columnas de auditoría.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    false,
    text,
    true,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsUsuario(Base):
    """§3.5 — usuarios autenticables (Argon2id en password_hash).

    [CORREGIDO] password -> password_hash; email, controles de bloqueo,
    password_changed_at y token_version (claim "ver") agregados. La columna
    ultimo_ingreso no lleva DEFAULT: se escribe al autenticar.
    """

    __tablename__ = "us_usuario"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pe_persona.id", ondelete="RESTRICT")
    )
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(Text)  # Argon2id, jamás texto plano
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    bloqueado: Mapped[bool] = mapped_column(Boolean, server_default=false())
    intentos_fallidos: Mapped[int] = mapped_column(Integer, server_default="0")
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_ingreso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    token_version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "uq_usuario_username",
            "username",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_usuario_email",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND email IS NOT NULL"),
            sqlite_where=text("deleted_at IS NULL AND email IS NOT NULL"),
        ),
        Index("idx_usuario_persona", "persona_id"),
    )


class UsRol(Base):
    """§3.6 — roles (admin, docente, alumno)."""

    __tablename__ = "us_rol"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsPermiso(Base):
    """§3.7 — permisos granulares (mesa.crear, reporte.exportar)."""

    __tablename__ = "us_permiso"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsUsuarioRol(Base):
    """§3.8 [CORREGIDO — PK compuesta] usuario ⇄ rol, sin auditoría (§1.9)."""

    __tablename__ = "us_usuario_rol"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="CASCADE"), primary_key=True
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_rol.id", ondelete="CASCADE"), primary_key=True
    )


class UsRolPermiso(Base):
    """§3.9 [CORREGIDO — PK compuesta] rol ⇄ permiso, sin auditoría (§1.9)."""

    __tablename__ = "us_rol_permiso"

    rol_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_rol.id", ondelete="CASCADE"), primary_key=True
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_permiso.id", ondelete="CASCADE"), primary_key=True
    )


class UsModulo(Base):
    """§3.10 — módulos por app (landing, sigme_web, sigme_mobile)."""

    __tablename__ = "us_modulo"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    descripcion: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsUsuarioModulo(Base):
    """§3.11 [CORREGIDO — PK compuesta] usuario ⇄ módulo, sin auditoría (§1.9)."""

    __tablename__ = "us_usuario_modulo"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="CASCADE"), primary_key=True
    )
    modulo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_modulo.id", ondelete="CASCADE"), primary_key=True
    )


class UsSesion(Base):
    """§3.12 [CORREGIDO — hash, familia y estado] sesiones de refresh.

    [CORREGIDO] jamás se persiste el token tal cual circula por la red: sólo
    su hash SHA-256 hex. Una sesión cambia de estado, no se borra, por eso no
    tiene updated_at ni deleted_at.
    """

    __tablename__ = "us_sesion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )  # sid
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="CASCADE")
    )
    modulo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_modulo.id", ondelete="RESTRICT")
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    familia_id: Mapped[uuid.UUID] = mapped_column(Uuid)  # para reuse detection
    estado: Mapped[str] = mapped_column(String(12), server_default="activo")
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip: Mapped[str | None] = mapped_column(
        String(45).with_variant(postgresql.INET(), "postgresql")
    )
    user_agent: Mapped[str | None] = mapped_column(String(300))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (
        # §1.2: el DDL no lo nombra -> ck_{tabla}_{regla} en el nombre explícito.
        CheckConstraint("estado IN ('activo','revocado')", name="ck_us_sesion_estado_valido"),
        Index("idx_sesion_usuario", "usuario_id", "estado"),
        Index("idx_sesion_familia", "familia_id"),
        Index("idx_sesion_expira", "expires_at"),
    )


class UsPasswordReset(Base):
    """PD-04 [CERRADO 2026-10-06] — tokens de restablecimiento de clave.

    Sólo se persiste el hash SHA-256 del token opaco: el token en claro viaja
    únicamente por la cola de email (RB-25), jamás se guarda. Un token se
    consume una única vez (usado_en) y expira (expira_en); por eso no tiene
    updated_at ni deleted_at (mismo criterio que UsSesion).
    """

    __tablename__ = "us_password_reset"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("us_usuario.id", ondelete="CASCADE")
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True
    )  # SHA-256 hex, NUNCA crudo
    ip: Mapped[str | None] = mapped_column(
        String(45).with_variant(postgresql.INET(), "postgresql")
    )
    user_agent: Mapped[str | None] = mapped_column(String(300))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    __table_args__ = (Index("idx_us_password_reset_usuario_id", "usuario_id"),)
