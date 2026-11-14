"""RBAC: require_permiso / require_modulo y alcance de módulo (S6/S7).

S6 (§2.7): "Cada endpoint declara su permiso requerido vía dependencia de
FastAPI"; la decisión sale de los claims del token (§2.1: roles, permisos y
módulos viajan en el payload "para autorizar sin consulta").

S7 (§2.8): "El usuario sólo puede operar en los módulos que tiene asignados".
Vale para ENTRAR (login rechaza el módulo no asignado) y para OPERAR
(require_modulo en cada endpoint).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import Depends
from sqlalchemy import select

from app.core.dependencies import get_db
from app.core.security import hash_password
from app.features.auth.dependencies import require_modulo, require_permiso
from app.features.auth.tokens import Principal
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


async def make_usuario(
    db,
    *,
    username="docente",
    permisos=("mesa.listar",),
    modulos=("sigme_web",),
):
    """Usuario con rol, permisos y módulos asignados (§2.7/§2.8)."""
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
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
    rol_row = UsRol(
        id=uuid.uuid4(), codigo="rol-rbac", descripcion="rol de test", activo=True, created_at=now
    )
    db.add_all([user, rol_row])
    await db.flush()
    db.add(UsUsuarioRol(usuario_id=user.id, rol_id=rol_row.id))
    for codigo in modulos:
        modulo_row = await db.scalar(select(UsModulo).where(UsModulo.codigo == codigo))
        db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo_row.id))
    for codigo in permisos:
        permiso_row = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol_row.id, permiso_id=permiso_row.id))
    await db.commit()
    return user


@pytest.fixture
def rbac_app(db_session):
    """App real (con sus manejadores PD-24) + dos endpoints de prueba."""
    app = create_app()

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override

    @app.get("/prueba/permiso")
    async def _permiso(principal: Principal = Depends(require_permiso("mesa.crear"))):
        return {"sub": str(principal.sub)}

    @app.get("/prueba/modulo")
    async def _modulo(principal: Principal = Depends(require_modulo("sigme_mobile"))):
        return {"sub": str(principal.sub)}

    return app


@pytest.fixture
async def client(rbac_app):
    transport = httpx.ASGITransport(app=rbac_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _access(client, *, modulo="sigme_web"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "docente", "password": _PASSWORD, "modulo": modulo},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access"]


def _auth(access: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access}"}


# ---------------------------------------------------------------------------
# S6 — require_permiso (§2.7)
# ---------------------------------------------------------------------------
async def test_require_permiso_con_permiso_pasa(client, db_session):
    await make_usuario(db_session, permisos=("mesa.listar", "mesa.crear"))
    access = await _access(client)

    resp = await client.get("/prueba/permiso", headers=_auth(access))
    assert resp.status_code == 200


async def test_require_permiso_sin_permiso_403(client, db_session):
    await make_usuario(db_session, permisos=("mesa.listar",))
    access = await _access(client)

    resp = await client.get("/prueba/permiso", headers=_auth(access))
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == "permiso-denegado"
    assert "errors" not in body  # errors[] SÓLO en 422 (PD-24)


async def test_endpoints_protegidos_sin_token_401(client, db_session):
    await make_usuario(db_session)
    resp = await client.get("/prueba/permiso")
    assert resp.status_code == 401
    assert resp.json()["code"] == "no-autenticado"


# ---------------------------------------------------------------------------
# S7 — require_modulo (§2.8) y alcance del login
# ---------------------------------------------------------------------------
async def test_require_modulo_asignado_pasa(client, db_session):
    await make_usuario(db_session, modulos=("sigme_web", "sigme_mobile"))
    access = await _access(client)

    resp = await client.get("/prueba/modulo", headers=_auth(access))
    assert resp.status_code == 200


async def test_require_modulo_no_asignado_403(client, db_session):
    await make_usuario(db_session, modulos=("sigme_web",))
    access = await _access(client)

    resp = await client.get("/prueba/modulo", headers=_auth(access))
    assert resp.status_code == 403
    assert resp.json()["code"] == "modulo-no-asignado"


async def test_login_rechaza_modulo_no_asignado(client, db_session):
    user = await make_usuario(db_session, modulos=("sigme_web",))

    # Credenciales correctas pero módulo sin asignar: no se puede entrar (§2.8)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "docente", "password": _PASSWORD, "modulo": "sigme_mobile"},
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "modulo-no-asignado"

    # No es un fallo de credenciales: no cuenta para el rate limit (PD-27)
    await db_session.refresh(user)
    assert user.intentos_fallidos == 0

    # El módulo asignado sigue funcionando
    ok = await client.post(
        "/api/v1/auth/login",
        json={"username": "docente", "password": _PASSWORD, "modulo": "sigme_web"},
    )
    assert ok.status_code == 200
