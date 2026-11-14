"""T3 (S3) — Acta volante: GET /api/v1/reportes/acta-volante/{mesa_id}.

Spec: odd/tasks/sdd-5-reportes.md, T3, S3.
CU-28 (doc 05 §5.9, doc 01 §2.4 línea 75). Permiso `reporte.exportar`.
Reporte por mesa de una materia: todos los alumnos inscriptos en esa mesa
(estado='inscripto', deleted_at IS NULL). RB-22: mesa debe tener ≥ 1
inscripción activa -> si no, 404 `mesa-sin-inscriptos`. Devuelve snapshots
de la mesa (RB-11/19) y lista de alumnos con nombre, documento, materia,
condición.
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

_URL = "/api/v1/reportes/acta-volante"


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


async def test_acta_volante_sin_token_es_401(app_client):
    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_acta_volante_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=(), rol_codigo="alumno")
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_acta_volante_mesa_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-no-encontrada"


# ---------------------------------------------------------------------------
# RB-22: mesa sin inscriptos activos
# ---------------------------------------------------------------------------


async def test_acta_volante_mesa_sin_inscriptos_es_404(app_client, db_session):
    """Mesa existe pero sin inscriptos activos -> 404 mesa-sin-inscriptos."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
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
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-sin-inscriptos"


# ---------------------------------------------------------------------------
# Caso feliz
# ---------------------------------------------------------------------------


async def test_acta_volante_ok_devuelve_alumnos_con_snapshots(app_client, db_session):
    """Caso feliz: mesa con inscriptos -> acta con snapshots y lista de alumnos."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

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
        db_session, cant_materias=1, cant_condiciones=1
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
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    # Inscribir ambos alumnos
    await inscribir_alumno(db_session, alumno_user_id=a1_id, mesa=mesa)
    await inscribir_alumno(db_session, alumno_user_id=a2_id, mesa=mesa)

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()

    # Validar estructura
    assert cuerpo["mesa_id"] == str(mesa.id)
    assert cuerpo["grupo_id"] == str(mesa.grupo_id)
    assert cuerpo["fecha"] is not None
    assert cuerpo["hora"] is not None
    assert cuerpo["materia_id"] == str(materias[0].id)
    assert cuerpo["materia_nombre"] == materias[0].descripcion  # snapshot
    assert cuerpo["condicion_id"] == str(condiciones[0].id)
    assert cuerpo["condicion_nombre"] == condiciones[0].descripcion
    assert "orientacion_nombre" in cuerpo
    assert "curso_nombre" in cuerpo

    # Alumnos
    assert len(cuerpo["alumnos"]) == 2
    for alumno in cuerpo["alumnos"]:
        assert "usuario_id" in alumno
        assert "username" in alumno
        assert "persona_documento" in alumno  # vacío por ahora
        assert alumno["materia_nombre"] == materias[0].descripcion
        assert alumno["condicion_nombre"] == condiciones[0].descripcion


async def test_acta_volante_rb22_solo_inscriptos_activos(app_client, db_session):
    """RB-22: solo inscriptos activos (no anulados) aparecen en el acta."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

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
        db_session, cant_materias=1, cant_condiciones=1
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
    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )

    # Alumno 1 activo, alumno 2 anulado
    await inscribir_alumno(db_session, alumno_user_id=a1_id, mesa=mesa, estado="inscripto")
    await inscribir_alumno(db_session, alumno_user_id=a2_id, mesa=mesa, estado="anulado")

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["alumnos"]) == 1
    assert resp.json()["alumnos"][0]["usuario_id"] == str(a1_id)


async def test_acta_volante_mesa_borrada_es_404(app_client, db_session):
    """Mesa con deleted_at -> 404."""
    from datetime import UTC as _UTC

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    sec_headers_grupo = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    creada = await post_grupo(
        app_client, sec_headers_grupo, conv, materias, condiciones
    )
    assert creada.status_code == 201, creada.text

    mesa = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.convocatoria_id == conv)
    )
    mesa.deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await app_client.get(f"{_URL}/{mesa.id}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "mesa-no-encontrada"