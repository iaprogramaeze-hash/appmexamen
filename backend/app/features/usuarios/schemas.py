"""Schemas Pydantic de usuarios (SDD-2 S5; CU-09, §3.5)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class UsuarioCreate(BaseModel):
    """POST /sigme/usuarios: alta sobre una persona existente (CU-09).

    §2.5: la política de 12 caracteres rige al CREAR la clave.
    """

    persona_id: uuid.UUID
    username: str = Field(min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=150)
    password: str = Field(min_length=12, max_length=128)


class UsuarioResponse(BaseModel):
    """Salida de usuario; password_hash NUNCA viaja (§2.5, PD-05)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    persona_id: uuid.UUID
    username: str
    email: str | None = None
    activo: bool
    bloqueado: bool
    roles: list[str] = Field(default_factory=list)
