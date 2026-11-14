"""Schemas Pydantic de reportes (SDD-5).

Todos los reportes aplican RB-22 (solo mesas con inscriptos activos) y RB-19
(leer snapshots de la mesa, no nombres actuales del catálogo).
"""
from __future__ import annotations

from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PermisoExamenMesa(BaseModel):
    """Una mesa del permiso de examen individual."""

    model_config = ConfigDict(from_attributes=True)

    mesa_id: UUID
    grupo_id: UUID
    fecha: date
    hora: time | None
    materia_id: UUID
    materia_nombre: str
    condicion_id: UUID
    condicion_nombre: str
    orientacion_nombre: str
    curso_nombre: str


class PermisoExamenResponse(BaseModel):
    """Respuesta del permiso de examen individual (S1)."""

    model_config = ConfigDict(from_attributes=True)

    usuario_id: UUID
    convocatoria_id: UUID
    convocatoria_descripcion: str
    mesas: list[PermisoExamenMesa]


class PermisoExamenMasivoAlumno(BaseModel):
    """Alumno en el listado masivo (S2)."""

    model_config = ConfigDict(from_attributes=True)

    usuario_id: UUID
    username: str
    materias: list[dict]  # [{materia_id, materia_nombre, condicion_id, condicion_nombre}]


class PermisoExamenMasivoMesa(BaseModel):
    """Mesa en el listado masivo (S2)."""

    model_config = ConfigDict(from_attributes=True)

    mesa_id: UUID
    grupo_id: UUID
    fecha: date
    hora: time | None
    materia_id: UUID
    materia_nombre: str
    condicion_id: UUID
    condicion_nombre: str
    orientacion_nombre: str
    curso_nombre: str
    alumnos: list[PermisoExamenMasivoAlumno]


class PermisoExamenMasivoResponse(BaseModel):
    """Respuesta del permiso de examen masivo (S2)."""

    model_config = ConfigDict(from_attributes=True)

    convocatoria_id: UUID
    convocatoria_descripcion: str
    mesas: list[PermisoExamenMasivoMesa]


class ActaVolanteAlumno(BaseModel):
    """Alumno en el acta volante (S3)."""

    model_config = ConfigDict(from_attributes=True)

    usuario_id: UUID
    username: str
    persona_documento: str
    materia_nombre: str
    condicion_nombre: str


class ActaVolanteResponse(BaseModel):
    """Respuesta del acta volante (S3)."""

    model_config = ConfigDict(from_attributes=True)

    mesa_id: UUID
    grupo_id: UUID
    fecha: date
    hora: time | None
    materia_id: UUID
    materia_nombre: str
    condicion_id: UUID
    condicion_nombre: str
    orientacion_nombre: str
    curso_nombre: str
    alumnos: list[ActaVolanteAlumno]


class MesaSnapshotResponse(BaseModel):
    """Snapshot de mesa (S4)."""

    model_config = ConfigDict(from_attributes=True)

    mesa_id: UUID
    grupo_id: UUID
    convocatoria_id: UUID
    fecha: date
    hora: time | None
    estado: str
    orientacion_nombre: str
    curso_nombre: str
    materia_nombre: str
    condicion_nombre: str


class PlanillaGruposMesa(BaseModel):
    """Mesa dentro de un grupo en la planilla (S5)."""

    model_config = ConfigDict(from_attributes=True)

    mesa_id: UUID
    materia_id: UUID
    materia_nombre: str
    condicion_id: UUID
    condicion_nombre: str


class PlanillaGruposGrupo(BaseModel):
    """Grupo en la planilla (S5)."""

    model_config = ConfigDict(from_attributes=True)

    grupo_id: UUID
    fecha: date
    hora: time | None
    nombre: str | None
    mesas: list[PlanillaGruposMesa]


class PlanillaGruposResponse(BaseModel):
    """Respuesta de la planilla de grupos (S5)."""

    model_config = ConfigDict(from_attributes=True)

    convocatoria_id: UUID
    convocatoria_descripcion: str
    grupos: list[PlanillaGruposGrupo]