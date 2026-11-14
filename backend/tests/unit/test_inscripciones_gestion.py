"""T4 (S4) — Inscripciones de gestión: GET /api/v1/inscripciones.

Spec: odd/tasks/sdd-4-inscripciones.md, T4, S4.
CU-23 (doc 05 §5.8). Permiso `inscripcion.listar`. Listado de las filas de
`es_mesa_inscripcion` con su estado (`inscripto`/`anulado`, RB-21); filtros
opcionales `?mesa_id=&convocatoria_id=`; un filtro que referencia un ID
inexistente -> 404 `mesa-no-encontrada` / `convocatoria-no-encontrada`
(patrón T4). RB-22 NO aplica (lista INSCRIPCIONES, no mesas). Orden
determinístico `inscripto_en` desc. La anulación por secretaría (INS-03)
queda FUERA de SDD-4.
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

_URL = "/api/v1/inscripciones"


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
    return conv.id


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=2):
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


async def usuario_id_de(db, username):
    from sqlalchemy import select

    from app.features.usuarios.models import UsUsuario

    return await db.scalar(select(UsUsuario.id).where(UsUsuario.username == username))


async def primera_mesa(db, conv, materia, condicion):
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    return await db.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.convocatoria_id == conv,
            EsMesaExamen.materia_id == materia.id,
            EsMesaExamen.condicion_id == condicion.id,
        )
    )


async def crear_inscripcion(db, *, usuario_id, mesa, estado="inscripto",
                            inscripto_en=None):
    from app.features.mesas.models import EsMesaInscripcion

    momento = inscripto_en or datetime.now(UTC)
    fila = EsMesaInscripcion(
        id=uuid.uuid4(), usuario_id=usuario_id, mesa_examen_id=mesa.id,
        convocatoria_id=mesa.convocatoria_id, materia_id=mesa.materia_id,
        condicion_id=mesa.condicion_id, estado=estado,
        inscripto_en=momento, created_at=momento,
    )
    db.add(fila)
    await db.commit()
    return fila


# ---------------------------------------------------------------------------
# Puertas: sesión y permiso
# ---------------------------------------------------------------------------


async def test_inscripciones_gestion_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_inscripciones_gestion_sin_permiso_es_403(app_client, db_session):
    """Sesión válida pero sin `inscripcion.listar` -> 403 permiso-denegado."""
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


# ---------------------------------------------------------------------------
# Listado y filtros
# ---------------------------------------------------------------------------


async def test_inscripciones_gestion_lista_todo_ordenado(app_client, db_session):
    """CU-23: listado sin filtros, con estado, orden `inscripto_en` desc."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mesa = await primera_mesa(db_session, conv, materias[0], condiciones[0])

    alumno_a = await usuario_id_de(db_session, await make_usuario(db_session))
    alumno_b = await usuario_id_de(db_session, await make_usuario(db_session))
    alumno_c = await usuario_id_de(db_session, await make_usuario(db_session))
    base = datetime.now(UTC)
    await crear_inscripcion(
        db_session, usuario_id=alumno_a, mesa=mesa,
        inscripto_en=base - timedelta(hours=3),
    )
    await crear_inscripcion(
        db_session, usuario_id=alumno_b, mesa=mesa, estado="anulado",
        inscripto_en=base - timedelta(hours=1),
    )
    ultima = await crear_inscripcion(
        db_session, usuario_id=alumno_c, mesa=mesa,
        inscripto_en=base - timedelta(hours=2),
    )

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    filas = resp.json()
    assert len(filas) == 3
    # Orden inscripto_en desc: la de -1h (anulada), luego -2h, luego -3h.
    assert [f["estado"] for f in filas] == ["anulado", "inscripto", "inscripto"]
    assert [f["id"] for f in filas][1] == str(ultima.id)
    assert set(filas[0].keys()) >= {
        "id", "usuario_id", "convocatoria_id", "mesa_examen_id",
        "materia_id", "condicion_id", "estado", "inscripto_en",
    }


async def test_inscripciones_gestion_filtra_por_mesa(app_client, db_session):
    """Filtro `mesa_id`: sólo las filas de esa mesa."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(
        db_session, permisos=("inscripcion.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mesa_a = await primera_mesa(db_session, conv, materias[0], condiciones[0])
    mesa_b = await db_session.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.convocatoria_id == conv,
            EsMesaExamen.materia_id == materias[1].id,
        )
    )
    alumno = await usuario_id_de(db_session, await make_usuario(db_session))
    fila_a = await crear_inscripcion(db_session, usuario_id=alumno, mesa=mesa_a)
    await crear_inscripcion(db_session, usuario_id=alumno, mesa=mesa_b)

    resp = await app_client.get(_URL, params={"mesa_id": str(mesa_a.id)}, headers=headers)
    assert resp.status_code == 200, resp.text
    filas = resp.json()
    assert len(filas) == 1
    assert filas[0]["id"] == str(fila_a.id)
    assert filas[0]["mesa_examen_id"] == str(mesa_a.id)


async def test_inscripciones_gestion_filtra_por_convocatoria(app_client, db_session):
    """Filtro `convocatoria_id`: sólo las filas de esa convocatoria."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    otra_conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mesa = await primera_mesa(db_session, conv, materias[0], condiciones[0])
    alumno = await usuario_id_de(db_session, await make_usuario(db_session))
    await crear_inscripcion(db_session, usuario_id=alumno, mesa=mesa)

    resp = await app_client.get(
        _URL, params={"convocatoria_id": str(otra_conv)}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []  # la convocatoria existe pero no tiene filas


async def test_inscripciones_gestion_mesa_inexistente_es_404(app_client, db_session):
    """Filtro `mesa_id` que referencia una mesa inexistente -> 404."""
    username = await make_usuario(db_session, permisos=("inscripcion.listar",))
    headers = await login(app_client, username)

    resp = await app_client.get(
        _URL, params={"mesa_id": str(uuid.uuid4())}, headers=headers
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-no-encontrada"


async def test_inscripciones_gestion_convocatoria_inexistente_es_404(
    app_client, db_session
):
    """Filtro `convocatoria_id` que referencia una convocatoria inexistente -> 404."""
    username = await make_usuario(db_session, permisos=("inscripcion.listar",))
    headers = await login(app_client, username)

    resp = await app_client.get(
        _URL, params={"convocatoria_id": str(uuid.uuid4())}, headers=headers
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"
