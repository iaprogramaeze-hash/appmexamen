"""Esquemas Pydantic de preinscripción (landing pública, sin autenticación).

Los 6 campos del cliente coinciden con §3.20: todos obligatorios (O-2) y
sin mesa_id — la preinscripción es una anotación a la escuela, ajena a
las mesas de examen (PD-01).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PreInscripcionCreate(BaseModel):
    """Payload exacto que envía el formulario de la landing."""

    nombre_alumno: str = Field(min_length=1, max_length=150)
    documento: str = Field(min_length=1, max_length=20)
    fecha_nacimiento: date
    orientacion: str = Field(max_length=150)
    nombre_tutor: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PreInscripcionRead(BaseModel):
    """Respuesta con la fila persistida (campos de servidor incluidos)."""

    id: uuid.UUID
    nombre_alumno: str
    documento: str
    fecha_nacimiento: date
    orientacion: str
    nombre_tutor: str
    email: str
    anio_lectivo: int
    ip: str | None = None
    user_agent: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    estado: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreInscripcionAccion(BaseModel):
    """Respuesta del upsert de la landing (§6; doc 11 §11.4.3).

    El cuerpo del 201/200 es SOLO { accion }, no la fila completa.
    """

    accion: Literal["creada", "actualizada"]
