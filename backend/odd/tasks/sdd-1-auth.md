# SDD-1 — Seguridad y autenticación (§2 + endpoints /api/v1/auth)

- **Objetivo:** login/refresh/logout con rotación y reuse detection, RBAC por
  permisos/módulos, contrato de error único y los endpoints de `/api/v1/auth`.
- **Branch:** `feat/sdd-1-auth` (desde `43729b3`). **Estrategia:**
  `feature-branch-chain` (cacheada del SDD-0): work-unit commits en la rama,
  **un único PR contra `main` al cerrar** (= `size:exception` por forecast
  > 400 líneas). **Runner:** `python -m pytest` + `python -m ruff check .`
- **Mapa de progreso (% honestos por hito):** exploración+doc = 10% · T1 = 25%
  · T2 = 45% · T3 = 70% · T4 = 85% · T5 (docs+PR) = 100%.

## Specs

Citas textuales de `analisis.txt` §2 (líneas 109–184) y §6 (1045–1154), la
fuente de requisitos de este feature.

- **S1 — Access Token (§2.1):** "TTL corto: 15 minutos (máx. 30)."
  "Asimétrico: RS256 o ES256 con kid, para rotación de claves."
  "Claims obligatorios: iss, aud, exp, nbf, iat, jti, sid, ver, sub."
  "En el payload: roles, permisos y módulos (para autorizar sin consulta)."
  "Nunca datos sensibles en el payload (JWT es sólo firmado, no cifrado)."
- **S2 — Refresh Token (§2.2):** "Opaco aleatorio (32 bytes), TTL 7 días."
  "ROTACIÓN: cada uso emite un refresh nuevo y revoca el anterior."
  "REUSE DETECTION: si llega un refresh ya usado -> se revoca toda la familia
  de tokens y se exige login nuevo."
  "En base de datos se guarda SOLO el hash SHA-256."
- **S3 — Endpoints de auth (§2.4 + §6):** "POST /auth/login -> access + refresh",
  "/auth/refresh rota el par", "/auth/logout revoca la sesión",
  "/auth/logout-all revoca todas las sesiones del usuario",
  "/auth/cambiar-clave", "GET /yo".
  Rate limit (§2.4): "max 5 intentos fallidos por usuario/IP cada 15 minutos;
  tras ello bloqueo temporal (us_usuario.bloqueado_hasta)." PD-27 (§6):
  "5 fallos en 15 min (§2.4) → 429 + Retry-After Y cuenta bloqueada 15 min
  (bloqueado_hasta = now + 15 min); intentos_fallidos → 0 al vencer;
  token_version sube (§2.6)."
- **S4 — Contraseñas (§2.5):** "Algoritmo: Argon2id, m=19456 (19 MiB), t=2, p=1
  (OWASP Password Storage)." "Longitud mínima 12 caracteres. Nunca SHA-256 /
  MD5 puros."
- **S5 — Invalidación global (§2.6):** "us_usuario.token_version (claim "ver").
  Al cambiar la clave, cambiar un rol o bloquear la cuenta: subir token_version.
  Todo request valida ver == token_version vigente, así los access tokens ya
  emitidos mueren aunque tengan TTL pendiente."
- **S6 — RBAC (§2.7):** "usuario -> rol -> permiso, más asignación usuario ->
  módulo." Códigos exactos: "mesa.listar, mesa.crear, mesa.modificar,
  mesa.eliminar, inscripcion.listar, inscripcion.crear, inscripcion.anular,
  persona.listar, persona.modificar, usuario.gestionar, reporte.exportar,
  preinscripcion.crear, preinscripcion.listar." "Cada endpoint declara su
  permiso requerido vía dependencia de FastAPI."
- **S7 — Alcance por aplicación (§2.8):** "us_modulo contiene: 'landing',
  'sigme_web', 'sigme_mobile'." "El prefijo de módulo no reemplaza el permiso:
  módulo = a qué app puede entrar; permiso = qué puede hacer adentro."
- **S8 — Contrato de error (§6, PD-24):** `{ "code": "clase-de-problema",
  "detail": "mensaje", "errors": [ ... ] }` — "Content-Type: application/json.
  Forma ÚNICA, no varía por endpoint: "errors[]" SÓLO en 422; "code"
  kebab-case estable por clase (p. ej. "ventana-cerrada")."
- **S9 — Seed de permisos (§2.7):** los **13** códigos de S6 (verbatim de §2.7,
  líneas 163–166; la lista tiene 13, no 14 — corregido en L4) existen como
  `us_permiso` sembrados en la base de desarrollo/tests, junto con los 3
  módulos de §2.8 (`landing`, `sigme_web`, `sigme_mobile`); el modelo
  `us_permiso` ya está creado en el SDD-0.

### Assumptions (supuestos, marcados)

- **A1:** de "RS256 o ES256" elige **ES256** (llaves compactas para `.env`;
  ambos son aceptados por §2.1). `kid` fijo por keyset con rotación futura
  (S1 sólo exige el claim).
- **A2:** dev/test generan un keyset efímero si no hay claves en env;
  producción exige claves privadas en variables de entorno. `JWT_SECRET`
  (HS256) se **elimina**: §2.1 exige firma asimétrica (superficie mínima).
- **A3 — fuera de alcance de SDD-1:** `POST /auth/olvido-clave` y
  `POST /auth/restablecer-clave` (PD-04). Dependen de la cola obligatoria
  RB-25 (no existe aún) y de la tabla adicional `us_password_reset`. Se
  implementarán en la fase de infraestructura de colas.
- **A4:** el rate limit de login persiste en las columnas ya existentes de
  `us_usuario` (`intentos_fallidos`, `bloqueado_hasta`) — sin Redis (entorno
  serverless Vercel + Neon).
- **A5:** `security.py` (T1 del SDD-0) es base placeholder: su docstring ya
  remite a "fase SDD-1". Se corrigen sus divergias con §2 en T1: HS256 → ES256
  con `kid`, claims faltantes (`iss, aud, nbf, jti, sid`), Argon2 con defaults
  de librería → `m=19456, t=2, p=1`, y `typ="refresh"` JWT → refresh opaco.

## Tasks

| ID | Specs | Ruta | Estado | Commit / evidencia |
|----|-------|------|--------|--------------------|
| T1 | S1, S4, A1, A2, A5 | inline | ✅ hecha | RED (ImportError `generate_keypair`) → GREEN: 32 tests + ruff; commit en L3 |
| T2 | S2, S9 | inline | ✅ hecha | RED (ModuleNotFoundError) → GREEN: 43 tests + ruff; commit en L5 |
| T3 | S3, S5, S8 | inline | ✅ hecha | RED (17: 404s + `tokens` inexistente) → GREEN: 61 tests + ruff; commit en L7 |
| T4 | S6, S7 | inline | ✅ hecha | RED (ImportError `require_*`) → GREEN: 82 tests + ruff; commit en L9 |
| T5 | docs | inline | ✅ hecha | README/env.example + PR único: PR #3, commit `84cd740` (ver L10-L11) |

- Ruta por tarea: **inline** — secuencia dependiente y sin razón de writer
  (ni paralelismo ni backstop de contexto); el padre escribe siguiendo este doc.

## Log

- **L1 (2026-10-14) — petición verbatim:** "por lo que creas mejor, te dejo
  esta vez la decision, solo muestrame siempre el progreso en porcentaje, por
  favor"
- **L2 (2026-10-14) — decisión de alcance (delegada al orquestador):** SDD-1 =
  §2 seguridad/autenticación + endpoints `/api/v1/auth` de §6. Evidencia:
  `app/core/security.py` ya declara "El flujo de login, rotación y reuse
  detection vive en el dominio auth (fase SDD-1)"; §2.7 es dependencia de todos
  los endpoints siguientes (sigme/sigme-mobile declaran permisos vía FastAPI).
  Exploración: `analisis.txt` §2 (109–184) y §6 (1045–1154), `app/core/security.py`,
  `app/core/config.py`, `pyproject.toml` (argon2-cffi y PyJWT ya presentes;
  falta `PyJWT[crypto]` para ES256). Pendientes de análisis que NO entran
  (quedan abiertos): NFR-023, CU sin RN, divergencia §1.5 vs §3.
- **L3 (2026-10-14) — T1 completado (commit `0c3a6a3`):** RED observado (ImportError
  `generate_keypair`) → implementación GREEN: ES256 con `cryptography`
  (SECP256R1, PEM PKCS8), claims completos `iss/aud/exp/nbf/iat/jti/sid/ver/sub`
  + `roles/permisos/módulos` en el payload y `kid` en el header; Argon2 con
  parámetros explícitos `m=19456, t=2, p=1`; config con
  `JWT_PRIVATE_KEY/JWT_PUBLIC_KEY/JWT_KID/JWT_ISSUER/JWT_AUDIENCE` (producción
  las exige; sólo algoritmo ES256; `JWT_SECRET` eliminado por §2.1);
  `PyJWT[crypto]` en pyproject + instalación del extra. Suite: **32 passed,
  ruff limpio**. Candidato de review del commit de docs (`00ff849`): el usuario
  lo **declinó** vía defect handoff (dos `operation_timeout` consecutivos en
  `review status`; eligió "continuar sin reportar"; lineage
  `review-883c6cba62103c68`, sin recibo, entrega bajo política ordinaria).
- **L4 (2026-10-14) — corrección de S9 y estado del review:** al preparar T2
  verifiqué §2.7 (líneas 160–167) y la lista verbatim tiene **13** códigos de
  permiso, no 14 como decía S9 (error de transcripción del feature doc, no del
  análisis); S9 queda reescrito y el seed usa los 13 exactos. Review del
  candidato T1 (lineage `review-8f5a9572f3b2f628`): consentimiento granted,
  transacción creada, pero las 2 lentes (`review-risk` orden 0,
  `review-readability` orden 1) fallaron dos veces con
  `opencode_review_transport_relay_refused (provider_failed)` tras reofrecer
  el STATUS bound los mismos slots; sin receipt, transacción preservada en
  `collect` (misma clase de defecto que gentle-ai#4972, ocurrencias previas).
- **L5 (2026-10-14) — T2 completado (commit `bada5a7`):** RED observado
  (`ModuleNotFoundError: app.features.auth`) → implementación: refresh opaco
  `secrets.token_urlsafe(32)` del que se persiste sólo el hash SHA-256 hex en
  `us_sesion`; `create_session` / `rotate_session` (familia estable,
  `rotated_at`), reuse detection que revoca la familia completa,
  `revoke_session` / `revoke_all_sessions` (logout y logout-all de 2.4) y seed
  idempotente de los 13 permisos de §2.7 y los 3 módulos de §2.8. Fixture nueva
  `db_session` (SQLite en memoria sobre el metadata real, con los
  server_default de Postgres apagados sólo durante el DDL de test). Suite:
  **43 passed, ruff limpio**. Review del candidato T2: **pendiente al cierre**
  (el usuario pidió cerrar la jornada; la máquina de review sigue devolviendo
  `provider_failed`) — se retoma al inicio de la próxima sesión.
- **L6 (2026-10-19) — Review del slice T1+T2: interrumpido y declinado, con
  reporte canónico:** consentimiento **granted** → transacción creada (lineage
  `review-dee5998e2101c1c4`) → el STATUS bound devolvió `operation_timeout`
  (`pre_native`, 3ª ocurrencia de la clase en 5 días) → defect handoff: el
  usuario eligió **"Reportar el defecto y continuar"**. Búsqueda definitiva
  (abiertos+cerrados): la clase tiene origen en #5094 (cerrado NOT_PLANNED,
  "nueva issue linkeada por recurrencia") y hilo de ocurrencias #5422 (50+
  comentarios, sin fix publicado; ocurrencias reportadas hasta 4.2.0). Se
  posteó **un** comentario de ocurrencia con evidencia observada
  (privacy-scrubbed):
  https://github.com/Gentleman-Programming/gentle-ai/issues/5422#issuecomment-6266256249.
  Luego la continuación compartida: decline exacto validado
  (`declined_this_candidate`, target `sha256:33fe3aaf…`) y reentrada STATUS OK
  (transacción residual en `collect`, sin deuda nuestra). **El slice T1+T2
  queda sin revisar** (entrega bajo política ordinaria del repo); el próximo
  candidato vuelve a pedir consentimiento. Sin labels tocados; verificado que
  un POST malformado anterior con `gh api -f` no creó comentarios (422).
- **L7 (2026-10-19) — T3 completado (commit `ad96ec2`):** RED observado (17
  fallos: 404s de endpoints sin cablear + `ModuleNotFoundError app.features.auth.tokens`)
  → GREEN **61 tests + ruff limpio**. Se cierra **PD-24**: `exceptions.py`
  reescrito con códigos kebab-case estables (`no-encontrado`, `no-autenticado`,
  `token-expirado`, `token-invalido`, `sesion-revocada`, `credenciales-invalidas`,
  `cuenta-bloqueada`, `refresh-invalido`, `refresh-reutilizado`, `clave-invalida`,
  `error-validacion`, `error-interno`) + `register_error_handlers` en `main.py`
  (AppError / RequestValidationError con `errors[]` SÓLO en 422 / HTTPException
  / Exception sin filtrar internals). Endpoints: login con bloqueo PD-27 en base
  (5 fallos/15 min → 429 + Retry-After + `bloqueado_hasta` + `token_version`
  sube; reset al vencer y al loguear bien; 403 `cuenta-suspendida` si
  `bloqueado`), refresh (rotación; el 401 de reuse PERSISTE la revocación de la
  familia), logout/logout-all (204; el access muere al instante porque la
  dependencia valida `sid` activo), yo (identidad desde claims, §2.1) y
  cambiar-clave (sube `ver`, responde access nuevo). Dependencia
  `get_current_principal`: ES256 + `ver == token_version` (§2.6) + sesión activa.
  Decisiones de diseño (no en el análisis): `LoginRequest.modulo` (§2.8:
  `us_sesion.modulo_id` es NOT NULL); login sin min_length en password (la
  política de §2.5 rige al crear); cambiar-clave devuelve access nuevo en vez de
  forzar re-login; **bug real encontrado**: los PEM del `.env` van con `\n`
  literal y cryptography los rechaza → validador `_normalize_pem` en Settings
  (des-escapa y `""` → None); conftest fija `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY`
  vacíos (aislamiento del `.env` del usuario) e importa TODOS los modelos (FK
  cruzado `pe_persona` al correr un solo archivo); ruff `ignore B008`
  (Depends en defaults es el idioma de FastAPI).

- **L8 (2026-10-20) — Consulta del dev de sigme-m sobre tablas faltantes:**
  pregunta por `aud_evento`, `es_permiso_examen`, `es_permiso_inscripcion` y
  `us_password_reset`. Verificado contra el análisis: **planeadas** `aud_evento`
  (PD-05 cerrado 2026-10-06) y `us_password_reset` (PD-04 cerrado 2026-10-06);
  **no existen ni se planean** `es_permiso_examen`/`es_permiso_inscripcion` —
  el "permiso de examen" es un REPORTE impreso (§3/plan de análisis) servido
  por las tablas reales `es_mesa_examen` y `es_mesa_inscripcion`, ya creadas
  en la 0001. Implementación (commit `0344c1e`): migración
  `0002_auditoria_password_reset.py` con ambas tablas + modelos SQLAlchemy
  (`app/features/auditoria/models.py` y `UsPasswordReset` en usuarios) +
  7 tests nuevos → **76 tests + ruff limpio**. Decisiones de diseño: token con
  hash SHA-256 único (`uq_us_password_reset_token_hash`), uso único
  (`usado_en`) y expiración (`expira_en`); `aud_evento` append-only real
  (trigger `trg_aud_evento_append_only` bloquea UPDATE/DELETE en Postgres),
  `usuario_id` FK RESTRICT (un borrado físico no reescribe la bitácora) y
  snapshot JSONB sin password_hash/refresh tokens/hashes de sesión (regla
  PD-05, validable por el servicio a futuro). **Fuera de alcance** (se hacen
  en sus SDD): endpoints `/auth/olvido-clave` y `/auth/restablecer-clave`
  (esperan la cola de email obligatoria RB-25) y el servicio que escribe
  eventos de auditoría. El lint DDL (`test_migration_ddl.py`) ahora cubre
  todas las migraciones, no sólo la 0001.

- **L9 (2026-10-20) — T4 completado (RBAC, commit del feat):** RED observado
  (`ImportError: cannot import name 'require_modulo'`) → GREEN **82 tests +
  ruff limpio**. `require_permiso(codigo)` y `require_modulo(codigo)` viven en
  `app/features/auth/dependencies.py`, NO en `core/dependencies.py`: construyen
  sobre `Principal` y core no debe importar un dominio (el docstring de core
  queda con el puntero). Ambos leen los claims del token (§2.1: roles,
  permisos y módulos viajan "para autorizar sin consulta") — sin query por
  request; sin el permiso → 403 `permiso-denegado`, sin el módulo → 403
  `modulo-no-asignado` (códigos nuevos, convención PD-24). **Hueco real de S7
  cerrado**: el login sólo validaba que el módulo EXISTIERA; §2.8 exige "el
  usuario sólo puede operar en los módulos que tiene asignados" → ahora el
  login rechaza con 403 `modulo-no-asignado` y NO suma `intentos_fallidos`
  (no es fallo de credencial, el rate limit de PD-27 no aplica). En el camino:
  bug propio `select(UsUsuarioModulo.id)` — la tabla intermedia tiene PK
  compuesta y no tiene `id`. Naming: `require_permiso`/`require_modulo`
  (español, como el contrato previsto en el doc 5) y no `require_permission`
  (la fila T4 lo decía en inglés). 6 tests nuevos (`tests/unit/test_rbac.py`):
  endpoint con permiso → 200 / sin permiso → 403 sin `errors[]`, sin token →
  401, módulo asignado → 200 / no asignado → 403, y login con módulo no
  asignado → 403 + contadores intactos + login OK con el módulo asignado.
  **Aviso para sigme-m**: el login ahora puede responder 403
  `modulo-no-asignado` si el usuario no tiene esa app asignada.

- **L10 (2026-10-20) — intento de review RDD: BLOQUEADO por ambiente (no por
  código):** assess nativo dio `risk: high` / `review_due: true` (hot path
  auth). El ciclo avanzó hasta el collect `intended_untracked_selection_required`
  (el `.rar` untracked elegible). El shape exacto de
  `gentle-ai.review-intended-untracked-selection/v1` no está documentado en el
  CLI ni en capabilities; ~10 probes fallaron todos con el mismo error genérico
  hasta extraer el fuente v4.1.1 del Go module proxy: el JSON es
  `{"schema":"gentle-ai.review-intended-untracked-selection/v1","untracked_scope":"exclude|select","expected_untracked_inventory":"sha256:...","intended_untracked":[...]}`
  con `DisallowUnknownFields`; el discriminador `schema` es obligatorio y
  `intended_untracked` no puede ser null. **Aprendizaje**: PowerShell 5.1
  rompe las comillas embebidas al invocar procesos nativos (todos los probes
  llegaban con JSON mangleado — el error era por JSON roto, no por forma);
  solución: `[Diagnostics.ProcessStartInfo]` con command line crudo y `\"`
  escapadas (los decodifica `CommandLineToArgvW`). Con la selección válida
  (scope=exclude, el `.rar` queda fuera del candidato) la operación expiró
  SIEMPRE a los 25s: `reviewFacadeOperationTimeout = 25s` para todo salvo
  `review.start` (120s). Causa ambiental determinista (3/3 intentos + STATUS
  bare a 25.5s): con 360 Total Security activo (QHSafeTray) el spawn de git
  sube a ~270ms y el STATUS dispara ~80 llamadas git secuenciales → >25s.
  Cada timeout deja git huérfanos atascados (limpiables con Stop-Process).
  **Decisión**: no es defecto de gentle-ai (no corresponde reporte al repo
  upstream); la entrega queda bajo política ordinaria. Al volver, el usuario
  elige: (a) allowlist de `git.exe`/`gentle-ai.exe` en 360 Total Security,
  (b) reintentar el ciclo con la máquina más liviana, o (c) desactivar RDD con
  su switch (`gentle-ai review mode disable`) — el agente nunca lo toca.

- **L11 (2026-10-20) — T5 completado: SDD-1 CERRADO, PR #3 abierto:** README
  con la sección "Auth (SDD-1)" (tabla de endpoints `/api/v1/auth`, modelo de
  tokens ES256 + refresh opaco con rotación/reuse, rate limit PD-27, RBAC
  `require_permiso`/`require_modulo` con sus 403, contrato PD-24 con el
  vocabulario exacto de codes) y `env.example` con los TTLs/issuer/audience
  opcionales. 82 tests + ruff limpio antes del commit. `84cd740` docs(auth)
  empujado y **PR único** `#3` (feat/sdd-1-auth → main). SDD-1 completo: T1-T5
  ✅. Pendiente sólo del usuario: la decisión de L10 sobre el review.

- **L12 (2026-10-21) — Review ejecutado y abandonado (runtime sin relay) + fixes
  de findings aplicados:** el review nativo del candidato (lineage
  review-94a2c34a, 36 paths) capturó los 4 lenses y el refuter corrió 3 veces
  (veredictos: bloqueado sin enforcement, preinscripción sin auth y login-500
  corroborados en los 3 runs; keyset refutado en 2 de 3 — hardening
  out-of-domain, supuesto A2 — no aplica), pero opencode no ofrece vía de
  sometido del refuter (`capture-refuter`: "opencode has no Go-owned role
  capture contract"; live transport: `provider_failed` determinista ×7, no
  sanado por `opencode service restart`). Con consentimiento del usuario:
  `review abandon` liberó la autoridad sin recibo (entrega a política
  ordinaria). Fixes como commits ordinarios: (1) ELIMINADO
  `GET /preinscripcion/{id}` (decisión del usuario: nadie lo usa; exponía PII
  sin auth) + sus 2 tests; (2) §2.6/PD-27: cuenta `bloqueado` o
  `bloqueado_hasta` vigente ya no opera — `verificar_cuenta_operativa()` en
  `get_current_principal` y `refresh` (403 cuenta-suspendida / 429
  cuenta-bloqueada con Retry-After; la rotación sin commitear se descarta);
  (3) login con módulo inexistente ahora `DomainValidationError` (422 +
  errors[], PD-24) — era 500 sin errors[]; (4) README: rate limit documentado
  por-usuario real (sin dimensión IP, decisión del usuario) y `logout-all` por
  su observable real (revoca sesiones; no sube token_version); (5) tests
  nuevos: suspendida en /yo y refresh, bloqueo PD-27 en refresh, módulo
  inexistente 422, token-expirado, code sesion-revocada. RED observado (4
  failed) antes de los fixes; 85 tests + ruff verdes después.
