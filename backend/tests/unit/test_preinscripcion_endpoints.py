"""Endpoints públicos de preinscripción (analisis.txt §3.20-§3.21, PD-01).

Cubre: POST sin login con ventana vigente, 409 ventana-cerrada, upsert
RB-13 (201 creada / 200 actualizada, nunca 409 por documento repetido) y
422 con errors[] (PD-24). La preinscripción es ajena a las mesas: no
envía ni pide mesa_id.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.features.preinscripcion.models import PrPreinscripcion, PrVentana
from app.main import create_app


@pytest.fixture
def app(db_session):
    application = create_app()

    async def _override():
        yield db_session

    application.dependency_overrides[get_db] = _override
    return application


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _ventana(db, *, anio=2027, desde=None, hasta=None, activa=True):
    hoy = date.today()
    ventana = PrVentana(
        id=uuid.uuid4(),
        anio_lectivo=anio,
        descripcion=f"Preinscripción {anio}",
        fecha_desde=desde or (hoy - timedelta(days=1)),
        fecha_hasta=hasta or (hoy + timedelta(days=1)),
        activa=activa,
        created_at=datetime.now(UTC),
    )
    db.add(ventana)
    return ventana


_PAYLOAD = {
    "nombre_alumno": "Lucía Gómez",
    "documento": "45.123.456",
    "fecha_nacimiento": "2014-05-12",
    "orientacion": "Ciencias Sociales",
    "nombre_tutor": "María Gómez",
    "email": "maria.gomez@example.com",
}


async def _post(client, payload=None, query=""):
    return await client.post(
        f"/api/v1/preinscripcion/{query}", json=payload or _PAYLOAD
    )


async def test_post_crea_preinscripcion_sin_login(client, db_session):
    ventana = _ventana(db_session, anio=2027)
    await db_session.commit()

    resp = await _post(client, query="?utm_source=instagram&utm_medium=social")
    assert resp.status_code == 201
    # §6 y doc 11 §11.4.3: el cuerpo del upsert es SOLO { accion } — sin
    # campos extra (p. ej. mesa_id: la preinscripción es ajena a las mesas,
    # PD-01)
    assert resp.json() == {"accion": "creada"}

    fila = (
        await db_session.scalars(
            select(PrPreinscripcion).where(
                PrPreinscripcion.documento == _PAYLOAD["documento"]
            )
        )
    ).one()
    assert fila.nombre_alumno == "Lucía Gómez"
    assert fila.email == "maria.gomez@example.com"
    assert fila.anio_lectivo == 2027  # lo pone la ventana, no el cliente
    assert fila.estado == "pendiente"
    assert fila.utm_source == "instagram"
    assert fila.ip is not None  # metadata de servidor capturada
    assert ventana.anio_lectivo == 2027


async def test_post_ventana_cerrada_409(client, db_session):
    # No hay ventana vigente
    resp = await _post(client)
    assert resp.status_code == 409
    assert resp.json()["code"] == "ventana-cerrada"
    assert "errors" not in resp.json()  # errors[] sólo en 422 (PD-24)


async def test_post_ventana_fuera_de_rango_409(client, db_session):
    hoy = date.today()
    _ventana(db_session, desde=hoy + timedelta(days=10), hasta=hoy + timedelta(days=20))
    await db_session.commit()
    resp = await _post(client)
    assert resp.status_code == 409
    assert resp.json()["code"] == "ventana-cerrada"


async def test_post_reenvio_200_actualizada(client, db_session):
    """RB-13: reenviar el formulario actualiza, no duplica ni devuelve 409."""
    _ventana(db_session, anio=2027)
    await db_session.commit()
    assert (await _post(client)).status_code == 201

    fila = (
        await db_session.scalars(
            select(PrPreinscripcion).where(
                PrPreinscripcion.documento == _PAYLOAD["documento"]
            )
        )
    ).one()
    created_at_inicial = fila.created_at

    repetida = await _post(client, payload={**_PAYLOAD, "nombre_tutor": "Otro Tutor"})
    assert repetida.status_code == 200
    assert repetida.json() == {"accion": "actualizada"}

    filas = (
        await db_session.scalars(
            select(PrPreinscripcion).where(
                PrPreinscripcion.documento == _PAYLOAD["documento"]
            )
        )
    ).all()
    assert len(filas) == 1  # ninguna fila duplicada (RN-034)
    assert filas[0].nombre_tutor == "Otro Tutor"  # mutables actualizados
    assert filas[0].created_at == created_at_inicial  # conservado (doc 11 §11.4.1)


async def test_post_payload_invalido_422_con_errors(client, db_session):
    _ventana(db_session)
    await db_session.commit()
    invalido = {k: v for k, v in _PAYLOAD.items() if k != "fecha_nacimiento"}
    resp = await _post(client, payload=invalido)
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validacion"
    assert isinstance(body["errors"], list) and body["errors"]  # PD-24


async def test_post_email_invalido_422(client, db_session):
    _ventana(db_session)
    await db_session.commit()
    resp = await _post(client, payload={**_PAYLOAD, "email": "no-es-un-email"})
    assert resp.status_code == 422
    assert resp.json()["code"] == "validacion"
