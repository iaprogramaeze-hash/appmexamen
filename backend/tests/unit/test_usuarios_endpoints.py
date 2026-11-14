"""Endpoints /api/v1/sigme/usuarios (SDD-2 S5; CU-09, analisis.txt §6).

POST crea usuario sobre persona existente con usuario.gestionar; username y
email únicos entre no borrados (409); política §2.5 (12 caracteres) en 422
errors[]. GET lista con roles por código; nunca password_hash.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.core.security import hash_password, verify_password
from app.features.personas.models import PeDocumentoTipo, PePersona
from app.features.usuarios.models import (
    UsModulo,
    UsPermiso,
    UsRol,
    UsRolPermiso,
    UsUsuario,
    UsUsuarioModulo,
    UsUsuarioRol,
)
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app

_PASSWORD = "clave-de-12-caracteres"


@pytest.fixture
def sigme_app(db_session):
    app = create_app()

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    return app


@pytest.fixture
async def client(sigme_app):
    transport = httpx.ASGITransport(app=sigme_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def make_gestor(db, *, permisos=("usuario.gestionar",)):
    """Usuario logueable con los permisos indicados (patrón test_rbac.py)."""
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
    username = f"gestor-{uuid.uuid4().hex[:8]}"
    user = UsUsuario(
        id=uuid.uuid4(), persona_id=uuid.uuid4(), username=username,
        password_hash=hash_password(_PASSWORD), activo=True, bloqueado=False,
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
    modulo = await db.scalar(select(UsModulo).where(UsModulo.codigo == "sigme_web"))
    db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo.id))
    for codigo in permisos:
        permiso = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db.commit()
    return username


async def login(client, username):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": _PASSWORD, "modulo": "sigme_web"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access']}"}


async def make_persona(db):
    tipo = PeDocumentoTipo(
        id=uuid.uuid4(), descripcion=f"DNI-{uuid.uuid4().hex[:6]}", orden=1,
        activo=True, created_at=datetime.now(UTC),
    )
    db.add(tipo)
    await db.flush()
    persona = PePersona(
        id=uuid.uuid4(), documento_tipo_id=tipo.id,
        documento=str(uuid.uuid4().int)[:8], apellido="Prueba",
        nombre="Usuario", nacionalidad="Argentino", created_at=datetime.now(UTC),
    )
    db.add(persona)
    await db.flush()
    return persona


async def test_post_usuarios_crea_201_y_persiste_hash(client, db_session):
    persona = await make_persona(db_session)
    headers = await login(client, await make_gestor(db_session))
    r = await client.post(
        "/api/v1/sigme/usuarios",
        headers=headers,
        json={
            "persona_id": str(persona.id), "username": "nuevo.usuario",
            "email": "nuevo@epet36.edu.ar", "password": _PASSWORD,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "nuevo.usuario"
    assert "password_hash" not in body
    # El hash persiste con el mismo algoritmo que auth (§2.5).
    row = await db_session.scalar(
        select(UsUsuario).where(UsUsuario.username == "nuevo.usuario")
    )
    assert verify_password(row.password_hash, _PASSWORD)


async def test_post_usuarios_username_duplicado_409(client, db_session):
    persona = await make_persona(db_session)
    headers = await login(client, await make_gestor(db_session))
    payload = {
        "persona_id": str(persona.id), "username": "duplicado",
        "password": _PASSWORD,
    }
    primero = await client.post(
        "/api/v1/sigme/usuarios", headers=headers, json=payload
    )
    assert primero.status_code == 201
    otra_persona = await make_persona(db_session)
    payload["persona_id"] = str(otra_persona.id)
    r = await client.post("/api/v1/sigme/usuarios", headers=headers, json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "username-existente"


async def test_post_usuarios_email_duplicado_409(client, db_session):
    persona = await make_persona(db_session)
    headers = await login(client, await make_gestor(db_session))
    payload = {
        "persona_id": str(persona.id), "username": "uno",
        "email": "duplicado@epet36.edu.ar", "password": _PASSWORD,
    }
    primero = await client.post(
        "/api/v1/sigme/usuarios", headers=headers, json=payload
    )
    assert primero.status_code == 201
    otra = await make_persona(db_session)
    payload["persona_id"] = str(otra.id)
    payload["username"] = "dos"
    r = await client.post("/api/v1/sigme/usuarios", headers=headers, json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "email-existente"


async def test_post_usuarios_persona_inexistente_404(client, db_session):
    headers = await login(client, await make_gestor(db_session))
    r = await client.post(
        "/api/v1/sigme/usuarios",
        headers=headers,
        json={
            "persona_id": str(uuid.uuid4()), "username": "huerfano",
            "password": _PASSWORD,
        },
    )
    assert r.status_code == 404
    assert r.json()["code"] == "persona-no-encontrada"


async def test_post_usuarios_clave_corta_422(client, db_session):
    persona = await make_persona(db_session)
    headers = await login(client, await make_gestor(db_session))
    r = await client.post(
        "/api/v1/sigme/usuarios",
        headers=headers,
        json={
            "persona_id": str(persona.id), "username": "corta",
            "password": "seis123",
        },
    )
    # §2.5: 12 caracteres mínimos; errors[] sólo en 422 (PD-24).
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validacion"
    assert body["errors"]


async def test_get_usuarios_lista_con_roles(client, db_session):
    persona = await make_persona(db_session)
    gestor = await make_gestor(db_session)
    headers = await login(client, gestor)
    await client.post(
        "/api/v1/sigme/usuarios",
        headers=headers,
        json={
            "persona_id": str(persona.id), "username": "listado",
            "password": _PASSWORD,
        },
    )
    r = await client.get("/api/v1/sigme/usuarios", headers=headers)
    assert r.status_code == 200
    usernames = {u["username"] for u in r.json()}
    assert {"listado", gestor} <= usernames
    for u in r.json():
        assert "password_hash" not in u
        assert isinstance(u["roles"], list)
