"""T2 (S2) — Mesas-disponibles: GET /api/v1/mesas-disponibles.

Spec: odd/tasks/sdd-4-inscripciones.md, T2, S2.
CU-35 + cascada G-04 (doc 06 §6.2). Permiso `mesa.listar` (agnóstico de
dispositivo). "Sólo dentro de la ventana de inscripción" (RB-07/RB-23, `hoy`
BA): fuera de la ventana -> 409 `ventana-cerrada`. Devuelve las mesas VIVAS
(`deleted_at IS NULL`) de la convocatoria vigente, cada una con
materia_id/condicion_id (para alimentar el POST de CU-37), los 4 snapshots
(RB-11), `fecha` y `hora`. RB-22 NO aplica (A-SDD4-2/PD-23): las mesas sin
inscripciones SÍ aparecen. RN-019: nunca expone `grupo_id` ni campos del
grupo. G-04: la cascada orientación -> curso -> materia -> condición se
deriva de las combinaciones únicas de esta misma respuesta.
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

_URL = "/api/v1/mesas-disponibles"


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME (harness T1/T2/T3 de test_mesas)."""
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
        id=uuid.uuid4(), codigo=f"rol-{uuid.uuid4().hex[:8]}",
        descripcion="rol de test", activo=True, created_at=now,
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
    return conv.id  # UUID plano: evita ORM vencido tras commit


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=2):
    """Orientación + curso + N materias + M condiciones activas (harness T3)."""
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
    """RB-28/29: crea el grupo y sus mesas en bloque (harness T3)."""
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


async def test_mesas_disponibles_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_mesas_disponibles_sin_permiso_es_403(app_client, db_session):
    """Sesión válida pero sin `mesa.listar` -> 403 permiso-denegado."""
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_mesas_disponibles_fuera_de_ventana_es_409(app_client, db_session):
    """RB-07/RB-23: sólo dentro de la ventana -> 409 ventana-cerrada."""
    hoy = hoy_buenos_aires()
    await crear_convocatoria(
        db_session,
        inicio=hoy - timedelta(days=20),
        fin=hoy - timedelta(days=3),  # vigente (activa) pero ventana cerrada
    )
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "ventana-cerrada"


async def test_mesas_disponibles_sin_convocatoria_es_404(app_client, db_session):
    """Sin convocatoria vigente (activa) -> 404 (reuse de convocatoria_vigente)."""
    await crear_convocatoria(db_session, activa=False)  # borrador
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"


async def test_mesas_disponibles_devuelve_mesas_vivas(app_client, db_session):
    """PD-23/A-SDD4-2: mesas sin inscripciones SÍ aparecen; con snapshots,
    fecha y hora; los ids para alimentar el POST de CU-37."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )
    creada = await post_grupo(
        app_client, headers, conv, materias, condiciones, nombre="Mañana"
    )
    assert creada.status_code == 201, creada.text

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    mesas = resp.json()
    # 2 materias × 2 condiciones = 4 mesas, todas sin inscripciones
    assert len(mesas) == 4
    assert {(m["materia_id"], m["condicion_id"]) for m in mesas} == {
        (str(ma.id), str(c.id)) for ma in materias for c in condiciones
    }
    muestra = next(m for m in mesas if m["materia_id"] == str(materias[0].id))
    assert muestra["materia_nombre"] == "Materia 0"
    assert muestra["curso_nombre"] == "3er Año"
    assert muestra["orientacion_nombre"].startswith("Orientación")
    assert muestra["condicion_nombre"].startswith("Condición")
    assert muestra["fecha"] is not None
    assert muestra["hora"] is not None


async def test_mesas_disponibles_mesa_borrada_no_aparece(app_client, db_session):
    """`deleted_at IS NULL` (S2): una mesa borrada no se lista."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=2
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    completa = await app_client.get(_URL, headers=headers)
    assert len(completa.json()) == 2

    mesa = await db_session.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.grupo_id == uuid.UUID(creada.json()["id"]),
            EsMesaExamen.materia_id == materias[0].id,
        )
    )
    mesa.deleted_at = datetime.now(UTC)
    await db_session.commit()

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    restantes = resp.json()
    assert len(restantes) == 1
    assert restantes[0]["materia_id"] == str(materias[0].id)


async def test_mesas_disponibles_no_expone_grupo(app_client, db_session):
    """RN-019: la respuesta nunca expone `grupo_id` ni campos del grupo."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    mesa = resp.json()[0]
    assert "grupo_id" not in mesa
    assert "grupo" not in mesa
    assert "convocatoria_id" not in mesa


async def test_mesas_disponibles_cascada_combinaciones_unicas(app_client, db_session):
    """G-04/A-SDD4-3: la cascada orientación -> curso -> materia -> condición
    se deriva de las combinaciones ÚNICAS de la respuesta."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    combos = {
        (
            m["orientacion_nombre"],
            m["curso_nombre"],
            m["materia_nombre"],
            m["condicion_nombre"],
        )
        for m in resp.json()
    }
    assert len(combos) == 4  # combinaciones únicas, sin duplicados
