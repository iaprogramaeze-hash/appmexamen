# 06 · Casos de uso SIGME-M — Backend EPET36

**Respuesta corta:** el cliente SIGME-M necesita **12 casos de uso**
(`CU-31`…`CU-42`) repartidos en siete dominios: sesión móvil, consulta de
convocatoria y mesas, inscripción, mis inscripciones, anulación y
reinscripción, operación degradada con idempotencia, y notificaciones push.
Cada operación se apoya en un endpoint declarado en `analisis.txt` §6 o en un
permiso del catálogo §2.7; las que carecen de contrato quedan **PENDIENTE**
con su PD/G en **6.8** — la cascada de la combinación (CU-36, **G-04**) —,
nunca se completan por suposición.

Vocabulario: se usan los términos de `01-glosario-y-alcance.md` (1.2 y 1.3), el
consumidor y sus lesiones de `02-actores-y-consumidores.md` (2.1.2 y 2.4), los
eventos de `03-eventos-y-gatillos.md` (3.1–3.4, incluidas las tablas con
destino doc 06) y las transiciones de `04-maquinas-de-estados.md` (4.3, 4.4.2 y
4.6.1). Toda cita `RB-xx` y `PD-xx` remite a `analisis.txt` (§4 y §7); `§n.m`
remite a la sección de ese archivo; `E-xx`, `S-xx` y `T-xx` remiten a doc 03;
`G-xx` a doc 01 §1.5.2.

## Rápido recorrido

1. **6.1** — sesión móvil: autenticarse, renovar y cerrar la sesión (E-10,
   T-07…T-09).
2. **6.2** — consulta: convocatoria vigente, mesas disponibles y la cascada
   orientación → curso → materia → condición (E-03, G-04).
3. **6.3** — inscribirse, con reintentos, ventana cerrada y duplicado (E-01,
   E-13; 409 por duplicado).
4. **6.4** — mis inscripciones y fechas (E-03, RB-26).
5. **6.5** — anular por error de elección y reinscribirse (E-02, RB-08b,
   RB-08c).
6. **6.6** — contratos para operar degradado: caché sin red ni token,
   escritura online, sin cola offline y semántica de idempotencia por
   operación (RB-26, plan §3.06).
7. **6.7** — notificaciones push por evento de usuario (RB-24, S-20).
8. **6.8** — consolidado de pendientes: PD-02, PD-03, PD-10…PD-19,
   PD-23, PD-28 y G-01…G-05.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Alcance** | Sólo el consumidor `sigme_mobile` (Alumno). Las operaciones de gestión de SIGME son del **doc 05**; el envío de la landing, del **doc 11**; los códigos de error y los estados críticos, del **doc 07** — aquí se referencian, no se definen. | doc 02 §2.1.2, §2.2; plan §3 (05, 06, 07, 11) |
| **Rutas** | Las operaciones del alumno viven bajo `/api/v1/sigme-mobile` y las de sesión bajo `/api/v1/auth`. | `analisis.txt` §6 |
| **Permisos** | `analisis.txt` §6 **no declara** el permiso de cada endpoint; §2.7 exige la dependencia `require_permiso()`. El reparto por rol citado acá sale de la matriz de doc 02 §2.4, **[CERRADO — 2026-10-06]**: con PD-03 esa matriz es la fuente definitiva (roles y permisos en la migración inicial de Alembic, primer superadmin por variable de entorno); sus celdas `PENDIENTE` son huecos de la matriz y siguen abiertos. | `analisis.txt` §2.7; doc 02 §2.4; PD-03 (cerrado 2026-10-06) |
| **PENDIENTE** | Toda operación sin endpoint en §6 o sin código de permiso en §2.7 queda marcada **PENDIENTE** con su `PD-xx`/`G-xx` en **6.8**; los casos que hasta el 2026-10-05 no tenían ID llevan hoy el que les asignó el mantenedor en `analisis.txt` §7. No se inventan endpoints, identificadores, roles ni permisos. | doc 01 §1.1; `analisis.txt` §2.7, §6, §7 |
| **Identificadores** | `CU-31`…`CU-42` continúan en este documento la serie única de los docs 05 y 06 (doc 03 §3.4 dejó la numeración a los dos). `RB-xx`/`PD-xx` → `analisis.txt` (§4, §7); `E-xx`/`S-xx`/`T-xx` → doc 03; `G-xx` → doc 01 §1.5.2; `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` → doc 04. | doc 03 §3.4; plan §3 (06) |
| **Ventanas y reloj** | Toda ventana se **constata** en cada request por fecha de calendario en `America/Argentina/Buenos_Aires`, inclusive hasta las 23:59:59; el reloj autoritativo es el del backend, nunca el del dispositivo; no hay ningún job programado en v1. | RB-23; doc 03 §3.2; doc 02 §2.1.2 |
| **Offline (RB-26)** | Lectura con caché: la última respuesta se muestra localmente con su "última actualización", sin red ni token. Toda escritura exige conexión y sesión válida. No existe ninguna cola de acciones offline. | RB-26; doc 02 §2.1.2 |
| **Vocabulario** | Se respetan los términos de doc 01 §1.2: el alumno elige **sólo materia y condición** y ve la fecha y la hora de la mesa — nunca elige ni ve el grupo; la planificación vive en **grupos de mesas** (`fecha` + `hora`). | doc 01 §1.2; RB-30, RB-27 |

---

## 6.1 Sesión y autenticación móvil

| CU | Operación (§6) | Control |
|---|---|---|
| CU-31 | `POST /auth/login` (+ `GET /auth/yo`) | autenticación |
| CU-32 | `POST /auth/refresh` | autenticación |
| CU-33 | `POST /auth/logout`, `POST /auth/logout-all` | autenticación |

**CU-31 — Autenticarse desde el móvil · `POST /auth/login`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno con credenciales y módulo `sigme_mobile` asignado | doc 02 §2.2, §2.5 |
| Gatillo | E-10 · login con credenciales válidas | doc 03 §3.1 |
| Precondiciones | Clave verificada con Argon2id (m=19456, t=2, p=1; longitud mínima 12); `username` único entre cuentas no borradas; cuenta no bloqueada; rate limit de hasta 5 fallos por usuario/IP cada 15 minutos; módulo `sigme_mobile` asignado (`us_sesion.modulo_id NOT NULL`) | `analisis.txt` §2.4, §2.5, §3.5, §3.12, §2.8 |
| Flujo principal | 1) `POST /auth/login`; 2) verificación del hash y del rate limit; 3) alta de `us_sesion` en `activo` con el módulo `sigme_mobile`; 4) emisión de access token (15 min, máx. 30) con roles, permisos y módulos, y de refresh token (7 días) | `analisis.txt` §2.1, §2.2, §2.4; doc 04 SES-01 |
| Resultado | Sesión vigente; en base de datos sólo se guarda el SHA-256 del refresh. Los tokens se guardan en Keychain/Keystore: el almacenamiento en memoria del navegador o en AsyncStorage está prohibido. El cliente comprueba su identidad con `GET /auth/yo` (`GET /yo` bajo `/api/v1/auth`) | `analisis.txt` §2.1, §2.2, §6 |
| Permisos | No aplica: autenticación, no autorización — el permiso gobierna los endpoints protegidos | `analisis.txt` §2.7; doc 04 SES-01 |
| Excepciones y pendientes | **Sin alternativos declarados:** el login es lineal. **Excepción:** 5 fallos en 15 minutos → bloqueo temporal (`bloqueado_hasta`) y subida de `token_version` (E-14, S-16, US-02); vencido el bloqueo se reanudan los intentos (T-09, US-03). Credenciales inválidas o módulo sin asignar → no se crea sesión. El rate limit y el bloqueo aplican igual que en la web | `analisis.txt` §2.4, §2.6, §2.8; doc 03 §3.1–§3.2; doc 04 US-02, US-03; doc 02 §2.1.2 |

**CU-32 — Renovar la sesión · `POST /auth/refresh`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno con sesión vigente en el cliente móvil | doc 02 §2.2 |
| Gatillo | T-07 · vence el access token (15 minutos); rotación proactiva del cliente | doc 03 §3.2 |
| Precondiciones | Refresh token vigente (7 días, `us_sesion.expires_at`) y aún no consumido; sesión en `activo` | `analisis.txt` §2.2, §3.12 |
| Flujo principal | 1) `POST /auth/refresh`; 2) rotación: se emite un refresh nuevo y se revoca el anterior; 3) se emite un access token nuevo con la versión vigente | `analisis.txt` §2.1, §2.2 |
| Resultado | La sesión sigue `activo` hasta `expires_at`; el access renovado vuelve a autorizar las escrituras de 6.3 y 6.5. La lectura en caché de 6.6 no lo necesita | `analisis.txt` §2.2, §2.6; RB-26 |
| Permisos | No aplica (autenticación) | `analisis.txt` §2.7 |
| Excepciones y pendientes | **Flujos alternativos:** access token vencido → 401 en la acción protegida y el cliente rota con este endpoint (T-07). **T-08** · vencidos los 7 días la sesión ya no rota: se exige login nuevo. **S-14** · un refresh reutilizado (timeout con respuesta perdida y reintento, escenario típico de red móvil inestable) revoca **toda la familia** de la sesión y exige login nuevo | doc 03 §3.2–§3.3; `analisis.txt` §2.1, §2.2; doc 04 SES-04 |

**CU-33 — Cerrar sesión · `POST /auth/logout` y `POST /auth/logout-all`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | El dueño de la sesión (logout) o el dueño del usuario sobre todas sus sesiones (logout-all: cerrar sesión en todos los dispositivos) | doc 04 SES-02, SES-03; `analisis.txt` §2.3 |
| Gatillo | E-10 · cierre de sesión | doc 03 §3.1 |
| Precondiciones | Sesión propia vigente en `activo` | `analisis.txt` §3.12 |
| Flujo principal | 1) `POST /auth/logout` revoca la sesión actual; 2) `POST /auth/logout-all` revoca todas las sesiones del usuario; 3) el refresh deja de rotar | `analisis.txt` §2.3, §2.4 |
| Resultado | `us_sesion.estado = 'revocado'` (S-18); el siguiente acceso exige un login nuevo | `analisis.txt` §3.12; doc 03 §3.3 |
| Permisos | No aplica (autenticación) | `analisis.txt` §2.7 |
| Excepciones y pendientes | **Sin alternativos declarados:** la operación sólo cambia el estado de la sesión y no toca datos de negocio | doc 04 §4.4.2 |

---

## 6.2 Consulta de convocatoria y mesas disponibles

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-34 | `GET /convocatoria-vigente` | **PENDIENTE** (sin código en §2.7) |
| CU-35 | `GET /mesas-disponibles` | `mesa.listar` |
| CU-36 | *(sin endpoint declarado: la cascada vive como comentario de §6)* | **PENDIENTE (G-04)** |

**CU-34 — Consultar la convocatoria vigente · `GET /convocatoria-vigente`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno (SIGME-M), para saber si hay ventana abierta | doc 02 §2.1.2, §2.2 |
| Gatillo | E-03 · consulta de la convocatoria vigente; T-01/T-02 · se cumple la fecha de inicio o la de fin | doc 03 §3.1, §3.2 |
| Precondiciones | Convocatoria existente; la ventana **se constata** en cada request con la fecha de calendario del backend, sin intervención humana ni scheduler (RB-23) | `analisis.txt` §3.17; doc 04 C-02, C-04 |
| Flujo principal | 1) `GET /convocatoria-vigente`; 2) el backend devuelve la convocatoria vigente con `fecha_inicio_inscripcion` y `fecha_fin_inscripcion` y deriva su estado (`borrador`, `abierta`, `cerrada`, `archivada`) | `analisis.txt` §6, §3.17; doc 04 §4.1 |
| Resultado | El alumno sabe si puede inscribir o anular: en `abierta` ambas acciones están habilitadas (RB-06, RB-07); en `cerrada` sólo consulta la fecha de rendir (RB-07); con la convocatoria inactiva no se inscribe (RB-09). La respuesta es autosuficiente para mostrarse desactualizada desde la caché (RB-26) | `analisis.txt` §4; doc 02 §2.1.2 |
| Permisos | **PENDIENTE** — el catálogo §2.7 no contiene ningún código de lectura de convocatoria y §6 no declara el permiso de esta ruta; doc 02 §2.4 no la asigna a ningún permiso. El reparto sale de esa matriz (**[CERRADO — 2026-10-06]**, PD-03) y el hueco de código sigue en §2.7 | `analisis.txt` §2.7; doc 02 §2.4; PD-03 |
| Excepciones y pendientes | **Flujos alternativos:** convocatoria cerrada o inactiva → sólo lectura, sin inscripción ni anulación (RB-07, RB-09, S-07, T-03). **T-06/RB-16** · pasada la última fecha de grupos la campaña se cierra y en la fecha que corresponda se abre **otra** convocatoria: el alumno verá la nueva sin acción propia. **G-05** **[RESUELTA — 2026-10-06]** — nadie dispara ese cierre: es una constatación del calendario, y determina cuándo cambia lo que devuelve este endpoint | `analisis.txt` §4; doc 03 §3.2, §3.4; doc 01 §1.5.2; doc 04 §4.6.2 |

**CU-35 — Consultar las mesas disponibles · `GET /mesas-disponibles`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno (`mesa.listar` en **S**); la consulta alimenta la pantalla de inscripción | doc 02 §2.1.2, §2.4 |
| Gatillo | E-03 · consulta de mesas disponibles | doc 03 §3.1 |
| Precondiciones | Sólo dentro de la ventana de inscripción (§6 restringe el endpoint); las mesas ya existen porque las creó el secretario en bloque dentro de un grupo (RB-27, RB-28) — el alumno nunca crea mesas | `analisis.txt` §6, §4 |
| Flujo principal | 1) `GET /mesas-disponibles` dentro de la ventana; 2) el backend devuelve cada mesa con su **fecha** y su **hora**, presentadas agrupadas para su lectura; 3) la respuesta alimenta la cascada orientación → curso → materia → condición (comentario de §6 junto a este endpoint) | `analisis.txt` §6; RB-30; doc 02 §2.1.2 |
| Resultado | El alumno ve día y hora para rendir y elige sólo materia + condición: el grupo es agrupación de presentación, nunca una elección ni una entrada de validación (RB-30). La última respuesta queda cacheable con su "última actualización" (RB-26) | `analisis.txt` §4; doc 02 §2.1.2 |
| Permisos | `mesa.listar` — Alumno **S**, Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S**; la justificación de doc 02 §2.4 nombra exactamente esta consulta ("Consulta de mesas disponibles (§6)") | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **Flujos alternativos:** fuera de la ventana el endpoint no participa (§6 lo restringe) y la consulta de RB-07 la cubren CU-34 y CU-38 · S-03 · una mesa que **quedó** con 0 alumnos tras anular todas no aparece y no se borra (RB-22). **PD-12** — si el secretario mueve un grupo con la ventana abierta, la fecha y la hora que devuelve este endpoint cambian para el alumno sin intervención suya: el efecto sobre los ya inscriptos queda **PENDIENTE**. **PD-17** — la interpretación de `hora` (`time` sin zona) al mostrarse sigue sin definirse. **Alcance de RB-22 sin resolver:** su cláusula operativa describe mesas que quedaron con 0 alumnos (S-03); si el filtro alcanzara a las mesas recién creadas, ninguna inscripción podría iniciarse en ellas (RB-28, RB-31) — **PENDIENTE (PD-23)**, ver 6.8 | `analisis.txt` §4, §6, §7; doc 03 §3.4; RB-22, RB-28, RB-31 |

**CU-36 — Alimentar la cascada orientación → curso → materia → condición — PENDIENTE (G-04)**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno, dentro de la pantalla de inscripción | doc 02 §2.1.2; `analisis.txt` §6 |
| Gatillo | E-01 · el alumno arma la cascada antes de tocar "inscribirse"; doc 03 §3.1 no tiene un `E-xx` propio para armarla — el comportamiento vive en el comentario de §6 | doc 03 §3.1; `analisis.txt` §6 |
| Precondiciones | §6 **no declara** endpoint de catálogo para el alumno: la cascada figura sólo como comentario junto a `GET /mesas-disponibles` (combo de orientación → curso filtrado por orientación → materias del curso → condiciones de la materia). El catálogo existe como datos (PD-09, resuelto) pero §2.7 no tiene código de catálogo para este consumidor | `analisis.txt` §6, §2.7, §7; doc 01 §1.5.2 |
| Flujo principal | **No definido** — no hay contrato de operación. El comentario de §6 sólo declara el comportamiento esperado del cliente y que, al aceptar, "las mesas ya EXISTEN": se busca la mesa de esa combinación y se crea la inscripción (RB-28, RB-31) | `analisis.txt` §6; RB-28, RB-31 |
| Resultado | Si existiera, produciría las opciones que consume CU-37. **Propuesta (no es contrato):** que `GET /mesas-disponibles` devuelva además las opciones derivadas de las mesas vigentes de la convocatoria, agrupadas orientación → curso → materia → condición, de modo que la cascada sólo ofrezca combinaciones con mesa | `analisis.txt` §6; RB-31; doc 01 §1.5.2 |
| Permisos | **PENDIENTE (G-04)** — sin endpoint no hay permiso que declarar; el catálogo §2.7 no contiene ningún código que cubra esta lectura para el alumno, el mismo hueco que dejó el doc 05 §5.2 para el catálogo de SIGME | `analisis.txt` §2.7; doc 02 §2.4; PD-03 (cerrado 2026-10-06, no creó el código); G-04 |
| Excepciones y pendientes | **G-04** — pregunta abierta de doc 01 §1.5.2 con destino a este documento ("¿Cómo obtiene SIGME-M las opciones de orientación → curso → materia → condición?"): mientras siga abierta, la cascada no puede certificarse y ninguna fuente autoriza a inventar el endpoint. Operación marcada **PENDIENTE**: sin contrato en §6 | doc 01 §1.5.2; `analisis.txt` §6 |

---

## 6.3 Inscribirse

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-37 | `POST /inscripciones` | `inscripcion.crear` |

**CU-37 — Inscribirse · `POST /inscripciones`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno (SIGME-M) sobre una mesa que **ya existe**. `inscripcion.crear` — Alumno **S**; inscribir en nombre de un alumno desde SIGME sigue **PENDIENTE** (sin endpoint en `/api/v1/sigme`) en doc 05 §5.8 — el cierre de PD-03 (2026-10-06) no lo creó | doc 02 §2.4; doc 04 INS-01 |
| Gatillo | E-01 · el alumno envía la cascada completa elegida, sobre una mesa que ya existe | doc 03 §3.1 |
| Precondiciones | Sesión válida y módulo asignado (RB-26, §2.8); convocatoria `activa` (RB-09); `hoy` dentro de la ventana, inclusive hasta las 23:59:59 (RB-07, RB-23); unicidad por **materia × convocatoria** (`uq_inscripcion_unica`, RB-08); límite de la condición validado **sólo aquí** (RB-03, valores **[CERRADO — 2026-10-06]**, PD-02: Previa hasta 3, Regular hasta 8, Libre sin límite, unidad por convocatoria); sin cupo por mesa (RB-01); sin etapa de aprobación (RB-02); la mesa ya existe porque la creó el secretario en bloque dentro de un grupo (RB-27, RB-28); el alumno elige sólo materia + condición, nunca grupo (RB-30) | `analisis.txt` §4, §3.19; doc 04 INS-01 |
| Flujo principal | 1) `POST /inscripciones` con la combinación elegida; 2) el backend evalúa convocatoria activa, ventana, unicidad y límite de la condición; 3) busca la mesa de esa materia × condición en la convocatoria; 4) crea la fila en `inscripto`; 5) encola la confirmación de la inscripción con fecha/hora por email (RB-24, RB-25, S-20) | `analisis.txt` §6, §4; doc 04 INS-01; doc 03 §3.3 |
| Resultado | INS-01 · nace `inscripto`. El alumno puede anotarse a una o varias materias dentro de la ventana (RB-06); la lista se fija al cerrar la ventana (RB-17) y no se revalida el día de la mesa (RB-18): no hay notas, asistencia ni aprobación que guardar (RB-21). La confirmación **no** va por push: el canal push de RB-24 sólo cubre apertura y cierre de ventanas (PD-07, cerrado) — la confirmación con fecha/hora es un email (RB-24, RB-25) | `analisis.txt` §4; doc 04 §4.3; RB-24 |
| Permisos | `inscripcion.crear` — Alumno **S**; Secretario/a **PENDIENTE**, Administrador **PENDIENTE**, Superadmin **PENDIENTE**, Director **—**; reparto definitivo en la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**, PD-03), donde esos roles siguen en celdas `PENDIENTE` | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **Flujos alternativos:** materia ya inscripta en la convocatoria → **409** y no se crea fila (RB-08, S-06, §6) · ventana cerrada → **409** (§6); convocatoria inactiva o fuera de la ventana → rechazo sin fila (RB-09, RB-07, S-07) · límite de la condición alcanzado → rechazo (RB-03, RB-08c, S-05) · combinación materia × condición sin mesa → no hay inscripción posible y nada falla de forma ruidosa (RB-31), con el código HTTP todavía en **PD-19**. **Flujo de reintento (E-13):** ante un timeout el cliente reintenta la misma escritura; la unicidad impide el duplicado — misma respuesta aplicable, sin duplicar (ver 6.6). **PD-15** — el origen del conjunto esperado de pares materia × condición comparte contrato con este endpoint | `analisis.txt` §6, §4, §7; doc 03 §3.3, §3.4; RB-08, RB-31; doc 04 INS-01 |

---

## 6.4 Mis inscripciones y fechas

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-38 | `GET /mis-inscripciones` | `inscripcion.listar` |

**CU-38 — Ver mis inscripciones y fechas · `GET /mis-inscripciones`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno, sobre sus propias inscripciones (`inscripcion.listar` en **S**) | doc 02 §2.4 |
| Gatillo | E-03 · consulta de las inscripciones propias | doc 03 §3.1 |
| Precondiciones | Filas propias del alumno autenticado; la lectura desde la caché local (6.6) no exige red ni token (RB-26) | `analisis.txt` §3.19; RB-26 |
| Flujo principal | 1) `GET /mis-inscripciones`; 2) el backend devuelve las filas con su estado (`inscripto` o `anulado`) y, para cada una, la fecha y la hora de la mesa, agrupadas para lectura — el grupo no se expone | `analisis.txt` §6; RB-21, RB-30; doc 04 §4.3 |
| Resultado | El alumno ve qué materias rinde y cuándo; sólo existen dos estados posibles (RB-21) y no hay notas ni asistencia (RB-18); después de `fecha_fin_inscripcion` la lista es la definitiva y no se revalida nada (RB-17). La respuesta es cacheable con su "última actualización" (RB-26) | `analisis.txt` §4; doc 03 §3.4 |
| Permisos | `inscripcion.listar` — Alumno **S**, Secretario/a **S**, Director **S**, Administrador **S**, Superadmin **S**; el alumno usa esta ruta y la gestión usa `GET /inscripciones` (doc 05 §5.8) | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **Flujos alternativos:** sin red o con sesión vencida → el cliente sirve su caché con "última actualización" y el backend no es llamado (RB-26, ver 6.6 y CU-41) · ventana cerrada → la consulta sigue disponible (RB-07, T-03). Una anulación conserva la fila y la muestra como `anulado`, sin ocupar en el índice único (S-04, RB-08b). **Paginación:** el plan §3.06 la pide para operar degradado y §6 no declara parámetros en ninguna ruta — **PENDIENTE (PD-28)**, ver 6.8 | `analisis.txt` §4, §6, §7; doc 03 §3.4; plan §3.06 |

---

## 6.5 Anular y reinscribirse

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-39 | `DELETE /mis-inscripciones/{id}` | `inscripcion.anular` |
| CU-40 | `POST /inscripciones` (reutiliza el alta de 6.3) | `inscripcion.crear` |

**CU-39 — Anular la propia inscripción · `DELETE /mis-inscripciones/{id}`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno, sobre su **propia** inscripción (`inscripcion.anular` — Alumno **S**) | doc 02 §2.4; doc 04 INS-02 |
| Gatillo | E-02 · el alumno toca "anular" por error de elección | doc 03 §3.1 |
| Precondiciones | Fila propia en `inscripto`; **sólo dentro de la ventana** de la convocatoria (RB-08b, RB-07), inclusive hasta las 23:59:59 (RB-23); la anulación conserva la fila y la saca del índice único, de modo que libera la materia (§3.19) | `analisis.txt` §4, §3.19; doc 04 INS-02 |
| Flujo principal | 1) `DELETE /mis-inscripciones/{id}`; 2) la fila pasa a `anulado` y queda para auditoría; 3) el resto de las inscripciones del alumno se mantiene intacto | `analisis.txt` §6, §3.19; RB-08b |
| Resultado | INS-02 · estado `anulado`; la materia queda libre para reinscribirse dentro de la ventana (RB-08c → CU-40). P-02 del plan queda respondida: sí se puede anular la propia inscripción, sólo durante la ventana (RB-08b, RB-07) | doc 04 §4.3; plan §6 |
| Permisos | `inscripcion.anular` — Alumno **S**, Secretario/a **S**, Administrador **S**, Superadmin **S**, Director **—**; la anulación desde SIGME no tiene endpoint declarado y sigue en doc 05 §5.8 | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **Flujos alternativos:** fuera de la ventana → rechazo; sólo consulta (RB-07, RB-08b, doc 03 §3.4). Sólo alcanza a la fila propia: INS-02 es del alumno sobre su inscripción — revocar la de otro alumno es gestión de SIGME (doc 04 INS-03). **Reintento (E-13):** un `DELETE` repetido tras timeout no cambia la fila, que ya está `anulado`; responde **204 No Content** igual que la primera llamada (idempotente, sin cuerpo) — **CERRADO (PD-25)** (ver 6.6 y doc 07) | `analisis.txt` §4, §6; doc 03 §3.3, §3.4; doc 04 INS-02, INS-03 |

**CU-40 — Reinscribirse después de anular · `POST /inscripciones`**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno (`inscripcion.crear` — Alumno **S**) | doc 02 §2.4; doc 04 INS-04 |
| Gatillo | S-05 · se anota a la mesa correcta después de anular | doc 03 §3.3 |
| Precondiciones | Sólo dentro de la ventana (RB-08b); la unicidad no choca porque la fila `anulado` queda fuera de `uq_inscripcion_unica` (§3.19, RB-08); el límite de la condición se respeta (RB-08c, RB-03 — valores **[CERRADO — 2026-10-06]**, PD-02: Previa hasta 3, Regular hasta 8, Libre sin límite, unidad por convocatoria); la mesa destino debe existir (RB-31) | `analisis.txt` §4, §3.19; doc 04 INS-04 |
| Flujo principal | 1) `POST /inscripciones`, el mismo alta que CU-37; 2) evaluación de ventana, unicidad y límite; 3) creación de una fila **nueva** — la anulada no se reutiliza | `analisis.txt` §6; doc 04 INS-04 |
| Resultado | INS-04 · fila nueva en `inscripto`; la fila `anulado` queda como registro de la corrección | doc 04 §4.3 |
| Permisos | `inscripcion.crear` — Alumno **S**; reparto definitivo en la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**, PD-03) | `analisis.txt` §2.7; doc 02 §2.4 |
| Excepciones y pendientes | **Flujos alternativos:** límite de la condición alcanzado → rechazo de la reinscripción (RB-08c, RB-03, S-05) · si la combinación elegida no tiene mesa → el mismo rechazo sin código de CU-37 (**PD-19**). Sin otros alternativos declarados: es el mismo alta que CU-37 con la unicidad ya liberada por la anulación | `analisis.txt` §4, §7; doc 03 §3.3, §3.4; doc 04 INS-04 |

---

## 6.6 Operación degradada e idempotencia

El plan §3.06 pide contratos concretos para que el cliente opere degradado:
idempotencia, reintentos, paginación y respuestas offline-friendly. RB-26 ya
resolvió la pregunta P-07 (plan §6): lectura con caché sin red ni token,
escritura siempre online y ninguna cola offline. Estas son las dos tablas que
cierran ese criterio.

| Contrato | Qué exige | Fuente |
|---|---|---|
| **Lectura con caché** | La última respuesta de `GET /convocatoria-vigente`, `GET /mesas-disponibles` y `GET /mis-inscripciones` se guarda localmente y se muestra con su "última actualización". **No requiere red ni token**: sirve con el teléfono sin datos y con la sesión vencida; la respuesta del backend debe ser autosuficiente para mostrarse desactualizada | RB-26; doc 02 §2.1.2 |
| **Escritura online** | Inscribir (CU-37, CU-40) y anular (CU-39) exigen conexión y sesión válida; el backend exige autenticación y sesión activa en toda escritura | RB-26; doc 02 §2.1.2 |
| **Sin cola offline** | No existe ninguna cola de acciones offline: RB-17, RB-23, RB-08, RB-08c y RB-22 se romperían al sincronizar tarde — ventana cerrada, límite de horas, duplicado, límite de la condición o mesa inexistente | RB-26 |
| **Reloj autoritativo** | La ventana se evalúa con el reloj del **backend** por fecha de calendario en `America/Argentina/Buenos_Aires`; nunca con un timestamp del reloj del dispositivo, por desfasado que esté | RB-23; doc 02 §2.1.2 |
| **401 en la acción** | Access token vencido mientras el alumno navega → 401 en la escritura; la lectura en caché del cliente sigue funcionando sin llamar al backend | `analisis.txt` §2.1; doc 02 §2.1.2 |
| **Paginación** | El plan §3.06 la pide para operar degradado y §6 **no declara** parámetros de paginación en ninguna ruta del alumno — **PENDIENTE (PD-28)**, ver 6.8 | plan §3.06; `analisis.txt` §6 |

**Semántica de idempotencia por operación** — criterio de cierre del plan
§3.06: cada operación que el cliente reintenta (E-13) declara qué pasa si se
repite:

| Operación | Semántica de reintento (E-13) | Fuente |
|---|---|---|
| `POST /auth/login` | No idempotente pero inocuo para los datos de negocio: cada intento crea su propia fila de sesión (SES-01, y SES-05 en un login nuevo) o suma al rate limit; 5 fallos en 15 minutos → `429` + `Retry-After` y bloqueo de 15 minutos (**PD-27**, cerrado) | `analisis.txt` §2.4, §6; doc 03 E-14; doc 04 SES-01, SES-05 |
| `POST /auth/refresh` | **No idempotente**: la rotación revoca el refresh anterior; un reintento con la respuesta perdida dispara la reuse detection, revoca toda la familia y exige login nuevo (401 declarado en T-07) | `analisis.txt` §2.2; doc 03 S-14, T-07; doc 04 SES-04 |
| `GET /convocatoria-vigente`, `GET /mesas-disponibles`, `GET /mis-inscripciones` | Idempotentes: reintento seguro, misma respuesta. Si no hay red, el cliente muestra la caché sin llamar al backend | RB-26; doc 03 §3.4 |
| `POST /inscripciones` | Reintento seguro **sin duplicar**: si la fila ya existe, `uq_inscripcion_unica` responde 409 y no se crea otra — misma respuesta aplicable, sin duplicar | RB-08, S-06, §6; doc 03 §3.4 |
| `DELETE /mis-inscripciones/{id}` | El **efecto** de un reintento es nulo: la fila ya está `anulado` y vuelve a quedar `anulado` (INS-02); la respuesta repetida devuelve **204 No Content**, igual que la primera (idempotente, sin cuerpo) — **CERRADO (PD-25)** | RB-08b; doc 04 INS-02; `analisis.txt` §6 |

**CU-41 — Consultar sin conexión (caché local) · el backend no es llamado**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno con el teléfono sin datos o con la sesión vencida | doc 02 §2.1.2; RB-26 |
| Gatillo | E-03 · consulta sin red o con sesión vencida | doc 03 §3.1, §3.4 |
| Precondiciones | El cliente conserva la última respuesta de una de las tres lecturas (convocatoria vigente, mesas disponibles o mis inscripciones); **no se exige red ni token** | RB-26; doc 02 §2.1.2 |
| Flujo principal | 1) el alumno abre la pantalla; 2) el cliente sirve la última respuesta guardada con su fecha de "última actualización"; 3) no hay llamada al backend | RB-26; doc 03 §3.4 |
| Resultado | La lectura sigue funcionando con el teléfono sin datos y con la sesión vencida; la pantalla queda marcada como desactualizada hasta la próxima sincronización con red | RB-26; doc 02 §2.1.2 |
| Permisos | No aplica: no hay request que autorizar — sólo las escrituras de 6.3 y 6.5 pasan por `require_permiso()` | `analisis.txt` §2.7; RB-26 |
| Excepciones y pendientes | **Flujos alternativos:** con red, la próxima sincronización reemplaza la caché con la respuesta vigente. **Sin cola offline:** ninguna acción queda encolada — inscribir o anular sin conexión falla en el cliente y debe reintentarse online (RB-26); la caché **nunca** sirve para decidir ventana, unicidad ni límite de condición (RB-23, RB-08, RB-03) | RB-26; doc 02 §2.1.2 |

---

## 6.7 Notificaciones push

| CU | Operación (§6) | Permiso |
|---|---|---|
| CU-42 | `POST /dispositivos` y `DELETE /dispositivos/{id}` (token propio); envío por evento de usuario | No aplica (notificación) — alta y baja sólo del dispositivo propio del alumno, sin permiso nuevo (**PD-26**, cerrado) |

**CU-42 — Recibir notificaciones push · registro de token y envío por evento**

| Campo | Contenido | Fuente |
|---|---|---|
| Actor | Alumno con el dispositivo registrado, junto con el servicio push (sistema externo) | doc 01 §1.4; RB-24 |
| Gatillo | S-20 · evento de usuario — apertura o cierre de las inscripciones; nunca un cron: todos los envíos nacen de una acción de usuario y no hay ningún job programado en v1 | doc 03 §3.3; RB-24, RB-25 |
| Precondiciones | Tabla `us_dispositivo` con el token push por usuario, con refresco y purga de caducos (infraestructura que RB-24 arrastra); el alta y la baja del token se declaran en §6 (`POST /dispositivos`, `DELETE /dispositivos/{id}`, sólo el dispositivo propio — **PD-26** cerrado). El conjunto de eventos push está cerrado por RB-24: apertura y cierre de ventanas (PD-07, cerrado) | `analisis.txt` §4, §6, §7; RB-24 |
| Flujo principal | 1) al producirse la apertura o el cierre de las inscripciones, el backend encola la notificación push (S-20); 2) el servicio push la entrega a los dispositivos registrados; 3) el alumno, al ver el aviso, consulta la convocatoria (CU-34) o se inscribe (CU-37) | doc 03 §3.3; RB-24; `analisis.txt` §4 |
| Resultado | El alumno entera de la apertura o el cierre sin entrar a la app. La confirmación de su inscripción con fecha/hora **no** va por push: es un **email** con cola obligatoria (RB-24, RB-25), igual que el aviso de retiro de permisos de examen | RB-24, RB-25 |
| Permisos | No aplica: el alta y la baja sólo alcanzan al dispositivo propio del alumno autenticado — no se introduce permiso nuevo (PD-26, cerrado), así que el asunto no entra en PD-03 | `analisis.txt` §2.7, §6; PD-03 |
| Excepciones y pendientes | **Flujos alternativos:** token caducado → la infraestructura de `us_dispositivo` refresca los tokens y depura los caducos (RB-24). **PD-11 / T-10** — el recordatorio 48 h antes de la mesa está **deferido a v2**: exige un job programado que en v1 no existe. **PD-10** — el conjunto exacto de notificaciones in-app por rol (la campanita de SIGME) sigue abierto e iterativo; al alumno sólo le incumbe el push de RB-24. **PD-07** está **cerrado**: las push existen y sólo se disparan por eventos de usuario | `analisis.txt` §4, §7; doc 03 §3.2, §3.3; RB-24, PD-07, PD-10, PD-11 |

---

## 6.8 Consolidado de pendientes

Las filas siguientes se heredan de `analisis.txt` §7 y de doc 01 §1.5.2. Las
marcadas **[CERRADO — 2026-10-06]** (o **[RESUELTA]** para G-05) ya tienen
decisión escrita en la fuente y se conservan aquí —sin renumerar el ID— para
que los documentos 07, 08, 09 y 10 las hereden trazadas; el resto sigue siendo
**pregunta abierta** y ninguna se resuelve en este documento. No se inventan
endpoints ni códigos para ellas: cada fila queda referenciada a la fuente que
la marca.

| ID | Pregunta abierta | Dónde toca en este documento | Fuente |
|---|---|---|---|
| **PD-02** | **[CERRADO — 2026-10-06]** Valores de `es_condicion.limite_materias`: Previa hasta 3, Regular hasta 8, Libre sin límite (NULL); unidad de conteo **por convocatoria** (multi-día y multi-grupo). Se valida **sólo** al inscribirse (RB-03); editables desde SIGME (`PATCH /condiciones`) | CU-37, CU-40 | `analisis.txt` §7; RB-03 |
| **PD-03** | **[CERRADO — 2026-10-06]** Semilla inicial de roles, permisos y usuarios, incluido el reparto exacto rol × permiso y el mapeo endpoint → permiso — migración inicial de Alembic, primer superadmin por variable de entorno, reparto desde la matriz de doc 02 §2.4 | Filas de permisos de 6.1–6.5; CU-34, CU-37, CU-40, CU-42 | `analisis.txt` §7; doc 02 §2.4 |
| **PD-10** | Conjunto exacto de notificaciones in-app por rol; RB-24 sólo fija el canal | CU-42 (la campanita es de SIGME; al alumno le incumbe el push) | `analisis.txt` §7; RB-24 |
| **PD-11** | Recordatorio 48 h antes de la mesa: deferido a v2, exige un job programado que en v1 no existe | CU-42 (T-10 fuera de alcance de v1) | `analisis.txt` §7; RB-24 |
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? ¿qué efecto tiene sobre alumnos ya inscriptos? | CU-35, CU-38 — la fecha y la hora que el alumno ve cambian sin intervención suya | `analisis.txt` §7; doc 05 §5.6 |
| **PD-15** | ¿De dónde sale el conjunto esperado de pares materia × condición, si la convocatoria no tiene FK al catálogo? Comparte contrato con `POST /inscripciones` | CU-37 | `analisis.txt` §7; RB-31; doc 05 §5.7 |
| **PD-17** | ¿Cómo se interpreta `grupo.hora` (`time` sin zona) al combinarse con `fecha` frente a RB-23? | CU-35, CU-38 — ambas muestran la hora al alumno | `analisis.txt` §7 |
| **PD-19** | ¿Qué código HTTP devuelve el rechazo de `POST /inscripciones` cuando la combinación no tiene mesa? | CU-37, CU-40 | `analisis.txt` §7; RB-31 |
| **PD-23** | Alcance de RB-22 sobre `GET /mesas-disponibles`: la regla dice "todo listado" pero su cláusula operativa describe mesas que quedaron con 0 alumnos (S-03); si el filtro alcanzara a las mesas recién creadas, ninguna inscripción podría iniciarse en ellas | CU-35 | `analisis.txt` §7; doc 03 §3.4; RB-28, RB-31 |
| **PD-28** | Paginación de `GET /mis-inscripciones` y de las demás rutas: el plan §3.06 la pide para operar degradado y §6 no declara parámetros | CU-38, 6.6 | `analisis.txt` §7; plan §3.06 |
| **G-01** | ¿Qué significa **"matrícula"** para el cliente? La palabra no existe en `analisis.txt`; ningún caso de uso la usa | Vocabulario de 6.1–6.7 (palabra no empleada) | doc 01 §1.5.2, §1.3 |
| **G-02** | ¿Qué rol usa el permiso `preinscripcion.crear`? La landing es anónima y no pasa por RBAC | No toca este documento: la landing es el doc 11 — se lista por herencia del catálogo G | doc 01 §1.5.2; doc 02 §2.4 |
| **G-03** | ¿Existe el rol **"docente"**? Aparece como comentario de ejemplo en el DDL de `us_rol`, pero P-08 no lo incluye | No toca este documento: el docente no opera SIGME-M — herencia de doc 01 §1.5.2 | doc 01 §1.5.2; `analisis.txt` §3.6 |
| **G-04** | ¿Cómo obtiene SIGME-M las opciones de orientación → curso → materia → condición? | CU-36 — pregunta con destino a este documento; aquí sigue **PENDIENTE** | doc 01 §1.5.2; `analisis.txt` §6 |
| **G-05** | **[RESUELTA — 2026-10-06]** ¿Quién y cómo cambia el estado de la convocatoria y de la mesa? — nadie: el disparador es el calendario y la constatación se calcula al leer | CU-34 — el alumno sólo lee el estado derivado (C-02, C-04) | doc 01 §1.5.2; doc 04 §4.6.2 |

---

## Checklist de cierre (6 · Casos de uso SIGME-M)

- [x] **12 casos de uso con ID estable** (`CU-31`…`CU-42`), agrupados en siete
      dominios que reproducen el plan §3.06 — sesión, consulta, inscripción,
      mis inscripciones, anulación y operación degradada — más notificaciones
      push (RB-24, PD-07), consolidados los pendientes en 6.8.
- [x] **Cada CU declara** actor, gatillo, precondiciones, flujo principal,
      resultado, permisos y fuentes (`RB-xx`, `PD-xx`, `E-xx`, `S-xx`,
      `T-xx`, `G-xx`, `§6`), con flujos alternativos explícitos o la nota de
      "sin alternativos declarados".
- [x] **Todo endpoint citado existe en `analisis.txt` §6**: las tres rutas de
      sesión (`/auth/login`, `/auth/refresh`, `/auth/logout`,
      `/auth/logout-all`, más `GET /auth/yo`) y las cinco del alumno
      (`/convocatoria-vigente`, `/mesas-disponibles`, `/inscripciones`,
      `GET /mis-inscripciones`, `DELETE /mis-inscripciones/{id}`); las
      operaciones sin contrato —la cascada (CU-36, **G-04**)— están marcadas
      **PENDIENTE** con su ID, sin inventar rutas ni códigos; el alta y la
      baja de push ya están declaradas en §6 (PD-26).
- [x] **Ciclo completo del alumno cubierto (plan §3.06):** login → consultar
      convocatoria y mesas → inscribir → ver mis inscripciones → anular →
      reinscribir → operar degradado → recibir push.
- [x] **Semántica de idempotencia declarada por cada operación que el cliente
      reintenta (plan §3.06):** la tabla de 6.6 cubre login, refresh, las
      tres lecturas, `POST /inscripciones` y `DELETE /mis-inscripciones/{id}`
      — con la respuesta repetida del `DELETE` declarada en §6 con `204 No Content` (PD-25) en lugar de suponerse.
- [x] **RB-26 aplicado de punta a punta:** lectura con caché sin red ni token
      (CU-41), escritura siempre online (CU-37, CU-39, CU-40), ninguna cola
      offline y reloj del backend (RB-23) por encima del reloj del
      dispositivo.
- [x] **Permisos idénticos a doc 02 §2.4:** `mesa.listar`,
      `inscripcion.listar`, `inscripcion.crear` y `inscripcion.anular` con
      Alumno **S**; el mapeo de `GET /convocatoria-vigente` sigue sin código
      en §2.7 (hueco de la matriz de doc 02 §2.4, con **PD-03** cerrado el
      2026-10-06) y la cascada queda en **G-04**; el reparto completo sale
      de esa matriz ya definitiva.
- [x] **Cero vocabulario retirado**: ninguna de las expresiones que doc 01
      §1.3 marca como prohibidas o retiradas por el modelo de grupos aparece
      en este documento; verificación por búsqueda de patrón sobre el archivo
      final → **0 coincidencias**.
- [x] **Preguntas conservadas con su estado**: PD-02 y PD-03 figuran en 6.8
      marcados **[CERRADO — 2026-10-06]** y G-05 como **[RESUELTA —
      2026-10-06]**; PD-10, PD-11, PD-12, PD-15, PD-17, PD-19, PD-23, PD-28 y
      G-01…G-04 siguen como preguntas abiertas; ninguna se completa por
      suposición.
- [x] **Toda cita externa resuelve**: `RB-xx`/`PD-xx`/`§n` en `analisis.txt`;
      `E-xx`/`S-xx`/`T-xx` en doc 03; `G-xx` en doc 01 §1.5.2;
      `C-xx`/`INS-xx`/`US-xx`/`SES-xx` en doc 04; `CU-31`…`CU-42`
      definidos en este documento.
- [ ] **Las excepciones sin código HTTP concreto no se cierran acá**: los
      códigos de error y los estados críticos pertenecen al **doc 07** por
      decisión de alcance — este documento sólo referencia los que las
      fuentes ya declaran (401 en T-07, 409 en §6 para duplicado y ventana
      cerrada, `429` + bloqueo de 15 minutos en §6/PD-27) y deja **PD-19** abierto para el
      rechazo sin mesa. Las filas de excepción/pendiente sí existen en los
      12 CU.

## Siguiente paso

`07-estados-criticos-y-excepciones.md`: el catálogo de estados críticos con
escenarios Given/When/Then — hereda de este documento el rate limit de login
(E-14, US-02, US-03), la reuse detection del refresh (S-14), el reintento de
`POST /inscripciones` (E-13, 409), la ventana evaluada por el reloj del
backend (RB-23) frente al reloj del dispositivo, la operación sin cola offline
(RB-26) y el código todavía abierto (**PD-19**, el rechazo sin mesa).
