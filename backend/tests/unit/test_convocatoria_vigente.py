"""T1 (S1) — Convocatoria-vigente: GET /api/v1/convocatoria-vigente.

Spec: odd/tasks/sdd-4-inscripciones.md, T1, S1.
CU-34: sólo sesión válida (sin permiso ni módulo — L2: no discriminar por
dispositivo); devuelve la convocatoria vigente con estado DERIVADO y 404
`convocatoria-no-encontrada` sin activas (A-SDD4-1: abierta si existe; si no,
la activa más reciente por fecha_inicio).
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

_URL = "/api/v1/convocatoria-vigente"


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME (harness T1/T2/T3 de test_mesas)."""
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
        id=uuid.uuid4(), codigo=f"rol-{uuid.uuid4().hex[:8]}",
        descripcion="rol de test", activo=True, created_at=now,
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
    return conv.id  # UUID plano: evita ORM vencido tras commit


async def test_vigente_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_vigente_devuelve_abierta_sin_permisos(app_client, db_session):
    """CU-34: cualquier sesión válida (sin permisos ni módulo especial)."""
    conv_id = await crear_convocatoria(db_session)
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()
    assert cuerpo["id"] == str(conv_id)
    assert cuerpo["estado"] == "abierta"
    assert cuerpo["activa"] is True


async def test_vigente_prefiere_abierta_sobre_mas_reciente_cerrada(
    app_client, db_session
):
    """A-SDD4-1: abierta gana aunque otra activa sea más reciente."""
    hoy = hoy_buenos_aires()
    abierta_id = await crear_convocatoria(
        db_session,
        inicio=hoy - timedelta(days=30),
        fin=hoy + timedelta(days=10),
    )
    await crear_convocatoria(
        db_session,
        inicio=hoy - timedelta(days=5),
        fin=hoy - timedelta(days=2),  # vencida: la más reciente por inicio
    )
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(abierta_id)
    assert resp.json()["estado"] == "abierta"


async def test_vigente_sin_activas_es_404(app_client, db_session):
    """A-SDD4-1: sin convocatorias activas (vivas) → 404 con su code."""
    await crear_convocatoria(db_session, activa=False)  # borrador
    borrada_id = await crear_convocatoria(db_session)  # activa pero borrada
    from sqlalchemy import update

    from app.features.mesas.models import EsConvocatoria

    await db_session.execute(
        update(EsConvocatoria)
        .where(EsConvocatoria.id == borrada_id)
        .values(deleted_at=datetime.now(UTC))
    )
    await db_session.commit()
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"


async def test_vigente_muestra_cerrada_si_no_hay_abierta(app_client, db_session):
    """A-SDD4-1: fallback a la activa más reciente con su estado derivado."""
    hoy = hoy_buenos_aires()
    await crear_convocatoria(
        db_session,
        inicio=hoy - timedelta(days=20),
        fin=hoy - timedelta(days=3),
    )
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "cerrada"


async def test_vigente_no_expone_mesas_ni_grupo(app_client, db_session):
    """S1: la respuesta es sólo la convocatoria + estado derivado."""
    await crear_convocatoria(db_session)
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert set(resp.json()) == {
        "id",
        "descripcion",
        "fecha_inicio_inscripcion",
        "fecha_fin_inscripcion",
        "activa",
        "estado",
    }
