"""Schemas Pydantic de roles, permisos y módulos (SDD-2 S6; CU-10, §3.6-3.10)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CatalogoCreate(BaseModel):
    """POST de catálogo cerrado: { codigo, descripcion } (§3.6-3.10)."""

    codigo: str = Field(min_length=1, max_length=80)
    descripcion: str = Field(min_length=1, max_length=150)


class RolResponse(BaseModel):
    """Rol con sus permisos por código (catálogo §2.7)."""

    id: uuid.UUID
    codigo: str
    descripcion: str
    activo: bool
    permisos: list[str] = Field(default_factory=list)


class PermisoResponse(BaseModel):
    """§3.7: permiso granular; no tiene activo."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    descripcion: str


class ModuloResponse(BaseModel):
    """§3.8: módulo con activo booleano (§1.11)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    descripcion: str
    activo: bool
