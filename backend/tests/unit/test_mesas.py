"""T4 (S4) — Mesas SIGME: GET listado/detalle/por-fecha y PATCH asignación.

Spec: odd/tasks/sdd-3-mesas-convocatorias.md, T4, S4.
CU-19 (lecturas, `mesa.listar`): RB-22 en las 3 operaciones — sólo mesas con
AL MENOS UNA INSCRIPCIÓN ACTIVA (`estado='inscripto'`, `deleted_at IS NULL`);
las mesas VENCIDAS dejan de listarse en SIGME (7 fuentes, L11a) en
`GET /mesas` y `por-fecha`; el detalle por id sí las muestra con estado
DERIVADO (ME-03/ME-04 constatan al leer sin escritura; A-SDD3-6: vencida →
`cerrada`). `por-fecha` exige `desde`/`hasta` con rango inclusive (RB-23).
CU-20 (PATCH asignación, `mesa.modificar`): cambia materia/condición
recalculando los 4 snapshots en la MISMA transacción (RB-11), respeta
`uq_mesa_unica` → 409, `extra="forbid"` (fecha/hora son del grupo, RB-29),
sin gate temporal (CU-20 no declara ventana) y sin filtro RB-22 (escritura
sobre fila existente).
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.dependencies import get_db
from app.features.usuarios.seed import seed_modulos, seed_permisos
from app.main import create_app


async def make_usuario(db, *, permisos=(), modulos=("sigme_web",)):
    """Usuario con sesión SIGME para los tests de mesas (harness T1/T2/T3)."""
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


async def dar_vida(db, mesa):
    """RB-22: inscripción ACTIVA que da 'vida' a la mesa (usuario nuevo por
    llamada para no tropezar con uq_inscripcion_unica)."""
    from app.core.security import hash_password
    from app.features.mesas.models import EsMesaInscripcion
    from app.features.usuarios.models import UsUsuario

    ahora = datetime.now(UTC)
    usuario = UsUsuario(
        id=uuid.uuid4(), persona_id=uuid.uuid4(),
        username=f"alu-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("cl4ve-S3gura."), activo=True,
        bloqueado=False, intentos_fallidos=0, token_version=1,
        password_changed_at=ahora, created_at=ahora,
    )
    db.add(usuario)
    await db.flush()
    db.add(
        EsMesaInscripcion(
            id=uuid.uuid4(), usuario_id=usuario.id,
            mesa_examen_id=mesa.id, convocatoria_id=mesa.convocatoria_id,
            materia_id=mesa.materia_id, condicion_id=mesa.condicion_id,
            estado="inscripto", inscripto_en=ahora, created_at=ahora,
        )
    )
    await db.commit()
    return mesa


async def mesas_de(db, *, grupo_id=None, convocatoria_id=None):
    from app.features.mesas.models import EsMesaExamen

    consulta = select(EsMesaExamen)
    if grupo_id is not None:
        consulta = consulta.where(EsMesaExamen.grupo_id == grupo_id)
    if convocatoria_id is not None:
        consulta = consulta.where(EsMesaExamen.convocatoria_id == convocatoria_id)
    return list((await db.execute(consulta)).scalars().all())


async def test_mesas_requiere_auth(app_client):
    get_listado = await app_client.get("/api/v1/sigme/mesas")
    get_detalle = await app_client.get(f"/api/v1/sigme/mesas/{uuid.uuid4()}")
    get_fecha = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha",
        params={"desde": "2026-01-01", "hasta": "2026-12-31"},
    )
    patch = await app_client.patch(f"/api/v1/sigme/mesas/{uuid.uuid4()}", json={})
    assert get_listado.status_code == 401
    assert get_detalle.status_code == 401
    assert get_fecha.status_code == 401
    assert patch.status_code == 401


async def test_get_mesas_requiere_mesa_listar(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.crear",))
    headers = await login(app_client, username)
    respuesta = await app_client.get("/api/v1/sigme/mesas", headers=headers)
    assert respuesta.status_code == 403


async def test_patch_mesa_requiere_mesa_modificar(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    respuesta = await app_client.patch(
        f"/api/v1/sigme/mesas/{uuid.uuid4()}", json={}, headers=headers
    )
    assert respuesta.status_code == 403


async def test_get_mesas_rb22_oculta_mesas_sin_inscripcion(app_client, db_session):
    """RB-22 + CU-19: recién creadas (0 alumnos) no aparecen en el listado
    ni en el detalle (S-03: no aparece, pero no se borra)."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    assert len(filas) == 1

    listado = await app_client.get("/api/v1/sigme/mesas", headers=headers)
    assert listado.status_code == 200, listado.text
    assert listado.json() == []

    detalle = await app_client.get(
        f"/api/v1/sigme/mesas/{filas[0].id}", headers=headers
    )
    assert detalle.status_code == 404, detalle.text
    assert detalle.json()["code"] == "mesa-no-encontrada"


async def test_get_mesas_con_inscripcion_activa_y_filtros(app_client, db_session):
    """RB-22: sólo mesas con inscripción activa; filtros opcionales
    convocatoria_id / materia_id / condicion_id."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=2,
                                                 cant_condiciones=2)
    creada = await post_grupo(
        app_client, headers, conv, [materias[0], materias[1]], [condiciones[0]]
    )
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    assert len(filas) == 2
    for fila in filas:
        await dar_vida(db_session, fila)

    listado = await app_client.get("/api/v1/sigme/mesas", headers=headers)
    assert listado.status_code == 200, listado.text
    cuerpo = listado.json()
    assert len(cuerpo) == 2
    mesa = next(m for m in cuerpo if m["materia_id"] == str(materias[0].id))
    assert mesa["convocatoria_id"] == str(conv.id)
    assert mesa["grupo_id"] == creada.json()["id"]
    assert mesa["condicion_id"] == str(condiciones[0].id)
    assert mesa["fecha"] == creada.json()["fecha"]
    assert mesa["hora"] == "10:00:00"
    assert mesa["estado"] == "planificada"
    assert mesa["materia_nombre"] == "Materia 0"
    assert mesa["curso_nombre"] == "3er Año"
    assert mesa["orientacion_nombre"].startswith("Orientación")
    assert mesa["condicion_nombre"].startswith("Condición 0")

    por_conv = await app_client.get(
        "/api/v1/sigme/mesas",
        params={"convocatoria_id": str(conv.id)},
        headers=headers,
    )
    assert len(por_conv.json()) == 2
    por_materia = await app_client.get(
        "/api/v1/sigme/mesas",
        params={"materia_id": str(materias[0].id)},
        headers=headers,
    )
    assert len(por_materia.json()) == 1
    por_condicion = await app_client.get(
        "/api/v1/sigme/mesas",
        params={"condicion_id": str(condiciones[1].id)},
        headers=headers,
    )
    assert por_condicion.json() == []


async def test_get_mesas_excluye_vencidas(app_client, db_session):
    """L11a: las mesas vencidas dejan de listarse en SIGME (7 fuentes);
    las futuras con vida sí aparecen."""
    username = await make_usuario(db_session, permisos=("mesa.listar", "mesa.crear"))
    headers = await login(app_client, username)
    hoy = date.today()
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)

    pasada = await post_grupo(
        app_client, headers, conv, materias, condiciones,
        fecha=hoy - timedelta(days=5), hora="10:00",
    )
    assert pasada.status_code == 201
    futura = await post_grupo(
        app_client, headers, conv, materias, condiciones,
        fecha=hoy + timedelta(days=20), hora="18:00",
    )
    assert futura.status_code == 201

    filas_pasadas = await mesas_de(
        db_session, grupo_id=uuid.UUID(pasada.json()["id"])
    )
    filas_futuras = await mesas_de(
        db_session, grupo_id=uuid.UUID(futura.json()["id"])
    )
    await dar_vida(db_session, filas_pasadas[0])
    await dar_vida(db_session, filas_futuras[0])

    listado = await app_client.get("/api/v1/sigme/mesas", headers=headers)
    assert listado.status_code == 200, listado.text
    assert [m["id"] for m in listado.json()] == [str(filas_futuras[0].id)]

    rango_pasado = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha",
        params={"desde": (hoy - timedelta(days=10)).isoformat(),
                "hasta": (hoy - timedelta(days=1)).isoformat()},
        headers=headers,
    )
    assert rango_pasado.status_code == 200, rango_pasado.text
    assert rango_pasado.json() == []


async def test_get_mesa_por_fecha_rango_inclusive(app_client, db_session):
    """RB-23: desde/hasta inclusivos sobre la fecha de la mesa."""
    username = await make_usuario(db_session, permisos=("mesa.listar", "mesa.crear"))
    headers = await login(app_client, username)
    hoy = date.today()
    fecha = hoy + timedelta(days=20)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(
        app_client, headers, conv, materias, condiciones, fecha=fecha
    )
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    await dar_vida(db_session, filas[0])

    dia_exacto = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha",
        params={"desde": fecha.isoformat(), "hasta": fecha.isoformat()},
        headers=headers,
    )
    assert dia_exacto.status_code == 200, dia_exacto.text
    assert [m["id"] for m in dia_exacto.json()] == [str(filas[0].id)]

    fuera = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha",
        params={"desde": (fecha + timedelta(days=1)).isoformat(),
                "hasta": (fecha + timedelta(days=2)).isoformat()},
        headers=headers,
    )
    assert fuera.json() == []


async def test_get_mesa_por_fecha_parametros_invalidos(app_client, db_session):
    """422 validacion con errors[] (PD-24): faltan desde/hasta o desde>hasta."""
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    hoy = date.today()

    sin_params = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha", headers=headers
    )
    assert sin_params.status_code == 422, sin_params.text
    assert sin_params.json()["code"] == "validacion"
    assert sin_params.json()["errors"]

    invertido = await app_client.get(
        "/api/v1/sigme/mesas/por-fecha",
        params={"desde": (hoy + timedelta(days=30)).isoformat(),
                "hasta": hoy.isoformat()},
        headers=headers,
    )
    assert invertido.status_code == 422, invertido.text
    assert invertido.json()["code"] == "validacion"


async def test_get_mesa_detalle(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar", "mesa.crear"))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    await dar_vida(db_session, filas[0])

    detalle = await app_client.get(
        f"/api/v1/sigme/mesas/{filas[0].id}", headers=headers
    )
    assert detalle.status_code == 200, detalle.text
    cuerpo = detalle.json()
    assert cuerpo["id"] == str(filas[0].id)
    assert cuerpo["convocatoria_id"] == str(conv.id)
    assert cuerpo["estado"] == "planificada"
    assert cuerpo["materia_nombre"] == "Materia 0"
    assert cuerpo["condicion_nombre"].startswith("Condición 0")


async def test_get_mesa_detalle_vencida_deriva_cerrada(app_client, db_session):
    """A-SDD3-6 (L11c): la constatación de calendario deriva `cerrada` al
    leer; la columna `estado` NO se escribe (ME-03/ME-04, CU-22)."""
    username = await make_usuario(db_session, permisos=("mesa.listar", "mesa.crear"))
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(
        app_client, headers, conv, materias, condiciones,
        fecha=date.today() - timedelta(days=5),
    )
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    await dar_vida(db_session, filas[0])

    detalle = await app_client.get(
        f"/api/v1/sigme/mesas/{filas[0].id}", headers=headers
    )
    assert detalle.status_code == 200, detalle.text
    assert detalle.json()["estado"] == "cerrada"

    mesa_id = filas[0].id  # UUID capturado ANTES de expire_all: acceder a un
    db_session.expire_all()  # ORM vencido dispara lazy load sin greenlet.
    from app.features.mesas.models import EsMesaExamen

    fila = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.id == mesa_id)
    )
    assert fila.estado == "planificada"  # sin escritura (CU-22)


async def test_get_mesa_detalle_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(
        f"/api/v1/sigme/mesas/{uuid.uuid4()}", headers=headers
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "mesa-no-encontrada"


async def test_get_mesas_convocatoria_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.listar",))
    headers = await login(app_client, username)
    respuesta = await app_client.get(
        "/api/v1/sigme/mesas",
        params={"convocatoria_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "convocatoria-no-encontrada"


async def test_patch_mesa_reasigna_y_recalcula_snapshots(app_client, db_session):
    """CU-20/RB-11: cambia materia y condición; los 4 snapshots se
    recalculan en la misma transacción; el estado no cambia."""
    username = await make_usuario(
        db_session, permisos=("mesa.listar", "mesa.crear", "mesa.modificar")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=2,
                                                 cant_condiciones=2)
    creada = await post_grupo(
        app_client, headers, conv, [materias[0]], [condiciones[0]]
    )
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    mesa_id = filas[0].id

    cambio_materia = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}",
        json={"materia_id": str(materias[1].id)},
        headers=headers,
    )
    assert cambio_materia.status_code == 200, cambio_materia.text
    assert cambio_materia.json()["materia_id"] == str(materias[1].id)
    assert cambio_materia.json()["materia_nombre"] == "Materia 1"
    assert cambio_materia.json()["estado"] == "planificada"

    cambio_condicion = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}",
        json={"condicion_id": str(condiciones[1].id)},
        headers=headers,
    )
    assert cambio_condicion.status_code == 200, cambio_condicion.text
    assert cambio_condicion.json()["condicion_id"] == str(condiciones[1].id)
    assert cambio_condicion.json()["condicion_nombre"].startswith("Condición 1")
    assert cambio_condicion.json()["materia_id"] == str(materias[1].id)

    materia_nueva_id = materias[1].id  # UUIDs capturados ANTES de expire_all:
    condicion_nueva_id = condiciones[1].id  # el acceso perezoso a un ORM
    db_session.expire_all()  # vencido necesita greenlet (ver comentario supra).
    from app.features.mesas.models import EsMesaExamen

    fila = await db_session.scalar(
        select(EsMesaExamen).where(EsMesaExamen.id == mesa_id)
    )
    assert fila.materia_id == materia_nueva_id
    assert fila.condicion_id == condicion_nueva_id
    assert fila.materia_nombre == "Materia 1"
    assert fila.condicion_nombre.startswith("Condición 1")
    assert fila.estado == "planificada"  # CU-20: el estado no cambia


async def test_patch_mesa_colision_es_409(app_client, db_session):
    """uq_mesa_unica: reasignar a materia×condición que ya tiene mesa esa
    fecha en la convocatoria → 409 mesa-duplicada."""
    username = await make_usuario(
        db_session, permisos=("mesa.crear", "mesa.modificar")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=2,
                                                 cant_condiciones=1)
    fecha = date.today() + timedelta(days=20)
    primera = await post_grupo(
        app_client, headers, conv, [materias[0]], [condiciones[0]],
        fecha=fecha, hora="10:00",
    )
    assert primera.status_code == 201
    segunda = await post_grupo(
        app_client, headers, conv, [materias[1]], [condiciones[0]],
        fecha=fecha, hora="18:00",
    )
    assert segunda.status_code == 201
    filas_a = await mesas_de(db_session, grupo_id=uuid.UUID(primera.json()["id"]))

    respuesta = await app_client.patch(
        f"/api/v1/sigme/mesas/{filas_a[0].id}",
        json={"materia_id": str(materias[1].id)},
        headers=headers,
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "mesa-duplicada"


async def test_patch_mesa_catalogo_inexistente_es_404(app_client, db_session):
    username = await make_usuario(
        db_session, permisos=("mesa.crear", "mesa.modificar")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    mesa_id = filas[0].id

    materia_mala = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}",
        json={"materia_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert materia_mala.status_code == 404
    assert materia_mala.json()["code"] == "materia-no-encontrada"

    condicion_mala = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}",
        json={"condicion_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert condicion_mala.status_code == 404
    assert condicion_mala.json()["code"] == "condicion-no-encontrada"


async def test_patch_mesa_cuerpo_invalido_es_422(app_client, db_session):
    """422 validacion: sin ninguna asignación o con campos que no son de la
    mesa (fecha/hora pertenecen al grupo, RB-29 → extra=forbid)."""
    username = await make_usuario(
        db_session, permisos=("mesa.crear", "mesa.modificar")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                                 cant_condiciones=1)
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201
    filas = await mesas_de(db_session, grupo_id=uuid.UUID(creada.json()["id"]))
    mesa_id = filas[0].id

    vacio = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}", json={}, headers=headers
    )
    assert vacio.status_code == 422, vacio.text
    assert vacio.json()["code"] == "validacion"

    con_fecha = await app_client.patch(
        f"/api/v1/sigme/mesas/{mesa_id}",
        json={"materia_id": str(materias[0].id),
              "fecha": (date.today() + timedelta(days=40)).isoformat()},
        headers=headers,
    )
    assert con_fecha.status_code == 422, con_fecha.text
    assert con_fecha.json()["code"] == "validacion"


async def test_patch_mesa_inexistente_es_404(app_client, db_session):
    username = await make_usuario(db_session, permisos=("mesa.modificar",))
    headers = await login(app_client, username)
    _, condiciones = await crear_catalogo(db_session, cant_materias=1,
                                          cant_condiciones=1)
    respuesta = await app_client.patch(
        f"/api/v1/sigme/mesas/{uuid.uuid4()}",
        json={"condicion_id": str(condiciones[0].id)},
        headers=headers,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "mesa-no-encontrada"
