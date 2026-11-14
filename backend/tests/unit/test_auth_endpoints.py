"""Endpoints /api/v1/auth + contrato de error PD-24 (analisis.txt 2.4, 2.6, §6).

Cubre: login con rate limit y bloqueo (PD-27), refresh con rotación y reuse
detection, logout/logout-all, cambiar-clave con token_version, GET /yo, el
restablecimiento por correo (olvido-clave + restablecer-clave, decisión
2026-11-12) y la forma única de error {code, detail, errors[]} (errors[] SÓLO
en 422).
"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, decode_token, hash_password
from app.features.auth.service import solicitar_recuperacion
from app.features.usuarios.models import (
    UsModulo,
    UsPasswordReset,
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
_CLAVE_NUEVA = "clave-nueva-9999"


@pytest.fixture
def auth_app(db_session):
    app = create_app()

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    return app


@pytest.fixture
async def client(auth_app):
    transport = httpx.ASGITransport(app=auth_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def make_usuario(
    db,
    *,
    username="directora",
    password=_PASSWORD,
    rol="direccion",
    permisos=("mesa.listar", "mesa.crear"),
    modulo="sigme_web",
    email=None,
):
    """Usuario completo con rol, permisos y módulo (§2.7/§2.8)."""
    await seed_modulos(db)
    await seed_permisos(db)
    now = datetime.now(UTC)
    user = UsUsuario(
        id=uuid.uuid4(),
        persona_id=uuid.uuid4(),
        username=username,
        email=email,
        password_hash=hash_password(password),
        activo=True,
        bloqueado=False,
        intentos_fallidos=0,
        token_version=1,
        password_changed_at=now,
        created_at=now,
    )
    rol_row = UsRol(
        id=uuid.uuid4(), codigo=rol, descripcion="rol de test", activo=True, created_at=now
    )
    db.add_all([user, rol_row])
    await db.flush()
    db.add(UsUsuarioRol(usuario_id=user.id, rol_id=rol_row.id))
    modulo_row = await db.scalar(select(UsModulo).where(UsModulo.codigo == modulo))
    db.add(UsUsuarioModulo(usuario_id=user.id, modulo_id=modulo_row.id))
    for codigo in permisos:
        permiso_row = await db.scalar(select(UsPermiso).where(UsPermiso.codigo == codigo))
        db.add(UsRolPermiso(rol_id=rol_row.id, permiso_id=permiso_row.id))
    await db.commit()
    return user


async def login(client, username="directora", password=_PASSWORD, modulo="sigme_web"):
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "modulo": modulo},
    )


async def test_login_devuelve_par_y_claims_completos(client, db_session):
    user = await make_usuario(db_session)
    resp = await login(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["access"] and body["refresh"]

    claims = decode_token(
        body["access"],
        public_key=_public_key(),
        issuer="backend-epet-n36",
        audience="epet36-api",
    )
    assert claims["sub"] == str(user.id)
    assert claims["ver"] == 1
    assert claims["roles"] == ["direccion"]
    assert sorted(claims["permisos"]) == ["mesa.crear", "mesa.listar"]
    assert claims["modulos"] == ["sigme_web"]
    assert claims["sid"]

    # El refresh es opaco y en la base sólo quedó su hash (§2.2)
    from app.features.auth.sessions import hash_refresh_token
    from app.features.usuarios.models import UsSesion

    sesion = await db_session.get(UsSesion, uuid.UUID(str(claims["sid"])))
    assert sesion is not None
    assert sesion.refresh_token_hash == hash_refresh_token(body["refresh"])
    assert sesion.estado == "activo"


async def test_login_clave_erronea_401_sin_errors(client, db_session):
    await make_usuario(db_session)
    resp = await login(client, password="otra-clave-incorrecta")
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "credenciales-invalidas"  # kebab-case estable (PD-24)
    assert body["detail"]
    assert "errors" not in body  # errors[] SÓLO en 422


async def test_login_quinto_fallo_bloquea_cuenta(client, db_session):
    user = await make_usuario(db_session)
    for _ in range(4):
        resp = await login(client, password="falla-segura-123456")
        assert resp.status_code == 401
    quinto = await login(client, password="falla-segura-123456")
    assert quinto.status_code == 429  # PD-27: 5 fallos -> 429 + bloqueo
    assert int(quinto.headers["retry-after"]) > 0
    assert quinto.json()["code"] == "cuenta-bloqueada"
    await db_session.refresh(user)
    assert user.intentos_fallidos == 5
    assert user.bloqueado_hasta is not None
    assert user.token_version == 2  # token_version sube al bloquear (§2.6/PD-27)


async def test_login_bloqueado_rechaza_antes_de_verificar(client, db_session):
    await make_usuario(db_session)
    for _ in range(5):
        await login(client, password="falla-segura-123456")
    resp = await login(client)  # aun con la clave CORRECTA
    assert resp.status_code == 429
    assert resp.json()["code"] == "cuenta-bloqueada"
    assert int(resp.headers["retry-after"]) > 0


async def test_login_bloqueo_vencido_se_resetea(client, db_session):
    user = await make_usuario(db_session)
    user.intentos_fallidos = 5
    user.bloqueado_hasta = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()
    resp = await login(client)
    assert resp.status_code == 200
    await db_session.refresh(user)
    assert user.intentos_fallidos == 0  # intentos_fallidos -> 0 al vencer (PD-27)
    assert user.bloqueado_hasta is None
    assert user.ultimo_ingreso is not None


async def test_login_ok_resetea_intentos_fallidos(client, db_session):
    user = await make_usuario(db_session)
    user.intentos_fallidos = 3
    await db_session.commit()
    resp = await login(client)
    assert resp.status_code == 200
    await db_session.refresh(user)
    assert user.intentos_fallidos == 0


async def test_refresh_rota_el_par_y_matricula_reuse(client, db_session):
    from app.features.auth.sessions import hash_refresh_token
    from app.features.usuarios.models import UsSesion

    await make_usuario(db_session)
    primero = (await login(client)).json()

    resp = await client.post("/api/v1/auth/refresh", json={"refresh": primero["refresh"]})
    assert resp.status_code == 200
    segundo = resp.json()
    assert segundo["access"] != primero["access"]
    assert segundo["refresh"] != primero["refresh"]

    # La sesión vieja quedó revocada con rotated_at (§2.2)
    vieja = await db_session.scalar(
        select(UsSesion).where(
            UsSesion.refresh_token_hash == hash_refresh_token(primero["refresh"])
        )
    )
    assert vieja.estado == "revocado"
    assert vieja.rotated_at is not None

    # Reusar el refresh ya rotado revoca la familia completa (§2.2)
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh": primero["refresh"]})
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "refresh-reutilizado"
    reciente = await client.post("/api/v1/auth/refresh", json={"refresh": segundo["refresh"]})
    assert reciente.status_code == 401  # la familia entera murió


async def test_refresh_invalido_401(client, db_session):
    await make_usuario(db_session)
    resp = await client.post("/api/v1/auth/refresh", json={"refresh": "token-inexistente"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "refresh-invalido"


async def test_logout_revoca_la_sesion_del_token(client, db_session):
    await make_usuario(db_session)
    par = (await login(client)).json()
    resp = await client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {par['access']}"}
    )
    assert resp.status_code == 204
    yo = await client.get(
        "/api/v1/auth/yo", headers={"Authorization": f"Bearer {par['access']}"}
    )
    assert yo.status_code == 401  # el access murió con la sesión
    assert yo.json()["code"] == "sesion-revocada"


async def test_logout_all_revoca_todas_las_sesiones(client, db_session):
    await make_usuario(db_session)
    par_a = (await login(client)).json()
    par_b = (await login(client)).json()
    resp = await client.post(
        "/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {par_a['access']}"}
    )
    assert resp.status_code == 204
    for par in (par_a, par_b):
        yo = await client.get(
            "/api/v1/auth/yo", headers={"Authorization": f"Bearer {par['access']}"}
        )
        assert yo.status_code == 401


async def test_yo_devuelve_identidad_desde_claims(client, db_session):
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    resp = await client.get(
        "/api/v1/auth/yo", headers={"Authorization": f"Bearer {par['access']}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(user.id)
    assert body["username"] == "directora"
    assert body["roles"] == ["direccion"]
    assert sorted(body["permisos"]) == ["mesa.crear", "mesa.listar"]
    assert body["modulos"] == ["sigme_web"]


async def test_yo_sin_token_401(client, db_session):
    await make_usuario(db_session)
    resp = await client.get("/api/v1/auth/yo")
    assert resp.status_code == 401
    assert resp.json()["code"] == "no-autenticado"


async def test_ver_distinto_a_token_version_401(client, db_session):
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    user.token_version = 99  # simula cambio de clave/rol (§2.6)
    await db_session.commit()
    resp = await client.get(
        "/api/v1/auth/yo", headers={"Authorization": f"Bearer {par['access']}"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "token-invalido"


async def test_cambiar_clave_sube_ver_y_devuelve_access(client, db_session):
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    resp = await client.post(
        "/api/v1/auth/cambiar-clave",
        headers={"Authorization": f"Bearer {par['access']}"},
        json={"clave_actual": _PASSWORD, "clave_nueva": "nueva-clave-12-caracteres"},
    )
    assert resp.status_code == 200
    await db_session.refresh(user)
    assert user.token_version == 2  # §2.6: subir token_version al cambiar clave
    assert user.password_changed_at is not None
    claims = decode_token(
        resp.json()["access"],
        public_key=_public_key(),
        issuer="backend-epet-n36",
        audience="epet36-api",
    )
    assert claims["ver"] == 2
    # La clave vieja ya no sirve; la nueva sí
    assert (await login(client)).status_code == 401
    ok = await login(client, password="nueva-clave-12-caracteres")
    assert ok.status_code == 200


async def test_cambiar_clave_corta_422_con_errors(client, db_session):
    await make_usuario(db_session)
    par = (await login(client)).json()
    resp = await client.post(
        "/api/v1/auth/cambiar-clave",
        headers={"Authorization": f"Bearer {par['access']}"},
        json={"clave_actual": _PASSWORD, "clave_nueva": "corta"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validacion"
    assert isinstance(body["errors"], list) and body["errors"]  # errors[] SÓLO en 422


async def test_ruta_desconocida_respeta_el_contrato(client, db_session):
    await make_usuario(db_session)
    resp = await client.get("/api/v1/auth/no-existe")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "no-encontrado"
    assert "errors" not in body


def _public_key() -> str:
    from app.features.auth.tokens import get_signing_keypair

    return get_signing_keypair()[1]


def test_public_key_helper_importable():
    # Fixture de arranque: el keyset efímero de dev/test existe (supuesto A2).
    assert _public_key()


async def test_login_modulo_inexistente_422_con_errors(client, db_session):
    """PD-24: módulo inexistente es clase de validación -> 422 + errors[]."""
    await make_usuario(db_session)
    resp = await login(client, modulo="modulo_inexistente")
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "validacion"
    assert any(err["field"] == "modulo" for err in body["errors"])


async def test_yo_con_cuenta_suspendida_403(client, db_session):
    """§2.6: una cuenta bloqueada no opera aunque el access siga vigente."""
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    user.bloqueado = True
    await db_session.commit()
    resp = await client.get(
        "/api/v1/auth/yo", headers={"Authorization": f"Bearer {par['access']}"}
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "cuenta-suspendida"


async def test_refresh_con_cuenta_suspendida_403(client, db_session):
    """§2.6: el refresh no renueva sesión de una cuenta suspendida."""
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    user.bloqueado = True
    await db_session.commit()
    resp = await client.post("/api/v1/auth/refresh", json={"refresh": par["refresh"]})
    assert resp.status_code == 403
    assert resp.json()["code"] == "cuenta-suspendida"


async def test_refresh_con_bloqueo_pd27_429(client, db_session):
    """PD-27: el bloqueo temporal vigente frena la renovación vía refresh."""
    user = await make_usuario(db_session)
    par = (await login(client)).json()
    user.bloqueado_hasta = datetime.now(UTC) + timedelta(minutes=10)
    await db_session.commit()
    resp = await client.post("/api/v1/auth/refresh", json={"refresh": par["refresh"]})
    assert resp.status_code == 429
    assert resp.json()["code"] == "cuenta-bloqueada"
    assert resp.headers["Retry-After"]


async def test_access_expirado_401_token_expirado(client, db_session):
    """Código documentado token-expirado (§2.1, contrato PD-24)."""
    await make_usuario(db_session)
    from app.features.auth.tokens import get_signing_keypair

    settings = get_settings()
    private, _ = get_signing_keypair()
    token = create_access_token(
        subject=str(uuid.uuid4()),
        sid=str(uuid.uuid4()),
        token_version=1,
        roles=[],
        permisos=[],
        modulos=[],
        private_key=private,
        kid=settings.jwt_kid,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        expires_delta=timedelta(minutes=-5),
    )
    resp = await client.get(
        "/api/v1/auth/yo", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "token-expirado"


# ---------------------------------------------------------------------------
# olvido-clave — pedido automático de recuperación con verificación por correo
# (decisión 2026-11-12: el usuario blanquea su clave con el token que llega a
# su email, sin intervención del admin; el email se encola en background)
# ---------------------------------------------------------------------------
async def test_olvido_clave_desconocido_202_sin_fila(client, db_session):
    """202 siempre y sin filas: no se revela si la cuenta existe (anti-enumeración)."""
    resp = await client.post(
        "/api/v1/auth/olvido-clave", json={"identificador": "no-existe"}
    )
    assert resp.status_code == 202
    assert resp.json() == {"status": "solicitado"}
    filas = (await db_session.execute(select(UsPasswordReset))).scalars().all()
    assert filas == []


async def test_olvido_clave_crea_solicitud_pendiente(client, db_session):
    """Con cuenta existente queda UNA fila pendiente (usado_en NULL) con vencimiento."""
    user = await make_usuario(db_session, username="alumno01")
    resp = await client.post(
        "/api/v1/auth/olvido-clave", json={"identificador": "alumno01"}
    )
    assert resp.status_code == 202
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila is not None
    assert fila.usuario_id == user.id
    assert fila.usado_en is None
    assert len(fila.token_hash) == 64  # hash opaco, jamás un token en claro
    expira = fila.expira_en
    if expira.tzinfo is None:  # SQLite devuelve naive
        expira = expira.replace(tzinfo=UTC)
    assert expira > datetime.now(UTC) + timedelta(hours=23)


async def test_olvido_clave_coincide_por_email(client, db_session):
    """El identificador puede ser el correo de la cuenta (case-insensitive)."""
    user = await make_usuario(db_session, username="alumno02")
    user.email = "Alumno@Correo.com"
    await db_session.commit()
    resp = await client.post(
        "/api/v1/auth/olvido-clave", json={"identificador": "alumno@correo.com"}
    )
    assert resp.status_code == 202
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila is not None
    assert fila.usuario_id == user.id


async def test_olvido_clave_no_duplica_solicitud_pendiente(client, db_session):
    """Pedir varias veces mantiene UNA sola fila pendiente por usuario."""
    await make_usuario(db_session, username="alumno03")
    for _ in range(3):
        resp = await client.post(
            "/api/v1/auth/olvido-clave", json={"identificador": "alumno03"}
        )
        assert resp.status_code == 202
    filas = (await db_session.execute(select(UsPasswordReset))).scalars().all()
    assert len(filas) == 1


async def test_olvido_clave_respuesta_identica_conocido_y_desconocido(
    client, db_session
):
    """La respuesta para una cuenta existente y una inexistente es indistinguible."""
    await make_usuario(db_session, username="alumno04")
    conocido = await client.post(
        "/api/v1/auth/olvido-clave", json={"identificador": "alumno04"}
    )
    desconocido = await client.post(
        "/api/v1/auth/olvido-clave", json={"identificador": "otro-usuario"}
    )
    assert conocido.status_code == desconocido.status_code == 202
    assert conocido.json() == desconocido.json()


async def test_olvido_clave_el_correo_lleva_el_token_cuyo_hash_es_la_fila(
    client, db_session
):
    """El token en claro viaja SÓLO por el correo; la fila guarda su SHA-256."""
    user = await make_usuario(db_session, username="alumno05", email="a5@correo.com")
    correo = await solicitar_recuperacion(db_session, identificador="alumno05")
    await db_session.commit()
    assert correo is not None
    assert correo.destinatario == "a5@correo.com"
    token = _token_del_correo(correo.cuerpo)
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila is not None
    assert fila.usuario_id == user.id
    assert fila.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert len(fila.token_hash) == 64  # jamás el token en claro en la fila


async def test_olvido_clave_sin_email_registra_fila_sin_correo(client, db_session):
    """Sin correo registrado queda la fila (contrato PD-04) pero no hay email."""
    user = await make_usuario(db_session, username="alumno06")
    correo = await solicitar_recuperacion(db_session, identificador="alumno06")
    await db_session.commit()
    assert correo is None
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila is not None
    assert fila.usuario_id == user.id


async def test_olvido_clave_reenvio_regenera_el_token(client, db_session):
    """Un solo pedido vigente: el reenvío invalida el token del correo anterior."""
    await make_usuario(db_session, username="alumno07", email="a7@correo.com")
    correo1 = await solicitar_recuperacion(db_session, identificador="alumno07")
    await db_session.commit()
    token1 = _token_del_correo(correo1.cuerpo)
    correo2 = await solicitar_recuperacion(db_session, identificador="alumno07")
    await db_session.commit()
    token2 = _token_del_correo(correo2.cuerpo)
    assert token1 != token2
    filas = (await db_session.execute(select(UsPasswordReset))).scalars().all()
    assert len(filas) == 1  # jamás se duplican filas pendientes
    assert filas[0].token_hash == hashlib.sha256(token2.encode()).hexdigest()
    # el token viejo ya no tiene fila que lo respalde
    assert filas[0].token_hash != hashlib.sha256(token1.encode()).hexdigest()


# ---------------------------------------------------------------------------
# restablecer-clave — el usuario blanquea su propia clave con el token del
# correo (decisión 2026-11-12; PD-04: un solo uso, vencimiento, hash SHA-256)
# ---------------------------------------------------------------------------
async def _pedir_token(db, *, username: str) -> str:
    """Pide la recuperación por servicio y extrae el token del correo."""
    correo = await solicitar_recuperacion(db, identificador=username)
    await db.commit()
    assert correo is not None
    return _token_del_correo(correo.cuerpo)


def _token_del_correo(cuerpo: str) -> str:
    match = re.search(r"token de recuperación es:\n\n    (\S+)", cuerpo)
    assert match is not None, cuerpo
    return match.group(1)


async def test_restablecer_clave_ok_y_login_solo_con_la_nueva(client, db_session):
    """200: cambia la clave, marca el token usado y sube token_version (§2.6)."""
    user = await make_usuario(db_session, username="alumno08", email="a8@correo.com")
    token = await _pedir_token(db_session, username="alumno08")
    resp = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": _CLAVE_NUEVA},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "restablecida"}
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila.usado_en is not None  # un solo uso
    assert user.token_version == 2  # invalida los access vigentes (§2.6)

    viejo = await client.post(
        "/api/v1/auth/login",
        json={"username": "alumno08", "password": _PASSWORD, "modulo": "sigme_web"},
    )
    assert viejo.status_code == 401
    nuevo = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "alumno08",
            "password": _CLAVE_NUEVA,
            "modulo": "sigme_web",
        },
    )
    assert nuevo.status_code == 200


async def test_restablecer_clave_token_desconocido_error_unico(client, db_session):
    """Token falso: 401 con el mismo código que vencido o ya usado."""
    await make_usuario(db_session, username="alumno09", email="a9@correo.com")
    resp = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": "x" * 43, "clave_nueva": _CLAVE_NUEVA},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "recuperacion-invalida"


async def test_restablecer_clave_token_ya_usado_no_repite(client, db_session):
    """Un token consumido no se reutiliza: segundo intento → 401 idéntico."""
    await make_usuario(db_session, username="alumno10", email="a10@correo.com")
    token = await _pedir_token(db_session, username="alumno10")
    primero = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": _CLAVE_NUEVA},
    )
    assert primero.status_code == 200
    segundo = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": "otra-clave-1234"},
    )
    assert segundo.status_code == 401
    assert segundo.json()["code"] == "recuperacion-invalida"


async def test_restablecer_clave_token_vencido(client, db_session):
    """expira_en en el pasado: el token no sirve (ventana de 24 h)."""
    user = await make_usuario(db_session, username="alumno11", email="a11@correo.com")
    token = "vencido-token"
    db_session.add(
        UsPasswordReset(
            id=uuid.uuid4(),
            usuario_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expira_en=datetime.now(UTC) - timedelta(hours=1),
            created_at=datetime.now(UTC) - timedelta(hours=25),
        )
    )
    await db_session.commit()
    resp = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": _CLAVE_NUEVA},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "recuperacion-invalida"
    # la clave NO cambió
    fila = await db_session.scalar(select(UsPasswordReset))
    assert fila.usado_en is None


async def test_restablecer_clave_requiere_12_caracteres(client, db_session):
    """§2.5: la nueva clave respeta la política mínima (422 con errors[])."""
    await make_usuario(db_session, username="alumno12", email="a12@correo.com")
    token = await _pedir_token(db_session, username="alumno12")
    resp = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": "cortita"},
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "validacion"
    assert resp.json()["errors"][0]["field"] == "clave_nueva"


async def test_restablecer_clave_revoca_las_sesiones(client, db_session):
    """§2.6: tras el blanqueo el refresh viejo no rota (sesiones revocadas)."""
    await make_usuario(db_session, username="alumno13", email="a13@correo.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "alumno13", "password": _PASSWORD, "modulo": "sigme_web"},
    )
    assert login.status_code == 200
    refresh_viejo = login.json()["refresh"]

    token = await _pedir_token(db_session, username="alumno13")
    resp = await client.post(
        "/api/v1/auth/restablecer-clave",
        json={"token": token, "clave_nueva": _CLAVE_NUEVA},
    )
    assert resp.status_code == 200

    refresco = await client.post(
        "/api/v1/auth/refresh", json={"refresh": refresh_viejo}
    )
    assert refresco.status_code == 401
