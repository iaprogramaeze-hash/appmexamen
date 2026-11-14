"""Schemas Pydantic del catálogo (SDD-2 S7; CU-05/CU-06, PD-02, PD-21)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class OrientacionCreate(BaseModel):
    descripcion: str = Field(min_length=1, max_length=150)


class OrientacionUpdate(BaseModel):
    descripcion: str | None = Field(default=None, min_length=1, max_length=150)


class OrientacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    descripcion: str
    activo: bool


class CursoCreate(BaseModel):
    orientacion_id: uuid.UUID
    descripcion: str = Field(min_length=1, max_length=100)
    anio: int | None = None  # RB-15: año sin letra ni turno


class CursoUpdate(BaseModel):
    descripcion: str | None = Field(default=None, min_length=1, max_length=100)
    anio: int | None = None


class CursoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    orientacion_id: uuid.UUID
    descripcion: str
    anio: int | None = None
    activo: bool


class MateriaCreate(BaseModel):
    curso_id: uuid.UUID
    descripcion: str = Field(min_length=1, max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    es_taller: bool = False  # RB-04: talleres como materia normal


class MateriaUpdate(BaseModel):
    descripcion: str | None = Field(default=None, min_length=1, max_length=150)
    codigo: str | None = Field(default=None, max_length=20)
    es_taller: bool | None = None


class MateriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    curso_id: uuid.UUID
    codigo: str | None = None
    descripcion: str
    es_taller: bool
    activo: bool


class CondicionCreate(BaseModel):
    descripcion: str = Field(min_length=1, max_length=50)
    limite_materias: int | None = Field(default=None, ge=0)  # NULL = sin límite


class CondicionUpdate(BaseModel):
    descripcion: str | None = Field(default=None, min_length=1, max_length=50)
    limite_materias: int | None = Field(default=None, ge=0)


class CondicionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    descripcion: str
    limite_materias: int | None = None
    activo: bool
