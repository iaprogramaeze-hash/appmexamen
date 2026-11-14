# 05 · Casos de uso SIGME — Backend EPET36

**Respuesta corta:** el cliente SIGME web necesita **30 casos de uso** repartidos
en diez dominios: sesión, catálogo, personas y usuarios, convocatorias, ventana
de preinscripción, grupos de mesas, mesas y cobertura, inscripciones de gestión,
consulta de preinscripciones y reportes de cierre. Cada operación se apoya en un
endpoint declarado en `analisis.txt` §6 o en un permiso del catálogo §2.7; las
que carecen de contrato quedan **PENDIENTE** con su PD/G en **5.11** (CU-18,
CU-24 y CU-25; CU-22 quedó sin escritura por la regla temporal del
2026-10-06), nunca se completan por suposición.

Vocabulario: se usan los términos de `01-glosario-y-alcance.md` (1.2 y 1.3), los
actores y la matriz rol × permiso de `02-actores-y-consumidores.md` (2.2 y 2.4),
los eventos de `03-eventos-y-gatillos.md` (3.1–3.4) y las transiciones de
`04-maquinas-de-estados.md` (4.1–4.6). Toda cita `RB-xx` y `PD-xx` remite a
`analisis.txt` (§4 y §7); `§n.m` remite a la sección de ese archivo; `E-xx`,
`S-xx` y `T-xx` remiten a doc 03; `G-xx` a doc 01 §1.5.2.

## Rápido recorrido

1. **5.1** — sesión: autenticarse, renovar, cerrar y cambiar clave (E-10, T-07…T-09).
2. **5.2** — catálogo: consultar y mantener orientaciones, cursos, materias y
   condiciones (E-08).
3. **5.3** — personas, usuarios, roles, permisos y módulos (E-11).
4. **5.4** — convocatorias: crear o editar, consultar la ventana vigente y
   cerrar la campaña (E-06, T-01, T-02, T-03, T-06).
5. **5.5** — ventana de preinscripción gestionada **desde SIGME** (E-05, T-04, T-05).
6. **5.6** — grupos de mesas: alta en bloque, edición de fecha/hora, listado y
   baja (E-15, E-16, S-01, S-21).
7. **5.7** — mesas: consulta, edición de asignación, cobertura y cambio de
   estado (E-07, E-17, S-08).
8. **5.8** — inscripciones de gestión: consulta, anulación por secretaría e
   inscripción en nombre de un alumno.
9. **5.9** — consulta de preinscripciones desde SIGME (E-12).
10. **5.10** — reportes de cierre: permiso de examen, acta volante, detalle de
    mesa y planilla de grupos (E-09).
11. **5.11** — consolidado de pendientes: PD-03, PD-12…PD-22, PD-29 y G-01…G-05.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Alcance** | Sólo el consumidor `sigme_web` (Secretario/a, Director, Administrador, Superadmin). Las operaciones del alumno en SIGME-M son del **doc 06**; el envío de la landing, del **doc 11**; los códigos de error y los estados críticos, del **doc 07** — aquí se referencian, no se definen. | doc 02 §2.2; plan §3 (05, 06, 07, 11) |
| **Rutas** | Los endpoints de sesión viven bajo `/api/v1/auth` y los de gestión bajo `/api/v1/sigme`. | `analisis.txt` §6 |
| **Permisos** | `analisis.txt` §6 **no declara** el permiso de cada endpoint; §2.7 exige la dependencia `require_permiso()`. El reparto por rol citado acá sale de la matriz de doc 02 §2.4, **[CERRADO — 2026-10-06]**: con PD-03 esa matriz es la fuente definitiva (roles y permisos en la migración inicial de Alembic, primer superadmin por variable de entorno); sus celdas `PENDIENTE` son huecos de la matriz y siguen abiertos. | `analisis.txt` §2.7; doc 02 §2.4; PD-03 (cerrado 2026-10-06) |
| **PENDIENTE** | Toda operación sin endpoint en §6 o sin código de permiso en §2.7 queda marcada **PENDIENTE** con su PD/G existente. No se inventan endpoints, identificadores, roles ni permisos. | doc 01 §1.1; `analisis.txt` §2.7, §6 |
| **Identificadores** | `CU-01`…`CU-30` se asignan en este documento (doc 03 §3.4 dejó la numeración a los docs 05 y 06). `RB-xx`/`PD-xx` → `analisis.txt` (§4, §7); `E-xx`/`S-xx`/`T-xx` → doc 03; `G-xx` → doc 01 §1.5.2; `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` → doc 04. | doc 03 §3.4; plan §3 (05) |
| **Ventanas** | Toda ventana se **constata** en cada request por fecha de calendario en `America/Argentina/Buenos_Aires`, inclusive hasta las 23:59:59; no hay ningún job programado en v1. | RB-23, RB-24; doc 03 §3.2 |
| **Vocabulario** | Se respetan los términos de doc 01 §1.2 y el vocabulario retirado de §1.3: la planificación vive en **grupos de mesas** (`fecha` + `hora`), nunca en la convocatoria. | doc 01 §1.2, §1.3; RB-27 |

---

## 5.1 Sesión y autenticación

| CU | Operación (§6) | Control |
|---|---|---|
| CU-01 | `POST /auth/login` (+ `GET /auth/yo`) | autenticación |
| CU-02 | `POST /auth/refresh` | autenticación |
| CU-03 | `POST /auth/logout`, `POST /auth/logout-all` | autenticación |
| CU-04 | `POST /auth/cambiar-clave` | autenticación |

**CU-01 — Autenticarse · `POST /auth/login`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Usuario de `sigme_web` (Secretario/a, Director, Administrador o Superadmin) con credenciales y módulo asignado | doc 02 §2.2, §2.5 |
| Gatillo | E-10 · login con credenciales válidas | doc 03 §3.1 |
| Precondiciones | Clave verificada con Argon2id (m=19456, t=2, p=1; longitud mínima 12); `username` único entre cuentas no borradas; cuenta no bloqueada; rate limit de hasta 5 fallos por usuario/IP cada 15 minutos; módulo `sigme_web` asignado (`us_sesion.modulo_id NOT NULL`) | `analisis.txt` §2.4, §2.5, §3.5, §3.12, §2.8 |
| Flujo principal | 1) `POST /auth/login`; 2) verificación del hash y del rate limit; 3) alta de `us_sesion` en `activo`; 4) emisión de access token (15 min, máx. 30) con roles, permisos y módulos, y de refresh token (7 días) | `analisis.txt` §2.1, §2.2, §2.4; doc 04 SES-01 |
| Resultado | Sesión vigente; en base de datos sólo se guarda el SHA-256 del refresh. El cliente comprueba su identidad con `GET /auth/yo` (`GET /yo` bajo `/api/v1/auth`) | `analisis.txt` §2.2, §6 |
| Permisos | No aplica: autenticación, no autorización — el permiso gobierna los endpoints protegidos | `analisis.txt` §2.7; doc 04 SES-01 |
| Excepciones y pendientes | 5 fallos en 15 minutos → bloqueo temporal (`bloqueado_hasta`) y subida de `token_version` (E-14, S-16); vencido el bloqueo se reanudan los intentos (T-09, US-03). El restablecimiento de clave por email queda fuera de este flujo: **PD-04** **[CERRADO — 2026-10-06]**: SÍ desde v1, con la tabla `us_password_reset` y email por la cola obligatoria (RB-25); el contrato de reintento de la cola no lo resuelve | `analisis.txt` §2.4, §2.6, §7; doc 03 §3.1–§3.2 |

**CU-02 — Renovar la sesión · `POST /auth/refresh`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Cualquier usuario autenticado de `sigme_web` | doc 02 §2.2 |
| Gatillo | T-07 · vence el access token (15 minutos); rotación proactiva del cliente | doc 03 §3.2 |
| Precondiciones | Refresh token vigente (7 días, `us_sesion.expires_at`) y aún no consumido; sesión en `activo` | `analisis.txt` §2.2, §3.12 |
| Flujo principal | 1) `POST /auth/refresh`; 2) rotación: se emite un refresh nuevo y se revoca el anterior; 3) se emite un access token nuevo con la versión vigente | `analisis.txt` §2.1, §2.2 |
| Resultado | La sesión sigue `activo` hasta `expires_at`; el access token renovado vuelve a autorizar los endpoints de 5.2–5.10 | `analisis.txt` §2.2, §2.6 |
| Permisos | No aplica (autenticación) | `analisis.txt` §2.7 |
| Excepciones y pendientes | T-08 · vencidos los 7 días la sesión ya no rota: se exige login nuevo. S-14 · un refresh reutilizado revoca **toda la familia** de la sesión y exige login nuevo (respuesta 401 declarada en T-07) | doc 03 §3.2–§3.3; `analisis.txt` §2.2; doc 04 SES-04 |

**CU-03 — Cerrar sesión · `POST /auth/logout` y `POST /auth/logout-all`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | El dueño de la sesión (logout) o el dueño del usuario sobre todas sus sesiones (logout-all) | doc 04 SES-02, SES-03 |
| Gatillo | E-10 · cierre de sesión | doc 03 §3.1 |
| Precondiciones | Sesión propia vigente en `activo` | `analisis.txt` §3.12 |
| Flujo principal | 1) `POST /auth/logout` revoca la sesión actual; 2) `POST /auth/logout-all` revoca todas las sesiones del usuario; 3) el refresh deja de rotar | `analisis.txt` §2.3, §2.4 |
| Resultado | `us_sesion.estado = 'revocado'` (S-18); el siguiente acceso exige un login nuevo | `analisis.txt` §3.12; doc 03 §3.3 |
| Permisos | No aplica (autenticación) | `analisis.txt` §2.7 |
| Excepciones y pendientes | Sin alternativos declarados: la operación sólo cambia el estado de la sesión y no toca datos de negocio | doc 04 §4.4.2 |

**CU-04 — Cambiar la clave · `POST /auth/cambiar-clave`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Cualquier usuario autenticado de `sigme_web`, sobre su propia cuenta | `analisis.txt` §2.4 |
| Gatillo | E-10 · cambio de clave; S-15 · el cambio sube `token_version` | doc 03 §3.1, §3.3 |
| Precondiciones | Sesión válida; nueva clave de longitud mínima 12 con Argon2id | `analisis.txt` §2.5 |
| Flujo principal | 1) `POST /auth/cambiar-clave`; 2) verificación de la clave actual; 3) almacenamiento del hash nuevo; 4) subida de `token_version` | `analisis.txt` §2.5, §2.6 |
| Resultado | Los access tokens ya emitidos dejan de servir aunque tengan TTL pendiente; el cliente debe autenticarse de nuevo | `analisis.txt` §2.6; doc 03 §3.3 |
| Permisos | No aplica (autenticación) | `analisis.txt` §2.7 |
| Excepciones y pendientes | Mismo efecto de invalidación global producen el cambio de rol y el bloqueo de cuenta (S-15); ambos llegan por gestión de usuario, ver CU-09 y CU-10. **PD-04** (reset por email) **[CERRADO — 2026-10-06]**: tabla `us_password_reset` desde v1, email por la cola obligatoria (RB-25) | doc 03 §3.3; `analisis.txt` §7 |

---

## 5.2 Catálogo — orientaciones, cursos, materias y condiciones

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-05 | `GET /orientaciones`, `/cursos`, `/materias`, `/condiciones` | **PENDIENTE** (sin código en §2.7) |
| CU-06 | `POST /orientaciones`, `/cursos`, `/materias`, `/condiciones` | **PENDIENTE** (sin código en §2.7) |

**CU-05 — Consultar el catálogo**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Cualquier rol de `sigme_web`; la lectura alimenta la planificación de grupos, la edición de mesas y la búsqueda de personas | doc 02 §2.1.1, §2.3 |
| Gatillo | Consulta de gestión declarada para el consumidor; doc 03 §3.1 no tiene un `E-xx` de lectura de catálogo | doc 02 §2.1.1; doc 03 §3.1 |
| Precondiciones | Sesión válida con módulo `sigme_web`; filas no borradas (soft delete con índice parcial) | `analisis.txt` §2.8, §1.5, §1.7 |
| Flujo principal | 1) `GET` sobre la colección pedida; 2) el backend devuelve sólo filas vigentes | `analisis.txt` §6 |
| Resultado | Catálogo vigente: `es_curso` identifica el año, sin división ni turno (RB-15); el taller es una materia con `es_taller = true` y sin comportamiento diferenciado (RB-04) | `analisis.txt` §4, §3.14, §3.15 |
| Permisos | **PENDIENTE** — el catálogo §2.7 no contiene ningún código de catálogo (ninguno de los 13 permisos cubre esta lectura). **PD-03** **[CERRADO — 2026-10-06]** fijó el reparto desde la matriz de doc 02 §2.4 sin crear ese código: el hueco queda en la matriz | `analisis.txt` §2.7; doc 02 §2.4; PD-03 (cerrado 2026-10-06) |
| Excepciones y pendientes | **PD-20** — el catálogo de materias existe como texto libre, sin IDs ni flags `es_taller`, por lo que no puede validarse programáticamente | `analisis.txt` §7 |

**CU-06 — Mantener el catálogo**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Rol de gestión de SIGME; el reparto por rol sale de la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**, PD-03) | doc 02 §2.3 (Administrador), doc 02 §2.4; PD-03 |
| Gatillo | E-08 · se renombra o se da de alta una fila de catálogo | doc 03 §3.1 |
| Precondiciones | Sesión válida; la fila existe y no está borrada; las FK de las mesas a catálogo son `ON DELETE RESTRICT` | `analisis.txt` §1.8, §3.18 |
| Flujo principal | 1) `POST /orientaciones` (o `/cursos`, `/materias`, `/condiciones`) para el alta; 2) el backend guarda la fila; 3) los snapshot de las mesas existentes **no** se recalculan por el renombre | `analisis.txt` §6; RB-11, RB-12 |
| Resultado | Las mesas históricas conservan el nombre con que fueron creadas (S-09); sólo la edición de la asignación de una mesa recalcula snapshot (S-08, CU-20) | RB-11, RB-12; doc 03 §3.3 |
| Permisos | **PENDIENTE** — mismo hueco que CU-05: no hay código de catálogo en §2.7; el reparto sale de la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**) y el hueco sigue en esa matriz | `analisis.txt` §2.7; doc 02 §2.4; PD-03 |
| Excepciones y pendientes | Inconsistencia de fuentes: doc 03 §3.1 materializa el renombre como `PATCH /orientaciones` (y equivalentes), mientras que §6 sólo declara `GET\|POST` para estas colecciones. El alcance del `PATCH` queda **PENDIENTE** de reconciliación — **PD-21** (ver 5.11) | doc 03 §3.1; `analisis.txt` §6 |

---

## 5.3 Personas, usuarios y seguridad

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-07 | `GET /personas`, `GET /personas/{id}` | `persona.listar` |
| CU-08 | `PATCH /personas/{id}` | `persona.modificar` |
| CU-09 | `GET`, `POST /usuarios` | `usuario.gestionar` |
| CU-10 | `GET`, `POST /roles`, `/permisos`, `/modulos` | `usuario.gestionar` |

**CU-07 — Buscar y consultar personas**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`persona.listar` en **S**); Alumno fuera de alcance | doc 02 §2.4 |
| Gatillo | Consulta de gestión del consumidor (búsqueda de personas para altas de usuario y reportes); sin `E-xx` propio en doc 03 §3.1 | doc 02 §2.1.1, §2.4 |
| Precondiciones | Sesión válida con módulo `sigme_web` | `analisis.txt` §2.8 |
| Flujo principal | 1) `GET /personas` (o `GET /personas/{id}`); 2) el backend devuelve las filas no borradas | `analisis.txt` §6, §1.5 |
| Resultado | Datos de la persona disponibles para el alta de usuario (CU-09) y para los reportes por alumno (CU-27) | `analisis.txt` §3.2, §3.5 |
| Permisos | `persona.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S**, Alumno **—** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | Una persona referenciada no se puede eliminar: las FK son `ON DELETE RESTRICT` (S-17) | `analisis.txt` §1.8; doc 03 §3.3 |

**CU-08 — Editar datos de una persona**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Administrador y Superadmin (`persona.modificar` en **S**); Director **—** | doc 02 §2.4 |
| Gatillo | Corrección de datos de contacto declarada como justificación del permiso | doc 02 §2.4 |
| Precondiciones | Persona existente y no borrada; sesión válida | `analisis.txt` §3.2, §1.5 |
| Flujo principal | 1) `PATCH /personas/{id}` con los campos corregidos; 2) el backend actualiza la fila y `updated_at` | `analisis.txt` §6, §1.6 |
| Resultado | Persona con datos vigentes; las cuentas asociadas no cambian | `analisis.txt` §3.5 |
| Permisos | `persona.modificar` — Secretario/a **S**, Director **—**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | El detalle de si una persona puede editarse a sí mismo no está determinado: **PD-03** (cerrado el 2026-10-06 con el reparto de la matriz, no resuelve este caso) | doc 02 §2.4, §2.6; PD-03 |

**CU-09 — Dar de alta y consultar usuarios**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Administrador y Superadmin (`usuario.gestionar` en **S**); Secretario/a y Director en **—** | doc 02 §2.4 |
| Gatillo | E-11 · se gestiona un usuario | doc 03 §3.1 |
| Precondiciones | Persona existente (FK `RESTRICT`); `username` único entre no borrados (`uq_usuario_username`); clave con Argon2id; `activo = true` por defecto; los roles y los módulos se asignan por separado | `analisis.txt` §3.5, §2.5, §2.8, §3.8, §3.11 |
| Flujo principal | 1) `GET /usuarios` para listar; 2) `POST /usuarios` para el alta sobre una persona existente; 3) asignación de roles (`us_usuario_rol`) y módulos (`us_usuario_modulo`); 4) la cuenta nace `activo` | `analisis.txt` §6, §3.5; doc 04 US-01 |
| Resultado | Usuario autenticable en `sigme_web`; la semilla inicial de cuentas administrativas viaja en la migración inicial de Alembic y el primer superadmin entra por variable de entorno (**[CERRADO — 2026-10-06]**, PD-03) | `analisis.txt` §7 |
| Permisos | `usuario.gestionar` — Administrador **S**, Superadmin **S**, Secretario/a **—**, Director **—** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | El bloqueo por gestión (S-15, US-04), el desbloqueo (US-05), la desactivación (US-06, US-07), la baja lógica (US-08) y la restauración (US-09) **no tienen endpoint declarado**: §6 sólo expone `GET\|POST /usuarios` — **PENDIENTE** (sin PD propio; ver doc 04 §4.6.1) | `analisis.txt` §6; doc 04 §4.4.1, §4.6.1; PD-03 |

**CU-10 — Gestionar roles, permisos y módulos**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Administrador y Superadmin, con predominio del Superadmin sobre la estructura de seguridad | doc 02 §2.3, §2.4 |
| Gatillo | E-11 · se gestiona roles, permisos o módulos | doc 03 §3.1 |
| Precondiciones | Catálogo cerrado: 13 permisos (§2.7), 3 módulos (§2.8) y la lista de roles de P-08 | `analisis.txt` §2.7, §2.8; plan §6 |
| Flujo principal | 1) `GET\|POST /roles`, `/permisos`, `/modulos`; 2) asignación rol × permiso (`us_rol_permiso`) y usuario × módulo; 3) al cambiar un rol, sube `token_version` | `analisis.txt` §6, §3.9, §2.6 |
| Resultado | Los access tokens emitidos con la versión vieja dejan de servir (S-15); el usuario afectado debe renovar sesión | `analisis.txt` §2.6; doc 03 §3.3 |
| Permisos | `usuario.gestionar` — Administrador **S**, Superadmin **S**; los demás roles **—** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **G-03** — ¿existe el rol "docente"? El comentario de ejemplo del DDL de `us_rol` no es un rol del sistema: la lista es cerrada (P-08) y el profesor evaluador sólo recibe el acta volante en papel. Reparto exacto: matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**) | doc 01 §1.5.2; `analisis.txt` §3.6; RB-19; PD-03 |

---

## 5.4 Convocatorias y ventanas de inscripción

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-11 | `POST /convocatorias` | **PENDIENTE** (no existe `convocatoria.*` en §2.7) |
| CU-12 | `GET /convocatorias` | **PENDIENTE** (mismo hueco) |
| CU-13 | Cierre por calendario y archivado | Cierre derivado del calendario (**G-05**, **[RESUELTA — 2026-10-06]**); archivado **PENDIENTE** (sin endpoint) |

**CU-11 — Crear o editar una convocatoria (incluido `activa`)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a o administración, desde SIGME | doc 04 C-01; doc 02 §2.3 |
| Gatillo | E-06 · se crea o edita una convocatoria, o su marca `activa` | doc 03 §3.1 |
| Precondiciones | `descripcion`, `fecha_inicio_inscripcion` y `fecha_fin_inscripcion` `NOT NULL`; `ck_convocatoria_ventana` exige inicio ≤ fin; una sola ventana de inscripción por convocatoria y ésta cierra antes de la primera fecha de grupo (RB-05) | `analisis.txt` §3.17, §4; doc 04 C-01 |
| Flujo principal | 1) `POST /convocatorias` con nombre y las dos fechas de la ventana; 2) `activa` nace en `true`; 3) la edición posterior puede activar o desactivar la inscripción | `analisis.txt` §6, §3.17; E-06 |
| Resultado | Convocatoria en `borrador` (derivado: `activa = false` o aún sin llegar la fecha de inicio). Con `activa = false`, cualquier inscripción se rechaza (RB-09) | doc 04 §4.1; RB-09 |
| Permisos | **PENDIENTE** — el catálogo §2.7 no contiene ningún código `convocatoria.*`; la propuesta de doc 04 es `convocatoria.gestionar`. **PD-03** **[CERRADO — 2026-10-06]** fijó la semilla desde la matriz de doc 02 §2.4 y no creó el código | `analisis.txt` §2.7, §7; doc 04 C-01, §4.6.2 |
| Excepciones y pendientes | `activa = false` con la ventana ya vencida deja la convocatoria atrapada en `borrador`; doc 04 prevé una transición de archivado (C-06) sin endpoint declarado — **PENDIENTE** (hueco de §2.7; PD-03 cerrado 2026-10-06 no lo cubrió) | doc 04 §4.1, §4.6.1 |

**CU-12 — Consultar convocatorias y constatar la ventana**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Los cuatro roles de `sigme_web` | doc 02 §2.4 |
| Gatillo | T-01 · llega `fecha_inicio_inscripcion`; T-02/T-03 · se cumple `fecha_fin_inscripcion` hasta las 23:59:59 y cambia la fecha | doc 03 §3.2 |
| Precondiciones | Ninguna acción humana: la ventana **se constata** en cada request comparando la fecha de calendario del backend; no hay scheduler en v1 | RB-23; doc 03 §3.2; doc 04 C-02, C-04 |
| Flujo principal | 1) `GET /convocatorias`; 2) el backend deriva el estado (`borrador`, `abierta`, `cerrada`, `archivada`) y responde con las fechas vigentes | `analisis.txt` §6; doc 04 §4.1 |
| Resultado | En `abierta` están habilitadas la inscripción y la anulación (RB-06, RB-07); en `cerrada` la lista de inscriptos queda fija (RB-17) | `analisis.txt` §4 |
| Permisos | **PENDIENTE** — mismo hueco que CU-11: no hay código de lectura de convocatoria en §2.7; el reparto sale de la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**) | `analisis.txt` §2.7; doc 02 §2.4; PD-03 |
| Excepciones y pendientes | Una convocatoria inactiva rechaza cualquier inscripción (RB-09, fila E-06 de doc 03 §3.4); el cierre no admite códigos de error propios aquí: los estados críticos son del doc 07 | doc 03 §3.4; plan §3 (07) |

**CU-13 — Cerrar y archivar la convocatoria**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Reloj del sistema para el cierre derivado; administración para el archivado (propuesto) | doc 04 C-04, C-06, C-07 |
| Gatillo | T-06 · pasó el último día de rendir de la convocatoria, es decir la **última fecha de sus grupos** | doc 03 §3.2; RB-16, RB-27 |
| Precondiciones | La ventana ya está vencida (`hoy > fecha_fin_inscripcion`) para el estado `cerrada`; el archivado exige soft delete (`deleted_at`) | doc 04 §4.1 |
| Flujo principal | 1) al cambiar la fecha de calendario, la convocatoria pasa a `cerrada` sin intervención de nadie (C-04); 2) la campaña se cierra al cumplirse la última fecha de grupos (T-06, RB-16); 3) en la fecha que corresponda se crea **otra** convocatoria y el ciclo arranca de nuevo (C-01) | doc 03 §3.2, §3.4; RB-16; doc 04 §4.1 |
| Resultado | Cerrada la campaña, no se inscribe ni se anula; las consultas siguen disponibles. El archivado conserva la fila para auditoría | RB-17, RB-07; `analisis.txt` §1.4, §1.7 |
| Permisos | Cierre derivado: no aplica (constatación del reloj, C-04). Archivado y restauración: **PENDIENTE** — §6 no expone `DELETE` ni `PATCH /convocatorias`, y no hay código `convocatoria.*` en §2.7 (hueco que PD-03, cerrado 2026-10-06, no cubrió) | doc 04 C-04, C-06, C-07, C-08; `analisis.txt` §6, §2.7 |
| Excepciones y pendientes | **G-05** **[RESUELTA — 2026-10-06]** — nadie dispara el cierre tras la última fecha de grupos: es una constatación del calendario, igual que la ventana (RB-23, C-04); el archivado sigue sin endpoint declarado | doc 01 §1.5.2; doc 03 §3.2; doc 04 §4.6.2 |

---

## 5.5 Ventana de preinscripción desde SIGME

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-14 | `GET`, `POST /ventanas-preinscripcion` | **PENDIENTE** (sin código en §2.7) |

**CU-14 — Gestionar la ventana de preinscripción**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Administrador o Superadmin, **sólo desde SIGME** — nunca desde la landing | doc 02 §2.4, §2.6; `analisis.txt` §3.21 |
| Gatillo | E-05 · se abre o se cierra una ventana de preinscripción | doc 03 §3.1 |
| Precondiciones | `pr_ventana` con `fecha_desde` y `fecha_hasta`; sólo puede haber **una vigente** a la vez (`vw_ventana_vigente`); RB-14 | `analisis.txt` §3.21; RB-14 |
| Flujo principal | 1) `POST /ventanas-preinscripcion` para abrir o cerrar la ventana vigente; 2) `GET /ventanas-preinscripcion` para consultarla; 3) el cambio alterna quién recibe 409 en el envío de la landing (S-19) | `analisis.txt` §6; doc 03 §3.3 |
| Resultado | T-05 · dentro de la ventana el formulario de la landing acepta envíos; T-04 · fuera de ella `POST /landing/preinscripcion` responde 409 `ventana-cerrada` — efecto declarado en el doc 11, no acá | `analisis.txt` §4, §6; doc 03 §3.2; RB-14 |
| Permisos | **PENDIENTE** — no existe código en §2.7 para esta acción; el dueño propuesto es Administrador o Superadmin (§3.21) y la decisión de si se agrega un código quedó sin cubrir con el cierre de **PD-03** (2026-10-06) | doc 02 §2.4; `analisis.txt` §2.7, §7 |
| Excepciones y pendientes | **G-02** — el permiso `preinscripcion.crear` no puede aplicarse: la landing es anónima y no pasa por RBAC; su dueño dentro de SIGME no está determinado. La landing **no** toca `pr_ventana` | doc 01 §1.5.2; doc 02 §2.4, §2.6; `analisis.txt` §2.9 |

---

## 5.6 Grupos de mesas

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-15 | `POST /grupos` | `mesa.crear` |
| CU-16 | `PATCH /grupos/{id}` | `mesa.modificar` |
| CU-17 | `GET /grupos?convocatoria_id=` | `mesa.listar` |
| CU-18 | *(sin endpoint en §6)* | `mesa.eliminar` — **PENDIENTE** |

**CU-15 — Crear un grupo con sus mesas en bloque**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a; también Administrador y Superadmin con el mismo permiso. Director **—** | doc 02 §2.4; doc 04 GR-01, ME-01 |
| Gatillo | E-15 · se crea un grupo con materias[] × condiciones[] × fecha × hora | doc 03 §3.1 |
| Precondiciones | Convocatoria existente (FK `RESTRICT`); `fecha` y `hora` `NOT NULL`; el grupo es **sólo** fecha + hora, sin aula ni profesor (RB-27); combinación única `uq_mesa_unica` (**[CERRADO — 2026-10-06]**, PD-13: convocatoria × materia × condición × fecha, sin `hora`); los 4 snapshot se rellenan de materia y condición (RB-11) | `analisis.txt` §3.18, §3.22, §4; PD-13 |
| Flujo principal | 1) `POST /grupos` con convocatoria, fecha, hora, `materias[]` y `condiciones[]`; 2) se crea el grupo; 3) se crean N = materias × condiciones mesas en estado `planificada`, todas con `grupo_id NOT NULL`; 4) cada mesa copia `fecha` y `hora` de su grupo; 5) se rellenan los snapshot | RB-28, RB-29; doc 03 S-01; `analisis.txt` §6 |
| Resultado | Alta masiva de una sola vez (S-01). Las mesas que queden sin inscriptos activos no aparecen en listados ni impresiones (RB-22, S-03), por lo que crear el catálogo completo no ensucia la operación | RB-22; doc 03 §3.3, §3.4 |
| Permisos | `mesa.crear` — Secretario/a **S**, Administrador **S**, Superadmin **S**, Director **—**, Alumno **—**. Crear un grupo **es** `mesa.crear`: no se agrega ningún código nuevo | `analisis.txt` §2.7, §4; doc 02 §2.4 |
| Excepciones y pendientes | **PD-12** — ¿se puede crear con la ventana de inscripción abierta? · **PD-13** **[CERRADO — 2026-10-06]** — `uq_mesa_unica` gana `convocatoria_id` y sigue sin `hora` (migración del índice) · **PD-16** **[CERRADO — 2026-10-06]** — `uq_grupo_unico` sobre `(convocatoria_id, fecha, hora)` parcial, colisión → 409 · **PD-17** — interpretación de `hora` (`time` sin zona) frente a RB-23. **PD-12** y **PD-17** siguen sin resolverse acá | `analisis.txt` §7; doc 04 §4.5, §4.6.5 |

**CU-16 — Editar la fecha u hora de un grupo**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Rol con `mesa.modificar`: Secretario/a, Administrador, Superadmin; Director **—** | doc 02 §2.4 |
| Gatillo | E-16 · se cambia la fecha o la hora de un grupo | doc 03 §3.1 |
| Precondiciones | Grupo vigente de una convocatoria existente; la edición del `nombre` del grupo es informativa y no afecta a las mesas | `analisis.txt` §3.22; doc 04 §4.5 |
| Flujo principal | 1) `PATCH /grupos/{id}` con la fecha y la hora nuevas; 2) todas las mesas del grupo actualizan `fecha` y `hora` en la **misma transacción**; 3) el estado del grupo no cambia (no es una transición) | RB-29; doc 03 S-21; doc 04 §4.5 |
| Resultado | El grupo queda como fuente de verdad del horario (RB-29); los reportes leen la fecha y la hora vigentes de la mesa (CU-27, CU-30) | `analisis.txt` §4; RB-32 |
| Permisos | `mesa.modificar` — Secretario/a **S**, Administrador **S**, Superadmin **S**, Director **—** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-12** — mover con la ventana abierta y el efecto sobre alumnos ya inscriptos queda **PENDIENTE**: aquí no se decide · **PD-17** — zona de `hora` | `analisis.txt` §7; doc 03 S-21; doc 04 §4.6.5 |

**CU-17 — Listar los grupos de una convocatoria**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`mesa.listar` en **S**) | doc 02 §2.4 |
| Gatillo | Consulta de planificación del consumidor; sin `E-xx` propio en doc 03 §3.1 (la operación nace de §6 y de doc 02 §2.1.1) | doc 02 §2.1.1; `analisis.txt` §6 |
| Precondiciones | Convocatoria existente; sólo grupos no borrados | `analisis.txt` §3.22, §1.5 |
| Flujo principal | 1) `GET /grupos?convocatoria_id=`; 2) el backend devuelve los grupos con su `fecha` y su `hora` | `analisis.txt` §6 |
| Resultado | Vista de planificación por fecha y franja horaria; sus mesas siguen el filtro de RB-22 (una mesa sin inscriptos activos no aparece) | RB-27, RB-22; doc 03 §3.4 |
| Permisos | `mesa.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-16** **[CERRADO — 2026-10-06]** — `uq_grupo_unico` ya impide grupos idénticos duplicados en el listado; **PD-18** **[CERRADO — 2026-10-06]** — el borrado lógico de un grupo arrastra lógicamente sus mesas en la misma transacción | `analisis.txt` §7 |

**CU-18 — Eliminar un grupo — PENDIENTE (sin endpoint)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Administrador y Superadmin (`mesa.eliminar` en **S**); Secretario/a **PENDIENTE** | doc 02 §2.4 |
| Gatillo | Baja lógica de un grupo, prevista como transición GR-02 | doc 04 §4.5 |
| Precondiciones | §6 **no** declara `DELETE /grupos/{id}` ni ninguna operación de baja: sólo `POST`, `PATCH` y `GET /grupos` | `analisis.txt` §6; doc 04 GR-02 |
| Flujo principal | **No definido** — no hay contrato de operación. La única vía prevista es el soft delete (`deleted_at`) con cascada lógica transaccional sobre sus mesas (**[CERRADO — 2026-10-06]**, PD-18); el `ON DELETE RESTRICT` de la FK sigue cubriendo sólo el borrado físico | `analisis.txt` §1.4, §1.7, §3.18, §3.22 |
| Resultado | Quedaría el grupo en estado `borrada` (derivado) y la restauración GR-03 tampoco tiene endpoint declarado | doc 04 §4.5 |
| Permisos | `mesa.eliminar` — Administrador **S**, Superadmin **S**, Secretario/a **PENDIENTE**; el dueño definitivo queda como hueco de la matriz de doc 02 §2.4 (PD-03 cerrado 2026-10-06 no lo fijó) | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-18** **[CERRADO — 2026-10-06]** — borrado lógico con cascada lógica transaccional: si alguna mesa del grupo tiene inscripciones activas, la operación entera falla y no se borra nada · dueño del permiso: hueco de la matriz de doc 02 §2.4 (PD-03 cerrado 2026-10-06 no fijó al Secretario/a). Operación marcada **PENDIENTE**: sin endpoint en §6 | `analisis.txt` §7; doc 04 GR-02; PD-03 |

---

## 5.7 Mesas y cobertura

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-19 | `GET /mesas`, `GET /mesas/{id}`, `GET /mesas/por-fecha` | `mesa.listar` |
| CU-20 | `PATCH /mesas/{id}` | `mesa.modificar` |
| CU-21 | `GET /cobertura-mesas?convocatoria_id=` | `mesa.listar` |
| CU-22 | *(sin escritura: el estado se constata al leer)* | no aplica (constatación, sin permiso) |

**CU-19 — Consultar mesas**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Los cuatro roles de `sigme_web` (`mesa.listar` en **S**) | doc 02 §2.4 |
| Gatillo | Consulta de gestión del consumidor; sin `E-xx` de lectura en doc 03 §3.1 | doc 02 §2.1.1 |
| Precondiciones | Sesión válida con módulo `sigme_web`; filtro RB-22 aplicado por el backend | `analisis.txt` §6, §2.8 |
| Flujo principal | 1) `GET /mesas`, `GET /mesas/{id}` o `GET /mesas/por-fecha?desde=&hasta=`; 2) el backend devuelve sólo mesas con al menos una inscripción activa | `analisis.txt` §6; RB-22 |
| Resultado | Mesas con su `fecha` y `hora` copiadas del grupo (RB-29) y con los 4 snapshot vigentes (RB-11); una mesa con 0 alumnos no aparece, pero **no** se borra (S-03) | `analisis.txt` §3.18, §4; doc 03 §3.3 |
| Permisos | `mesa.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | El alta individual `POST /mesas` (§6) no tiene ninguna regla que declare su alcance fuera de la alta masiva del grupo: **PENDIENTE (PD-29)** | `analisis.txt` §6, §7; doc 04 §4.6.4; RB-28 |

**CU-20 — Editar la asignación de una mesa**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Rol con `mesa.modificar`: Secretario/a, Administrador, Superadmin; Director **—** | doc 02 §2.4 |
| Gatillo | E-07 · se edita la materia o la condición de una mesa | doc 03 §3.1 |
| Precondiciones | Mesa existente y no borrada; la nueva materia y condición existen en el catálogo | `analisis.txt` §3.18 |
| Flujo principal | 1) `PATCH /mesas/{id}` con otra materia u otra condición; 2) el servicio **recalcula los 4 snapshot en la misma transacción**; 3) el estado de la mesa no cambia | RB-11; doc 03 S-08; doc 04 §4.2 |
| Resultado | La mesa refleja la nueva asignación; si luego se renombra el catálogo, el snapshot de esta mesa no vuelve a cambiar (S-09) | RB-11, RB-12 |
| Permisos | `mesa.modificar` — Secretario/a **S**, Administrador **S**, Superadmin **S**, Director **—** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | El `PATCH` **no** cubre el cambio de estado de la mesa (ver CU-22); la bitácora de auditoría de quién modificó qué mesa queda en `aud_evento` (**[CERRADO — 2026-10-06]**, PD-05) | doc 04 §4.2; `analisis.txt` §7 |

**CU-21 — Consultar la cobertura de mesas**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Rol con `mesa.listar` (Secretario/a, Director, Administrador, Superadmin) | doc 02 §2.4; doc 03 E-17 |
| Gatillo | E-17 · se pide la cobertura de una convocatoria | doc 03 §3.1 |
| Precondiciones | Convocatoria existente; la consulta está pensada para usarse **antes** de abrir la ventana de inscripción | `analisis.txt` §6, §4 (RB-31) |
| Flujo principal | 1) `GET /cobertura-mesas?convocatoria_id=`; 2) el backend devuelve las materias × condiciones **sin mesa** en esa convocatoria | `analisis.txt` §6; RB-31 |
| Resultado | El secretario ve qué combinaciones faltan antes de abrir el formulario, de modo que ningún alumno se encuentre sin mesa posible (RB-31) | `analisis.txt` §4 |
| Permisos | `mesa.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-15** — de dónde sale el conjunto esperado de pares materia × condición (la convocatoria no tiene FK al catálogo) · **PD-20** — el catálogo no es machine-readable · **PD-19** — código HTTP del rechazo cuando la combinación no tiene mesa, contrato que bloquea este documento según doc 01 §1.5.1 | `analisis.txt` §7; doc 01 §1.5.1 |

**CU-22 — Cambiar el estado de una mesa — [CERRADO — 2026-10-06]: sin escritura, se constata al leer**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | **No aplica** — con la regla temporal del 2026-10-06 nadie escribe el estado: la progresión se deriva del calendario (G-05) | doc 01 §1.5.2; doc 04 ME-03, ME-04 |
| Gatillo | S-10 · la `fecha`/`hora` de la mesa pasó: constatación de calendario sin request ni acción de usuario | doc 03 §3.3; `analisis.txt` §7 |
| Precondiciones | La constatación ocurre en toda lectura; el `CHECK` de `es_mesa_examen` sólo admite `planificada`, `cerrada` y `realizada`, y ninguno de los tres se escribe (DEFAULT `planificada`). Siguen sin declarar el significado de `cerrada`, si es saltable y la frontera con `realizada` | `analisis.txt` §3.18; doc 04 §4.2, §4.6.2 |
| Flujo principal | **No hay flujo de escritura** — §6 sólo declara `GET\|POST /mesas` y `GET\|PATCH /mesas/{id}`, y el alcance declarado del `PATCH` es la asignación (E-07). El estado no se modifica: la constatación ocurre al leer | `analisis.txt` §6; doc 03 E-07 |
| Resultado | Las mesas cuya `fecha`/`hora` pasó dejan de listarse; la constatación se calcula **al leer** en `America/Argentina/Buenos_Aires` y no se graba en `estado`. La secuencia `planificada → cerrada → realizada` queda derivada; el estado `acta cerrada` sigue fuera del `CHECK` (opciones (i) y (ii) de doc 04 §4.2) | `analisis.txt` §3.18; doc 04 §4.2 |
| Permisos | No aplica (constatación de calendario, sin escritura) — **G-05** **[RESUELTA — 2026-10-06]** | doc 02 §2.4; doc 04 ME-03 |
| Excepciones y pendientes | **G-05 resuelto en su mitad de la mesa**: el disparador es el calendario, no un usuario, y no hay job (RN-005). Quedan sin decidir, por falta de fuente, la frontera `cerrada`/`realizada` y si `cerrada` es saltable · el sistema **no** guarda notas ni asistencia (RB-21, RB-18), por lo que la máquina no admite resultados que agregar | doc 01 §1.5.2; doc 04 §4.6.2 |

---

## 5.8 Inscripciones de gestión

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-23 | `GET /inscripciones?mesa_id=&convocatoria_id=` | `inscripcion.listar` |
| CU-24 | *(sin endpoint de anulación en `/api/v1/sigme`)* | `inscripcion.anular` — contrato **PENDIENTE** |
| CU-25 | *(sin endpoint de inscripción en `/api/v1/sigme`)* | `inscripcion.crear` — **PENDIENTE** (sin endpoint en §6) |

**CU-23 — Consultar inscripciones**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Los cuatro roles de `sigme_web` (`inscripcion.listar` en **S**) | doc 02 §2.4 |
| Gatillo | Consulta de gestión del consumidor; sin `E-xx` de lectura en doc 03 §3.1 | doc 02 §2.1.1 |
| Precondiciones | Sesión válida; filtro por `mesa_id` o por `convocatoria_id` | `analisis.txt` §6 |
| Flujo principal | 1) `GET /inscripciones?mesa_id=&convocatoria_id=`; 2) el backend devuelve las filas con su estado | `analisis.txt` §6, §3.19 |
| Resultado | Sólo existen dos estados posibles: `inscripto` y `anulado` (RB-21, §3.19); después de `fecha_fin_inscripcion` la lista es la definitiva y no se revalida (RB-17, RB-18) | `analisis.txt` §4, §3.19 |
| Permisos | `inscripcion.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | La anulación de una fila conserva el registro para auditoría y lo saca del índice único (S-04, RB-08b); no hay estados de nota, asistencia ni aprobación (RB-21, RB-18, RB-02) | doc 03 §3.3; `analisis.txt` §4 |

**CU-24 — Anular una inscripción desde SIGME — PENDIENTE (contrato)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a (el modelo habilita al secretario a revocar, junto con el propio alumno) | `analisis.txt` §3.19; doc 04 INS-03 |
| Gatillo | S-04 · anulación de una inscripción | doc 03 §3.3 |
| Precondiciones | Fila en `inscripto`; la anulación deja la fila en `anulado`, conservada y fuera del índice único, de modo que libera la materia | `analisis.txt` §3.19; RB-08b |
| Flujo principal | **No definido para SIGME** — §6 no declara ninguna operación de anulación bajo `/api/v1/sigme`; `DELETE /mis-inscripciones/{id}` pertenece a `/api/v1/sigme-mobile` y es del **doc 06** | `analisis.txt` §6; doc 02 §2.1.2 |
| Resultado | El estado resultante sería `anulado` (INS-03), con la fila intacta para auditoría | doc 04 §4.3 |
| Permisos | `inscripcion.anular` — Secretario/a **S**, Administrador **S**, Superadmin **S**, Director **—**; el permiso existe, el contrato no | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PENDIENTE** sin PD propio: (a) falta el endpoint en §6; (b) ¿la ventana de inscripción limita también al secretario? RB-08b y RB-07 se formulan desde el alumno y §3.19 no pone ese límite (doc 04 INS-03) | doc 04 INS-03, §4.6.1; `analisis.txt` §4 |

**CU-25 — Inscribir en nombre de un alumno desde SIGME — PENDIENTE (sin endpoint)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | **PENDIENTE** — Secretario/a, Administrador y Superadmin figuran con `inscripcion.crear` en duda; Director **—** | doc 02 §2.4 |
| Gatillo | Necesidad de gestión no declarada como evento: doc 03 §3.1 no tiene un `E-xx` de inscripción desde SIGME | doc 03 §3.1; doc 02 §2.4 |
| Precondiciones | Si existiera, exigiría ventana vigente (RB-06, RB-07, RB-09, RB-23), unicidad por materia × convocatoria (RB-08 → 409), límite de la condición (RB-03, **[CERRADO — 2026-10-06]**, PD-02: Previa hasta 3, Regular hasta 8, Libre sin límite, unidad por convocatoria) y mesa ya creada por el secretario (RB-28, RB-31) | `analisis.txt` §4; doc 04 INS-01 |
| Flujo principal | **No definido** — §6 declara `POST /inscripciones` sólo bajo `/api/v1/sigme-mobile`; no hay operación equivalente en `/api/v1/sigme` | `analisis.txt` §6 |
| Resultado | El alta de inscripciones queda reservada al alumno en SIGME-M (**doc 06**) mientras el permiso siga sin dueño | doc 02 §2.4; doc 01 §1.5.1 |
| Permisos | `inscripcion.crear` — Alumno **S**; Secretario/a, Administrador y Superadmin **PENDIENTE** (hueco de la matriz de doc 02 §2.4, **[CERRADO — 2026-10-06]**, PD-03) | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-03** **[CERRADO — 2026-10-06]** — el reparto sale de la matriz de doc 02 §2.4, que no asigna estos roles · **PD-02** **[CERRADO — 2026-10-06]** — Previa hasta 3, Regular hasta 8, Libre sin límite (NULL), unidad por convocatoria · **PD-19** — código HTTP del rechazo cuando la combinación no tiene mesa | `analisis.txt` §7 |

---

## 5.9 Consulta de preinscripciones

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-26 | `GET /preinscripciones` | `preinscripcion.listar` |

**CU-26 — Consultar preinscripciones**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`preinscripcion.listar` en **S**) | doc 02 §2.4 |
| Gatillo | E-12 · se consulta una preinscripción desde SIGME | doc 03 §3.1 |
| Precondiciones | Sesión válida con módulo `sigme_web`; `pr_preinscripcion` está aislada: sin FK hacia `pe_*` ni `es_*` | `analisis.txt` §2.8, §3.20 |
| Flujo principal | 1) `GET /preinscripciones`; 2) el backend devuelve las filas con su estado (`pendiente`, `convertido`, `descartado`) y sus campos de identidad (`anio_lectivo`, `documento`) | `analisis.txt` §6, §3.20 |
| Resultado | Consulta de seguimiento de las solicitudes de ingreso al próximo año lectivo; la escritura del formulario es exclusiva de la landing (RB-10, doc 11) | `analisis.txt` §4; doc 02 §2.1.3 |
| Permisos | `preinscripcion.listar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | §6 declara `GET\|PATCH /preinscripciones (sólo consulta)`: el efecto del `PATCH` no lo declara ninguna regla — **PENDIENTE**, **PD-22** (ver 5.11) · **G-02** — el permiso `preinscripcion.crear` no puede aplicarse dentro de SIGME porque la landing es anónima | `analisis.txt` §6; doc 01 §1.5.2; doc 02 §2.1.1, §2.4 |

---

## 5.10 Reportes de cierre

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-27 | `GET /reportes/permiso-examen/{usuario_id}`, `GET /reportes/permisos-examen` | `reporte.exportar` |
| CU-28 | `GET /reportes/acta-volante/{mesa_id}` | `reporte.exportar` |
| CU-29 | `GET /reportes/mesa/{id}` | `reporte.exportar` (propuesto) |
| CU-30 | `GET /reportes/planilla-grupos/{convocatoria_id}` | `reporte.exportar` |

**CU-27 — Emitir el permiso de examen (individual y masivo)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`reporte.exportar` en **S**) | doc 02 §2.4 |
| Gatillo | E-09 · se solicita un reporte impreso de cierre | doc 03 §3.1 |
| Precondiciones | Mesas con **al menos una inscripción activa** (RB-22); cada mesa aporta su `fecha` y su `hora` copiadas del grupo (RB-27, RB-29) | `analisis.txt` §4, §3.18 |
| Flujo principal | 1) `GET /reportes/permiso-examen/{usuario_id}` para el documento individual de un alumno; 2) `GET /reportes/permisos-examen` para la impresión masiva agrupada por mesa; 3) el backend filtra mesas sin inscriptos activos | `analisis.txt` §6; RB-19, RB-22 |
| Resultado | Impresión en papel entregada en mano al alumno; el sistema no almacena notas, por lo que el documento no es un registro editable (RB-21) | `analisis.txt` §4; doc 01 §1.2.1 |
| Permisos | `reporte.exportar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S**; el reparto exacto entre roles sale de la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**) | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | La impresión masiva "a toda ley" depende de RB-22: una mesa cuya última inscripción activa se anule desaparece de la impresión (S-11) sin borrarse (S-03) | doc 03 §3.3 |

**CU-28 — Emitir el acta volante**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`reporte.exportar` en **S**) | doc 02 §2.4 |
| Gatillo | E-09 · se solicita un reporte impreso de cierre | doc 03 §3.1 |
| Precondiciones | Mesa con al menos una inscripción activa (RB-22) | `analisis.txt` §4 |
| Flujo principal | 1) `GET /reportes/acta-volante/{mesa_id}`; 2) el backend devuelve los inscriptos activos de esa mesa | `analisis.txt` §6; RB-19 |
| Resultado | Impresión en papel destinada a los profesores evaluadores; la mesa con 0 alumnos no se imprime y no se borra (S-03) | `analisis.txt` §4; doc 03 §3.3 |
| Permisos | `reporte.exportar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | El profesor evaluador **no** es un rol del sistema: sólo recibe el documento en papel (**G-03**, PD-03) | doc 01 §1.5.2; RB-19 |

**CU-29 — Consultar el detalle de una mesa para reporte**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Rol con acceso a reportes (propuesta: `reporte.exportar`) | doc 02 §2.1.1, §2.4 |
| Gatillo | E-09 · consulta del detalle que alimenta la impresión | doc 03 §3.1 |
| Precondiciones | Mesa existente; los 4 snapshot están rellenos desde su creación o desde su última edición de asignación (RB-11) | `analisis.txt` §3.18 |
| Flujo principal | 1) `GET /reportes/mesa/{id}`; 2) el backend lee las columnas snapshot de la mesa, no el nombre actual de las tablas de catálogo | `analisis.txt` §6; RB-11, RB-12 |
| Resultado | Detalle estable: un renombre de catálogo posterior no altera lo que se imprime (S-09) | `analisis.txt` §4; doc 03 §3.3 |
| Permisos | Propuesto `reporte.exportar` (doc 02 agrupa este endpoint bajo Reportes); la asignación endpoint → permiso sale de la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**), mientras que §6 no declara el permiso de esta ruta | doc 02 §2.1.1; `analisis.txt` §2.7; PD-03 |
| Excepciones y pendientes | Sin alternativos declarados en la fuente: es una lectura sobre una mesa existente, con los mismos filtros que CU-19 | `analisis.txt` §6 |

**CU-30 — Emitir la planilla de grupos**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Secretario/a, Director, Administrador y Superadmin (`reporte.exportar` en **S**) | doc 02 §2.4 |
| Gatillo | E-09 · se solicita un reporte impreso de cierre | doc 03 §3.1 |
| Precondiciones | Convocatoria con grupos (fecha + hora); sólo mesas con al menos una inscripción activa (RB-22); **[CONFIRMADO — 2026-10-04]** para la primera entrega (RB-32) | `analisis.txt` §4; doc 01 §1.2.1 |
| Flujo principal | 1) `GET /reportes/planilla-grupos/{convocatoria_id}`; 2) el backend lista cada grupo con sus mesas (materia y condición) | `analisis.txt` §6; RB-32 |
| Resultado | Vista de horario por convocatoria en papel; **no** es una lista de alumnos por mesa — ese detalle sigue siendo exclusivo del acta volante (RB-19, RB-32) | `analisis.txt` §4 |
| Permisos | `reporte.exportar` — Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S** | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **PD-16** **[CERRADO — 2026-10-06]** — `uq_grupo_unico` impide grupos idénticos duplicados; **PD-17** sigue abierto: la interpretación de `hora` no está definida; los grupos borrados arrastran lógicamente sus mesas (**PD-18** **[CERRADO — 2026-10-06]**) | `analisis.txt` §7 |

---

## 5.11 Consolidado de pendientes

Las filas siguientes se heredan de `analisis.txt` §7 y de doc 01 §1.5.2. Las
marcadas **[CERRADO — 2026-10-06]** (o **[RESUELTA]** para G-05) ya tienen
decisión escrita en la fuente y se conservan aquí —sin renumerar el ID— para
que los documentos 07, 08 y 10 las hereden trazadas; el resto sigue siendo
**pregunta abierta** y ninguna se resuelve en este documento.

| ID | Pregunta abierta | Dónde toca en este documento | Fuente |
|---|---|---|---|
| **PD-03** | **[CERRADO — 2026-10-06]** Semilla inicial de roles, permisos y usuarios administradores, incluido el reparto exacto rol × permiso y el mapeo endpoint → permiso — migración inicial de Alembic, primer superadmin por variable de entorno, reparto desde la matriz de doc 02 §2.4 | Todo el reparto de permisos citado (5.1–5.10); CU-08, CU-09, CU-10, CU-11, CU-12, CU-13, CU-14, CU-18, CU-25, CU-29 | `analisis.txt` §7; doc 02 §2.4 |
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? ¿qué efecto tiene sobre alumnos ya inscriptos? | CU-15, CU-16 | `analisis.txt` §7; doc 04 §4.6.5 |
| **PD-13** | **[CERRADO — 2026-10-06]** ¿Debe `uq_mesa_unica` incluir `hora`? — no: `UNIQUE (convocatoria_id, materia_id, condicion_id, fecha) WHERE deleted_at IS NULL`, con `convocatoria_id` agregado y `hora` fuera (dos franjas serían turnos, RB-15); migración del índice | CU-15 | `analisis.txt` §7 |
| **PD-15** | ¿De dónde sale el conjunto esperado de pares materia × condición para la cobertura, si la convocatoria no tiene FK al catálogo? | CU-21 | `analisis.txt` §7; RB-31 |
| **PD-16** | **[CERRADO — 2026-10-06]** ¿Se agrega `UNIQUE (convocatoria_id, fecha, hora)` a `es_grupo_horario`? — sí: `uq_grupo_unico` parcial `WHERE deleted_at IS NULL`; la colisión responde 409 | CU-15, CU-17, CU-30 | `analisis.txt` §7 |
| **PD-17** | ¿Cómo se interpreta `grupo.hora` (`time` sin zona) al combinarse con `fecha` frente a RB-23? | CU-15, CU-16, CU-30 | `analisis.txt` §7 |
| **PD-18** | **[CERRADO — 2026-10-06]** ¿Se permite el borrado lógico de un grupo con mesas vivas que lo referencian, y considera `vw_mesa_con_alumnos` ese `deleted_at`? — cascada lógica transaccional: borrar el grupo borra lógicamente todas sus mesas en la misma transacción, y si alguna tiene inscripciones activas la operación entera falla | CU-17, CU-18, CU-30 | `analisis.txt` §7 |
| **PD-19** | ¿Qué código HTTP devuelve el rechazo de `POST /inscripciones` cuando la combinación no tiene mesa? | CU-21, CU-25 | `analisis.txt` §7; RB-31 |
| **PD-20** | El catálogo de materias es texto sin estructura machine-readable (sin IDs, sin mapping a condiciones, sin flags `es_taller`): ¿formato canónico para validarlo? | CU-05, CU-06, CU-21 | `analisis.txt` §7 |
| **PD-21** | Renombrado/alta de catálogo sin endpoint: §6 declara sólo `GET\|POST` para `/orientaciones`, `/cursos`, `/materias` y `/condiciones`, mientras que E-08 y S-09 lo materializan como `PATCH` — ¿se agrega el `PATCH` o se declara el renombre fuera de contrato? | CU-06 | `analisis.txt` §7; doc 03 §3.1 |
| **PD-22** | Efecto del `PATCH /preinscripciones`: §6 lo anota como "sólo consulta" pero ninguna regla de §4/§6 define qué cambia — ¿se define el efecto o se elimina el `PATCH`? | CU-26 | `analisis.txt` §7; doc 02 §2.1.1 |
| **PD-29** | Alcance de `POST /mesas` fuera de la alta masiva del grupo: §6 declara la ruta pero ninguna regla de estado describe la creación de una mesa suelta | CU-19 | `analisis.txt` §7; doc 04 §4.6.4 |
| **G-01** | ¿Qué significa **"matrícula"** para el cliente? La palabra no existe en `analisis.txt`; ningún caso de uso la usa | Vocabulario de 5.1–5.10 (palabra no empleada) | doc 01 §1.5.2, §1.3 |
| **G-02** | ¿Qué rol usa el permiso `preinscripcion.crear`? La landing es anónima y no pasa por RBAC | CU-14, CU-26 | doc 01 §1.5.2; doc 02 §2.4 |
| **G-03** | ¿Existe el rol **"docente"**? Aparece como comentario de ejemplo en el DDL de `us_rol`, pero P-08 no lo incluye | CU-10, CU-28 | doc 01 §1.5.2; `analisis.txt` §3.6 |
| **G-04** | ¿Cómo obtiene SIGME-M las opciones de orientación → curso → materia → condición? | Fuera de este documento: lo resuelve el **doc 06** | doc 01 §1.5.2; `analisis.txt` §6 |
| **G-05** | **[RESUELTA — 2026-10-06]** ¿Quién y cómo cambia el estado de la convocatoria y de la mesa? — nadie: el disparador es el calendario y la constatación se calcula al leer; el archivado de la convocatoria sigue sin endpoint | CU-13, CU-22 | doc 01 §1.5.2; doc 04 §4.6.2 |

**Operaciones sin contrato declarado.** No se inventan endpoints ni permisos
para ellas; quedan referenciadas a la fuente que las marca:

| Operación | Situación | Fuente |
|---|---|---|
| Baja de un grupo | `mesa.eliminar` existe en §2.7, pero §6 no expone operación de baja — CU-18 **PENDIENTE** | `analisis.txt` §6, §2.7; doc 04 GR-02 |
| Cambio de estado de la mesa | El `CHECK` de `es_mesa_examen` admite tres valores y ninguno los escribe: con la regla temporal el estado se constata al leer — CU-22 **[CERRADO — 2026-10-06]**, sin endpoint ni permiso | `analisis.txt` §3.18; doc 04 §4.2 |
| Anulación de inscripción desde SIGME | Permiso real (`inscripcion.anular`), sin endpoint en `/api/v1/sigme` — CU-24 **PENDIENTE** | `analisis.txt` §6; doc 04 INS-03 |
| Inscripción en nombre de un alumno | `inscripcion.crear` sin endpoint en SIGME y sin dueño en la matriz de doc 02 §2.4 (PD-03 cerrado 2026-10-06) — CU-25 **PENDIENTE** | `analisis.txt` §2.7, §6; doc 02 §2.4 |
| Renombrado de catálogo | E-08 lo formula como `PATCH`; §6 sólo declara `GET\|POST` para el catálogo — **PENDIENTE** de reconciliación, **PD-21** | doc 03 §3.1; `analisis.txt` §6 |
| Efecto del `PATCH /preinscripciones` | §6 lo anota como "sólo consulta" y ninguna regla declara su efecto — **PENDIENTE**, **PD-22** | `analisis.txt` §6; doc 02 §2.1.1 |

---

## Checklist de cierre (5 · Casos de uso SIGME)

- [x] **30 casos de uso con ID estable** (`CU-01`…`CU-30`), agrupados en 10
      secciones que reproducen los grupos de doc 03 §3.4 con destino doc 05
      (ventanas y convocatorias, grupos de mesas, reportes de cierre, seguridad
      y sesión) más catálogo, personas-usuarios, inscripciones de gestión y
      consulta de preinscripciones.
- [x] **Cada CU declara** actor, gatillo, precondiciones, flujo principal,
      resultado, permisos y fuentes (`RB-xx`, `PD-xx`, `E-xx`, `S-xx`, `T-xx`,
      `G-xx`, `§6`).
- [x] **Todo endpoint citado existe en `analisis.txt` §6**: 27 de los 30 CU
      operan rutas declaradas en §6 (o una constatación sin endpoint, como el
      cierre por calendario de CU-13 y el estado de CU-22); los 3 sin
      contrato —CU-18, CU-24 y CU-25— están marcados **PENDIENTE** con su
      PD/G o con la referencia de doc 04, sin inventar rutas ni códigos.
- [x] **Permisos idénticos a doc 02 §2.4**: `mesa.crear` y `mesa.modificar` en
      Secretario/a **S** y Director **—**; `mesa.eliminar` con Secretario/a
      **PENDIENTE**; `inscripcion.crear` con Secretario/a **PENDIENTE**;
      `usuario.gestionar` sólo en Administrador y Superadmin;
      `reporte.exportar` y `preinscripcion.listar` en los cuatro roles;
      `preinscripcion.crear` citado sólo como anónimo y fuera de RBAC (G-02).
- [x] **Cero vocabulario retirado**: ninguna de las expresiones que doc 01
      §1.3 marca como prohibidas o retiradas por el modelo de grupos aparece en
      este documento; verificación por búsqueda de patrón sobre el archivo
      final → **0 coincidencias**.
- [x] **Preguntas conservadas con su estado**: PD-03, PD-13, PD-16 y PD-18
      figuran en 5.11 marcados **[CERRADO — 2026-10-06]** y G-05 como
      **[RESUELTA — 2026-10-06]**; PD-12, PD-15, PD-17, PD-19, PD-20, PD-21,
      PD-22, PD-29 y G-01…G-04 siguen como preguntas abiertas; ninguna se
      completa por suposición.
- [x] **Consistencia con doc 04**: la ventana se constata por calendario
      (RB-23, C-02/C-04), la alta de mesas es del secretario en bloque dentro
      de un grupo (RB-27, RB-28, GR-01/ME-01), el estado de la mesa se
      constata al leer sin escritura (**G-05 resuelta** 2026-10-06) y la
      inscripción sólo admite `inscripto` y `anulado` (RB-21).
- [x] **Reportes**: los tres documentos de cierre de RB-19 y RB-32 están
      cubiertos (CU-27, CU-28, CU-30) con `reporte.exportar` y con el filtro
      RB-22; el detalle de mesa (CU-29) lee snapshot (RB-11, RB-12).
- [x] **Toda cita externa resuelve**: `RB-xx`/`PD-xx`/`§n` en `analisis.txt`;
      `E-xx`/`S-xx`/`T-xx` en doc 03; `G-xx` en doc 01 §1.5.2;
      `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` en doc 04; `CU-xx`
      definidos en este documento.
- [ ] **Criterio del plan (plan §3.05): cada excepción mapea a un código HTTP
      concreto — no se cierra acá.** Los códigos de error y los estados
      críticos pertenecen al **doc 07** por decisión de alcance: este documento
      sólo referencia los que las fuentes ya declaran (401 en T-07, 409
      ventana-cerrada en RB-14) y deja **PD-19** abierto para el rechazo sin
      mesa. Las filas de excepción/pendiente sí existen en los 30 CU.

## Siguiente paso

`06-casos-de-uso-sigme-m.md`: los casos de uso del alumno en SIGME-M — sesión,
consulta de convocatoria y mesas, inscripción con reintentos, mis inscripciones
y anulación — tomando de este documento el límite entre lo que el alumno sólo
lee (RB-30, RB-22) y lo que el secretario planifica (RB-28, RB-29), y dejando
del **doc 05** los pendientes de cobertura (PD-15, PD-19) que comparten
contrato con `POST /inscripciones`.
