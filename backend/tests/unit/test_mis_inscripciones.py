"""T5 (S5) — Mis-inscripciones: GET y DELETE /api/v1/mis-inscripciones.

Spec: odd/tasks/sdd-4-inscripciones.md, T5, S5.
CU-38 (GET) + CU-39 (DELETE, INS-02; PD-25/PD-28; doc 06 §6.4/§6.5).
GET: permiso `inscripcion.listar`; sólo las filas del usuario autenticado;
para cada una: estado (`inscripto`/`anulado`), nombres de materia/condición,
`fecha` y `hora` de la mesa; nunca grupo (RN-019); sin paginación
(A-SDD4-9); la lectura sigue disponible con la ventana cerrada (RB-07).
DELETE: permiso `inscripcion.anular`; sólo la propia (de otro alumno o
inexistente -> 404 `inscripcion-no-encontrada`, sin filtrar existencia
ajena); sólo dentro de la ventana de ESA convocatoria (RB-08b/RB-07) ->
fuera -> 409 `ventana-cerrada`; `inscripto` -> `anulado` (fila conservada
para auditoría y libera la unicidad); ya `anulado` -> 204 idempotente sin
cuerpo (PD-25).
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

_URL = "/api/v1/mis-inscripciones"


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
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
    return conv.id


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=1):
    from app.features.catalogo.models import (
        EsCondicion,
        EsCurso,
        EsMateria,
        EsOrientacion,
    )

    orientacion = EsOrientacion(
        id=uuid.uuid4(), descripcion=f"Orientación {uuid.uuid4().hex[:6]}",
        activo=True, created_at=datetime.now(UTC),
    )
    curso = EsCurso(
        id=uuid.uuid4(), orientacion_id=orientacion.id, descripcion="3er Año",
        anio=3, activo=True, created_at=datetime.now(UTC),
    )
    db.add_all([orientacion, curso])
    await db.flush()
    materias = []
    for i in range(cant_materias):
        materia = EsMateria(
            id=uuid.uuid4(), curso_id=curso.id, descripcion=f"Materia {i}",
            es_taller=False, activo=True, created_at=datetime.now(UTC),
        )
        db.add(materia)
        materias.append(materia)
    condiciones = []
    for i in range(cant_condiciones):
        condicion = EsCondicion(
            id=uuid.uuid4(), descripcion=f"Condición {i} {uuid.uuid4().hex[:4]}",
            activo=True, created_at=datetime.now(UTC),
        )
        db.add(condicion)
        condiciones.append(condicion)
    await db.commit()
    return materias, condiciones


async def post_grupo(client, headers, conv, materias, condiciones,
                     fecha=None, hora="10:00", nombre=None):
    hoy = hoy_buenos_aires()
    payload = {
        "convocatoria_id": str(conv),
        "fecha": (fecha or (hoy + timedelta(days=20))).isoformat(),
        "hora": hora,
        "materias": [str(m.id) for m in materias],
        "condiciones": [str(c.id) for c in condiciones],
    }
    if nombre is not None:
        payload["nombre"] = nombre
    return await client.post("/api/v1/sigme/grupos", json=payload, headers=headers)


async def inscribir(client, headers, materia, condicion):
    return await client.post(
        "/api/v1/inscripciones",
        json={"materia_id": str(materia.id), "condicion_id": str(condicion.id)},
        headers=headers,
    )


_ALUMNO = ("inscripcion.listar", "inscripcion.crear", "inscripcion.anular", "mesa.crear")


# ---------------------------------------------------------------------------
# GET /mis-inscripciones (CU-38)
# ---------------------------------------------------------------------------


async def test_mis_inscripciones_sin_token_es_401(app_client):
    resp = await app_client.get(_URL)
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_mis_inscripciones_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_mis_inscripciones_solo_las_propias(app_client, db_session):
    """CU-38: sólo las filas del usuario autenticado, con nombres de
    materia/condición, fecha y hora de la mesa; nunca grupo (RN-019)."""
    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mia = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert mia.status_code == 201, mia.text

    # Otro alumno se inscribe a la MISMA materia (unicidad es por usuario).
    otro = await make_usuario(db_session, permisos=("inscripcion.crear",))
    otros_headers = await login(app_client, otro)
    suya = await inscribir(app_client, otros_headers, materias[0], condiciones[0])
    assert suya.status_code == 201, suya.text

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    filas = resp.json()
    assert len(filas) == 1  # sólo la mía, no la del otro alumno
    fila = filas[0]
    assert fila["id"] == mia.json()["id"]
    assert fila["estado"] == "inscripto"
    assert fila["materia_nombre"] == "Materia 0"
    assert fila["condicion_nombre"].startswith("Condición")
    assert fila["fecha"] is not None
    assert fila["hora"] is not None
    assert "grupo_id" not in fila
    assert "grupo" not in fila


async def test_mis_inscripciones_disponible_con_ventana_cerrada(app_client, db_session):
    """RB-07: la LECTURA de mis inscripciones sigue disponible con la ventana
    cerrada (T-03) — el endpoint no exige ventana."""
    from sqlalchemy import select

    from app.features.mesas.models import EsConvocatoria

    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mia = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert mia.status_code == 201, mia.text

    fila_conv = await db_session.scalar(
        select(EsConvocatoria).where(EsConvocatoria.id == conv)
    )
    fila_conv.fecha_fin_inscripcion = hoy_buenos_aires() - timedelta(days=3)
    await db_session.commit()

    resp = await app_client.get(_URL, headers=headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# DELETE /mis-inscripciones/{id} (CU-39 / INS-02)
# ---------------------------------------------------------------------------


async def test_anular_inscripcion_sin_token_es_401(app_client):
    resp = await app_client.delete(f"{_URL}/{uuid.uuid4()}")
    assert resp.status_code == 401, resp.text


async def test_anular_inscripcion_sin_permiso_es_403(app_client, db_session):
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await app_client.delete(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


async def test_anular_inscripcion_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)

    resp = await app_client.delete(f"{_URL}/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "inscripcion-no-encontrada"


async def test_anular_inscripcion_ajena_es_404(app_client, db_session):
    """Sólo la propia: la de otro alumno -> 404 (sin filtrar existencia ajena)."""
    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    otro = await make_usuario(db_session, permisos=("inscripcion.crear",))
    otros_headers = await login(app_client, otro)
    suya = await inscribir(app_client, otros_headers, materias[0], condiciones[0])
    assert suya.status_code == 201, suya.text

    resp = await app_client.delete(
        f"{_URL}/{suya.json()['id']}", headers=headers
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "inscripcion-no-encontrada"


async def test_anular_inscripcion_fuera_de_ventana_es_409(app_client, db_session):
    """RB-08b/RB-07: sólo dentro de la ventana de ESA convocatoria -> 409."""
    from sqlalchemy import select

    from app.features.mesas.models import EsConvocatoria

    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mia = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert mia.status_code == 201, mia.text

    fila_conv = await db_session.scalar(
        select(EsConvocatoria).where(EsConvocatoria.id == conv)
    )
    fila_conv.fecha_fin_inscripcion = hoy_buenos_aires() - timedelta(days=3)
    await db_session.commit()

    resp = await app_client.delete(f"{_URL}/{mia.json()['id']}", headers=headers)
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "ventana-cerrada"


async def test_anular_inscripcion_204_y_libera_unicidad(app_client, db_session):
    """`inscripto` -> `anulado` (fila conservada) y libera la unicidad:
    reinscribir tras anular crea una fila NUEVA."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaInscripcion

    username = await make_usuario(db_session, permisos=_ALUMNO)
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text
    mia = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert mia.status_code == 201, mia.text
    original_id = uuid.UUID(mia.json()["id"])

    resp = await app_client.delete(f"{_URL}/{original_id}", headers=headers)
    assert resp.status_code == 204, resp.text
    assert resp.content == b""  # sin cuerpo

    fila = await db_session.scalar(
        select(EsMesaInscripcion).where(EsMesaInscripcion.id == original_id)
    )
    assert fila.estado == "anulado"  # conservada para auditoría

    # Idempotente (PD-25): repetir -> 204 otra vez, sin duplicar.
    segunda = await app_client.delete(f"{_URL}/{original_id}", headers=headers)
    assert segunda.status_code == 204, segunda.text

    # La anulada libera la unicidad: reinscribir a la misma materia -> 201.
    reinscripcion = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert reinscripcion.status_code == 201, reinscripcion.text
    assert uuid.UUID(reinscripcion.json()["id"]) != original_id
