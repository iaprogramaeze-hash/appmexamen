"""T3 (S3) — Grupos de mesas SIGME: POST|PATCH|GET bajo /sigme.

Spec: odd/tasks/sdd-3-mesas-convocatorias.md, T3, S3.
CU-15 (POST /grupos, `mesa.crear`): crea el grupo y N = materias × condiciones
mesas en `planificada` con `grupo_id NOT NULL` (RB-28), copiando `fecha` y
`hora` del grupo (RB-29) y rellenando los 4 snapshots (GR-01/ME-01).
CU-16 (PATCH /grupos/{id}, `mesa.modificar`): mueve todas sus mesas en la
misma transacción (RB-29). PD-12 CERRADO: crear con ventana abierta está
permitido; mover con ventana abierta → 409 ventana-abierta.
CU-17 (GET /grupos?convocatoria_id=, `mesa.listar`).
`uq_grupo_unico` (convocatoria, fecha, hora) → 409 grupo-duplicado;
`uq_mesa_unica` (convocatoria, materia, condición, fecha) → 409
mesa-duplicada.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME para los tests de grupos (harness T1/T2)."""
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


async def crear_convocatoria(db, *, inicio=None, fin=None, activa=True):
    from app.features.mesas.models import EsConvocatoria

    hoy = date.today()
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
    return conv


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=2):
    """Orientación + curso + N materias + M condiciones activas."""
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
    hoy = date.today()
    payload = {
        "convocatoria_id": str(conv.id),
        "fecha": (fecha or (hoy + timedelta(days=20))).isoformat(),
        "hora": hora,
        "materias": [str(m.id) for m in materias],
        "condiciones": [str(c.id) for c in condiciones],
    }
    if nombre is not None:
        payload["nombre"] = nombre
    return await client.post("/api/v1/sigme/grupos", json=payload, headers=headers)


async def test_grupos_requiere_auth(app_client):
    get = await app_client.get(
        "/api/v1/sigme/grupos", params={"convocatoria_id": str(uuid.uuid4())}
    )
    post = await app_client.post("/api/v1/sigme/grupos", json={})
    patch = await app_client.patch(
        f"/api/v1/sigme/grupos/{uuid.uuid4()}", json={}
    )
    assert get.status_code == 401
    assert post.status_code == 401
    assert patch.status_code == 401


async def test_post_grupo_crea_mesas_en_bloque(app_client, db_session):
    """RB-28/GR-01: N = materias × condiciones mesas, todas con grupo_id,
    fecha/hora copiadas del grupo (RB-29) y snapshots rellenos."""
    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)

    respuesta = await post_grupo(
        app_client, headers, conv, materias, condiciones, nombre="Mañana"
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["convocatoria_id"] == str(conv.id)
    assert cuerpo["nombre"] == "Mañana"
    assert cuerpo["mesas_creadas"] == 4  # 2 × 2

    filas = (
        await db_session.execute(
            select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(cuerpo["id"]))
        )
    ).scalars().all()
    assert len(filas) == 4
    for mesa in filas:
        assert mesa.estado == "planificada"
        assert mesa.fecha.isoformat() == cuerpo["fecha"]
        assert mesa.hora == time(10, 0)
        # Los 4 snapshots rellenos desde el catálogo (ME-01).
        assert mesa.materia_nombre in {"Materia 0", "Materia 1"}
        assert mesa.curso_nombre == "3er Año"
        assert mesa.orientacion_nombre.startswith("Orientación")
        assert mesa.condicion_nombre.startswith("Condición")


async def test_post_grupo_requiere_mesa_crear(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session)
    respuesta = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert respuesta.status_code == 403


async def test_post_grupo_duplicado_es_409(app_client, db_session):
    """uq_grupo_unico: mismo (convocatoria, fecha, hora) → 409."""
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)

    primera = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert primera.status_code == 201
    segunda = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert segunda.status_code == 409, segunda.text
    assert segunda.json()["code"] == "grupo-duplicado"


async def test_post_grupo_mesa_ya_existente_es_409(app_client, db_session):
    """uq_mesa_unica: la materia × condición ya tiene mesa en la convocatoria
    ese día (otra franja horaria) → 409 mesa-duplicada."""
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)

    fecha = date.today() + timedelta(days=20)
    primera = await post_grupo(
        app_client, headers, conv, materias, condiciones, fecha=fecha, hora="10:00"
    )
    assert primera.status_code == 201
    segunda = await post_grupo(
        app_client, headers, conv, materias, condiciones, fecha=fecha, hora="18:00"
    )
    assert segunda.status_code == 409, segunda.text
    assert segunda.json()["code"] == "mesa-duplicada"


async def test_post_grupo_con_ventana_abierta_esta_permitido(app_client, db_session):
    """PD-12 CERRADO (crear sí): el alta es aditiva aunque la ventana de
    inscripción de la convocatoria esté abierta."""
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    hoy = date.today()
    conv = await crear_convocatoria(
        db_session, inicio=hoy - timedelta(days=1), fin=hoy + timedelta(days=1)
    )
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    respuesta = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert respuesta.status_code == 201, respuesta.text


async def test_post_grupo_convocatoria_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    fantasma = type("C", (), {"id": uuid.uuid4()})
    respuesta = await post_grupo(app_client, headers, fantasma, materias, condiciones)
    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "convocatoria-no-encontrada"


async def test_post_grupo_materia_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    _, condiciones = await crear_catalogo(db_session, cant_materias=1)
    fantasma = type("M", (), {"id": uuid.uuid4()})
    respuesta = await post_grupo(app_client, headers, conv, [fantasma], condiciones)
    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "materia-no-encontrada"


async def test_post_grupo_listas_vacias_es_422(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    _, condiciones = await crear_catalogo(db_session, cant_materias=1)
    respuesta = await post_grupo(app_client, headers, conv, [], condiciones)
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json()["code"] == "validacion"


async def test_patch_grupo_mueve_sus_mesas(app_client, db_session):
    """CU-16/RB-29: el PATCH mueve TODAS sus mesas en la misma transacción."""
    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(db_session, permisos=("mesa.crear", "mesa.modificar"))
    headers = await login(app_client, username)
    hoy = date.today()
    # Convocatoria con ventana CERRADA (PD-12: mover sólo tras el cierre).
    conv = await crear_convocatoria(
        db_session, inicio=hoy - timedelta(days=30), fin=hoy - timedelta(days=10)
    )
    materias, condiciones = await crear_catalogo(db_session)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201
    grupo_id = creada.json()["id"]

    nueva_fecha = hoy + timedelta(days=30)
    respuesta = await app_client.patch(
        f"/api/v1/sigme/grupos/{grupo_id}",
        json={"fecha": nueva_fecha.isoformat(), "hora": "18:30"},
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["fecha"] == nueva_fecha.isoformat()
    assert respuesta.json()["hora"] == "18:30:00"

    filas = (
        await db_session.execute(
            select(EsMesaExamen).where(EsMesaExamen.grupo_id == uuid.UUID(grupo_id))
        )
    ).scalars().all()
    assert len(filas) == 4
    for mesa in filas:
        assert mesa.fecha == nueva_fecha  # RB-29: copia sincronizada
        assert mesa.hora == time(18, 30)


async def test_patch_grupo_con_ventana_abierta_es_409(app_client, db_session):
    """PD-12 CERRADO (mover no): 409 ventana-abierta hasta que cierre."""
    username = await make_usuario(db_session, permisos=("mesa.crear", "mesa.modificar"))
    headers = await login(app_client, username)
    hoy = date.today()
    conv = await crear_convocatoria(
        db_session, inicio=hoy - timedelta(days=1), fin=hoy + timedelta(days=1)
    )
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201

    respuesta = await app_client.patch(
        f"/api/v1/sigme/grupos/{creada.json()['id']}",
        json={"fecha": (hoy + timedelta(days=30)).isoformat(), "hora": "18:00"},
        headers=headers,
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "ventana-abierta"


async def test_patch_grupo_duplicado_es_409(app_client, db_session):
    """Mover un grupo a la franja de OTRO grupo → 409 grupo-duplicado."""
    username = await make_usuario(db_session, permisos=("mesa.crear", "mesa.modificar"))
    headers = await login(app_client, username)
    hoy = date.today()
    conv = await crear_convocatoria(
        db_session, inicio=hoy - timedelta(days=30), fin=hoy - timedelta(days=10)
    )
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    # uq_mesa_unica no incluye la hora (PD-13): dos grupos del mismo día
    # coexisten sólo con materias distintas (franjas con materias distintas).
    materias_b, _ = await crear_catalogo(db_session, cant_materias=1)
    primera = await post_grupo(
        app_client, headers, conv, materias, condiciones, hora="10:00"
    )
    segunda = await post_grupo(
        app_client, headers, conv, materias_b, condiciones, hora="18:00"
    )
    assert segunda.status_code == 201

    respuesta = await app_client.patch(
        f"/api/v1/sigme/grupos/{segunda.json()['id']}",
        json={"fecha": primera.json()["fecha"], "hora": "10:00"},
        headers=headers,
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "grupo-duplicado"


async def test_patch_grupo_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.modificar",))
    headers = await login(app_client, username)
    hoy = date.today()
    respuesta = await app_client.patch(
        f"/api/v1/sigme/grupos/{uuid.uuid4()}",
        json={"fecha": hoy.isoformat(), "hora": "10:00"},
        headers=headers,
    )
    assert respuesta.status_code == 404, respuesta.text
    assert respuesta.json()["code"] == "grupo-no-encontrado"


async def test_get_grupos_por_convocatoria(app_client, db_session):
    """CU-17: lista los grupos de la convocatoria; 404 si la convocatoria
    no existe."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1)
    creada = await post_grupo(
        app_client, headers, conv, materias, condiciones, nombre="Tarde"
    )
    assert creada.status_code == 201

    respuesta = await app_client.get(
        "/api/v1/sigme/grupos",
        params={"convocatoria_id": str(conv.id)},
        headers=headers,
    )
    assert respuesta.status_code == 200, respuesta.text
    grupos = respuesta.json()
    assert len(grupos) == 1
    assert grupos[0]["nombre"] == "Tarde"
    assert grupos[0]["id"] == creada.json()["id"]

    fantasma = await app_client.get(
        "/api/v1/sigme/grupos",
        params={"convocatoria_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert fantasma.status_code == 404
    assert fantasma.json()["code"] == "convocatoria-no-encontrada"
