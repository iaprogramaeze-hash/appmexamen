"""T1 (S1) — Permiso de examen individual: GET /api/v1/reportes/permiso-examen/{usuario_id}.

Spec: odd/tasks/sdd-5-reportes.md, T1, S1.
CU-27 (doc 05 §5.9, doc 01 §2.4). Permiso `reporte.exportar`.
Reporte individual por alumno: mesas donde está inscripto (estado='inscripto',
deleted_at IS NULL), con fecha/hora de cada mesa (de su grupo) y snapshots
(RB-11). RB-22: solo mesas con inscripción activa. Orden fecha asc, hora asc.
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

_URL = "/api/v1/reportes/permiso-examen"


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",), rol_codigo="secretario"):
    """Usuario con sesión SIGME y rol/permisos."""
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
    # Usar codigo único para evitar UNIQUE constraint en tests
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


async def usuario_tiene_modulo(db, user_id, modulo_codigo):
    from sqlalchemy import select

    from app.features.usuarios.models import UsModulo, UsUsuarioModulo
    return await db.scalar(
        select(UsUsuarioModulo.usuario_id)
        .join(UsModulo, UsModulo.id == UsUsuarioModulo.modulo_id)
        .where(UsUsuarioModulo.usuario_id == user_id, UsModulo.codigo == modulo_codigo)
    ) is not None


# ---------------------------------------------------------------------------
# Puertas: sesión y permiso
# ---------------------------------------------------------------------------


async def test_permiso_examen_sin_token_es_401(app_client):
    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_permiso_examen_sin_permiso_es_403(app_client, db_session):
    """Sesión válida pero sin `reporte.exportar` -> 403."""
    username = await make_usuario(db_session, permisos=(), rol_codigo="alumno")
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_permiso_examen_alumno_sin_permiso_es_403(app_client, db_session):
    """Alumno (tiene modulo sigme_mobile) SIN reporte.exportar -> 403."""
    username = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    headers = await login(app_client, username, modulo="sigme_mobile")

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


# ---------------------------------------------------------------------------
# Validaciones de entrada
# ---------------------------------------------------------------------------


async def test_permiso_examen_usuario_inexistente_es_404(app_client, db_session):
    """usuario_id que no existe -> 404 usuario-no-encontrado."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "usuario-no-encontrado"


async def test_permiso_examen_usuario_no_alumno_es_404(app_client, db_session):
    """usuario_id existe pero NO es alumno (no tiene modulo sigme_mobile) -> 404."""

    # Crear usuario secretario (no alumno)
    username = await make_usuario(
        db_session, permisos=("reporte.exportar",), rol_codigo="secretario"
    )
    headers = await login(app_client, username)
    user_id = await usuario_id_de(db_session, username)

    # El user creado es secretario, no alumno (no tiene modulo sigme_mobile)
    # Verificar que no tiene sigme_mobile
    tiene_mobile = await usuario_tiene_modulo(db_session, user_id, "sigme_mobile")
    assert not tiene_mobile

    # Pedir reporte de ese mismo usuario (secretario)
    resp = await app_client.get(f"{_URL}/{user_id}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "usuario-no-es-alumno"


# ---------------------------------------------------------------------------
# Caso feliz
# ---------------------------------------------------------------------------


async def test_permiso_examen_ok_devuelve_mesas_con_snapshots(app_client, db_session):
    """Caso feliz: alumno con inscripciones -> reporte con mesas, snapshots,
    orden fecha asc, hora asc."""
    # Secretario pide el reporte
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    # Alumno que se inscribe
    alumno_user = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    alumno_id = await usuario_id_de(db_session, alumno_user)

    # Setup: convocatoria, catalogo, grupo, mesas
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

    # Inscribir alumno en ambas materias
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesas = list(mesas)
    assert len(mesas) == 2

    for mesa in mesas:
        await inscribir_alumno(db_session, alumno_user_id=alumno_id, mesa=mesa)

    # Pedir reporte
    resp = await app_client.get(f"{_URL}/{alumno_id}", headers=sec_headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()

    # Validar estructura
    assert cuerpo["usuario_id"] == str(alumno_id)
    assert cuerpo["convocatoria_id"] == str(conv)
    assert "convocatoria_descripcion" in cuerpo
    assert "mesas" in cuerpo
    assert len(cuerpo["mesas"]) == 2

    # Orden fecha asc, hora asc
    for i in range(len(cuerpo["mesas"]) - 1):
        a = cuerpo["mesas"][i]
        b = cuerpo["mesas"][i + 1]
        assert (a["fecha"], a["hora"] or "00:00") <= (b["fecha"], b["hora"] or "00:00")

    # Snapshots presentes
    for m in cuerpo["mesas"]:
        assert "mesa_id" in m
        assert "grupo_id" in m
        assert "fecha" in m
        assert "hora" in m
        assert "materia_id" in m
        assert "materia_nombre" in m
        assert "condicion_id" in m
        assert "condicion_nombre" in m
        assert "orientacion_nombre" in m
        assert "curso_nombre" in m


async def test_permiso_examen_rb22_solo_mesas_con_inscripcion_activa(app_client, db_session):
    """RB-22: solo mesas donde el alumno tiene inscripción ACTIVA (no anulada)."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    alumno_user = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    alumno_id = await usuario_id_de(db_session, alumno_user)

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

    # Inscribir en mesa 0 (activa)
    await inscribir_alumno(db_session, alumno_user_id=alumno_id, mesa=mesas[0], estado="inscripto")
    # Inscribir en mesa 1 (anulada)
    await inscribir_alumno(db_session, alumno_user_id=alumno_id, mesa=mesas[1], estado="anulado")

    resp = await app_client.get(f"{_URL}/{alumno_id}", headers=sec_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["mesas"]) == 1
    assert resp.json()["mesas"][0]["mesa_id"] == str(mesas[0].id)


async def test_permiso_examen_sin_inscripciones_devuelve_array_vacio(app_client, db_session):
    """Alumno sin inscripciones -> array mesas vacío (no 404)."""
    sec_user = await make_usuario(db_session, permisos=("reporte.exportar",))
    sec_headers = await login(app_client, sec_user)

    alumno_user = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    alumno_id = await usuario_id_de(db_session, alumno_user)

    await crear_convocatoria(db_session)

    resp = await app_client.get(f"{_URL}/{alumno_id}", headers=sec_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["mesas"] == []