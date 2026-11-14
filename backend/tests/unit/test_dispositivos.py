"""T6 (S6) — Dispositivos: POST/GET/DELETE /api/v1/dispositivos.

Spec: odd/tasks/sdd-4-inscripciones.md, T6, S6.
Tabla nueva `es_dispositivo` + alembic 0004 (riesgo item 1). Upsert
idempotente por (usuario_id, device_id). Gate por SESIÓN VÁLIDA
(`get_current_principal`) — sin permiso extra; el usuario gestiona SUS
dispositivos. Soft delete en DELETE (idempotente). Push notifications fuera
de alcance SDD-4 (sólo la tabla).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest

from app.core.dependencies import get_db
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app

_URL = "/api/v1/dispositivos"


async def make_usuario(db, *, modulos=("sigme_web",)):
    from app.core.security import hash_password
    from app.features.usuarios.models import (
        UsRol,
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
    await db.commit()
    return username


def select_modulo(codigo):
    from sqlalchemy import select

    from app.features.usuarios.models import UsModulo
    return select(UsModulo).where(UsModulo.codigo == codigo)


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


async def post_dispositivo(app_client, headers, device_id, plataforma="android",
                           push_token=None):
    payload = {"device_id": device_id, "plataforma": plataforma}
    if push_token is not None:
        payload["push_token"] = push_token
    return await app_client.post(_URL, json=payload, headers=headers)


# ---------------------------------------------------------------------------
# Puertas: sesión
# ---------------------------------------------------------------------------


async def test_dispositivo_sin_token_es_401(app_client):
    resp = await app_client.post(_URL, json={"device_id": "abc", "plataforma": "android"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_dispositivo_listar_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text


async def test_dispositivo_delete_sin_token_es_401(app_client):
    resp = await app_client.delete(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# POST /dispositivos (upsert idempotente)
# ---------------------------------------------------------------------------


async def test_registrar_dispositivo_crea_nuevo(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    resp = await post_dispositivo(app_client, headers, "device-abc-123", "android", "token-push-1")
    assert resp.status_code == 201, resp.text
    cuerpo = resp.json()
    assert cuerpo["device_id"] == "device-abc-123"
    assert cuerpo["plataforma"] == "android"
    assert cuerpo["push_token"] == "token-push-1"
    assert cuerpo["activo"] is True


async def test_registrar_dispositivo_upsert_idempotente(app_client, db_session):
    """Mismo device_id -> actualiza (no duplica)."""
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    r1 = await post_dispositivo(app_client, headers, "device-abc-123", "android", "token-1")
    assert r1.status_code == 201, r1.text
    id_1 = r1.json()["id"]

    r2 = await post_dispositivo(app_client, headers, "device-abc-123", "ios", "token-2")
    assert r2.status_code == 201, r2.text  # 201 también en upsert (crea o actualiza)
    assert r2.json()["id"] == id_1  # MISMA fila
    assert r2.json()["plataforma"] == "ios"
    assert r2.json()["push_token"] == "token-2"

    # Listar: solo 1
    lista = await app_client.get(_URL, headers=headers)
    assert lista.status_code == 200, lista.text
    assert len(lista.json()) == 1


async def test_registrar_dispositivo_multiples_por_usuario(app_client, db_session):
    """Un usuario puede tener varios dispositivos (distintos device_id)."""
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    await post_dispositivo(app_client, headers, "device-1", "android")
    await post_dispositivo(app_client, headers, "device-2", "ios")
    await post_dispositivo(app_client, headers, "device-3", "web")

    lista = await app_client.get(_URL, headers=headers)
    assert lista.status_code == 200, lista.text
    assert len(lista.json()) == 3
    ids = {d["device_id"] for d in lista.json()}
    assert ids == {"device-1", "device-2", "device-3"}


async def test_registrar_dispositivo_aislamiento_entre_usuarios(app_client, db_session):
    """Mismo device_id para DOS usuarios -> filas distintas (unicidad por usuario)."""
    user1 = await make_usuario(db_session)
    h1 = await login(app_client, user1)
    user2 = await make_usuario(db_session)
    h2 = await login(app_client, user2)

    await post_dispositivo(app_client, h1, "shared-device", "android")
    await post_dispositivo(app_client, h2, "shared-device", "ios")

    l1 = await app_client.get(_URL, headers=h1)
    l2 = await app_client.get(_URL, headers=h2)
    assert len(l1.json()) == 1
    assert len(l2.json()) == 1
    assert l1.json()[0]["plataforma"] == "android"
    assert l2.json()[0]["plataforma"] == "ios"


async def test_registrar_dispositivo_campos_extra_422(app_client, db_session):
    """extra='forbid' en schema."""
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    resp = await app_client.post(
        _URL, json={"device_id": "abc", "plataforma": "android", "extra": "no"},
        headers=headers,
    )
    assert resp.status_code == 422, resp.text


# ---------------------------------------------------------------------------
# GET /dispositivos
# ---------------------------------------------------------------------------


async def test_listar_dispositivos_vacio(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


async def test_listar_dispositivos_orden_creado_desc(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    await post_dispositivo(app_client, headers, "device-1", "android")
    await post_dispositivo(app_client, headers, "device-2", "ios")

    lista = await app_client.get(_URL, headers=headers)
    assert lista.status_code == 200, lista.text
    assert len(lista.json()) == 2
    # Orden created_at desc: el último creado primero
    assert lista.json()[0]["device_id"] == "device-2"
    assert lista.json()[1]["device_id"] == "device-1"


# ---------------------------------------------------------------------------
# DELETE /dispositivos/{id} (soft delete idempotente)
# ---------------------------------------------------------------------------


async def test_dar_de_baja_dispositivo_204(app_client, db_session):
    from sqlalchemy import select

    from app.features.dispositivos.models import EsDispositivo

    username = await make_usuario(db_session)
    headers = await login(app_client, username)
    creado = await post_dispositivo(app_client, headers, "device-1", "android")
    assert creado.status_code == 201, creado.text
    did = creado.json()["id"]

    resp = await app_client.delete(f"{_URL}/{did}", headers=headers)
    assert resp.status_code == 204, resp.text
    assert resp.content == b""

    # Verifica soft delete en BD
    fila = await db_session.scalar(
        select(EsDispositivo).where(EsDispositivo.id == uuid.UUID(did))
    )
    assert fila is not None
    assert fila.deleted_at is not None
    assert fila.activo is False


async def test_dar_de_baja_dispositivo_idempotente(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)
    creado = await post_dispositivo(app_client, headers, "device-1", "android")
    did = creado.json()["id"]

    await app_client.delete(f"{_URL}/{did}", headers=headers)
    segunda = await app_client.delete(f"{_URL}/{did}", headers=headers)
    assert segunda.status_code == 204, segunda.text


async def test_dar_de_baja_dispositivo_inexistente_404(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)

    resp = await app_client.delete(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "dispositivo-no-encontrado"


async def test_dar_de_baja_dispositivo_ajeno_404(app_client, db_session):
    """Sólo los propios: dispositivo de otro usuario -> 404."""
    user1 = await make_usuario(db_session)
    h1 = await login(app_client, user1)
    user2 = await make_usuario(db_session)
    h2 = await login(app_client, user2)

    creado = await post_dispositivo(app_client, h1, "device-1", "android")
    did = creado.json()["id"]

    resp = await app_client.delete(f"{_URL}/{did}", headers=h2)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "dispositivo-no-encontrado"


async def test_dar_de_baja_dispositivo_ya_borrado_no_aparece_en_listar(app_client, db_session):
    username = await make_usuario(db_session)
    headers = await login(app_client, username)
    creado = await post_dispositivo(app_client, headers, "device-1", "android")
    did = creado.json()["id"]

    await app_client.delete(f"{_URL}/{did}", headers=headers)

    lista = await app_client.get(_URL, headers=headers)
    assert lista.status_code == 200, lista.text
    assert lista.json() == []