"""T2 (S2) — Ventanas de preinscripción SIGME: GET|POST bajo /sigme.

Spec: odd/tasks/sdd-3-mesas-convocatorias.md, T2, S2.
§6 declara SÓLO GET|POST (sin PATCH): el POST es un upsert por `anio_lectivo`
(CU-14 "abrir o cerrar la ventana vigente"). RN-035: nunca dos ventanas
vigentes a la vez — código propio `ventana-solapada` (A-SDD3-4). RB-23: la
vigencia se evalúa por fecha de calendario en America/Argentina/Buenos_Aires,
tanto en SIGME como en el chequeo del landing (`_ventana_activa`).
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
    """Usuario con sesión SIGME para los tests de ventanas (harness T1)."""
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


def _payload(anio=2027, *, desde=None, hasta=None, activa=True, **extra):
    hoy = date.today()
    datos = {
        "anio_lectivo": anio,
        "descripcion": f"Preinscripción {anio}",
        "fecha_desde": (desde or hoy - timedelta(days=1)).isoformat(),
        "fecha_hasta": (hasta or hoy + timedelta(days=1)).isoformat(),
        "activa": activa,
    }
    datos.update(extra)
    return datos


async def test_ventanas_requiere_auth(app_client):
    get = await app_client.get("/api/v1/sigme/ventanas-preinscripcion")
    post = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload()
    )
    assert get.status_code == 401
    assert post.status_code == 401


async def test_get_lista_vacia(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(
        "/api/v1/sigme/ventanas-preinscripcion", headers=headers
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == []


async def test_post_crea_ventana_y_devuelve_vigente(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2027),
        headers=headers,
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["anio_lectivo"] == 2027
    assert cuerpo["activa"] is True
    assert cuerpo["vigente"] is True  # su rango contiene hoy (límite inclusive)

    lista = await app_client.get(
        "/api/v1/sigme/ventanas-preinscripcion", headers=headers
    )
    assert lista.status_code == 200
    assert [item["anio_lectivo"] for item in lista.json()] == [2027]


async def test_post_mismo_anio_hace_upsert(app_client, db_session):
    """CU-14: con un sólo verbo declarado (POST), reenviar el mismo año
    actualiza la ventana existente en lugar de chocar con uq_ventana_anio."""
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    creada = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload(2027), headers=headers
    )
    assert creada.status_code == 201

    nueva_fecha = date.today() + timedelta(days=7)
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2027, desde=nueva_fecha, hasta=nueva_fecha + timedelta(days=2)),
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["id"] == creada.json()["id"]
    assert cuerpo["fecha_desde"] == nueva_fecha.isoformat()

    lista = await app_client.get(
        "/api/v1/sigme/ventanas-preinscripcion", headers=headers
    )
    assert len(lista.json()) == 1  # nunca duplica filas por año


async def test_cerrar_ventana_por_upsert(app_client, db_session):
    """CU-14: "cerrar la ventana vigente" = POST del mismo año con activa=false."""
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload(2027), headers=headers
    )
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2027, activa=False),
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["activa"] is False
    assert respuesta.json()["vigente"] is False


async def test_post_solapada_con_otra_activa_es_409(app_client, db_session):
    """RN-035: nunca dos ventanas vigentes a la vez (A-SDD3-4)."""
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload(2027), headers=headers
    )
    hoy = date.today()
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2028, desde=hoy, hasta=hoy + timedelta(days=5)),
        headers=headers,
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "ventana-solapada"


async def test_post_solape_sin_activa_no_conflicta(app_client, db_session):
    """Una ventana inactiva nunca puede ser vigente: su solape está permitido."""
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload(2027), headers=headers
    )
    hoy = date.today()
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2028, desde=hoy, hasta=hoy + timedelta(days=5), activa=False),
        headers=headers,
    )
    assert respuesta.status_code == 201, respuesta.text


async def test_post_fechas_invertidas_es_422(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    hoy = date.today()
    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion",
        json=_payload(2027, desde=hoy, hasta=hoy - timedelta(days=3)),
        headers=headers,
    )
    assert respuesta.status_code == 422, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["code"] == "validacion"
    assert any(
        error["field"] == "fecha_hasta" for error in cuerpo["errors"]
    ), cuerpo["errors"]


async def test_anio_en_borrado_logico_es_409(app_client, db_session):
    """uq_ventana_anio cuenta filas borradas: un año soft-deleted no se
    re-crea vía upsert (queda para una futura restauración, fuera de SDD-3)."""
    from app.features.preinscripcion.models import PrVentana

    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    borrada = PrVentana(
        id=uuid.uuid4(),
        anio_lectivo=2026,
        descripcion="Preinscripción 2026",
        fecha_desde=date.today() - timedelta(days=400),
        fecha_hasta=date.today() - timedelta(days=300),
        activa=False,
        created_at=datetime.now(UTC),
        deleted_at=datetime.now(UTC),
    )
    db_session.add(borrada)
    await db_session.commit()

    respuesta = await app_client.post(
        "/api/v1/sigme/ventanas-preinscripcion", json=_payload(2026), headers=headers
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "ventana-anio-existente"


async def test_landing_toma_hoy_desde_buenos_aires(
    app_client, db_session, monkeypatch
):
    """RB-23: el chequeo del landing usa la fecha de calendario BA, no la del
    servidor. Congelamos `hoy_buenos_aires` a 2030-01-15: con la ventana 2030
    vigente el POST anónimo pasa; con `date.today()` (2026) daría 409."""
    from sqlalchemy import select

    from app.features.preinscripcion.models import PrPreinscripcion, PrVentana

    monkeypatch.setattr(
        "app.features.preinscripcion.router.hoy_buenos_aires",
        lambda: date(2030, 1, 15),
    )
    ventana = PrVentana(
        id=uuid.uuid4(),
        anio_lectivo=2030,
        descripcion="Preinscripción 2030",
        fecha_desde=date(2030, 1, 1),
        fecha_hasta=date(2030, 1, 31),
        activa=True,
        created_at=datetime.now(UTC),
    )
    db_session.add(ventana)
    await db_session.commit()

    respuesta = await app_client.post(
        "/api/v1/preinscripcion/",
        json={
            "nombre_alumno": "Alumna De Prueba",
            "documento": "30.000.001",
            "fecha_nacimiento": "2015-03-02",
            "orientacion": "Ciencias Sociales",
            "nombre_tutor": "Tutora De Prueba",
            "email": "tutora@example.com",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json() == {"accion": "creada"}

    # el año lo pone la ventana vigente (2030), no el cliente (§6)
    fila = await db_session.scalar(
        select(PrPreinscripcion).where(PrPreinscripcion.documento == "30.000.001")
    )
    assert fila is not None and fila.anio_lectivo == 2030
