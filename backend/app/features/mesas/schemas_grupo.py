"""Schemas Pydantic de grupos de mesas (§3.22, RB-27/28/29, PD-12).

El alta masiva recibe `materias[]` y `condiciones[]`; el backend crea el
grupo y N = materias × condiciones mesas en 'planificada' con los 4
snapshots rellenos desde el catálogo (ME-01/GR-01).
"""
from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GrupoCrear(BaseModel):
    """POST /grupos — RB-28: el secretario elige materias y condiciones."""

    model_config = ConfigDict(extra="forbid")

    convocatoria_id: UUID
    fecha: date
    hora: time
    nombre: str | None = Field(default=None, max_length=100)
    materias: list[UUID] = Field(min_length=1)
    condiciones: list[UUID] = Field(min_length=1)


class GrupoMover(BaseModel):
    """PATCH /grupos/{id} — sólo fecha y hora (RB-27: el grupo es ese par)."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    hora: time


class GrupoLectura(BaseModel):
    """Columnas de negocio del grupo (§3.22)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    convocatoria_id: UUID
    fecha: date
    hora: time
    nombre: str | None


class GrupoCreado(GrupoLectura):
    """Respuesta del POST: agrega cuántas mesas generó la operación."""

    mesas_creadas: int
