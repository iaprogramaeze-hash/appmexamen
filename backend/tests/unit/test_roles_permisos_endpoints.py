"""Endpoints /api/v1/sigme/roles, /permisos y /modulos (SDD-2 S6; CU-10).

GET devuelve el catálogo cerrado (§2.7: 13 permisos, 3 módulos; roles de la
matriz §2.4). POST crea con {codigo, descripcion} y 409 codigo-existente.
Todo bajo usuario.gestionar (matriz doc02 §2.4).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
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
from app.features.usuarios.seed import seed_modulos, seed_permisos, seed_roles
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


async def test_get_roles_lista_catalogo_con_permisos(client, db_session):
    await seed_roles(db_session)
    headers = await login(client, await make_gestor(db_session))
    r = await client.get("/api/v1/sigme/roles", headers=headers)
    assert r.status_code == 200
    roles = {fila["codigo"]: fila["permisos"] for fila in r.json()}
    # Los 5 del seed (el rol del gestor de test también aparece en la lista).
    assert {
        "alumno", "secretario", "director", "administrador", "superadmin"
    } <= set(roles)
    assert "mesa.crear" in roles["secretario"]
    assert "mesa.crear" not in roles["director"]


async def test_get_permisos_y_modulos(client, db_session):
    headers = await login(client, await make_gestor(db_session))
    r = await client.get("/api/v1/sigme/permisos", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 13  # catálogo cerrado §2.7
    r = await client.get("/api/v1/sigme/modulos", headers=headers)
    assert r.status_code == 200
    assert {fila["codigo"] for fila in r.json()} == {
        "landing", "sigme_web", "sigme_mobile"
    }


async def test_post_rol_crea_201_y_duplicado_409(client, db_session):
    headers = await login(client, await make_gestor(db_session))
    r = await client.post(
        "/api/v1/sigme/roles", headers=headers,
        json={"codigo": "vigilante", "descripcion": "Vigilante"},
    )
    assert r.status_code == 201
    assert r.json()["codigo"] == "vigilante"
    r = await client.post(
        "/api/v1/sigme/roles", headers=headers,
        json={"codigo": "vigilante", "descripcion": "Otro"},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "codigo-existente"


async def test_post_rol_sin_permiso_403(client, db_session):
    headers = await login(client, await make_gestor(db_session, permisos=()))
    r = await client.post(
        "/api/v1/sigme/roles", headers=headers,
        json={"codigo": "nadie", "descripcion": "Sin permiso"},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "permiso-denegado"


async def test_post_modulo_crea_201(client, db_session):
    headers = await login(client, await make_gestor(db_session))
    r = await client.post(
        "/api/v1/sigme/modulos", headers=headers,
        json={"codigo": "kiosco", "descripcion": "Kiosco"},
    )
    assert r.status_code == 201
    assert r.json()["codigo"] == "kiosco"
    assert r.json()["activo"] is True  # default §3.10
