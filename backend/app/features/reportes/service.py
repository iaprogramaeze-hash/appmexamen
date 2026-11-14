"""Service de reportes (SDD-5).

RB-22 (vida): TODOS los reportes filtran mesas con `deleted_at IS NULL` Y que
tengan al menos una `es_mesa_inscripcion` con `estado='inscripto'`,
`deleted_at IS NULL`.

RB-19 (snapshots): Leer `materia_nombre`, `condicion_nombre`,
`orientacion_nombre`, `curso_nombre` desde las columnas snapshot de
`es_mesa_examen`, NO desde el catálogo actual.

Permiso: `reporte.exportar` (secretario, director, administrador, superadmin).
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.features.mesas.models import EsConvocatoria, EsMesaExamen, EsMesaInscripcion
from app.features.mesas.service_convocatoria import (
    estado_convocatoria,
    hoy_buenos_aires,
)
from app.features.usuarios.models import UsModulo, UsUsuario, UsUsuarioModulo


async def _convocatoria_vigente_o_activa(db: AsyncSession) -> EsConvocatoria:
    """La convocatoria vigente según A-SDD4-1 (reutiliza lógica de inscripciones)."""
    hoy = hoy_buenos_aires()
    resultado = await db.execute(
        select(EsConvocatoria)
        .where(
            EsConvocatoria.activa.is_(True),
            EsConvocatoria.deleted_at.is_(None),
        )
        .order_by(EsConvocatoria.fecha_inicio_inscripcion.desc())
    )
    candidatas = list(resultado.scalars().all())
    if not candidatas:
        raise NotFoundError("Convocatoria no encontrada", code="convocatoria-no-encontrada")
    for convocatoria in candidatas:
        if estado_convocatoria(convocatoria, hoy) == "abierta":
            return convocatoria
    return candidatas[0]


async def _validar_usuario_alumno(db: AsyncSession, usuario_id: uuid.UUID) -> UsUsuario:
    """Valida que el usuario exista y sea alumno (tiene módulo sigme_mobile)."""
    usuario = await db.get(UsUsuario, usuario_id)
    if usuario is None:
        raise NotFoundError("Usuario no encontrado", code="usuario-no-encontrado")
    # Verificar módulo sigme_mobile
    modulo = await db.scalar(
        select(UsModulo).where(UsModulo.codigo == "sigme_mobile")
    )
    if modulo is None:
        raise NotFoundError("Usuario no es alumno", code="usuario-no-es-alumno")
    tiene = await db.scalar(
        select(UsUsuarioModulo).where(
            UsUsuarioModulo.usuario_id == usuario_id,
            UsUsuarioModulo.modulo_id == modulo.id,
        )
    )
    if tiene is None:
        raise NotFoundError("Usuario no es alumno", code="usuario-no-es-alumno")
    return usuario


async def _obtener_convocatoria_para_reportes(
    db: AsyncSession, convocatoria_id: uuid.UUID | None
) -> EsConvocatoria:
    """Obtiene la convocatoria para reportes: la pasada por param o la vigente/activa."""
    if convocatoria_id is not None:
        conv = await db.get(EsConvocatoria, convocatoria_id)
        if conv is None or conv.deleted_at is not None:
            raise NotFoundError("Convocatoria no encontrada", code="convocatoria-no-encontrada")
        return conv
    return await _convocatoria_vigente_o_activa(db)


async def permiso_examen_individual(
    db: AsyncSession, *, usuario_id: uuid.UUID
) -> dict:
    """S1: Permiso de examen individual por alumno (CU-27).

    Lista mesas donde el alumno tiene inscripción ACTIVA (estado='inscripto',
    deleted_at IS NULL), con snapshots de la mesa. Orden fecha asc, hora asc.
    """
    await _validar_usuario_alumno(db, usuario_id)

    convocatoria = await _obtener_convocatoria_para_reportes(db, None)

    # Mesas con inscripción activa del alumno en esta convocatoria
    stmt = (
        select(EsMesaExamen)
        .join(
            EsMesaInscripcion,
            (EsMesaInscripcion.mesa_examen_id == EsMesaExamen.id)
            & (EsMesaInscripcion.usuario_id == usuario_id)
            & (EsMesaInscripcion.estado == "inscripto")
            & (EsMesaInscripcion.deleted_at.is_(None)),
        )
        .where(
            EsMesaExamen.convocatoria_id == convocatoria.id,
            EsMesaExamen.deleted_at.is_(None),
        )
        .order_by(EsMesaExamen.fecha, EsMesaExamen.hora, EsMesaExamen.id)
    )
    resultado = await db.execute(stmt)
    mesas = list(resultado.scalars().all())

    return {
        "usuario_id": usuario_id,
        "convocatoria_id": convocatoria.id,
        "convocatoria_descripcion": convocatoria.descripcion,
        "mesas": [
            {
                "mesa_id": m.id,
                "grupo_id": m.grupo_id,
                "fecha": m.fecha,
                "hora": m.hora,
                "materia_id": m.materia_id,
                "materia_nombre": m.materia_nombre,
                "condicion_id": m.condicion_id,
                "condicion_nombre": m.condicion_nombre,
                "orientacion_nombre": m.orientacion_nombre,
                "curso_nombre": m.curso_nombre,
            }
            for m in mesas
        ],
    }


async def permisos_examen_masivo(
    db: AsyncSession, *, convocatoria_id: uuid.UUID | None = None
) -> dict:
    """S2: Permisos de examen masivo, agrupados por mesa (CU-27).

    Para cada mesa con inscriptos activos, devuelve lista de alumnos con sus
    materias/condiciones. Aplica RB-22: solo mesas con ≥ 1 inscripción activa.
    """
    convocatoria = await _obtener_convocatoria_para_reportes(db, convocatoria_id)

    # Mesas con inscriptos activos (RB-22)
    subq = (
        select(EsMesaInscripcion.mesa_examen_id)
        .where(
            EsMesaInscripcion.convocatoria_id == convocatoria.id,
            EsMesaInscripcion.estado == "inscripto",
            EsMesaInscripcion.deleted_at.is_(None),
        )
        .distinct()
    )
    mesas_stmt = (
        select(EsMesaExamen)
        .where(
            EsMesaExamen.convocatoria_id == convocatoria.id,
            EsMesaExamen.deleted_at.is_(None),
            EsMesaExamen.id.in_(subq),
        )
        .order_by(EsMesaExamen.fecha, EsMesaExamen.hora, EsMesaExamen.id)
    )
    resultado = await db.execute(mesas_stmt)
    mesas = list(resultado.scalars().all())

    # Para cada mesa, obtener alumnos inscriptos con sus materias/condiciones
    mesas_data = []
    for mesa in mesas:
        # Alumnos inscriptos en esta mesa
        ins_stmt = (
            select(EsMesaInscripcion, UsUsuario)
            .join(UsUsuario, UsUsuario.id == EsMesaInscripcion.usuario_id)
            .where(
                EsMesaInscripcion.mesa_examen_id == mesa.id,
                EsMesaInscripcion.estado == "inscripto",
                EsMesaInscripcion.deleted_at.is_(None),
            )
        )
        ins_resultado = await db.execute(ins_stmt)
        inscripciones = list(ins_resultado.all())

        # Agrupar por alumno (una mesa = una materia x condición).
        # En la respuesta masiva, cada alumno puede aparecer en varias mesas.
        # Usar snapshots de la mesa (RB-19): todos los alumnos de la mesa
        # comparten la misma materia/condición.
        alumnos_dict = {}
        for _inscripcion, usuario in inscripciones:
            if usuario.id not in alumnos_dict:
                alumnos_dict[usuario.id] = {
                    "usuario_id": usuario.id,
                    "username": usuario.username,
                    "materias": [],
                }
            alumnos_dict[usuario.id]["materias"].append({
                "materia_id": str(mesa.materia_id),
                "materia_nombre": mesa.materia_nombre,
                "condicion_id": str(mesa.condicion_id),
                "condicion_nombre": mesa.condicion_nombre,
            })

        mesas_data.append({
            "mesa_id": mesa.id,
            "grupo_id": mesa.grupo_id,
            "fecha": mesa.fecha,
            "hora": mesa.hora,
            "materia_id": mesa.materia_id,
            "materia_nombre": mesa.materia_nombre,
            "condicion_id": mesa.condicion_id,
            "condicion_nombre": mesa.condicion_nombre,
            "orientacion_nombre": mesa.orientacion_nombre,
            "curso_nombre": mesa.curso_nombre,
            "alumnos": list(alumnos_dict.values()),
        })

    return {
        "convocatoria_id": convocatoria.id,
        "convocatoria_descripcion": convocatoria.descripcion,
        "mesas": mesas_data,
    }


async def acta_volante(
    db: AsyncSession, *, mesa_id: uuid.UUID
) -> dict:
    """S3: Acta volante por mesa (CU-28).

    Alumnos inscriptos en esa mesa con sus datos. RB-22: mesa debe tener ≥ 1
    inscripción activa.
    """
    mesa = await db.get(EsMesaExamen, mesa_id)
    if mesa is None or mesa.deleted_at is not None:
        raise NotFoundError("Mesa no encontrada", code="mesa-no-encontrada")

    # Verificar RB-22: al menos una inscripción activa
    hay_inscriptos = await db.scalar(
        select(func.count()).select_from(EsMesaInscripcion).where(
            EsMesaInscripcion.mesa_examen_id == mesa_id,
            EsMesaInscripcion.estado == "inscripto",
            EsMesaInscripcion.deleted_at.is_(None),
        )
    )
    if hay_inscriptos == 0:
        raise NotFoundError("Mesa sin inscriptos", code="mesa-sin-inscriptos")

    # Alumnos inscriptos
    stmt = (
        select(EsMesaInscripcion, UsUsuario)
        .join(UsUsuario, UsUsuario.id == EsMesaInscripcion.usuario_id)
        .where(
            EsMesaInscripcion.mesa_examen_id == mesa_id,
            EsMesaInscripcion.estado == "inscripto",
            EsMesaInscripcion.deleted_at.is_(None),
        )
    )
    resultado = await db.execute(stmt)
    inscripciones = list(resultado.all())

    return {
        "mesa_id": mesa.id,
        "grupo_id": mesa.grupo_id,
        "fecha": mesa.fecha,
        "hora": mesa.hora,
        "materia_id": mesa.materia_id,
        "materia_nombre": mesa.materia_nombre,
        "condicion_id": mesa.condicion_id,
        "condicion_nombre": mesa.condicion_nombre,
        "orientacion_nombre": mesa.orientacion_nombre,
        "curso_nombre": mesa.curso_nombre,
        "alumnos": [
            {
                "usuario_id": inscripcion.usuario_id,
                "username": usuario.username,
                "persona_documento": "",  # TODO: unir con pe_persona si existe
                "materia_nombre": mesa.materia_nombre,
                "condicion_nombre": mesa.condicion_nombre,
            }
            for inscripcion, usuario in inscripciones
        ],
    }


async def mesa_snapshot(
    db: AsyncSession, *, mesa_id: uuid.UUID
) -> dict:
    """S4: Snapshot de mesa (CU-29). Lee columnas snapshot + estado derivado."""
    mesa = await db.get(EsMesaExamen, mesa_id)
    if mesa is None or mesa.deleted_at is not None:
        raise NotFoundError("Mesa no encontrada", code="mesa-no-encontrada")

    # Estado derivado por fecha/hora BA vs hoy (inclusive hasta fin de día)
    hoy = hoy_buenos_aires()
    from datetime import datetime, time
    mesa_dt = datetime.combine(mesa.fecha, mesa.hora or time(0, 0))
    if mesa_dt.date() < hoy:
        estado = "cerrada"
    else:
        estado = "planificada"

    return {
        "mesa_id": mesa.id,
        "grupo_id": mesa.grupo_id,
        "convocatoria_id": mesa.convocatoria_id,
        "fecha": mesa.fecha,
        "hora": mesa.hora,
        "estado": estado,
        "orientacion_nombre": mesa.orientacion_nombre,
        "curso_nombre": mesa.curso_nombre,
        "materia_nombre": mesa.materia_nombre,
        "condicion_nombre": mesa.condicion_nombre,
    }


async def planilla_grupos(
    db: AsyncSession, *, convocatoria_id: uuid.UUID
) -> dict:
    """S5: Planilla de grupos (CU-30, RB-32).

    Por convocatoria: cada grupo (fecha, hora) con sus mesas (materia, condición).
    RB-22: solo grupos con al menos una mesa con inscriptos activos.
    """
    convocatoria = await _obtener_convocatoria_para_reportes(db, convocatoria_id)

    # Grupos de la convocatoria
    from app.features.mesas.models import EsGrupoHorario
    grupos_stmt = (
        select(EsGrupoHorario)
        .where(
            EsGrupoHorario.convocatoria_id == convocatoria.id,
            EsGrupoHorario.deleted_at.is_(None),
        )
        .order_by(EsGrupoHorario.fecha, EsGrupoHorario.hora, EsGrupoHorario.id)
    )
    grupos_resultado = await db.execute(grupos_stmt)
    grupos = list(grupos_resultado.scalars().all())

    grupos_data = []
    for grupo in grupos:
        # Mesas de este grupo con inscriptos activos (RB-22)
        subq = (
            select(EsMesaInscripcion.mesa_examen_id)
            .where(
                EsMesaInscripcion.convocatoria_id == convocatoria.id,
                EsMesaInscripcion.estado == "inscripto",
                EsMesaInscripcion.deleted_at.is_(None),
            )
            .distinct()
        )
        mesas_stmt = (
            select(EsMesaExamen)
            .where(
                EsMesaExamen.grupo_id == grupo.id,
                EsMesaExamen.deleted_at.is_(None),
                EsMesaExamen.id.in_(subq),
            )
            .order_by(EsMesaExamen.materia_id, EsMesaExamen.condicion_id)
        )
        mesas_resultado = await db.execute(mesas_stmt)
        mesas = list(mesas_resultado.scalars().all())

        if not mesas:
            continue  # RB-22: grupo sin mesas con inscriptos no aparece

        grupos_data.append({
            "grupo_id": grupo.id,
            "fecha": grupo.fecha,
            "hora": grupo.hora,
            "nombre": grupo.nombre,
            "mesas": [
                {
                    "mesa_id": m.id,
                    "materia_id": m.materia_id,
                    "materia_nombre": m.materia_nombre,
                    "condicion_id": m.condicion_id,
                    "condicion_nombre": m.condicion_nombre,
                }
                for m in mesas
            ],
        })

    return {
        "convocatoria_id": convocatoria.id,
        "convocatoria_descripcion": convocatoria.descripcion,
        "grupos": grupos_data,
    }