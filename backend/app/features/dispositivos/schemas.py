"""Schemas Pydantic de dispositivos (SDD-4 T6, S6)."""
from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlataformaDispositivo(enum.StrEnum):
    """Plataforma del dispositivo."""

    ios = "ios"
    android = "android"
    web = "web"


class DispositivoCrear(BaseModel):
    """POST /dispositivos: registra o actualiza (upsert por device_id)."""

    model_config = ConfigDict(extra="forbid")

    device_id: str
    plataforma: PlataformaDispositivo
    push_token: str | None = None


class DispositivoLectura(BaseModel):
    """Respuesta del dispositivo registrado."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: str
    plataforma: PlataformaDispositivo
    push_token: str | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime