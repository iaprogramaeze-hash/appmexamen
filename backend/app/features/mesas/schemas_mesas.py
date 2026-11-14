"""Schemas Pydantic de mesas SIGME (S4: CU-19/20, RB-11/22/23, PD-24).

`MesaAsignar` sólo admite materia/condición: fecha y hora pertenecen al
grupo (RB-29 → `extra="forbid"`). CU-20 exige AL MENOS UNA asignación por
PATCH.
"""
from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class MesaLectura(BaseModel):
    """Columnas de negocio de la mesa (§3.18) + los 4 snapshots (RB-11)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    convocatoria_id: UUID
    grupo_id: UUID
    materia_id: UUID
    condicion_id: UUID
    fecha: date
    hora: time | None
    estado: str
    orientacion_nombre: str
    curso_nombre: str
    materia_nombre: str
    condicion_nombre: str


class MesaAsignar(BaseModel):
    """PATCH /mesas/{id} — CU-20: cambia la asignación de la mesa."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    condicion_id: UUID | None = None

    @model_validator(mode="after")
    def _exige_al_menos_una(self) -> MesaAsignar:
        if self.materia_id is None and self.condicion_id is None:
            raise ValueError("Debe indicarse materia_id y/o condicion_id")
        return self


class CoberturaPar(BaseModel):
    """RB-31: par materia × condición SIN mesa en la convocatoria.

    Reporte de consulta (advisory) sobre el catálogo ACTIVO completo
    (PD-15/A-SDD3-1): el secretario lo usa para saber QUÉ crear antes de
    abrir la ventana de inscripción.
    """

    materia_id: UUID
    orientacion_nombre: str
    curso_nombre: str
    materia_nombre: str
    condicion_id: UUID
    condicion_nombre: str
