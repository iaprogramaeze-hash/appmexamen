# Backend EPET36

API backend para mesas de examenes (SIGME / SIGME-M) y preinscripcion de la
landing. Analisis completo en `analisis/` (docs 00-11) y fuente original en
`analisis.txt`.

## Stack (analisis.txt 0)

- FastAPI + Pydantic v2
- PostgreSQL (Neon) con SQLAlchemy 2.0 declarativo
- Alembic (migraciones)
- JWT access + refresh con rotacion; Argon2id

Restriccion operativa: despliegue serverless en Vercel -> en produccion se
retira el pool TCP de SQLAlchemy; las migraciones corren desde CI/local sobre
la conexion directa (host sin `-pooler`).

## Estructura (analisis.txt 5)

Organizacion por dominio: `app/features/<dominio>/{router,service,repository,models,schemas}.py`.
Los routers solo conocen HTTP; la logica vive en `service.py` sin importar
FastAPI; solo `app/api/v1/api.py` importa todos los routers.

## Auth (SDD-1, analisis.txt 2 y 6)

Endpoints bajo `/api/v1/auth`:

| Metodo  | Ruta              | Respuesta                             |
| ------- | ----------------- | ------------------------------------- |
| POST    | `/auth/login`     | `TokenPair` (access + refresh)        |
| POST    | `/auth/refresh`   | `TokenPair` (rota el par)             |
| POST    | `/auth/logout`    | 204 (revoca la sesion)                |
| POST    | `/auth/logout-all`| 204 (revoca todas las sesiones)       |
| POST    | `/auth/cambiar-clave` | `AccessOnly` (access nuevo)       |
| GET     | `/yo`             | `YoResponse` (usuario, roles, permisos, modulos) |

Tokens:

- **Access**: JWT ES256 con `kid`, TTL 15 minutos. Claims obligatorios
  `iss, aud, exp, nbf, iat, jti, sid, ver, sub` mas `roles`, `permisos` y
  `modulos` (autoriza sin consulta a BD). El claim `ver` es
  `us_usuario.token_version`: al cambiar clave o bloquear la cuenta sube, y
  los access ya emitidos mueren aunque tengan TTL pendiente; `logout-all`
  revoca todas las sesiones (los access y refresh previos dejan de servir).
- **Refresh**: opaco de 32 bytes, TTL 7 dias; en la base se guarda SOLO su
  hash SHA-256. Cada uso rota el par (emite refresh nuevo y revoca el
  anterior); presentar un refresh ya usado revoca la familia completa
  (`refresh-reutilizado`) y exige login nuevo.

Rate limit de login (PD-27): 5 fallos por usuario en 15 minutos (límite por
cuenta; no distingue origen ni IP) -> 429 con
`Retry-After` y cuenta bloqueada 15 minutos (`us_usuario.bloqueado_hasta`).

Autorizacion (§2.7 y §2.8): cada endpoint declara su permiso con
`require_permiso(<codigo>)` y su app con `require_modulo(<codigo>)`
(`app/features/auth/dependencies.py`). `us_modulo` define a que aplicacion
puede entrar el usuario (`landing`, `sigme_web`, `sigme_mobile`); el permiso
define que puede hacer adentro. Faltan ambos: 403 `permiso-denegado` /
`modulo-no-asignado`. El login tambien rechaza modulo no asignado (403
`modulo-no-asignado`, sin contar intento fallido).

Contrato de error (PD-24, forma unica en toda la API):
`{"code": "clase-de-problema", "detail": "mensaje", "errors": [ ... ]}` —
`errors[]` SOLO en 422. Codes de auth: `no-autenticado`, `token-expirado`,
`token-invalido`, `sesion-revocada`, `credenciales-invalidas`,
`cuenta-suspendida`, `refresh-invalido`, `refresh-reutilizado`,
`clave-invalida`, `permiso-denegado`, `modulo-no-asignado`.

## SIGME (SDD-2, analisis.txt 6)

Endpoints bajo `/api/v1/sigme` (SIGME Web, RBAC):

| Metodo | Ruta | Permiso / modulo | Notas |
| ------ | ---- | ---------------- | ----- |
| GET    | `/personas` | `persona.listar` | filtro `?q=` (documento/apellido/nombre) |
| GET    | `/personas/{id}` | `persona.listar` | 404 `persona-no-encontrada` |
| POST   | `/personas` | `usuario.gestionar` | 409 `persona-duplicada`, 422 `documento-tipo-invalido` |
| PATCH  | `/personas/{id}` | `persona.modificar` | campos mutables; identidad inmutable en v1 |
| GET    | `/usuarios` | `usuario.gestionar` | con `roles` por codigo; sin `password_hash` |
| POST   | `/usuarios` | `usuario.gestionar` | sobre persona existente; 404/409/422 |
| GET    | `/roles` | `usuario.gestionar` | catalogo con permisos por codigo |
| POST   | `/roles` | `usuario.gestionar` | 409 `codigo-existente` |
| GET    | `/permisos` | `usuario.gestionar` | catalogo cerrado (13, §2.7) |
| POST   | `/permisos` | `usuario.gestionar` | 409 `codigo-existente` |
| GET    | `/modulos` | `usuario.gestionar` | `landing`, `sigme_web`, `sigme_mobile` |
| POST   | `/modulos` | `usuario.gestionar` | 409 `codigo-existente` |
| GET    | `/orientaciones` | modulo `sigme_web` | |
| POST   | `/orientaciones` | `usuario.gestionar` | 409 `orientacion-existente` |
| PATCH  | `/orientaciones/{id}` | `usuario.gestionar` | 404 `orientacion-no-encontrada` |
| GET    | `/cursos` | modulo `sigme_web` | filtro `?orientacion_id=` |
| POST   | `/cursos` | `usuario.gestionar` | 404 `orientacion-no-encontrada` |
| PATCH  | `/cursos/{id}` | `usuario.gestionar` | 404 `curso-no-encontrado` |
| GET    | `/materias` | modulo `sigme_web` | filtro `?curso_id=` |
| POST   | `/materias` | `usuario.gestionar` | 404 `curso-no-encontrado` |
| PATCH  | `/materias/{id}` | `usuario.gestionar` | 404 `materia-no-encontrada` |
| GET    | `/condiciones` | modulo `sigme_web` | |
| POST   | `/condiciones` | `usuario.gestionar` | 409 `condicion-existente` |
| PATCH  | `/condiciones/{id}` | `usuario.gestionar` | PD-02: `limite_materias` editable |

Semilla (PD-03 + PD-02): la migracion `0003` siembra los 5 roles con su
matriz rol x permiso (doc 02 §2.4, celda PENDIENTE nunca otorga) y las 3
condiciones por defecto (`Previa`=3, `Regular`=8, `Libre`=NULL); es
idempotente (`ON CONFLICT DO NOTHING`). En dev/test, ademas,
`app/features/usuarios/seed.py` y `app/features/catalogo/seed.py` ofrecen la
misma data programatica.

Notas de diseno (asunciones cerradas en SDD-2):

- `POST /personas` y `POST`/`PATCH` de catalogo usan `usuario.gestionar`
  como gate temporal: la matriz §2.4 no define codigo de permiso para esas
  acciones (hueco declarado en doc 05); no se inventaron codigos nuevos.
- `POST /usuarios` no asigna roles ni modulos (CU-09: "roles/modulos por
  separado"; §6 no declara ese endpoint).
- `GET /usuarios/{id}` y `DELETE` de catalogo quedan fuera: §6 no los
  declara.
- La asignacion rol x permiso no tiene endpoint: vive en la semilla.

## SIGME — mesas y convocatorias (SDD-3, analisis.txt 6)

Endpoints bajo `/api/v1/sigme` (SIGME Web, RBAC); todos exigen JWT (la
superficie publica sigue siendo solo `POST /preinscripcion`, verificado por
`tests/unit/test_superficie_publica.py`).

| Metodo | Ruta | Permiso / modulo | Notas |
| ------ | ---- | ---------------- | ----- |
| GET    | `/convocatorias` | modulo `sigme_web` | orden por fecha de inicio desc |
| POST   | `/convocatorias` | `usuario.gestionar` | nace en su estado derivado (C-01) |
| PATCH  | `/convocatorias/{convocatoria_id}` | `usuario.gestionar` | CHECK de ventana sobre valores resultantes (422 con `errors[]`) |
| GET    | `/ventanas-preinscripcion` | modulo `sigme_web` | todas las ventanas con `vigente` derivado (A-SDD3-5) |
| POST   | `/ventanas-preinscripcion` | `usuario.gestionar` | upsert por `anio_lectivo`; 409 `ventana-solapada` (RN-035); 201/200 dinamico |
| POST   | `/grupos` | `mesa.crear` | RB-28: grupo + N = materias x-condiciones mesas; 409 `grupo-duplicado` / `mesa-duplicada` (PD-13: la hora NO participa en `uq_mesa_unica`) |
| PATCH  | `/grupos/{grupo_id}` | `mesa.modificar` | RB-29: mueve grupo y mesas en la MISMA transaccion; con ventana abierta → 409 `ventana-abierta` (PD-12/RB-17) |
| GET    | `/grupos` | `mesa.listar` | `?convocatoria_id=` requerido |
| GET    | `/mesas` | `mesa.listar` | RB-22: solo mesas con inscripcion activa; filtros `?convocatoria_id=&materia_id=&condicion_id=` |
| GET    | `/mesas/por-fecha` | `mesa.listar` | RB-23: `?desde=&hasta=` obligatorios, rango inclusive |
| GET    | `/mesas/{mesa_id}` | `mesa.listar` | RB-22 + estado DERIVADO: vencida → `cerrada` (A-SDD3-6, sin escritura) |
| PATCH  | `/mesas/{mesa_id}` | `mesa.modificar` | CU-20: reasigna materia/condicion; snapshots RB-11 recalculados en la misma transaccion; 409 `mesa-duplicada` |
| GET    | `/cobertura-mesas` | `mesa.listar` | RB-31: `?convocatoria_id=`; pares materia x condicion SIN mesa (advisory, PD-15) |

Notas de reglas clave (SDD-3):

- RB-22 (vida): las 3 lecturas de CU-19 devuelven solo mesas con AL MENOS
  UNA inscripcion activa (`estado='inscripto'`, sin borrar); las recien
  creadas no aparecen pero tampoco se borran.
- Vencidas (7 fuentes): dejan de listarse en SIGME (fecha/hora BA, UTC-3
  fijo); el detalle por id las muestra con estado derivado `cerrada` — la
  columna `estado` no se escribe (CU-22 / ME-03).
- PD-12 (cerrado 2026-10-22): crear grupo con ventana de inscripcion
  abierta esta permitido (alta aditiva); MOVER no — 409 hasta que cierre:
  las fechas nunca cambian bajo alumnos ya inscriptos (RB-17).
- RB-28/29: el grupo es SOLO fecha+hora; las 4 copias `_nombre` de cada
  mesa son snapshots inmutables que se recalculan solo al crear la mesa o
  reasignarla (RB-11); nunca por un renombre del catalogo.
- RB-31 (cobertura): reporte de consulta, no un gate — nada lo usa para
  rechazar operaciones; se consulta antes de abrir la ventana.

## Inscripciones y consultas de alumno (SDD-4, analisis.txt 6)

Endpoints a raíz bajo `/api/v1/` **SIN prefijo de dispositivo** (L2):
el contrato es el mismo para web, móvil o webhook. Gate por SESIÓN VÁLIDA
(`get_current_principal`) o permiso — nunca por módulo/dispositivo.

| Metodo  | Ruta                         | Permiso / session         | Notas |
| ------- | ---------------------------- | ------------------------- | ----- |
| GET     | `/convocatoria-vigente`      | sesión válida             | convocatoria `abierta` si existe, si no `activa` más reciente; estado derivado (A-SDD4-1) |
| GET     | `/mesas-disponibles`         | `mesa.listar`             | mesas vivas de la vigente, **sólo dentro de la ventana** (RB-07/RB-23) → 409 `ventana-cerrada`; RB-22 NO aplica (A-SDD4-2: mesas sin inscripciones SÍ); G-04 cascada orientación→curso→materia→condición desde combinaciones únicas; RN-019: sin `grupo_id` |
| POST    | `/inscripciones`             | `inscripcion.crear`       | cuerpo `{materia_id, condicion_id}` (RB-30; convocatoria NUNCA en cuerpo, A-SDD4-4); validaciones en orden: 404 `convocatoria-no-encontrada` → 409 `ventana-cerrada` → 404 `materia/condicion-no-encontrada` → 409 `inscripcion-duplicada` (RN-006, reintento E-13 idempotente) → 409 `limite-materias` (RN-013/PD-02, NULL=sin límite) → 409 `mesa-no-disponible` (A-SDD4-5); crea fila `inscripto` eligiendo mesa de fecha más próxima (A-SDD4-6 determinismo) |
| GET     | `/inscripciones`             | `inscripcion.listar`      | listado gestión (CU-23): filtros `?mesa_id=&convocatoria_id=`; 404 si filtro inexistente; orden `inscripto_en` desc; INS-03 (anulación secretaría) FUERA |
| GET     | `/mis-inscripciones`         | `inscripcion.listar`      | CU-38: **sólo las propias**; estado + nombres materia/condición + `fecha`/`hora` mesa; sin paginación (A-SDD4-9); lectura disponible con ventana cerrada (RB-07) |
| DELETE  | `/mis-inscripciones/{id}`    | `inscripcion.anular`      | CU-39/INS-02: **sólo la propia** (otro/inexistente → 404); **sólo dentro de ventana** (RB-08b) → 409 `ventana-cerrada`; `inscripto` → `anulado` (fila conservada, libera `uq_inscripcion_unica`); ya `anulado` → 204 idempotente (PD-25); reinscribir tras anular = fila NUEVA (CU-40) |
| POST    | `/dispositivos`              | sesión válida             | registra/actualiza (upsert por `device_id` del usuario); sin permiso extra |
| GET     | `/dispositivos`              | sesión válida             | lista propios, orden `created_at` desc |
| DELETE  | `/dispositivos/{id}`         | sesión válida             | soft delete idempotente (PD-25); 404 si ajeno/inexistente |

PDs cerrados en SDD-4 (asunciones A-SDD4-1..9): A-SDD4-1 (vigente=abierta/activa/404), A-SDD4-2/PD-23 (RB-22 no aplica a mesas-disponibles), A-SDD4-3/G-04 (cascada desde combinaciones únicas), A-SDD4-4 (convocatoria no en body), A-SDD4-5/PD-19 (`mesa-no-disponible` 409), A-SDD4-6 (mesa más próxima determinista), A-SDD4-8 (email fuera), A-SDD4-9 (sin paginación v1).

Superficie pública (verificada por `tests/unit/test_superficie_publica.py`): **sólo** `POST /preinscripcion` queda pública sin JWT; todos los endpoints de SDD-4 exigen sesión o permiso.

## Reportes de cierre (SDD-5, analisis.txt 6)

Endpoints bajo `/api/v1/reportes/` con permiso `reporte.exportar`
(roles: secretario, director, administrador, superadmin — **NO alumno**).
Aplican **RB-22 (vida)**: solo mesas con ≥ 1 inscripción `inscripto` activa.
Aplican **RB-19 (snapshots)**: nombres desde `es_mesa_examen` (NO catálogo actual).
Cada descarga/impresión registrada en `aud_evento` (PD-05).

| Metodo | Ruta | Descripción |
|--------|------|-------------|
| GET | `/reportes/permiso-examen/{usuario_id}` | Individual por alumno: mesas con inscripción activa + snapshots (fecha, hora, materia, condición, orientación, curso). Orden fecha asc, hora asc. |
| GET | `/reportes/permisos-examen?convocatoria_id=` | Masivo agrupado por mesa: para cada mesa con inscriptos, lista alumnos con sus materias/condiciones. `convocatoria_id` opcional (default: vigente). |
| GET | `/reportes/acta-volante/{mesa_id}` | Por mesa: alumnos inscriptos + snapshots. 404 `mesa-sin-inscriptos` si RB-22 falla. |
| GET | `/reportes/mesa/{mesa_id}` | Snapshot de mesa (RB-11/12) + estado derivado por fecha/hora BA vs hoy: `planificada` (futuro/hoy) / `cerrada` (pasado). |
| GET | `/reportes/planilla-grupos/{convocatoria_id}` | Por convocatoria: grupos ordenados fecha/hora con sus mesas (materia, condición). Vista de horario, sin detalle de alumnos. RB-22: solo grupos con mesas que tengan inscriptos. |

PDs relacionadas: PD-05 (auditoría reportes en `aud_evento`), NFR-003 (latencia p95 ≤ 2000 ms).

## Comandos

```bash
python -m pip install -e ".[dev]"   # dependencias
ruff check .                        # lint
python -m pytest                    # tests unit (SQLite/aiosqlite)
alembic upgrade head --sql          # DDL de la migracion, sin conexion
```

Variables: copiar `env.example` a `.env` (nunca commitear `.env`; el template
se llama `env.example` porque el runtime bloquea crear rutas `.env*`).
