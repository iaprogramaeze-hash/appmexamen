"""Esquemas de la ventana de preinscripción SIGME (§3.21, CU-14).

§6 declara SÓLO GET|POST /ventanas-preinscripcion (sin PATCH): el POST es un
upsert por `anio_lectivo` — "abrir o cerrar la ventana vigente" (CU-14) con
un único verbo, respetando `uq_ventana_anio`. `vigente` es DERIVADO al leer
(`activa AND hoy_BA BETWEEN fechas`, doc 11 §11.5); nunca se persiste.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VentanaUpsert(BaseModel):
    """POST /ventanas-preinscripcion — estado completo de la ventana del año."""

    model_config = ConfigDict(extra="forbid")

    anio_lectivo: int
    descripcion: str = Field(min_length=1, max_length=100)
    fecha_desde: date
    fecha_hasta: date
    activa: bool = True

    @field_validator("fecha_hasta")
    @classmethod
    def _ck_ventana(cls, hasta: date, info) -> date:
        # §3.21 ck_ventana — se materializa como 422 (PD-24) con el campo
        # offending reportado en errors[].
        desde = info.data.get("fecha_desde")
        if desde is not None and desde > hasta:
            raise ValueError("fecha_hasta no puede ser anterior a fecha_desde")
        return hasta


class VentanaLectura(BaseModel):
    """Columnas de negocio + vigencia derivada (sin tocar la fila)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    anio_lectivo: int
    descripcion: str
    fecha_desde: date
    fecha_hasta: date
    activa: bool
    vigente: bool
