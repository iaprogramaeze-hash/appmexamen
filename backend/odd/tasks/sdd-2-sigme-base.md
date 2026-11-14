# SDD-2 — SIGME base: personas, usuarios, roles y catálogo (§6 /api/v1/sigme)

- Objetivo: implementar el primer bloque de endpoints RBAC de SIGME Web: personas,
  usuarios, roles/permisos/módulos y catálogo (orientaciones, cursos, materias,
  condiciones), más la semilla de roles/condiciones que los hace utilizables.
- Rama: `feat/sdd-2-sigme-base` desde `origin/main` (merge de SDD-1 = `337b046`).
- Delivery: work-unit commits en la rama; PR único a main (patrón de SDD-1).
- Test runner: `python -m pytest tests -q` + `python -m ruff check .`.
- Fuente de requisitos: `analisis.txt` §6 (1045-1154), §2.7-2.8, §3.1-3.16,
  §4; `analisis/02-actores-y-consumidores.md` §2.4 (matriz definitiva PD-03);
  `analisis/05-casos-de-uso-sigme.md` CU-05..CU-10.

## Specs

### S1 — Semilla de roles y asignación rol × permiso (T1)

- Fuente: matriz `analisis/02-actores-y-consumidores.md` §2.4, "DEFINITIVA —
  fuente de la semilla (PD-03, [CERRADO — 2026-10-06])".
- Roles sembrados por código (5): `alumno`, `secretario`, `director`,
  `administrador`, `superadmin` (columnas de la matriz).
- Asignación rol × permiso EXACTA según la matriz, celda `S` = asigna el
  permiso; celda `—` o `PENDIENTE` = NO asigna (denegar por defecto; el doc
  §2.4 dice "las celdas marcadas PENDIENTE son huecos de esta matriz que el
  cierre de PD-03 no cubrió — quedan visibles para el cliente, no se resuelven
  por silencio ni por suposición", por lo que un hueco nunca otorga permiso):
  - `alumno`: inscripcion.listar, inscripcion.crear, inscripcion.anular,
    mesa.listar
  - `secretario`: mesa.listar, mesa.crear, mesa.modificar, inscripcion.listar,
    inscripcion.anular, persona.listar, persona.modificar, reporte.exportar,
    preinscripcion.listar
  - `director`: mesa.listar, inscripcion.listar, persona.listar,
    reporte.exportar, preinscripcion.listar
  - `administrador`: todos salvo preinscripcion.crear (que no se asigna a
    nadie: "La landing escribe sin JWT (§2.9): el permiso no puede aplicarse
    allí. Dueño dentro de SIGME no determinado — PENDIENTE (G-02)")
  - `superadmin`: todos salvo preinscripcion.crear (mismo motivo)
- Semilla idempotente por código (patrón de `app/features/usuarios/seed.py`),
  ejecutable para tests.

### S2 — Semilla de condiciones (PD-02) (T1)

- Fuente: PD-02 cerrado: "los valores de `es_condicion.limite_materias` se
  siembran como default (Previa 3, Regular 8, Libre NULL)".
- Filas: `Previa` → `limite_materias = 3`; `Regular` → `8`; `Libre` → `NULL`.
- Idempotente por `descripcion` (única).

### S3 — Migración de datos para producción (T2)

- Fuente: PD-03: "los roles y los permisos viajan en la migración inicial de
  Alembic (datos estáticos, reproducibles en dev, staging y prod)".
- Migración Alembic `0003` idempotente (INSERT ... ON CONFLICT DO NOTHING)
  con la MISMA data de S1+S2 (permisos y módulos ya sembrados por SDD-0 se
  verifican presentes, no se reinsertan a ciegas si el ON CONFLICT lo cubre).
- La migración no importa código de `app/`; la data se replica inline.

### S4 — Personas (T3)

Endpoints (`app/features/personas/` router + service + schemas):
- `GET /api/v1/sigme/personas` → permiso `persona.listar`; lista personas no
  borradas lógicamente; filtro query opcional `?q=` (substring en documento /
  apellido / nombre).
- `GET /api/v1/sigme/personas/{id}` → `persona.listar`; 404 `code:
  "persona-no-encontrada"` si no existe o está borrada.
- `POST /api/v1/sigme/personas` → permiso `usuario.gestionar` (asunción A1);
  body: documento_tipo_id, documento, apellido, nombre, razon_social?,
  fecha_nacimiento?, sexo?, direccion?, nacionalidad?; 201 con la persona.
  Validaciones: tipo de documento existe y activo (422 `errors[]`);
  unicidad parcial (tipo, documento) entre no borradas → 409
  `code: "persona-duplicada"`.
- `PATCH /api/v1/sigme/personas/{id}` → permiso `persona.modificar`;
  campos mutables: apellido, nombre, razon_social, fecha_nacimiento, sexo,
  direccion, nacionalidad (asunción A2: identidad inmutable en v1);
  `documento_tipo_id` y `documento` NO mutables; 200 con la persona.
- Nunca exponer `password_hash` ni campos de sesión.

### S5 — Usuarios (T4)

- `POST /api/v1/sigme/usuarios` → permiso `usuario.gestionar`; body:
  persona_id, username, email?, password; 201 con el usuario sin
  `password_hash`. Validaciones: persona existe y no borrada (404
  `code: "persona-no-encontrada"`); username único entre no borrados → 409
  `code: "username-existente"`; email único (parcial, sólo si no nulo) → 409
  `code: "email-existente"`; política de contraseña reutilizada del core de
  SDD-1 (`app/core/security.py`) con la misma respuesta 422 `errors[]`.
  `password_hash` con el mismo algoritmo que auth. No asigna roles
  (CU-09: "roles/módulos por separado"; §6 no declara endpoint de asignación
  — asunción A3, fuera de alcance).
- `GET /api/v1/sigme/usuarios` → permiso `usuario.gestionar`; lista usuarios
  no borrados con: id, username, email, activo, bloqueado, persona (id +
  nombre completo) y `roles: [codigos]`.
- `GET /api/v1/sigme/usuarios/{id}` no está en §6 → NO se implementa.

### S6 — Roles, permisos y módulos (T5)

- `GET|POST /api/v1/sigme/roles`, `/permisos`, `/modulos` → permiso
  `usuario.gestionar`.
- GET: lista completa (catálogo cerrado, CU-10). Rol incluye sus permisos
  por código; módulo y permiso devuelven id, codigo, descripcion (+ activo
  donde aplique).
- POST body: `{ codigo, descripcion }` (rol y módulo incluyen `activo`
  opcional default True; permiso no tiene `activo`, §3.7). `codigo` único →
  409 `code: "codigo-existente"`. 201 con el recurso.
- Cambio de asignación permiso-rol: fuera de alcance (§6 no lo declara;
  la asignación vive en la semilla).

### S7 — Catálogo (T6)

Bajo prefijo `/api/v1/sigme`: `orientaciones`, `cursos`, `materias`,
`condiciones`.
- GET (cada colección) → `require_modulo("sigme_web")` (asunción A4; CU-05:
  "cualquier rol sigme_web"); lista no borradas. Filtros query opcionales:
  `/cursos?orientacion_id=`, `/materias?curso_id=`.
- POST (cada colección) → permiso `usuario.gestionar` (asunción A1).
  - `/orientaciones` body `{ descripcion }` (única) → 409
    `code: "orientacion-existente"`.
  - `/cursos` body `{ orientacion_id, descripcion, anio? }`; FK orientación
    activa → 404 `code: "orientacion-no-encontrada"`.
  - `/materias` body `{ curso_id, codigo?, descripcion, es_taller? }` (default
    False, RB-04); FK curso → 404 `code: "curso-no-encontrado"`.
  - `/condiciones` body `{ descripcion, limite_materias? }` (NULL = sin
    límite); `descripcion` única → 409 `code: "condicion-existente"`;
    `limite_materias` entero >= 0 o null (422 `errors[]`).
- PATCH (cierra PD-02 y resuelve PD-21 "agrega el PATCH") →
  `usuario.gestionar`:
  - `PATCH /condiciones/{id}` body `{ descripcion?, limite_materias? }` → 200;
    404 `code: "condicion-no-encontrada"`.
  - `PATCH /orientaciones/{id}` `{ descripcion? }`; `PATCH /cursos/{id}`
    `{ descripcion?, anio? }`; `PATCH /materias/{id}`
    `{ descripcion?, codigo?, es_taller? }` → mismos códigos 404 por
    colección.
- RB-11 implícito: renombrar catálogo NO toca mesas (no hay mesas todavía;
  se documenta como restricción futura).
- DELETE: fuera de alcance (§6 no lo declara).

### S8 — Registro y documentación (T7)

- README: sección "SIGME (SDD-2)" con tabla de endpoints, permiso por
  endpoint y códigos de error 409/404.
- Feature doc: cerrar A1-A4 en Log; PD-21 queda resuelto por implementación
  (se agrega el PATCH) — dejar constancia.

## Asunciones (cerrar en Log al implementar)

- **A1** — `POST /personas`, `POST`/`PATCH` de catálogo: la matriz no define
  código de permiso (hueco declarado en doc 05). Gate temporal con
  `usuario.gestionar` (sólo Administrador/Superadmin), sin inventar códigos
  nuevos en §2.7. Cambio futuro de bajo impacto (una dependencia por
  endpoint).
- **A2** — Identidad (`documento_tipo_id`, `documento`) inmutable por
  `PATCH /personas/{id}` en v1; la matriz sólo declara "corrección de datos".
- **A3** — Asignación de roles/módulos a usuarios: sin endpoint en §6
  ("roles/módulos por separado"); fuera de alcance de SDD-2.
- **A4** — Lectura de catálogo gateada por módulo `sigme_web`
  (`require_modulo`), no por permiso, por CU-05 ("cualquier rol sigme_web").
- **A5** — Sin paginación en listados SIGME en v1 (escala escolar); §6 no la
  declara para estos endpoints (PD-28 sólo trata mis-inscripciones).

## Tasks

- T1 — seed roles + asignación matriz + condiciones default (S1, S2) — inline — COMPLETADO (`3dd7220`)
- T2 — migración Alembic 0003 idempotente con la data de S1+S2 (S3) — inline — COMPLETADO (`7f82614`)
- T3 — personas: schemas + service + router + tests (S4) — inline — COMPLETADO (`3b80265`)
- T4 — usuarios POST/GET + tests (S5) — inline — COMPLETADO (`e9f9f6c`)
- T5 — roles/permisos/módulos GET/POST + tests (S6) — inline — COMPLETADO (`22de641`)
- T6 — catálogo GET/POST/PATCH + tests (S7) — inline — COMPLETADO (`c2e32f3`)
- T7 — README + cierre de asunciones en Log (S8) — inline — COMPLETADO

## Log

- **L1 (2026-10-22) — solicitud original del usuario (verbatim):**
  "Ya podemos continuar con el backend" / "dale, arrancamos con ese"
  (aprobación de la propuesta SDD-2 — SIGME base: personas, usuarios,
  roles/permisos/módulos, catálogos, con PD-21 a resolver en el diseño).
- **L2 (2026-10-22) — diseño de permisos para catálogo y POST /personas:**
  la matriz §2.4 no define código para esas acciones (hueco declarado en
  doc 05). Decisión: gate temporal `usuario.gestionar` (A1) + lecturas por
  módulo `sigme_web` (A4); sin códigos nuevos en el catálogo cerrado §2.7.
  PD-21 se resuelve "agregando el PATCH" a las 4 colecciones de catálogo.
- **L3 (2026-10-22) — T1 completado (`3dd7220`):** seed de 5 roles con la
  matriz exacta de doc02 §2.4 (celdas PENDIENTE/`—` nunca otorgan;
  `preinscripcion.crear` sin dueño → sin asignar, G-02) + condiciones
  PD-02 (Previa 3, Regular 8, Libre NULL). Tests: matriz == seed, idempotencia.
  RED observado (2), GREEN 8/8.
- **L4 (2026-10-22) — T2 completado (`7f82614`):** migración Alembic `0003`
  idempotente (ON CONFLICT DO NOTHING, data inline sin importar app/) con
  la misma data de T1; test que compara migración == seed para que nunca
  divergan. RED observado (2), GREEN 6/6 + SQL offline verificado
  (3 INSERTs presentes). Cierra el hueco de proceso de PD-03 (antes los
  roles vivían sólo en seed.py de tests).
- **L5 (2026-10-22) — T3 completado (`3b80265`):** personas GET (lista con
  `?q=`, 404 por id), POST (201 / 409 persona-duplicada / 422
  documento-tipo-invalido, gate `usuario.gestionar` A1) y PATCH
  (`persona.modificar`, campos mutables, identidad inmutable A2). RED
  observado (8), GREEN 8/8. Hallazgo: los servicios deben escribir
  `created_at` explícito (conftest quita server_default en SQLite).
- **L6 (2026-10-22) — T4 completado (`e9f9f6c`):** usuarios POST (sobre
  persona existente; 404/409 username-existente/409 email-existente/422
  clave corta §2.5; hash con el algoritmo de auth) y GET (lista con roles
  por código; password_hash jamás viaja). `GET /usuarios/{id}` queda fuera
  (§6 no lo declara). RED observado (6), GREEN 6/6.
- **L7 (2026-10-22) — T5 completado (`22de641`):** roles/permisos/módulos
  GET|POST bajo `usuario.gestionar`; GET /roles incluye permisos por
  código; 409 `codigo-existente`. Asignación permiso-rol sin endpoint
  (vive en la semilla). RED observado (5), GREEN 5/5.
- **L8 (2026-10-22) — T6 completado (`c2e32f3`):** catálogo de las 4
  colecciones: lectura por módulo `sigme_web` (A4), escritura por
  `usuario.gestionar` (A1), 409 por colección, FK RESTRICT validada al
  escribir (404). PD-02 cierra (PATCH /condiciones con limite_materias
  editable, NULL = sin límite); PD-21 resuelto (PATCH a las 4). RB-11
  documentado como restricción para SDD-3. RED observado (10), GREEN 10/10.
- **L9 (2026-10-22) — T7 completado:** README con la sección
  "SIGME (SDD-2)" (tabla endpoint → permiso/modulo, códigos de error,
  semilla 0003, notas de diseño). SDD-2 CERRADO: T1-T7 completados,
  120 tests + ruff limpios; PR pendiente de aprobación de entrega.
