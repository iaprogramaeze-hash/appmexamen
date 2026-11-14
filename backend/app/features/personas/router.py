"""Endpoints /api/v1/sigme/personas (SDD-2 S4; analisis.txt §6, CU-07/CU-08).

RBAC (§2.7 vía claims): GET → persona.listar; PATCH → persona.modificar;
POST → usuario.gestionar (asunción A1: la matriz no define código propio
para el alta — hueco declarado en doc 05, gate temporal).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.features.auth.dependencies import require_permiso
from app.features.auth.tokens import Principal
from app.features.personas import service
from app.features.personas.schemas import PersonaCreate, PersonaResponse, PersonaUpdate

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("", response_model=list[PersonaResponse])
async def listar_personas(
    q: str | None = Query(default=None, description="Documento, apellido o nombre"),
    _: Principal = Depends(require_permiso("persona.listar")),
    db: AsyncSession = Depends(get_db),
) -> list[PersonaResponse]:
    """GET /sigme/personas: consulta de personas (CU-07, matrix §2.4)."""
    personas = await service.listar_personas(db, q=q)
    return [PersonaResponse.model_validate(p) for p in personas]


@router.get("/{persona_id}", response_model=PersonaResponse)
async def obtener_persona(
    persona_id: uuid.UUID,
    _: Principal = Depends(require_permiso("persona.listar")),
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """GET /sigme/personas/{id}: 404 persona-no-encontrada (CU-07)."""
    persona = await service.obtener_persona(db, persona_id)
    return PersonaResponse.model_validate(persona)


@router.post("", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def crear_persona(
    payload: PersonaCreate,
    _: Principal = Depends(require_permiso("usuario.gestionar")),
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """POST /sigme/personas: alta (§6; permiso A1) → 201 / 409 / 422."""
    persona = await service.crear_persona(db, payload)
    await db.commit()
    return PersonaResponse.model_validate(persona)


@router.patch("/{persona_id}", response_model=PersonaResponse)
async def modificar_persona(
    persona_id: uuid.UUID,
    payload: PersonaUpdate,
    _: Principal = Depends(require_permiso("persona.modificar")),
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """PATCH /sigme/personas/{id}: campos mutables, identidad inmutable (A2)."""
    persona = await service.modificar_persona(db, persona_id, payload)
    await db.commit()
    return PersonaResponse.model_validate(persona)
