"""T1 (S1) — Convocatorias SIGME: GET|POST|PATCH bajo /sigme/convocatorias.

Spec: odd/tasks/sdd-3-mesas-convocatorias.md, T1, S1.
RB-16, RB-17, RB-23 (límite inclusive por fecha de calendario BA).
Estado derivado doc 04 §4.1: borrador / abierta / cerrada (sin escritura).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME para los tests de convocatorias."""
    from datetime import UTC, datetime

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


async def test_convocatorias_requiere_auth(app_client):
    respuesta = await app_client.get("/api/v1/sigme/convocatorias")
    assert respuesta.status_code == 401


async def test_post_convocatoria_crea_y_devuelve_estado_derivado(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    hoy = date.today()
    payload = {
        "descripcion": "1er Cuatrimestre 2026",
        "fecha_inicio_inscripcion": (hoy + timedelta(days=1)).isoformat(),
        "fecha_fin_inscripcion": (hoy + timedelta(days=10)).isoformat(),
    }
    respuesta = await app_client.post(
        "/api/v1/sigme/convocatorias", json=payload, headers=headers
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["descripcion"] == "1er Cuatrimestre 2026"
    assert cuerpo["activa"] is True  # C-01: nace activa
    assert cuerpo["estado"] == "borrador"  # hoy < fecha_inicio

    # La lista la incluye.
    lista = await app_client.get("/api/v1/sigme/convocatorias", headers=headers)
    assert lista.status_code == 200
    assert any(item["id"] == cuerpo["id"] for item in lista.json())


async def test_post_convocatoria_ventana_invalida_es_422(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    hoy = date.today()
    payload = {
        "descripcion": "Invertida",
        "fecha_inicio_inscripcion": (hoy + timedelta(days=10)).isoformat(),
        "fecha_fin_inscripcion": (hoy + timedelta(days=1)).isoformat(),
    }
    respuesta = await app_client.post(
        "/api/v1/sigme/convocatorias", json=payload, headers=headers
    )
    assert respuesta.status_code == 422, respuesta.text
    cuerpo = respuesta.json()
    assert "errors" in cuerpo  # PD-24


async def test_estado_abierta_y_cerrada_derivados(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    hoy = date.today()
    abierta = await app_client.post(
        "/api/v1/sigme/convocatorias",
        json={
            "descripcion": "Abierta",
            "fecha_inicio_inscripcion": hoy.isoformat(),
            "fecha_fin_inscripcion": (hoy + timedelta(days=3)).isoformat(),
        },
        headers=headers,
    )
    assert abierta.status_code == 201, abierta.text
    assert abierta.json()["estado"] == "abierta"

    cerrada = await app_client.post(
        "/api/v1/sigme/convocatorias",
        json={
            "descripcion": "Cerrada",
            "fecha_inicio_inscripcion": (hoy - timedelta(days=10)).isoformat(),
            "fecha_fin_inscripcion": (hoy - timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )
    assert cerrada.status_code == 201, cerrada.text
    assert cerrada.json()["estado"] == "cerrada"


async def test_patch_edita_fechas_y_activa(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    hoy = date.today()
    creada = await app_client.post(
        "/api/v1/sigme/convocatorias",
        json={
            "descripcion": "Editable",
            "fecha_inicio_inscripcion": hoy.isoformat(),
            "fecha_fin_inscripcion": (hoy + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert creada.status_code == 201, creada.text
    convocatoria_id = creada.json()["id"]

    respuesta = await app_client.patch(
        f"/api/v1/sigme/convocatorias/{convocatoria_id}",
        json={
            "descripcion": "Editable v2",
            "fecha_fin_inscripcion": (hoy + timedelta(days=9)).isoformat(),
            "activa": False,
        },
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["descripcion"] == "Editable v2"
    assert cuerpo["activa"] is False
    assert cuerpo["estado"] == "borrador"  # C-05: activa=false


async def test_patch_con_id_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("usuario.gestionar",))
    headers = await login(app_client, username)
    respuesta = await app_client.patch(
        f"/api/v1/sigme/convocatorias/{uuid.uuid4()}",
        json={"descripcion": "nunca"},
        headers=headers,
    )
    assert respuesta.status_code == 404
