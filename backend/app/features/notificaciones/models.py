"""Modelo de la cola de email: `ntf_envio` (analisis.txt §4, RB-25 / NFR-033).

Tabla espejo de la migración 0005. Sin updated_at: como `us_password_reset`,
el estado se escribe explícitamente desde el servicio; la cola no tiene
triggers de auditoría propios. El reintento programado queda fuera (contrato
de reintento ABIERTO, ver 0005): aquí sólo se registra estado y fallos.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

#: NFR-033: estado de cada envío en la cola.
ESTADO_PENDIENTE = "pendiente"
ESTADO_ENVIADO = "enviado"
ESTADO_FALLIDO = "fallido"


class NtfEnvio(Base):
    """Un email encolado: destinatario, asunto, cuerpo, estado y reintentos."""

    __tablename__ = "ntf_envio"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    destinatario: Mapped[str] = mapped_column(String(320))
    asunto: Mapped[str] = mapped_column(String(200))
    cuerpo: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ESTADO_PENDIENTE
    )
    reintentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(String(500))
