"""T5 (S5) — Cobertura-mesas (RB-31, PD-15/A-SDD3-1, CU-21).

Spec: odd/tasks/sdd-3-mesas-convocatorias.md, T5, S5.
`GET /sigme/cobertura-mesas?convocatoria_id=` lista los pares
materia × condición del catálogo ACTIVO completo que quedan SIN mesa en la
convocatoria (mesa con `deleted_at IS NULL`, cualquier grupo y fecha).
Es un reporte de consulta (advisory), no un gate: nada lo usa para rechazar
operaciones. Se consulta ANTES de abrir la ventana de inscripción.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME (harness T1–T4)."""
    from app.core.security import hash_password
    from app.features.usuarios.models import (
        UsModulo,
        UsPermiso,
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
        id=uuid.uuid4(), codigo=f"rol-{uuid.uuid4().hex[:8]}",
        descripcion="rol de test", activo=True, created_at=now,
    )
    db.add_all([user, rol])
    await db.flush()
    db.add(UsUsuarioRol(usuario_id=user.id, rol_id=rol.id))
    for codigo in modulos:
        modulo = await db.scalar(select(UsModulo).where(UsModulo.codigo == codigo))
        db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo.id))
    for codigo in permisos:
        permiso = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db.commit()
    return username


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


async def crear_convocatoria(db):
    from app.features.mesas.models import EsConvocatoria

    hoy = date.today()
    conv = EsConvocatoria(
        id=uuid.uuid4(),
        descripcion="Cuatrimestre de test",
        fecha_inicio_inscripcion=hoy - timedelta(days=10),
        fecha_fin_inscripcion=hoy + timedelta(days=10),
        activa=True,
        created_at=datetime.now(UTC),
    )
    db.add(conv)
    await db.commit()
    return conv


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=2):
    """Orientación + curso + N materias + M condiciones activas."""
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


async def post_grupo(client, headers, conv, materias, condiciones):
    hoy = date.today()
    payload = {
        "convocatoria_id": str(conv.id),
        "fecha": (hoy + timedelta(days=20)).isoformat(),
        "hora": "10:00",
        "materias": [str(m.id) for m in materias],
        "condiciones": [str(c.id) for c in condiciones],
    }
    return await client.post("/api/v1/sigme/grupos", json=payload, headers=headers)


COBERTURA = "/api/v1/sigme/cobertura-mesas"


async def test_cobertura_requiere_auth(app_client):
    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(uuid.uuid4())}
    )
    assert respuesta.status_code == 401


async def test_cobertura_requiere_mesa_listar(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(uuid.uuid4())}, headers=headers
    )
    assert respuesta.status_code == 403


async def test_cobertura_convocatoria_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(uuid.uuid4())}, headers=headers
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "convocatoria-no-encontrada"


async def test_cobertura_sin_mesas_es_catalogo_completo(app_client, db_session):
    """PD-15 (A-SDD3-1): el conjunto esperado es catálogo ACTIVO completo —
    sin mesas creadas, TODOS los pares materia × condición faltan."""
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )

    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(conv.id)}, headers=headers
    )
    assert respuesta.status_code == 200, respuesta.text
    pares = respuesta.json()
    assert len(pares) == 4
    assert {(p["materia_id"], p["condicion_id"]) for p in pares} == {
        (str(m.id), str(c.id)) for m in materias for c in condiciones
    }
    muestra = next(p for p in pares if p["materia_id"] == str(materias[0].id))
    assert muestra["materia_nombre"] == "Materia 0"
    assert muestra["curso_nombre"] == "3er Año"
    assert muestra["orientacion_nombre"].startswith("Orientación")
    assert muestra["condicion_nombre"].startswith("Condición")


async def test_cobertura_descubre_pares_cubiertos(app_client, db_session):
    """RB-31: la cobertura muestra sólo los pares SIN mesa; los cubiertos
    por un grupo desaparecen del reporte."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )
    creada = await post_grupo(
        app_client, headers, conv, [materias[0], materias[1]], [condiciones[0]]
    )
    assert creada.status_code == 201

    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(conv.id)}, headers=headers
    )
    assert respuesta.status_code == 200, respuesta.text
    pares = respuesta.json()
    assert len(pares) == 2
    assert {(p["materia_id"], p["condicion_id"]) for p in pares} == {
        (str(materias[0].id), str(condiciones[1].id)),
        (str(materias[1].id), str(condiciones[1].id)),
    }


async def test_cobertura_mesa_borrada_no_cubre(app_client, db_session):
    """"mesa con deleted_at IS NULL" (S5): una mesa borrada libera el par
    y vuelve a faltar en el reporte."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201

    cubierta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(conv.id)}, headers=headers
    )
    assert cubierta.json() == []

    mesa = await db_session.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.grupo_id == uuid.UUID(creada.json()["id"])
        )
    )
    mesa.deleted_at = datetime.now(UTC)
    await db_session.commit()

    liberada = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(conv.id)}, headers=headers
    )
    assert liberada.status_code == 200, liberada.text
    assert len(liberada.json()) == 1
    assert liberada.json()[0]["materia_id"] == str(materias[0].id)
    assert liberada.json()[0]["condicion_id"] == str(condiciones[0].id)


async def test_cobertura_sin_parametros_es_422(app_client, db_session):
    """PD-24: convocatoria_id es obligatorio."""
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(COBERTURA, headers=headers)
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json()["code"] == "validacion"
    assert respuesta.json()["errors"]


async def test_cobertura_totalmente_cubierta_es_lista_vacia(
    app_client, db_session
):
    """Catálogo 1×1 con su mesa: el reporte queda vacío."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201

    respuesta = await app_client.get(
        COBERTURA, params={"convocatoria_id": str(conv.id)}, headers=headers
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == []
