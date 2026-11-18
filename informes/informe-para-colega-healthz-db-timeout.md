# Informe para el colega — `/healthz` informa `db=unavailable` (timeout del ping)

**Para:** equipo backend (`backend-epet-n36`)
**De:** equipo frontend (app móvil `appmexamen`)
**Fecha:** 2026-11-17
**Motivo:** aplicamos su `.env` (`variable de entorno para el backend.rar`) y el
`/healthz` responde `db=unavailable`. Tras el diagnóstico **el problema no es la
credencial ni Neon**: es el **timeout de 2 s** del `ping()` en
`app/db/session.py`, insuficiente para la latencia real de Neon.

---

## 1. Resumen ejecutivo

| Tema | Estado | Acción |
|---|---|---|
| Archivo `.env` recibido | **Aplicado** en `backend/.env` (SHA256 idéntico al suyo) | Ninguna de nuestra parte |
| Arranque de la app | **OK** — uvicorn levanta, `/healthz` HTTP 200 | — |
| DNS + TCP a Neon :5432 | **OK** — resuelve y conecta | — |
| Credenciales `DATABASE_URL` | **OK** — `asyncpg` directo ejecuta `SELECT 1` = 1 | — |
| `ping()` de `/healthz` | **Falla siempre** con timeout 2 s (`TimeoutError`) | **De ustedes** (§3) |
| API con auth (`/api/v1/...`) | Responde 401 sin token (esperado); la capa de app está viva | — |

**Conclusión:** la base es alcanzable y las credenciales del `.env` sirven. El
`/healthz` miente por un timeout demasiado agresivo, no por una BD caída.

---

## 2. Evidencia (máquina de desarrollo, Windows, 2026-11-17)

### 2.1 Lo que sí funciona

```
DNS  ep-cold-sunset-b5vhyom8.c-7.us-east-2.aws.neon.tech:5432  → 3 IPs OK
TCP  connect a :5432                                          → OK
asyncpg SELECT 1 (ssl=require, con la URL del .env)           → 1
```

Tiempos de conexión **directos con asyncpg** (misma URL):

| Intento | Duración |
|---|---|
| #1 | 1.62 s |
| #2 | 3.78 s |
| #3 | 1.59 s |

### 2.2 Lo que falla: el `ping()` de la app

`app/db/session.py` → `ping(settings, timeout: float = 2.0)`:

```
ping#1 timeout=2.0  → ok=False  (elapsed ~3.4 s)   ← expira
ping#2 timeout=2.0  → ok=False  (elapsed ~3.1 s)   ← expira
ping#3 timeout=10.0 → ok=True   (elapsed ~6.7 s)   ← conecta
ping#4 timeout=10.0 → ok=True   (elapsed ~1.4 s)   ← conecta (pool tibio)
raw engine.connect (sin wrapper de timeout) → ~1.2 s
```

Log del propio uvicorn:

```
WARNING app.db.session ping de base de datos expiró tras 2.0s
GET /healthz HTTP/1.1 200  {"status":"ok", ..., "db":"unavailable"}
```

### 2.3 Interpretación

- La primera conexión a Neon (handshake TLS + auth) **supera 2 s** con
  frecuencia desde esta red (1.5–3.8 s medidos).
- Con `timeout=10.0` el **mismo** `ping()` devuelve `True`.
- O sea: **credenciales y red OK; el umbral de 2 s es el que rompe el healthz.**

---

## 3. Qué pedimos (lado backend / de ustedes)

1. **Subir el timeout del `ping()`** en `app/db/session.py` (hoy `2.0`). Un
   valor razonable para desarrollo con Neon: **5–10 s**. Ejemplo mínimo:
   ```python
   async def ping(settings: Settings, timeout: float = 10.0) -> bool:
       ...
   ```
   Si prefieren no tocar el default global, podrían parametrizarlo por env
   (`HEALTHZ_DB_TIMEOUT`, default 10 en development).

2. **(Alternativa / complemento)** No tratar `TimeoutError` como “BD
   unavailable” sin distinguirlo de un error de auth: hoy ambos caen a
   `db=unavailable`. Un log con la causa ya distingue “timeout” de
   “password authentication failed”.

3. **(Opcional)** Calentar el pool en el `lifespan` de desarrollo para que el
   primer request no pague el handshake frío.

**Nosotros no tocamos `backend/`** (snapshot de ustedes; solo se reemplazó el
`.env` que enviaron). Este informe es el pedido de cambio.

---

## 4. Qué NO es el problema (para que no lo re-investiguen)

| Hipótesis | Veredicto |
|---|---|
| `.env` mal colocado o desactualizado | **No** — SHA256 idéntico al rar que enviaron |
| Contraseña/usuario de Neon inválidos | **No** — `asyncpg SELECT 1` = 1 con esa URL |
| Neon caído o puerto bloqueado | **No** — DNS + TCP :5432 OK |
| Falta `ssl=require` | **No** — se usa `ssl=require` y conecta |
| Host con sufijo `-pooler` | **No** en este caso — el host del `.env` ya es directo (sin `-pooler`) y funciona |

---

## 5. Cómo lo podemos verificar juntos

Con su `.env` ya aplicado, en esta máquina:

```bash
# desde backend/
python -c "import asyncio; from app.core.config import get_settings; from app.db.session import ping; print(asyncio.run(ping(get_settings(), timeout=10.0)))"
# → True

curl http://127.0.0.1:8000/healthz
# hoy: db=unavailable   |   tras subir el timeout: db=ok
```

Cuando ustedes confirmen el cambio de timeout (o manden un `.env`/snapshot
nuevo con el fix), lo reemplazamos igual que esta vez y volvemos a correr
`/healthz`.

---

## 6. Adjunto / contexto

- Archivo suyo aplicado: `informes/variable de entorno para el backend.rar`
  → contenido `.env` (ENVIRONMENT, DATABASE_URL a Neon, MIGRATE_DATABASE_URL,
  JWT ES256, CORS_ORIGINS=[]).
- **Nota de seguridad (sin acción nuestra):** el `.rar` venía con la contraseña
  de Neon y la clave JWT privada en texto plano. Si ese archivo pasó por un
  canal no privado, conviene **rotar** esos secretos del lado de ustedes.
- `MIGRATE_DATABASE_URL` del `.env` sigue con placeholders
  (`HOST-DIRECTO/DATABASE`); no la usamos (las migraciones no corren de
  nuestro lado), pero se las dejo anotada por si la necesitan completar.
