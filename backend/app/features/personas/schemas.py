"""Schemas Pydantic de personas (SDD-2 S4; §3.2 y CU-07/CU-08)."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PersonaCreate(BaseModel):
    """POST /sigme/personas: datos de alta (§3.2)."""

    documento_tipo_id: uuid.UUID
    documento: str = Field(min_length=1, max_length=20)
    apellido: str = Field(min_length=1, max_length=100)
    nombre: str = Field(min_length=1, max_length=100)
    razon_social: str | None = Field(default=None, max_length=150)
    fecha_nacimiento: date | None = None
    sexo: str | None = Field(default=None, max_length=1)
    direccion: str | None = Field(default=None, max_length=150)
    nacionalidad: str = Field(default="Argentino", max_length=50)


class PersonaUpdate(BaseModel):
    """PATCH /sigme/personas/{id}: campos mutables (A2: sin identidad).

    documento_tipo_id y documento no viajan en el modelo: la identidad es
    inmutable en v1, el modelo simplemente no los acepta.
    """

    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    razon_social: str | None = Field(default=None, max_length=150)
    fecha_nacimiento: date | None = None
    sexo: str | None = Field(default=None, max_length=1)
    direccion: str | None = Field(default=None, max_length=150)
    nacionalidad: str | None = Field(default=None, max_length=50)


class PersonaResponse(BaseModel):
    """Salida estándar de persona; nunca password_hash ni datos de sesión."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    documento_tipo_id: uuid.UUID
    documento: str
    apellido: str
    nombre: str
    razon_social: str | None = None
    fecha_nacimiento: date | None = None
    sexo: str | None = None
    direccion: str | None = None
    nacionalidad: str
