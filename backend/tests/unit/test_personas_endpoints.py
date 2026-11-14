"""Endpoints /api/v1/sigme/personas (SDD-2, S4; analisis.txt §6 y CU-07/CU-08).

GET lista y por id con persona.listar; POST con usuario.gestionar y 409
persona-duplicada; PATCH con persona.modificar e identidad inmutable (A2).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.core.security import hash_password
from app.features.personas.models import PeDocumentoTipo, PePersona
from app.features.usuarios.models import UsRol, UsUsuario, UsUsuarioModulo, UsUsuarioRol
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


async def make_usuario_sigme(db, *, permisos=("persona.listar",)):
    """Usuario con sesión vigente y los permisos indicados (§2.7).

    Loguea por el endpoint real: el access nace con los claims completos y
    la sesión queda registrada (patrón de test_rbac.py).
    """
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
    username = f"user-{uuid.uuid4().hex[:8]}"
    user = UsUsuario(
        id=uuid.uuid4(),
        persona_id=uuid.uuid4(),
        username=username,
        password_hash=hash_password(_PASSWORD),
        activo=True,
        bloqueado=False,
        intentos_fallidos=0,
        token_version=1,
        password_changed_at=now,
        created_at=now,
    )
    rol = UsRol(
        id=uuid.uuid4(), codigo=f"rol-{uuid.uuid4().hex[:8]}",
        descripcion="rol de test", activo=True, created_at=now,
    )
    db.add_all([user, rol])
    await db.flush()
    db.add(UsUsuarioRol(usuario_id=user.id, rol_id=rol.id))
    from app.features.usuarios.models import UsModulo, UsPermiso, UsRolPermiso

    modulo = await db.scalar(select(UsModulo).where(UsModulo.codigo == "sigme_web"))
    db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo.id))
    for codigo in permisos:
        permiso = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db.commit()
    return username


async def login(client, username):
    """Access token por el endpoint real (crea la sesión vigente)."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": _PASSWORD, "modulo": "sigme_web"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access']}"}


async def make_tipo_documento(db, descripcion="DNI"):
    tipo = PeDocumentoTipo(
        id=uuid.uuid4(), descripcion=descripcion, orden=1, activo=True,
        created_at=datetime.now(UTC),
    )
    db.add(tipo)
    await db.flush()
    return tipo


async def make_persona(db, tipo, *, documento="12345678", apellido="Perez",
                       nombre="Ana", **extra):
    persona = PePersona(
        id=uuid.uuid4(), documento_tipo_id=tipo.id, documento=documento,
        apellido=apellido, nombre=nombre, nacionalidad="Argentino",
        created_at=datetime.now(UTC), **extra,
    )
    db.add(persona)
    await db.flush()
    return persona


async def test_get_personas_requiere_permiso_listar(client, db_session):
    username = await make_usuario_sigme(db_session, permisos=())
    headers = await login(client, username)
    r = await client.get("/api/v1/sigme/personas", headers=headers)
    assert r.status_code == 403
    assert r.json()["code"] == "permiso-denegado"


async def test_get_personas_lista_y_filtra(client, db_session):
    tipo = await make_tipo_documento(db_session)
    await make_persona(db_session, tipo, documento="11111111", apellido="Gomez")
    await make_persona(db_session, tipo, documento="22222222", apellido="Lopez")
    headers = await login(client, await make_usuario_sigme(db_session))

    r = await client.get("/api/v1/sigme/personas", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = await client.get("/api/v1/sigme/personas?q=Gomez", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["apellido"] == "Gomez"
    assert "password_hash" not in body[0]


async def test_get_personas_por_id_404(client, db_session):
    headers = await login(client, await make_usuario_sigme(db_session))
    r = await client.get(f"/api/v1/sigme/personas/{uuid.uuid4()}", headers=headers)
    assert r.status_code == 404
    assert r.json()["code"] == "persona-no-encontrada"


async def test_post_personas_crea_201(client, db_session):
    tipo = await make_tipo_documento(db_session)
    headers = await login(
        client, await make_usuario_sigme(db_session, permisos=("usuario.gestionar",))
    )
    r = await client.post(
        "/api/v1/sigme/personas",
        headers=headers,
        json={
            "documento_tipo_id": str(tipo.id), "documento": "33333333",
            "apellido": "Sanchez", "nombre": "Luis",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["apellido"] == "Sanchez"
    assert body["nacionalidad"] == "Argentino"  # default §3.2


async def test_post_personas_duplicada_409(client, db_session):
    tipo = await make_tipo_documento(db_session)
    await make_persona(db_session, tipo, documento="44444444")
    headers = await login(
        client, await make_usuario_sigme(db_session, permisos=("usuario.gestionar",))
    )
    r = await client.post(
        "/api/v1/sigme/personas",
        headers=headers,
        json={
            "documento_tipo_id": str(tipo.id), "documento": "44444444",
            "apellido": "Otra", "nombre": "Persona",
        },
    )
    assert r.status_code == 409
    assert r.json()["code"] == "persona-duplicada"


async def test_post_personas_tipo_inexistente_422(client, db_session):
    headers = await login(
        client, await make_usuario_sigme(db_session, permisos=("usuario.gestionar",))
    )
    r = await client.post(
        "/api/v1/sigme/personas",
        headers=headers,
        json={
            "documento_tipo_id": str(uuid.uuid4()), "documento": "55555555",
            "apellido": "Fantasma", "nombre": "Sin",
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "documento-tipo-invalido"


async def test_patch_personas_modifica_campos_mutables(client, db_session):
    tipo = await make_tipo_documento(db_session)
    persona = await make_persona(db_session, tipo)
    headers = await login(
        client, await make_usuario_sigme(db_session, permisos=("persona.modificar",))
    )
    r = await client.patch(
        f"/api/v1/sigme/personas/{persona.id}",
        headers=headers,
        json={"apellido": "Corregido", "direccion": "Av. Siempreviva 742"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["apellido"] == "Corregido"
    assert body["direccion"] == "Av. Siempreviva 742"
    assert body["documento"] == persona.documento  # identidad intacta


async def test_patch_personas_no_toca_identidad(client, db_session):
    tipo = await make_tipo_documento(db_session)
    persona = await make_persona(db_session, tipo)
    headers = await login(
        client, await make_usuario_sigme(db_session, permisos=("persona.modificar",))
    )
    r = await client.patch(
        f"/api/v1/sigme/personas/{persona.id}",
        headers=headers,
        json={"documento": "99999999"},
    )
    # A2: identidad inmutable; el campo se ignora sin romper la operación.
    assert r.status_code == 200
    assert r.json()["documento"] == persona.documento
