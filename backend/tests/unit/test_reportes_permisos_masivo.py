"""T2 (S2) — Permisos de examen masivo: GET /api/v1/reportes/permisos-examen.

Spec: odd/tasks/sdd-5-reportes.md, T2, S2.
CU-27 (doc 05 §5.9). Permiso `reporte.exportar`. Impresión masiva: agrupa
TODOS los permisos de la convocatoria por mesa. Para cada mesa con inscriptos
activos (RB-22), lista alumnos con sus materias/condiciones.
`convocatoria_id` opcional (por defecto la vigente/activa).
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

_URL = "/api/v1/reportes/permisos-examen"


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


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=1):
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


async def inscribir_alumno(db, *, alumno_user_id, mesa, estado="inscripto"):
    from app.features.mesas.models import EsMesaInscripcion
    ahora = datetime.now(UTC)
    ins = EsMesaInscripcion(
        id=uuid.uuid4(),
        usuario_id=alumno_user_id,
        mesa_examen_id=mesa.id,
        convocatoria_id=mesa.convocatoria_id,
        materia_id=mesa.materia_id,
        condicion_id=mesa.condicion_id,
        estado=estado,
        inscripto_en=ahora,
        created_at=ahora,
    )
    db.add(ins)
    await db.commit()
    return ins


async def usuario_id_de(db, username):
    from sqlalchemy import select

    from app.features.usuarios.models import UsUsuario
    return await db.scalar(select(UsUsuario.id).where(UsUsuario.username == username))


# ---------------------------------------------------------------------------
# Puertas: sesión y permiso
# ---------------------------------------------------------------------------


async def test_permisos_masivo_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_permisos_masivo_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=(), rol_codigo="alumno")
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_permisos_masivo_conv_inexistente_es_404(app_client, db_session):
    """convocatoria_id que no existe -> 404."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    resp = await app_client.get(
        _URL, params={"convocatoria_id": str(uuid.uuid4())}, headers=headers
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"


# ---------------------------------------------------------------------------
# Caso feliz
# ---------------------------------------------------------------------------


async def test_permisos_masivo_ok_agrupa_por_mesa(app_client, db_session):
    """Caso feliz: agrupa por mesa, lista alumnos con materias/condiciones."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    # Dos alumnos
    alumno1 = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    alumno2 = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a1_id = await usuario_id_de(db_session, alumno1)
    a2_id = await usuario_id_de(db_session, alumno2)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=1
    )
    sec_headers_grupo = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    creada = await post_grupo(
        app_client, sec_headers_grupo, conv, materias, condiciones, nombre="Grupo 1"
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesas = list(mesas)
    assert len(mesas) == 2

    # Alumno 1 en mesa 0
    await inscribir_alumno(db_session, alumno_user_id=a1_id, mesa=mesas[0])
    # Alumno 2 en mesa 1
    await inscribir_alumno(db_session, alumno_user_id=a2_id, mesa=mesas[1])

    resp = await app_client.get(_URL, headers=sec_headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()

    assert cuerpo["convocatoria_id"] == str(conv)
    assert "convocatoria_descripcion" in cuerpo
    assert len(cuerpo["mesas"]) == 2

    # Cada mesa tiene sus alumnos
    mesa0 = next(m for m in cuerpo["mesas"] if m["mesa_id"] == str(mesas[0].id))
    mesa1 = next(m for m in cuerpo["mesas"] if m["mesa_id"] == str(mesas[1].id))

    assert len(mesa0["alumnos"]) == 1
    assert mesa0["alumnos"][0]["usuario_id"] == str(a1_id)
    assert len(mesa0["alumnos"][0]["materias"]) == 1

    assert len(mesa1["alumnos"]) == 1
    assert mesa1["alumnos"][0]["usuario_id"] == str(a2_id)


async def test_permisos_masivo_rb22_solo_mesas_con_inscriptos(app_client, db_session):
    """RB-22: solo mesas con ≥ 1 inscripción activa aparecen."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=1
    )
    sec_headers_grupo = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    creada = await post_grupo(
        app_client, sec_headers_grupo, conv, materias, condiciones, nombre="Grupo 1"
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesas = list(mesas)

    # Solo inscripción en mesa 0
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas[0])
    # Mesa 1 sin inscripciones

    resp = await app_client.get(_URL, headers=sec_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["mesas"]) == 1
    assert resp.json()["mesas"][0]["mesa_id"] == str(mesas[0].id)


async def test_permisos_masivo_conv_param_usada(app_client, db_session):
    """Si se pasa convocatoria_id, se usa esa (no la vigente)."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    conv1 = await crear_convocatoria(db_session)
    conv2 = await crear_convocatoria(db_session, inicio=None, fin=None)

    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    sec_headers_grupo = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Grupo solo en conv2
    creada = await post_grupo(
        app_client, sec_headers_grupo, conv2, materias, condiciones
    )
    assert creada.status_code == 201, creada.text

    # Alumno inscrito en conv2
    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv2)
    )
    mesas = list(mesas)
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas[0])

    # Pedir reporte de conv1 (sin grupos) -> 0 mesas
    resp = await app_client.get(_URL, params={"convocatoria_id": str(conv1)}, headers=sec_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["mesas"] == []

    # Pedir reporte de conv2 -> 1 mesa
    resp = await app_client.get(_URL, params={"convocatoria_id": str(conv2)}, headers=sec_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["mesas"]) == 1


async def test_permisos_masivo_alumno_en_varias_mesas(app_client, db_session):
    """Un alumno puede aparecer en varias mesas (materias distintas)."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=1
    )
    sec_headers_grupo = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    creada = await post_grupo(
        app_client, sec_headers_grupo, conv, materias, condiciones
    )
    assert creada.status_code == 201, creada.text

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesas = list(mesas)

    # Mismo alumno en ambas mesas
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas[0])
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas[1])

    resp = await app_client.get(_URL, headers=sec_headers)
    assert resp.status_code == 200, resp.text
    mesas_resp = resp.json()["mesas"]

    # El alumno aparece en ambas mesas
    for m in mesas_resp:
        assert len(m["alumnos"]) == 1
        assert m["alumnos"][0]["usuario_id"] == str(a_id)
        assert len(m["alumnos"][0]["materias"]) == 1