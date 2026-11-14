"""Modelos del dominio preinscripción (landing): §3.20 y §3.21.

Tabla AJENA al cuerpo principal del sistema [PD-01 CERRADO]: anotarse a la
escuela para el PRÓXIMO AÑO LECTIVO, sin conexión con mesas ni con pe_*/es_*
— NO hay foreign keys hacia ningún otro dominio (aislamiento por decisión
explícita del usuario). Usa la misma base sólo por practicidad.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    text,
    true,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrPreinscripcion(Base):
    """§3.20 [PAYLOAD CONFIRMADO — PD-01 CERRADO].

    CLIENTE = los 6 campos exactos del POST (todos obligatorios, O-2);
    SERVIDOR = lo que completa el backend (anio_lectivo desde la ventana
    vigente, ip, user_agent, utm_*). O-1: NO existe columna de
    consentimiento — el consentimiento real se recoge en papel, fuera del
    sistema. O-4: reenviar el formulario no es error; es un UPSERT sobre la
    identidad (anio_lectivo, documento).
    """

    __tablename__ = "pr_preinscripcion"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ===== CLIENTE — payload exacto del POST /landing/preinscripcion =====
    nombre_alumno: Mapped[str] = mapped_column(String(150))  # nombre completo
    documento: Mapped[str] = mapped_column(String(20))  # sin tipo: se asume DNI
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    orientacion: Mapped[str] = mapped_column(String(150))  # texto, NO fk (aislamiento)
    nombre_tutor: Mapped[str] = mapped_column(String(150))  # O-2: todos obligatorios
    email: Mapped[str] = mapped_column(String(150))

    # ===== SERVIDOR — no viene en el body =====
    anio_lectivo: Mapped[int] = mapped_column(Integer)  # de configuración, no enviado
    ip: Mapped[str | None] = mapped_column(
        String(45).with_variant(postgresql.INET(), "postgresql")
    )
    user_agent: Mapped[str | None] = mapped_column(String(300))
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(20), server_default="pendiente")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente','convertido','descartado')",
            name="ck_pr_preinscripcion_estado",
        ),
        # Identidad = (anio_lectivo, documento); un documento en otro año es
        # OTRA preinscripción (no pisa la anterior).
        Index(
            "uq_preinscripcion_unica",
            "anio_lectivo",
            "documento",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index("idx_preinscripcion_estado", "estado"),
        Index("idx_preinscripcion_fecha", "created_at"),
    )


class PrVentana(Base):
    """§3.21 [NUEVA — ventana de preinscripción].

    Motivo del usuario: "para que no estén jugando con el formulario todo el
    año". Sólo UNA ventana vigente a la vez (activa, sin deleted_at, rango
    que contiene hoy); fuera de ella el POST responde 409 ventana-cerrada.
    Se gestiona desde SIGME, nunca desde la landing anónima.
    """

    __tablename__ = "pr_ventana"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    anio_lectivo: Mapped[int] = mapped_column(Integer)  # año al que se preinscribe
    descripcion: Mapped[str] = mapped_column(String(100))  # "Preinscripción 2027"
    fecha_desde: Mapped[date] = mapped_column(Date)  # inclusive
    fecha_hasta: Mapped[date] = mapped_column(Date)  # inclusive
    activa: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # Nombres de constraint tal como los trae §3.21 (passthrough de base.py).
        CheckConstraint("fecha_desde <= fecha_hasta", name="ck_ventana"),
        UniqueConstraint("anio_lectivo", name="uq_ventana_anio"),
    )
