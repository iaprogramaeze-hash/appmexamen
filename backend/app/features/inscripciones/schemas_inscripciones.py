"""Schemas Pydantic de las consultas y la inscripción de alumno (SDD-4).

`MesaDisponible` NO es `MesaLectura` (SDD-3): RN-019 prohíbe exponer
`grupo_id` ni campos del grupo en esta respuesta — el grupo es agrupación de
presentación, nunca una elección ni una entrada de validación (RB-30).
Trae `materia_id`/`condicion_id` porque la cascada G-04 los necesita para
alimentar el `POST /inscripciones` (CU-37).

T3 (S3, CU-37): `InscripcionCrear` sólo admite materia + condición (RB-30);
la convocatoria NO viaja en el cuerpo (A-SDD4-4) — es siempre la vigente.
`InscripcionLectura` refleja la fila de `es_mesa_inscripcion` (§3.19).
"""
from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MesaDisponible(BaseModel):
    """Una mesa viva de la convocatoria vigente, dentro de la ventana."""

    model_config = ConfigDict(from_attributes=True)

    materia_id: UUID
    condicion_id: UUID
    orientacion_nombre: str
    curso_nombre: str
    materia_nombre: str
    condicion_nombre: str
    fecha: date
    hora: time | None


class InscripcionCrear(BaseModel):
    """Cuerpo del POST /inscripciones (CU-37): sólo materia + condición.

    `extra="forbid"` cierra la entrada: el alumno elige la combinación
    (RB-30) y nunca envía convocatoria, mesa ni usuario (A-SDD4-4).
    """

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    condicion_id: UUID


class InscripcionLectura(BaseModel):
    """La inscripción creada (§3.19): la fila en `es_mesa_inscripcion`."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    convocatoria_id: UUID
    mesa_examen_id: UUID
    materia_id: UUID
    condicion_id: UUID
    estado: str
    inscripto_en: datetime | None = None


class InscripcionGestion(BaseModel):
    """Fila del listado de gestión (CU-23, S4): además expone el `usuario_id`
    dueño de la inscripción — el gestor debe saber QUIÉN está inscripto."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    convocatoria_id: UUID
    mesa_examen_id: UUID
    materia_id: UUID
    condicion_id: UUID
    estado: str
    inscripto_en: datetime | None = None


class MisInscripcionLectura(BaseModel):
    """Fila de 'mis inscripciones' (CU-38, S5): estado + nombres de
    materia/condición + `fecha`/`hora` de la mesa (snapshots desde la mesa).
    RN-019: nunca expone `grupo_id` ni campos del grupo."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mesa_examen_id: UUID
    materia_id: UUID
    condicion_id: UUID
    estado: str
    materia_nombre: str
    condicion_nombre: str
    fecha: date
    hora: time | None
    inscripto_en: datetime | None = None
