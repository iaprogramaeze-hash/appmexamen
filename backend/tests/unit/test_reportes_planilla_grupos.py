"""T5 (S5) — Planilla de grupos: GET /api/v1/reportes/planilla-grupos/{convocatoria_id}.

Spec: odd/tasks/sdd-5-reportes.md, T5, S5.
CU-30 (doc 05 §5.9, doc 01 §2.4 línea 76, RB-32). Permiso `reporte.exportar`.
Por convocatoria: cada grupo (fecha, hora) con sus mesas (materia, condición).
Vista de horario, NO detalle de alumnos. RB-22: solo grupos con al menos una
mesa con inscriptos activos. Confirmada 2026-10-04 para primera entrega.
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

_URL = "/api/v1/reportes/planilla-grupos"


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


async def test_planilla_sin_token_es_401(app_client):
    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_planilla_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=(), rol_codigo="alumno")
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_planilla_conv_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    resp = await app_client.get(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"


async def test_planilla_conv_borrada_es_404(app_client, db_session):
    """Convocatoria con deleted_at -> 404."""
    from datetime import UTC as _UTC

    from app.features.mesas.models import EsConvocatoria

    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv_id = await crear_convocatoria(db_session)
    conv = await db_session.get(EsConvocatoria, conv_id)
    conv.deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await app_client.get(f"{_URL}/{str(conv_id)}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"


# ---------------------------------------------------------------------------
# Caso feliz
# ---------------------------------------------------------------------------


async def test_planilla_ok_grupos_con_mesas(app_client, db_session):
    """Caso feliz: grupos ordenados por fecha/hora, cada uno con sus mesas."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )
    # Materias adicionales para el segundo grupo (evitar uq_mesa_unica)
    materias2, _ = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=2
    )
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Dos grupos en fechas distintas
    hoy = hoy_buenos_aires()
    g1 = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        fecha=hoy + timedelta(days=20), hora="09:00", nombre="Grupo Mañana"
    )
    assert g1.status_code == 201, g1.text
    g2 = await post_grupo(
        app_client, sec_headers, conv, materias2, condiciones,
        fecha=hoy + timedelta(days=21), hora="14:00", nombre="Grupo Tarde"
    )
    assert g2.status_code == 201, g2.text

    # Alumno inscrito en una mesa de cada grupo (para RB-22)
    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas_g1 = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(g1.json()["id"]))
    )
    mesas_g1 = list(mesas_g1)
    mesas_g2 = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(g2.json()["id"]))
    )
    mesas_g2 = list(mesas_g2)

    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas_g1[0])
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas_g2[0])

    resp = await app_client.get(f"{_URL}/{str(conv)}", headers=headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()

    assert cuerpo["convocatoria_id"] == str(conv)
    assert "convocatoria_descripcion" in cuerpo
    assert len(cuerpo["grupos"]) == 2

    # Orden por fecha asc, hora asc
    assert cuerpo["grupos"][0]["fecha"] <= cuerpo["grupos"][1]["fecha"]
    if cuerpo["grupos"][0]["fecha"] == cuerpo["grupos"][1]["fecha"]:
        assert cuerpo["grupos"][0]["hora"] <= cuerpo["grupos"][1]["hora"]

    # Cada grupo tiene sus mesas (solo las con inscriptos activos, RB-22)
    for grupo in cuerpo["grupos"]:
        assert "grupo_id" in grupo
        assert "fecha" in grupo
        assert "hora" in grupo
        assert "mesas" in grupo
        # El test inscribe solo en 1 mesa por grupo -> 1 mesa por grupo en la planilla
        assert len(grupo["mesas"]) == 1  # 1 mesa con inscripción activa por grupo (RB-22)

        for mesa in grupo["mesas"]:
            assert "mesa_id" in mesa
            assert "materia_id" in mesa
            assert "materia_nombre" in mesa
            assert "condicion_id" in mesa
            assert "condicion_nombre" in mesa


async def test_planilla_rb22_solo_grupos_con_inscriptos(app_client, db_session):
    """RB-22: solo grupos con al menos una mesa con inscriptos activos."""
    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    # Grupo 1: con inscripción
    g1 = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        nombre="Grupo Con Inscriptos"
    )
    assert g1.status_code == 201, g1.text
    # Grupo 2: SIN inscripciones
    g2 = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        fecha=hoy_buenos_aires() + timedelta(days=25), nombre="Grupo Sin Inscriptos"
    )
    assert g2.status_code == 201, g2.text

    # Alumno solo en grupo 1
    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen
    mesas_g1 = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(g1.json()["id"]))
    )
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=list(mesas_g1)[0])

    resp = await app_client.get(f"{_URL}/{str(conv)}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["grupos"]) == 1
    assert resp.json()["grupos"][0]["grupo_id"] == g1.json()["id"]


async def test_planilla_grupo_borrado_no_aparece(app_client, db_session):
    """Grupo con deleted_at no aparece en la planilla."""
    from datetime import UTC as _UTC

    from sqlalchemy import select

    from app.features.mesas.models import EsGrupoHorario

    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    g1 = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        nombre="Grupo 1"
    )
    assert g1.status_code == 201, g1.text

    # Borrar grupo
    grupo = await db_session.scalar(
        select(EsGrupoHorario).where(EsGrupoHorario.id == uuid.UUID(g1.json()["id"]))
    )
    grupo.deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await app_client.get(f"{_URL}/{str(conv)}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["grupos"] == []


async def test_planilla_mesa_borrada_no_aparece(app_client, db_session):
    """Mesa borrada no aparece en su grupo."""
    from datetime import UTC as _UTC

    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(db_session, permisos=("reporte.exportar",))
    headers = await login(app_client, username)

    conv = await crear_convocatoria(db_session)
    # 2 materias x 1 condicion = 2 mesas
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=2, cant_condiciones=1
    )
    sec_headers = await login(
        app_client,
        await make_usuario(db_session, permisos=("mesa.crear", "mesa.listar"))
    )
    g1 = await post_grupo(
        app_client, sec_headers, conv, materias, condiciones,
        nombre="Grupo 1"
    )
    assert g1.status_code == 201, g1.text

    # Alumno inscrito en mesa 0
    alumno = await make_usuario(
        db_session, permisos=(), modulos=("sigme_mobile",), rol_codigo="alumno"
    )
    a_id = await usuario_id_de(db_session, alumno)
    mesas = await db_session.scalars(
        select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(g1.json()["id"]))
    )
    mesas = list(mesas)
    await inscribir_alumno(db_session, alumno_user_id=a_id, mesa=mesas[0])

    # Borrar mesa 0 (la que tiene inscripción)
    mesas[0].deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await app_client.get(f"{_URL}/{str(conv)}", headers=headers)
    assert resp.status_code == 200, resp.text
    # El grupo NO aparece: mesa 0 tiene inscripción pero está borrada;
    # mesa 1 no borrada pero sin inscripción -> 0 mesas válidas (RB-22)
    assert resp.json()["grupos"] == []