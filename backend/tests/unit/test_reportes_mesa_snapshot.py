"""T4 (S4) — Snapshot de mesa: GET /api/v1/reportes/mesa/{mesa_id}.

Spec: odd/tasks/sdd-5-reportes.md, T4, S4.
CU-29 (doc 05 §5.9, doc 08 RB-11/12). Permiso `reporte.exportar`.
Lee columnas snapshot de la mesa (orientacion_nombre, curso_nombre,
materia_nombre, condicion_nombre, fecha, hora) + estado derivado por
fecha/hora BA vs hoy (vencida -> "cerrada", sino "planificada").
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.core.dependencies import get_db
from app.core.fechas import hoy_buenos_aires
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app

_URL = "/api/v1/reportes/mesa"


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",), rol_codigo="secretario"):
    from app.core.security import hash_password
    from app.features.usuarios.models import (
        UsRol,
        UsRolPermiso,
        UsUsuario,
        UsUsuarioModulo,
        UsUsuarioRol,
    )
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
    username = f"user-{uuid.uuid4().hex[:8]}"
    user = UsUsuario(
        id=uuid.uuid4(), persona_id=uuid.uuid4(), username=username,
        password_hash=hash_password("cl4ve-S3gura."), activo=True, bloqueado=False,
        intentos_fallidos=0, token_version=1, password_changed_at=now,
        created_at=now,
    )
    rol = UsRol(
        id=uuid.uuid4(), codigo=f"{rol_codigo}-{uuid.uuid4().hex[:8]}",
        descripcion=f"{rol_codigo} de test", activo=True, created_at=now,
    )
    db.add_all([user, rol])
    await db.flush()
    db.add(UsUsuarioRol(usuario_id=user.id, rol_id=rol.id))
    for codigo in modulos:
        modulo = await db.scalar(select_modulo(codigo))
        db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo.id))
    for codigo in permisos:
        permiso = await db.scalar(select_permiso(codigo))
        db.add(UsRolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db.commit()
    return username


def select_modulo(codigo):
    from sqlalchemy import select

    from app.features.usuarios.models import UsModulo
    return select(UsModulo).where(UsModulo.codigo == codigo)


def select_permiso(codigo):
    from sqlalchemy import select

    from app.features.usuarios.models import UsPermiso
    return select(UsPermiso).where(UsPermiso.codigo == codigo)


async def login(client, username, modulo="sigme_web"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "cl4ve-S3gura.", "modulo": modulo},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access']}"}


@pytest.fixture
async def app_client(db_session):
    app = create_app()
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def crear_convocatoria(db, *, inicio=None, fin=None, activa=True):
    from app.features.mesas.models import EsConvocatoria
    hoy = hoy_buenos_aires()
    conv = EsConvocatoria(
        id=uuid.uuid4(),
        descripcion="Cuatrimestre de test",
        fecha_inicio_inscripcion=inicio or (hoy - timedelta(days=10)),
        fecha_fin_inscripcion=fin or (hoy + timedelta(days=10)),
        activa=activa,
        created_at=datetime.now(UTC),
    )
    db.add(conv)
    await db.commit()
    return conv.id


async def crear_catalogo(db, *, cant_materias=1, cant_condiciones=1):
    from app.features.catalogo.models import (
        EsCondicion,
        EsCurso,
        EsMateria,
        EsOrientacion,
    )
    orientacion = EsOrientacion(
        id=uuid.uuid4(), descripcion=f"Orientación {uuid.uuid4().hex[:6]}",
        activo=True, created_at=datetime.now(UTC),
    )
    curso = EsCurso(
        id=uuid.uuid4(), orientacion_id=orientacion.id, descripcion="3er Año",
        anio=3, activo=True, created_at=datetime.now(UTC),
    )
    db.add_all([orientacion, curso])
    await db.flush()
    materias = []
    for i in range(cant_materias):
        materia = EsMateria(
            id=uuid.uuid4(), curso_id=curso.id, descripcion=f"Materia {i}",
            es_taller=False, activo=True, created_at=datetime.now(UTC),
        )
        db.add(materia)
        materias.append(materia)
    condiciones = []
    for i in range(cant_condiciones):
        condicion = EsCondicion(
            id=uuid.uuid4(), descripcion=f"Condición {i} {uuid.uuid4().hex[:4]}",
            activo=True, created_at=datetime.now(UTC),
        )
        db.add(condicion)
        condiciones.append(condicion)
    await db.commit()
    return materias, condiciones


async def post_grupo(client, headers, conv, materias, condiciones,
                     fecha=None, hora="10:00", nombre=None):
    hoy = hoy_buenos_aires()
    payload = {
        "convocatoria_id": str(conv),
        "fecha": (fecha or (hoy + timedelta(days=20))).isoformat(),
        "hora": hora,
        "materias": [str(m.id) for m in materias],
        "condiciones": [str(c.id) for c in condiciones],
    }
    if nombre is not None:
        payload["nombre"] = nombre
    return await client.post("/api/v1/sigme/grupos", json=payload, headers=headers)


# ---------------------------------------------------------------------------
# Puertas: sesión y permiso
# ---------------------------------------------------------------------------


async def test_mesa_snapshot_sin_token_es_401(app_client):
    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_mesa_snapshot_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=(), rol_codigo="alumno")
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_mesa_snapshot_mesa_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-no-encontrada"


async def test_mesa_snapshot_mesa_borrada_es_404(app_client, db_session):
    """Mesa con deleted_at -> 404."""
    from datetime import UTC as _UTC

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    creada = await post_grupo(app_client, sec_headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesa.deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-no-encontrada"


# ---------------------------------------------------------------------------
# Estado derivado
# ---------------------------------------------------------------------------


async def test_mesa_snapshot_estado_planificada_futura(app_client, db_session):
    """Mesa en el futuro -> estado 'planificada'."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Mesa en 20 días
    fecha_futura = hoy_buenos_aires() + timedelta(days=20)
    creada = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        fecha=fecha_futura, hora="10:00"
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "planificada"
    # Validar snapshots
    assert resp.json()["mesa_id"] == str(mesa.id)
    assert resp.json()["grupo_id"] == str(mesa.grupo_id)
    assert resp.json()["convocatoria_id"] == str(conv)
    assert resp.json()["materia_nombre"] == materias[0].descripcion
    assert resp.json()["condicion_nombre"] == condiciones[0].descripcion
    assert "orientacion_nombre" in resp.json()
    assert "curso_nombre" in resp.json()


async def test_mesa_snapshot_estado_cerrada_pasada(app_client, db_session):
    """Mesa en el pasado -> estado 'cerrada'."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Mesa hace 5 días
    fecha_pasada = hoy_buenos_aires() - timedelta(days=5)
    creada = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        fecha=fecha_pasada, hora="10:00"
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "cerrada"


async def test_mesa_snapshot_fecha_hoy_es_planificada(app_client, db_session):
    """Mesa hoy -> estado 'planificada' (inclusive hasta fin de día)."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Mesa hoy
    fecha_hoy = hoy_buenos_aires()
    creada = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        fecha=fecha_hoy, hora="23:59"
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "planificada"