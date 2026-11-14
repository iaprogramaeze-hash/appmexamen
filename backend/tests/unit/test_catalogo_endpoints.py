"""Endpoints /api/v1/sigme del catálogo (SDD-2 S7; CU-05/CU-06, PD-02, PD-21).

4 colecciones (orientaciones, cursos, materias, condiciones):
- GET por módulo sigme_web (asunción A4, CU-05 "cualquier rol sigme_web").
- POST/PATCH por usuario.gestionar (asunción A1).
- PATCH cierra PD-02 (limite_materias editable) y resuelve PD-21 (agrega el
  PATCH a las 4 colecciones).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.core.security import hash_password
from app.features.catalogo.models import (
    EsCurso,
    EsMateria,
    EsOrientacion,
)
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


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
    username = f"user-{uuid.uuid4().hex[:8]}"
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
    for codigo in modulos:
        modulo = await db.scalar(select(UsModulo).where(UsModulo.codigo == codigo))
        db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo.id))
    for codigo in permisos:
        permiso = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    await db.commit()
    return username, modulos[0]


async def login(client, username, modulo="sigme_web"):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": _PASSWORD, "modulo": modulo},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access']}"}


async def make_orientacion(db, descripcion="Tec. Alimentos"):
    fila = EsOrientacion(
        id=uuid.uuid4(), descripcion=descripcion, activo=True,
        created_at=datetime.now(UTC),
    )
    db.add(fila)
    await db.flush()
    return fila


async def make_curso(db, orientacion, descripcion="1er Año", anio=1):
    fila = EsCurso(
        id=uuid.uuid4(), orientacion_id=orientacion.id, descripcion=descripcion,
        anio=anio, activo=True, created_at=datetime.now(UTC),
    )
    db.add(fila)
    await db.flush()
    return fila


# ---------------------------------------------------------------------------
# Lectura (A4: módulo sigme_web)
# ---------------------------------------------------------------------------
async def test_get_colecciones_lectura_por_modulo(client, db_session):
    await make_orientacion(db_session)
    username, modulo = await make_usuario(db_session)
    headers = await login(client, username, modulo)
    for coleccion in ("orientaciones", "cursos", "materias", "condiciones"):
        r = await client.get(f"/api/v1/sigme/{coleccion}", headers=headers)
        assert r.status_code == 200, coleccion


async def test_get_sin_modulo_sigme_web_403(client, db_session):
    username, _ = await make_usuario(db_session, modulos=("sigme_mobile",))
    headers = await login(client, username, modulo="sigme_mobile")
    r = await client.get("/api/v1/sigme/orientaciones", headers=headers)
    assert r.status_code == 403
    assert r.json()["code"] == "modulo-no-asignado"


async def test_get_cursos_filtra_por_orientacion(client, db_session):
    orientacion = await make_orientacion(db_session)
    otra = await make_orientacion(db_session, descripcion="Tec. Gestion")
    await make_curso(db_session, orientacion)
    await make_curso(db_session, otra, descripcion="2do Año", anio=2)
    username, modulo = await make_usuario(db_session)
    headers = await login(client, username, modulo)
    r = await client.get(
        f"/api/v1/sigme/cursos?orientacion_id={orientacion.id}", headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["descripcion"] == "1er Año"


# ---------------------------------------------------------------------------
# Escritura (A1: usuario.gestionar) + 409 por colección
# ---------------------------------------------------------------------------
async def test_post_orientacion_201_y_409(client, db_session):
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    r = await client.post(
        "/api/v1/sigme/orientaciones", headers=headers,
        json={"descripcion": "Tec. Alimentos"},
    )
    assert r.status_code == 201
    assert r.json()["descripcion"] == "Tec. Alimentos"
    r = await client.post(
        "/api/v1/sigme/orientaciones", headers=headers,
        json={"descripcion": "Tec. Alimentos"},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "orientacion-existente"


async def test_post_curso_fk_invalida_404(client, db_session):
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    r = await client.post(
        "/api/v1/sigme/cursos", headers=headers,
        json={"orientacion_id": str(uuid.uuid4()), "descripcion": "1er Año"},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "orientacion-no-encontrada"


async def test_post_materia_default_sin_taller(client, db_session):
    orientacion = await make_orientacion(db_session)
    curso = await make_curso(db_session, orientacion)
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    r = await client.post(
        "/api/v1/sigme/materias", headers=headers,
        json={"curso_id": str(curso.id), "descripcion": "Matematica"},
    )
    assert r.status_code == 201
    assert r.json()["es_taller"] is False  # RB-04 default
    r = await client.post(
        "/api/v1/sigme/materias", headers=headers,
        json={"curso_id": str(uuid.uuid4()), "descripcion": "Huerfana"},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "curso-no-encontrado"


async def test_post_condicion_y_patch_limite_pd02(client, db_session):
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    r = await client.post(
        "/api/v1/sigme/condiciones", headers=headers,
        json={"descripcion": "Regular", "limite_materias": 8},
    )
    assert r.status_code == 201
    condicion_id = r.json()["id"]
    # PD-02: limite_materias editable desde SIGME.
    r = await client.patch(
        f"/api/v1/sigme/condiciones/{condicion_id}", headers=headers,
        json={"limite_materias": 10},
    )
    assert r.status_code == 200
    assert r.json()["limite_materias"] == 10
    # NULL = sin límite (Libre).
    r = await client.patch(
        f"/api/v1/sigme/condiciones/{condicion_id}", headers=headers,
        json={"limite_materias": None},
    )
    assert r.status_code == 200
    assert r.json()["limite_materias"] is None


async def test_patch_colecciones_pd21(client, db_session):
    orientacion = await make_orientacion(db_session)
    curso = await make_curso(db_session, orientacion)
    materia = EsMateria(
        id=uuid.uuid4(), curso_id=curso.id, descripcion="Quimica",
        es_taller=False, activo=True, created_at=datetime.now(UTC),
    )
    db_session.add(materia)
    await db_session.flush()
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    # PD-21: PATCH agregado a las 4 colecciones.
    r = await client.patch(
        f"/api/v1/sigme/orientaciones/{orientacion.id}", headers=headers,
        json={"descripcion": "Tec. Alimentos y Bebidas"},
    )
    assert r.status_code == 200
    assert r.json()["descripcion"] == "Tec. Alimentos y Bebidas"
    r = await client.patch(
        f"/api/v1/sigme/cursos/{curso.id}", headers=headers,
        json={"descripcion": "Primero", "anio": 1},
    )
    assert r.status_code == 200
    assert r.json()["descripcion"] == "Primero"
    r = await client.patch(
        f"/api/v1/sigme/materias/{materia.id}", headers=headers,
        json={"es_taller": True},
    )
    assert r.status_code == 200
    assert r.json()["es_taller"] is True
    # RB-11: el renombre no toca nada más (aquí no hay mesas aún).


async def test_patch_condicion_no_encontrada_404(client, db_session):
    username, modulo = await make_usuario(
        db_session, permisos=("usuario.gestionar",)
    )
    headers = await login(client, username, modulo)
    r = await client.patch(
        f"/api/v1/sigme/condiciones/{uuid.uuid4()}", headers=headers,
        json={"limite_materias": 5},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "condicion-no-encontrada"


async def test_post_sin_permiso_403(client, db_session):
    username, modulo = await make_usuario(db_session)
    headers = await login(client, username, modulo)
    r = await client.post(
        "/api/v1/sigme/orientaciones", headers=headers,
        json={"descripcion": "Sin permiso"},
    )
    assert r.status_code == 403
    assert r.json()["code"] == "permiso-denegado"
