"""T3 (S3) — Inscribirse: POST /api/v1/inscripciones.

Spec: odd/tasks/sdd-4-inscripciones.md, T3, S3.
CU-37/CU-40 (doc 06 §6.3/§6.5). Permiso `inscripcion.crear`. Cuerpo
`{materia_id, condicion_id}` — el alumno elige sólo materia + condición
(RB-30); la convocatoria NO viaja en el cuerpo (A-SDD4-4): es siempre la
vigente. Validaciones en orden: 404 `convocatoria-no-encontrada` -> 409
`ventana-cerrada` -> 404 `materia/condicion-no-encontrada` -> 409
`inscripcion-duplicada` (RN-006: unicidad por materia × convocatoria) -> 409
`limite-materias` (`es_condicion.limite_materias`, NULL = sin límite,
RN-013/PD-02) -> 409 `mesa-no-disponible` (A-SDD4-5/PD-19: sin mesa viva
del combo) -> crea la fila `inscripto`. A-SDD4-6: elección determinística de
mesa (fecha más próxima, hora e id como desempate). CU-40: reinscribir tras
anular crea fila NUEVA (INS-04). A-SDD4-8: sin confirmación por email.
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

_URL = "/api/v1/inscripciones"


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


async def crear_catalogo(db, *, cant_materias=2, cant_condiciones=2,
                         limites_condiciones=None):
    """Orientación + curso + N materias + M condiciones activas (harness T3).

    `limites_condiciones` fija `limite_materias` por condición (None = sin
    límite, RN-013/PD-02).
    """
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
        limite = (
            limites_condiciones[i]
            if limites_condiciones is not None and i < len(limites_condiciones)
            else None
        )
        condicion = EsCondicion(
            id=uuid.uuid4(), descripcion=f"Condición {i} {uuid.uuid4().hex[:4]}",
            activo=True, limite_materias=limite, created_at=datetime.now(UTC),
        )
        db.add(condicion)
        condiciones.append(condicion)
    await db.commit()
    return materias, condiciones


async def post_grupo(client, headers, conv, materias, condiciones,
                     fecha=None, hora="10:00", nombre=None):
    """RB-28/29: crea el grupo y sus mesas en bloque (harness T3)."""
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


async def usuario_id_de(db, username):
    from sqlalchemy import select

    from app.features.usuarios.models import UsUsuario

    return await db.scalar(select(UsUsuario.id).where(UsUsuario.username == username))


async def conteo_inscripciones(db, usuario_id):
    from sqlalchemy import func, select

    from app.features.mesas.models import EsMesaInscripcion

    return await db.scalar(
        select(func.count())
        .select_from(EsMesaInscripcion)
        .where(EsMesaInscripcion.usuario_id == usuario_id)
    )


async def inscribir(client, headers, materia, condicion):
    return await client.post(
        _URL,
        json={"materia_id": str(materia.id), "condicion_id": str(condicion.id)},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Puertas: sesión y permiso
# ---------------------------------------------------------------------------


async def test_inscribirse_sin_token_es_401(app_client):
    resp = await app_client.post(
        _URL, json={"materia_id": str(uuid.uuid4()), "condicion_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == "no-autenticado"


async def test_inscribirse_sin_permiso_es_403(app_client, db_session):
    """Sesión válida pero sin `inscripcion.crear` -> 403 permiso-denegado."""
    username = await make_usuario(db_session, permisos=())
    headers = await login(app_client, username)

    resp = await inscribir(
        app_client, headers, type("M", (), {"id": uuid.uuid4()})(),
        type("C", (), {"id": uuid.uuid4()})(),
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["code"] == "permiso-denegado"


# ---------------------------------------------------------------------------
# Validaciones en orden del spec S3
# ---------------------------------------------------------------------------


async def test_inscribirse_sin_convocatoria_es_404(app_client, db_session):
    """(1) Sin convocatoria vigente (activa) -> 404 convocatoria-no-encontrada."""
    await crear_convocatoria(db_session, activa=False)  # borrador
    username = await make_usuario(db_session, permisos=("inscripcion.crear",))
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    materias, condiciones = await crear_catalogo(db_session)

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "convocatoria-no-encontrada"
    assert await conteo_inscripciones(db_session, usuario_id) == 0


async def test_inscribirse_fuera_de_ventana_es_409(app_client, db_session):
    """(2) RB-07/RB-23: fuera de la ventana -> 409 ventana-cerrada."""
    hoy = hoy_buenos_aires()
    await crear_convocatoria(
        db_session,
        inicio=hoy - timedelta(days=20),
        fin=hoy - timedelta(days=3),  # vigente (activa) pero ventana cerrada
    )
    username = await make_usuario(db_session, permisos=("inscripcion.crear",))
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    materias, condiciones = await crear_catalogo(db_session)

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "ventana-cerrada"
    assert await conteo_inscripciones(db_session, usuario_id) == 0


async def test_inscribirse_materia_inactiva_es_404(app_client, db_session):
    """(3) Materia inactiva/borrada -> 404 materia-no-encontrada."""
    from datetime import UTC as _UTC

    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    materias[0].activo = False
    materias[0].deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "materia-no-encontrada"
    assert await conteo_inscripciones(db_session, usuario_id) == 0


async def test_inscribirse_condicion_inactiva_es_404(app_client, db_session):
    """(3) Condición inactiva -> 404 condicion-no-encontrada."""
    from datetime import UTC as _UTC

    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    condiciones[0].activo = False
    condiciones[0].deleted_at = datetime.now(_UTC)
    await db_session.commit()

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 404, resp.text
    assert resp.json()["code"] == "condicion-no-encontrada"
    assert await conteo_inscripciones(db_session, usuario_id) == 0


# ---------------------------------------------------------------------------
# Éxito, unicidad, límite y elección determinística
# ---------------------------------------------------------------------------


async def test_inscribirse_exito_crea_fila(app_client, db_session):
    """201: crea la fila `inscripto` con los ids elegidos (CU-37)."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaInscripcion

    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 201, resp.text
    cuerpo = resp.json()
    assert cuerpo["estado"] == "inscripto"
    assert cuerpo["materia_id"] == str(materias[0].id)
    assert cuerpo["condicion_id"] == str(condiciones[0].id)
    assert cuerpo["convocatoria_id"] == str(conv)

    fila = await db_session.scalar(
        select(EsMesaInscripcion).where(
            EsMesaInscripcion.id == uuid.UUID(cuerpo["id"])
        )
    )
    assert fila is not None
    assert fila.usuario_id == usuario_id
    assert fila.estado == "inscripto"


async def test_inscribirse_duplicada_es_409_y_no_duplica(app_client, db_session):
    """(4) RN-006/RB-08: reintento E-13 -> misma respuesta, sin duplicar."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    primera = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert primera.status_code == 201, primera.text

    segunda = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert segunda.status_code == 409, segunda.text
    assert segunda.json()["code"] == "inscripcion-duplicada"
    assert await conteo_inscripciones(db_session, usuario_id) == 1


async def test_inscribirse_elige_mesa_mas_proxima(app_client, db_session):
    """A-SDD4-6: con varias mesas vivas del combo, elige la de fecha más
    próxima (hora e id como desempate) — elección determinística."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaExamen

    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    hoy = hoy_buenos_aires()
    fecha_lejana = hoy + timedelta(days=40)
    fecha_proxima = hoy + timedelta(days=15)
    lejana = await post_grupo(
        app_client, headers, conv, materias, condiciones,
        fecha=fecha_lejana, nombre="Lejana",
    )
    assert lejana.status_code == 201, lejana.text
    proxima = await post_grupo(
        app_client, headers, conv, materias, condiciones,
        fecha=fecha_proxima, nombre="Próxima",
    )
    assert proxima.status_code == 201, proxima.text

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 201, resp.text

    mesa_proxima = await db_session.scalar(
        select(EsMesaExamen).where(
            EsMesaExamen.convocatoria_id == conv,
            EsMesaExamen.materia_id == materias[0].id,
            EsMesaExamen.condicion_id == condiciones[0].id,
            EsMesaExamen.fecha == fecha_proxima,
        )
    )
    # Elige la mesa del grupo más cercano (fecha 15), no la del grupo lejano (40).
    assert resp.json()["mesa_examen_id"] == str(mesa_proxima.id)


async def test_inscribirse_limite_previa_es_409(app_client, db_session):
    """(5) RN-013/PD-02: Previa hasta 3 por convocatoria -> cuarta 409."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    # Previa (condición 0) con límite 3; Regular (condición 1) sin límite.
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=4, cant_condiciones=1, limites_condiciones=[3]
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    for i in range(3):
        ok = await inscribir(app_client, headers, materias[i], condiciones[0])
        assert ok.status_code == 201, ok.text

    cuarta = await inscribir(app_client, headers, materias[3], condiciones[0])
    assert cuarta.status_code == 409, cuarta.text
    assert cuarta.json()["code"] == "limite-materias"
    assert await conteo_inscripciones(db_session, usuario_id) == 3


async def test_inscribirse_libre_sin_limite(app_client, db_session):
    """RN-013: `limite_materias` NULL = sin límite (Libre) -> todas pasan."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=4, cant_condiciones=1
    )  # condición con limite_materias NULL
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    for materia in materias:
        ok = await inscribir(app_client, headers, materia, condiciones[0])
        assert ok.status_code == 201, ok.text
    assert await conteo_inscripciones(db_session, usuario_id) == 4


async def test_inscribirse_sin_mesa_es_409(app_client, db_session):
    """(6) A-SDD4-5/PD-19: sin mesa viva del combo -> 409 mesa-no-disponible."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    usuario_id = await usuario_id_de(db_session, username)
    await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    # No se crea ningún grupo -> no hay mesas.

    resp = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == "mesa-no-disponible"
    assert await conteo_inscripciones(db_session, usuario_id) == 0


# ---------------------------------------------------------------------------
# CU-40 / A-SDD4-4
# ---------------------------------------------------------------------------


async def test_inscribirse_reinscripcion_tras_anular_crea_fila_nueva(
    app_client, db_session
):
    """CU-40/INS-04: tras anular, reinscribir es un alta de fila NUEVA — la
    anulada no se reutiliza y la unicidad no choca (`anulado` fuera del índice)."""
    from sqlalchemy import select

    from app.features.mesas.models import EsMesaInscripcion

    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )
    creada = await post_grupo(app_client, headers, conv, materias, condiciones)
    assert creada.status_code == 201, creada.text

    primera = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert primera.status_code == 201, primera.text
    original_id = uuid.UUID(primera.json()["id"])

    fila = await db_session.scalar(
        select(EsMesaInscripcion).where(EsMesaInscripcion.id == original_id)
    )
    fila.estado = "anulado"
    await db_session.commit()

    nueva = await inscribir(app_client, headers, materias[0], condiciones[0])
    assert nueva.status_code == 201, nueva.text
    assert uuid.UUID(nueva.json()["id"]) != original_id
    assert nueva.json()["estado"] == "inscripto"


async def test_inscribirse_cuerpo_con_campos_extra_es_400(app_client, db_session):
    """A-SDD4-4: la convocatoria NO viaja en el cuerpo (extra='forbid')."""
    username = await make_usuario(
        db_session, permisos=("inscripcion.crear", "mesa.crear")
    )
    headers = await login(app_client, username)
    conv = await crear_convocatoria(db_session)
    materias, condiciones = await crear_catalogo(
        db_session, cant_materias=1, cant_condiciones=1
    )

    resp = await app_client.post(
        _URL,
        json={
            "materia_id": str(materias[0].id),
            "condicion_id": str(condiciones[0].id),
            "convocatoria_id": str(conv),
        },
        headers=headers,
    )
    assert resp.status_code == 422, resp.text
