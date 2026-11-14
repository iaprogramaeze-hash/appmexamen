"""Servicio de personas (SDD-2 S4; CU-07 consulta, CU-08 edición).

Reglas:
- Sólo filas no borradas lógicamente (§1.7).
- Unicidad parcial (documento_tipo_id, documento) entre no borradas → 409
  persona-duplicada.
- PATCH sólo acepta campos mutables; la identidad (tipo, documento) es
  inmutable en v1 (asunción A2).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.features.personas.models import PeDocumentoTipo, PePersona
from app.features.personas.schemas import PersonaCreate, PersonaUpdate


async def listar_personas(db: AsyncSession, *, q: str | None = None) -> list[PePersona]:
    """Lista personas vigentes; `q` filtra por documento, apellido o nombre."""
    statement = select(PePersona).where(PePersona.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        statement = statement.where(
            or_(
                PePersona.documento.ilike(like),
                PePersona.apellido.ilike(like),
                PePersona.nombre.ilike(like),
            )
        )
    statement = statement.order_by(PePersona.apellido, PePersona.nombre)
    return list(await db.scalars(statement))


async def obtener_persona(db: AsyncSession, persona_id: uuid.UUID) -> PePersona:
    """404 persona-no-encontrada si no existe o está borrada lógicamente."""
    persona = await db.get(PePersona, persona_id)
    if persona is None or persona.deleted_at is not None:
        raise NotFoundError("Persona no encontrada", code="persona-no-encontrada")
    return persona


async def crear_persona(db: AsyncSession, payload: PersonaCreate) -> PePersona:
    """Alta con validación de tipo de documento y unicidad parcial (§3.2)."""
    tipo = await db.get(PeDocumentoTipo, payload.documento_tipo_id)
    if tipo is None or tipo.deleted_at is not None or not tipo.activo:
        raise DomainValidationError(
            "El tipo de documento no existe o no está activo",
            code="documento-tipo-invalido",
            errors=[
                {
                    "field": "documento_tipo_id",
                    "message": "Tipo de documento inexistente o inactivo",
                }
            ],
        )

    duplicada = await db.scalar(
        select(PePersona.id).where(
            PePersona.documento_tipo_id == payload.documento_tipo_id,
            PePersona.documento == payload.documento,
            PePersona.deleted_at.is_(None),
        )
    )
    if duplicada is not None:
        raise ConflictError(
            "Ya existe una persona con ese documento", code="persona-duplicada"
        )

    persona = PePersona(
        id=uuid.uuid4(),
        documento_tipo_id=payload.documento_tipo_id,
        documento=payload.documento,
        apellido=payload.apellido,
        nombre=payload.nombre,
        razon_social=payload.razon_social,
        fecha_nacimiento=payload.fecha_nacimiento,
        sexo=payload.sexo,
        direccion=payload.direccion,
        nacionalidad=payload.nacionalidad,
        created_at=datetime.now(UTC),
    )
    db.add(persona)
    await db.flush()
    return persona


async def modificar_persona(
    db: AsyncSession, persona_id: uuid.UUID, payload: PersonaUpdate
) -> PePersona:
    """PATCH de campos mutables; la identidad queda intacta (A2)."""
    persona = await obtener_persona(db, persona_id)

    cambios = payload.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(persona, campo, valor)
    # §1.6: updated_at lo dispara el trigger en Postgres; explícito para que
    # la respuesta y SQLite de tests lo reflejen igual.
    persona.updated_at = datetime.now(UTC)
    await db.flush()
    return persona
