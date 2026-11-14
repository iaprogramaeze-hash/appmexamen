"""Schemas Pydantic de convocatorias (§3.17, doc 04 §4.1).

Estado derivado sin escritura (CU-22 / doc 04): borrador / abierta /
cerrada. El límite de ventana es por fecha de calendario en
America/Argentina/Buenos_Aires (RB-23).
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ESTADOS_CONVOCATORIA = ("borrador", "abierta", "cerrada")


class ConvocatoriaCrear(BaseModel):
    """POST /convocatorias — C-01: nace con `activa` en true por defecto."""

    model_config = ConfigDict(extra="forbid")

    descripcion: str = Field(min_length=1, max_length=100)
    fecha_inicio_inscripcion: date
    fecha_fin_inscripcion: date
    activa: bool = True

    @model_validator(mode="after")
    def _ventana_valida(self) -> ConvocatoriaCrear:
        # §3.17 ck_convocatoria_ventana — se materializa como 422 (PD-24).
        if self.fecha_inicio_inscripcion > self.fecha_fin_inscripcion:
            raise ValueError(
                "fecha_inicio_inscripcion no puede ser posterior a "
                "fecha_fin_inscripcion"
            )
        return self


class ConvocatoriaActualizar(BaseModel):
    """PATCH /convocatorias/{id} — sólo campos editables de negocio."""

    model_config = ConfigDict(extra="forbid")

    descripcion: str | None = Field(default=None, min_length=1, max_length=100)
    fecha_inicio_inscripcion: date | None = None
    fecha_fin_inscripcion: date | None = None
    activa: bool | None = None


class ConvocatoriaLectura(BaseModel):
    """Columnas de negocio + estado derivado (sin tocar la fila)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    descripcion: str
    fecha_inicio_inscripcion: date
    fecha_fin_inscripcion: date
    activa: bool
    estado: str
