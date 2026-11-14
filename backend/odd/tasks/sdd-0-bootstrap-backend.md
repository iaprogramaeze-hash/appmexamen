# SDD-0 — Bootstrap del backend FastAPI

**Objetivo.** Poner los cimientos ejecutables del backend: estructura por dominio
(§5), stack cerrado (§0), **todos los modelos** de §3, migración inicial de
Alembic, health check y tooling de verificación.

**Branch:** `feat/sdd-0-bootstrap` (nace de `6b27763`, HEAD de la rama de análisis).
**Estrategia de entrega:** `feature-branch-chain` (elegida por el usuario
2026-10-12): cada task es un work-unit commit en `feat/sdd-0-bootstrap`; al
cerrar SDD-0 se abre UN PR de la rama completa contra `main`.
**Test runner:** `python -m pytest` (unit con SQLite/aiosqlite; integración
contra PG sólo con string de conexión disponible). Lint: `ruff check .`.
**Entorno:** Python 3.14 / pip 26. Sin Docker ni psql → la migración se
verifica en modo offline (`alembic upgrade head --sql`), no contra Postgres vivo.

---

## Specs

### S1 — Stack cerrado (verbatim de `analisis.txt` §0)

- "Framework       : FastAPI"
- "Base de datos   : PostgreSQL (Neon Tech)"
- "ORM             : SQLAlchemy 2.0 (estilo declarativo moderno)"
- "Validación      : Pydantic v2"
- "Migraciones     : Alembic"
- "Autenticación   : JWT (access + refresh con rotación)"

### S2 — Restricciones operativas Vercel/Neon (verbatim de `analisis.txt` §0, PD-06 cerrado 2026-10-06)

- "No hay proceso persistente, así que se RETIRA el pool TCP de SQLAlchemy
  (desaparecen pool_pre_ping y pool_recycle) y la aplicación habla con Neon por
  el driver HTTP serverless."
- "Las migraciones de Alembic se ejecutan desde CI/local sobre la conexión
  DIRECTA (host sin sufijo `-pooler`)."
- "Variables de entorno: nunca en el repo; se definen en el panel de Vercel, por entorno."
- CORS obligatorio (servicio independiente; NFR-023 espera el origen exacto de
  la landing → `CORS_ORIGINS` vacío por defecto, sin `*`).

**Criterio:** en `ENVIRONMENT=production` el engine no configura pool ni
`pool_pre_ping`/`pool_recycle`; en desarrollo/local sí. `.env` jamás se commitea
(gitignore lo cubre); existe `.env.example`.

### S3 — Estructura por dominio (verbatim de `analisis.txt` §5)

```
app/
  main.py              # create_app() factory + lifespan
  api/v1/api.py         # único lugar que importa todos los routers
  core/                 # config.py, security.py, dependencies.py, exceptions.py, logging.py
  db/                   # session.py, base.py, triggers.sql
  features/<dominio>/   # router.py service.py repository.py models.py schemas.py
alembic/
tests/unit/  tests/integration/
pyproject.toml
.env.example
```

Reglas (verbatim):
- "Los routers sólo conocen HTTP: reciben, delegan al service, devuelven."
- "La lógica de negocio vive en service.py y NO importa FastAPI."
- "Sólo app/api/v1/api.py conoce todos los dominios."
- "Un dominio NUNCA importa a otro; si necesitan hablar, va por core/."
- "Cada router declara su prefijo propio; el prefijo de versión (/api/v1) lo aplica la factory."

**Criterio:** `create_app()` aplica `/api/v1`; los dominios de la Fase SDD-0 son
sólo los mínimos (`health`); auth/mesas/inscripciones/preinscripcion se crean en
fases posteriores.

### S4 — Modelos completos de `analisis.txt` §3 (22 tablas)

Las 22 tablas con sus columnas, tipos, PK/FK/UNIQUE/CHECK e índices tal como
están en §3.1–§3.22 (incluye los `[CORREGIDO]` y los únicos ya conocidos:
`uq_mesa_unica` §3.18, `uq_grupo_unico` §3.22, `uq_preinscripcion_unica` §3.20,
PK compuestas de §3.8/§3.9/§3.11, `uq_mesa_unica` sin `hora` — PD-13 sigue
abierto y el índice NO se modifica):

| § | Tabla | § | Tabla |
|---|---|---|---|
| 3.1 | `pe_documento_tipo` | 3.12 | `us_sesion` |
| 3.2 | `pe_persona` | 3.13 | `es_orientacion` |
| 3.3 | `pe_contacto_tipo` | 3.14 | `es_curso` |
| 3.4 | `pe_contacto` | 3.15 | `es_materia` |
| 3.5 | `us_usuario` | 3.16 | `es_condicion` |
| 3.6 | `us_rol` | 3.17 | `es_convocatoria` |
| 3.7 | `us_permiso` | 3.18 | `es_mesa_examen` |
| 3.8 | `us_usuario_rol` | 3.19 | `es_mesa_inscripcion` |
| 3.9 | `us_rol_permiso` | 3.20 | `pr_preinscripcion` |
| 3.10 | `us_modulo` | 3.21 | `pr_ventana` |
| 3.11 | `us_usuario_modulo` | 3.22 | `es_grupo_horario` |

**Sin cambios de modelo:** `es_mesa_examen.estado` conserva
`DEFAULT 'planificada'` sin backfill (decisión 2026-10-06, derivación al leer);
`es_convocatoria` no tiene `fecha_mesa` (PD-14, columna eliminada).

**Criterio:** `Base.metadata.create_all` sobre SQLite (unit) no lanza error de
declaración; los índices/únicos declarados coinciden con §3; ninguna tabla
extra ni faltante (22/22: 12 en T2 + 10 en T3).

### S5 — Migración inicial de Alembic

Una revisión `initial` que crea las **22 tablas** de §3 + constraints + índices
+ las **2 vistas** del DDL (`vw_mesa_con_alumnos` §3.18, `vw_ventana_vigente`
§3.21) + el trigger `trg_set_updated_at` (§1: función `set_updated_at()`),
verificable en modo offline: `alembic upgrade head --sql` emite el DDL completo
sin conexión.

**Criterio:** `alembic upgrade head --sql` sale 0 y el SQL contiene las 22
tablas; `alembic check`/`history` sin errores.

### S6 — Health check y OpenAPI

- `GET /healthz` → 200 con `{status, version, environment, db}` (db ping
  best-effort; degrada a `db: "unavailable"` sin tumbar el endpoint).
- `/openapi.json` servido por FastAPI; tags por dominio.

### S7 — Tooling de verificación

- `ruff check .` sin errores (reglas: E, F, I, UP, B).
- `pytest` verde: unit tests de config (producción sin pool), seguridad
  (hash/verify Argon2id, expiración JWT), healthz (TestClient).
- `pyproject.toml` con extras `dev`; `.env.example` documentado.

---

## Tasks

| ID | Specs | Ruta | Estado | Commit / evidencia |
|----|-------|------|--------|--------------------|
| T1 | S1, S2, S3, S6, S7 | inline | verificado 2026-10-12 | `ruff check .` → All checks passed; `pytest` → 19 passed. Commit `f23f775` (registrado en L7). |
| T2 | S4 (§3.1–§3.12: `pe_*`, `us_*`) | inline (delegación rechazada por permisos, ver L6) | verificado 2026-10-12 | `ruff check .` → All checks passed; `pytest` → 22 passed; conteo 12/12. Commit `59afbe3` (registrado en L7). |
| T3 | S4 (§3.13–§3.22: `es_*`, `pr_*`) | inline | verificado 2026-10-12 | `ruff check .` → All checks passed; `pytest` → 26 passed; 22/22 tablas. Commit `5da6d3f` (registrado en L9). |
| T4 | S5 | inline | verificado 2026-10-12 | `ruff check .` → All checks passed; `pytest` → 26 passed; `alembic history` OK; `alembic upgrade head --sql` → exit 0 (22 tablas + 26 índices + 2 vistas + 18 triggers + función §1.6). Commit `4ad3e60` (registrado en L10). |

---

## Log

- **L1 (2026-10-12) — petición original, verbatim:**
  "podemos seguir trabajando? ya estoy deseoso de ver como quedará el backend
  luego de tanto proceso de análisis"
- **L2 (2026-10-12) — aclaración de alcance, verbatim:**
  "dale, incluye los modelos, suena a que seria optimo asi"
  → S4 incluye las 23 tablas en SDD-0 (no sólo infraestructura).
- **L3 (2026-10-12) — corrección de integridad:** el orchestrator afirmó en un
  mensaje progreso inexistente (feature document, T1, commit `0f7c3ad`, review
  lineage); verificado contra disco: HEAD en `6b27763`, `app/` y el doc no
  existen. Se reinicia con evidencia verificada por comando.
- **L4 (2026-10-12) — entorno verificado:** Python 3.14.7, pip 26.2.1; sin
  Docker, sin psql, sin uv → verificación de migración en modo offline;
  integración con PG queda pendiente de string de conexión (pregunta abierta
  al usuario, no bloqueante para SDD-0).
- **L5 (2026-10-12) — estrategia de entrega, verbatim:**
  "Cadena en rama feature (Recomendado)" → `feature-branch-chain`: commit por
  task en `feat/sdd-0-bootstrap`, un único PR contra `main` al cerrar SDD-0.
  T1 verificado: `ruff check .` → All checks passed; `python -m pytest` →
  19 passed. Runtime bloquea crear rutas `.env*` → el template se llama
  `env.example` (desviación documentada, ver README). Esquema de §3: son
  **22 tablas** (3.1–3.22), no 23; la cuenta incluía un comentario `-- CREATE
  TABLE`.
- **L6 (2026-10-12) — T2 inline + sonda empírica:**
  - El delegado writer fue rechazado (`permission.rejected: subagent`), así
    que T2 se escribió inline siguiendo el logbook.
  - Sonda SQLite: `create_all` acepta `DEFAULT now()`/`gen_random_uuid()`
    (fallarían sólo al insertar; los tests sólo crean tablas) → fidelidad
    total al DDL de §3, sin dialect hacks para los defaults.
  - Fidelidad de índices: se implementan **exactamente los de §3**. §1.5 pide
    `idx_{tabla}_activa` en toda tabla con soft delete, pero §3 sólo la
    declara en `pe_persona` → divergencia §1.5 vs §3 **pendiente de decisión
    del usuario** (no se agregaron índices no pedidos).
  - `us_sesion.ip` modelado como `String(45).with_variant(INET,
    "postgresql")`: inet real en PG, varchar en SQLite.
  - Evidencia T2: `ruff check .` → All checks passed; `pytest` → 22 passed;
    conteo de metadata → 12 tablas (4 `pe_*` + 8 `us_*`).
- **L7 (2026-10-12) — hashes, assess de T2 y decisión de nombres:**
  - Commits: T1 = `f23f775`, T2 = `59afbe3` (ambos pusheados a
    `feat/sdd-0-bootstrap`).
  - Assess T2 (`--base-ref f23f775`): `risk=medium`,
    `review_due=false`, `reason=under_budget` → **queda pendiente en la
    slice** hasta que un commit alcance el presupuesto. Boundary actual:
    `59afbe3`.
  - [DECISIÓN TÉCNICA] Sonda empírica de naming: la convention
    `ck_%(table_name)s_%(constraint_name)s` REESCRIBE los CHECK con nombre
    explícito (`ck_ventana` → `ck_pr_ventana_ck_ventana`), lo que hace
    imposible reproducir los nombres del DDL (`ck_convocatoria_ventana`,
    `ck_ventana`). Cambio en `app/db/base.py`: `"ck": "%(constraint_name)s"`
    (pass-through — §3 es la fuente de verdad; el patrón §1.2
    `ck_{tabla}_{regla}` se aplica al elegir el nombre). En consecuencia
    `UsSesion` (T2) pasó de `estado_valido` a
    `ck_us_sesion_estado_valido` para conservar el mismo nombre resultante.
    Unnamed check + convention que exige `constraint_name` = error
    (validado): todo CHECK ahora lleva nombre explícito.
  - Los `CREATE VIEW` de §3 (`vw_mesa_con_alumnos`, `vw_ventana_vigente`)
    quedan **en T4** (S5 ampliado): no hay mapeo ORM para vistas.
  - Dos slips de generación corregidos antes de verificar en T3 (walrus en
    `es_taller` y en `activa`); verificados por releo + suite.
- **L8 (2026-10-12) — T3 verificado:** `ruff check .` → All checks passed;
  `python -m pytest -q` → 26 passed; conteo → **22/22 tablas** (12 de T2 +
  10 de T3). Unnamed checks de §3.18/§3.19/§3.20 nombrados según §1.2
  (`ck_es_mesa_examen_estado`, `ck_es_mesa_inscripcion_estado`,
  `ck_pr_preinscripcion_estado`); los nombrados por el DDL se conservan
  verbatim (`ck_convocatoria_ventana`, `ck_ventana`, `uq_ventana_anio`).
  `pr_preinscripcion` sin FK hacia otros dominios (test dedicado).
- **L9 (2026-10-12) — T3 hash/assess + T4 migración inicial:**
  - T3 commit `5da6d3f`; assess T3 (`--base-ref 59afbe3`): `risk=medium`,
    `review_due=false`, `reason=under_budget` → pendiente en la slice.
    Boundary: `5da6d3f`.
  - T4 (S5): scaffold `alembic.ini` + `alembic/env.py` (async sobre asyncpg;
    prioridad `MIGRATE_DATABASE_URL` > `DATABASE_URL` sin `-pooler` con aviso
    en log — §0/PD-06; en offline sólo normaliza el driver a
    `postgresql+asyncpg` para elegir dialecto, nunca conecta) +
    `alembic/script.py.mako`.
  - `alembic/versions/0001_initial.py` **generado desde analisis.txt §3**
    (script de una corrida en temp, fidelidad por construcción — sin
    transcripción manual): 22 `CREATE TABLE` + 19 `CREATE INDEX` + 7
    `CREATE UNIQUE INDEX` + 4 `COMMENT ON` + 2 `CREATE VIEW` + función §1.6 +
    18 `CREATE TRIGGER` (una por tabla con `updated_at`; junctions y
    `us_sesion` no la tienen). Orden FK: bloque `es_grupo_horario` (§3.22)
    movido **antes** de `es_mesa_examen` (§3.18) y las vistas **después** de
    todas las tablas (`vw_mesa_con_alumnos` referencia a
    `es_mesa_inscripcion`, que en el fuente aparece después de la vista) —
    notas de orden que el propio §3 exige y que el orden literal del DDL no
    cumpliría.
  - `pyproject.toml`: `known-third-party = ["alembic"]` — el directorio local
    `alembic/` hacía que ruff lo clasifique como first-party y reordenara mal
    los imports de `env.py`.
  - `env.example`: nota de `MIGRATE_DATABASE_URL` (override explícito para
    migraciones).
  - Evidencia T4: `ruff check .` → All checks passed; `pytest -q` → 26 passed;
    `alembic history` → `<base> -> 0001 (head)`; `alembic upgrade head --sql`
    → exit 0 con 23 `CREATE TABLE` (las 22 de §3 + `alembic_version` de
    Alembic), 26 índices, 2 vistas, 18 triggers, 1 función, 4 `COMMENT ON`;
    el orden en el SQL emitido muestra `es_grupo_horario` antes que
    `es_mesa_examen` y las vistas al final. **Pendiente (decisión del
    usuario):** `alembic check` y el apply real requieren una base viva
    (Neon host directo) — nada se aplicó a ninguna base.
- **L10 (2026-10-12) — T4 commit/assess y SDD-0 verde:** T4 = `4ad3e60`;
  assess (`--base-ref 5da6d3f`): `risk=medium`, `review_due=false`,
  `reason=under_budget` → pendiente en la slice. Boundary: `4ad3e60`.
  **T1–T4 verificados: SDD-0 cierra con las 4 tareas.** Quedan abiertos:
  (a) review T1 (lineage `review-80252fe1ce29f8b7`, 4 lentes, state
  `reviewing`, bloqueado en `provider_failed` — retomar SOLO con el STATUS
  exacto de esa transacción; no se reconstruye desde prosa); (b) assess de
  T2–T4 pendientes de presupuesto en la slice; (c) apply de la migración a
  una base viva + `alembic check` — decisión del usuario (Neon host directo);
  (d) push/PR según política del usuario. Evidencia de rama:
  `f23f775` → `59afbe3` → `5da6d3f` → `4ad3e60`, todos pusheados.
- **L11 (2026-10-12) — PR abierto:** el usuario eligió instalar GitHub CLI
  (zip portátil en `%LOCALAPPDATA%\Programs\GitHubCLI` + PATH de usuario; el
  MSI por winget pidió elevación y falló con 1602). `gh auth login` lo completó
  el usuario (cuenta `formulariosepetn36-ai`, scopes `repo`/`workflow`).
  **PR #1**: https://github.com/formulariosepetn36-ai/backend-epet-n36/pull/1
  — `feat/sdd-0-bootstrap` → `main`; título convencional en inglés, cuerpo en
  español neutro con Chain Context: `size:exception` aceptado (elegido por el
  usuario en L5, "un único PR contra main"), presupuesto real
  **+7617/−179 en 48 archivos** (~4557 de documentación de análisis — `main`
  sólo tenía la instantánea `53fceb4` — + ~3060 de backend), diagrama de
  dependencias, verificación y fuera de alcance.
- **L12 (2026-10-13) — PR #1 mergeado y migración aplicada a Neon:** merge
  `bef477c` (11:52 UTC). El usuario autorizó el apply y corrigió su `.env`
  (`?sslmode=require` → `?ssl=require`; asyncpg rechaza `sslmode`, es parámetro
  de libpq). Preflight: `public` con 0 objetos → `alembic upgrade head` falló
  (sintaxis: `ck_convocatoria_ventana CHECK(...)` sin `CONSTRAINT`) → rollback
  transaccional total, verificado por inventario antes de reintentar.
- **L13 (2026-10-13) — Fix DDL (PR #2) y cierre con base aplicada:** commit
  `e604c9e` → merge `43729b3`. Dos defectos de §3 detectados SÓLO por ejecución
  en Postgres vivo (offline `alembic upgrade head --sql` no parsea; SQLite
  acepta `ck_x CHECK(...)` como columna sin tipo): (a) 3 constraints con nombre
  sin keyword `CONSTRAINT` en `analisis.txt` §3 y `0001_initial.py`; (b) 8
  uniques con shorthand inline `NOT NULL UNIQUE` (Postgres los autonombra
  `<tabla>_<col>_key`) vs `uq_<tabla>_<columna>` de los modelos → `alembic check`
  marcaba 16 operaciones remove/add. Fix en ambos archivos + 4 tests de
  regresión (`tests/unit/test_migration_ddl.py`, RED→GREEN observado; ruff + 30
  tests). Re-aplicación: `downgrade base` → `upgrade head` (1 caída transitoria
  `WinError 121`, reintento exitoso) → **`0001 (head)`, 25 objetos = 22 tablas +
  `alembic_version` + 2 vistas, `alembic check` limpio**. Asses `e604c9e`:
  medium/under_budget. **SDD-0 cierra mergeado (PR #1 + PR #2) y con la base
  real aplicada.**
