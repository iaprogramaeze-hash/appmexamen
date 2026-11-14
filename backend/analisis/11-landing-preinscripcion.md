# 11 · Landing — contrato de preinscripción — Backend EPET36 [PROVISIONAL]

Este documento entrega el contrato completo del
`POST /api/v1/landing/preinscripcion` para que el equipo de la landing pueda
implementar el formulario sin esperar el resto del análisis. Fija payload,
reglas, códigos de respuesta, ventana de preinscripción, condiciones del
endpoint anónimo y trazabilidad.

**Estado: `[PROVISIONAL]`** — el **payload real** que envía la landing quedó
**aprobado el 2026-10-04**; siguen abiertos los puntos (b), (c) y (d) del
recuadro "Alcance de lo PROVISIONAL" (más abajo), que se cierran en la
verificación conjunta con el usuario (plan §3, 11).

Toda afirmación cita su fuente: `RB-xx` / `PD-xx` / `O-x` / `P-xx` remiten a
`analisis.txt` (§4, §7, §3.20 y, para P-xx, plan §6); `§n.m` remite a la
sección de ese archivo; `plan §n` remite a `00-plan-de-analisis.md`; `01 §n.n`
remite al glosario. Lo que ninguna fuente resuelve se marca **PENDIENTE**,
nunca se completa por suposición. Las marcas **(D)** indican un detalle
**derivado** de la fuente indicada (no escrito literalmente allí) y por eso
también entran en lo PROVISIONAL. Este documento **no crea reglas RB nuevas**:
todo se resuelve con RB existentes.

## Rápido recorrido

1. **11.3** — la tabla del payload: son los 6 campos; es lo primero que la
   landing necesita.
2. **11.4** — contrato HTTP copy-paste: request y las 5 respuestas con su
   cuerpo exacto.
3. **11.5** — `pr_ventana` y `vw_ventana_vigente`: cuándo responde 409.
4. **11.6** — anonimato, rate limit, CORS y trazabilidad (IP, user agent, UTM).
5. Al final: **PENDIENTE consolidados**, **checklist** y **siguiente paso**.

---

## Alcance de lo PROVISIONAL

| | |
|---|---|
| **Qué es provisional** | (a) ~~la lista exacta de campos del payload y sus límites/validaciones~~ **[RESUELTO — 2026-10-04]**: el payload real quedó verificado y coincide con 11.3; (b) las formas derivadas: item de `errors[]`, cuerpo del `429`, orden `422` vs `409`; (c) los números de rate limit y de tamaño de body; (d) el mecanismo de captura de UTM — **(b), (c) y (d) siguen PROVISIONALES**. |
| **Qué lo resuelve** | (a): **ya resuelto el 2026-10-04**, con los datos reales que la landing envía (plan §3, 11 — "Estado actual"). (b), (c) y (d): la verificación conjunta pendiente con el usuario. |
| **Qué NO cambia aunque cambie el payload** | La semántica de las respuestas `201`/`200`/`409`/`422`/`429` (RB-13, RB-14, §6); el anonimato del endpoint (§2.9); el aislamiento sin FK (§3.20); el consentimiento fuera del sistema (O-1); la ventana de preinscripción única (§3.21); la trazabilidad IP / user agent / UTM (§3.20). |
| **Qué SÍ cambiaría si el payload difiere** | La tabla de 11.3, los ejemplos y las reglas de validación de 11.4, las columnas "CLIENTE" de `pr_preinscripcion` (§3.20 → migración Alembic), el estado de **PD-01** (se reabriría) y **P-09** (plan §6). Si el campo `documento` dejara de existir o cambiara de significado, cambiaría además la **identidad del upsert `(anio_lectivo, documento)`** y por lo tanto la redacción de RB-13. |

---

## 11.1 Qué es la preinscripción

**Respuesta corta:** la **preinscripción** es la solicitud de ingreso a la
escuela para el **próximo año lectivo** (01 §1.2.2). Es ajena a las mesas de
exámenes: no tiene ninguna conexión con ellas ni con el resto del sistema; usa
la misma base de datos sólo por practicidad y para agilizar una futura
migración de datos (`analisis.txt` §3.20).

| Aspecto | Definición | Fuente |
|---|---|---|
| Quién escribe | La landing, de forma **anónima**: cualquiera completa el formulario, sin roles. **Sólo escribe**; no existe endpoint de lectura público. | RB-10; §2.9; §3.20 |
| Quién consulta / gestiona | SIGME (authenticated): consulta con permiso `preinscripcion.listar` (`GET\|PATCH /preinscripciones`, §6 — **PD-22 abierto**: el efecto del `PATCH` no está definido) y gestiona la ventana de preinscripción con `/ventanas-preinscripcion`. | §2.7; §6; §3.21 |
| Entidad | `pr_preinscripcion` | §3.20 |
| Identidad del registro | `(anio_lectivo, documento)`: el mismo documento en un año distinto es **otra** preinscripción. | §3.20 (`uq_preinscripcion_unica`) |
| Estados | `pendiente` → `convertido` / `descartado`. Nace en `pendiente`. | §3.20 (CHECK) |
| Qué **no** es | No es una inscripción a mesas de exámenes (en este sistema "inscribirse" es anotarse a una mesa). No es matrícula: la palabra no existe en `analisis.txt` (01 §1.3). | 01 §1.2.2, §1.3 |

---

## 11.2 Aislamiento

**Respuesta corta:** `pr_preinscripcion` y `pr_ventana` **no tienen foreign
keys hacia `pe_*` ni `es_*`**. Es una decisión explícita del usuario, no un
descuido (`analisis.txt` §3.20; plan §3, 11.2; `odd/tasks`).

| Decisión | Consecuencia en el contrato | Fuente |
|---|---|---|
| Sin FK hacia `pe_*` ni `es_*` | `orientacion` se guarda como **texto**, no como referencia a `es_orientacion`. | §3.20 |
| Sin tipo de documento | `documento` es un `varchar(20)` suelto: **se asume DNI**, no se envía tipo. | §3.20 (comentario de la columna) |
| Misma base de datos por practicidad | Sólo convivencia física de tablas; ninguna integridad referencial entre `pr_*` y el cuerpo del sistema. | §3.20 |
| Migración futura | La misma base existe para agilizar una migración de datos hacia `pe_persona` (ver 11.7). | §3.20; plan §3 (11.7) |

> **Este documento NO propone ninguna foreign key hacia `pe_*` ni `es_*`.**
> Toda referencia entre preinscripción y el resto del sistema es, hoy y por
> decisión, inexistente.

---

## 11.3 Payload del `POST /api/v1/landing/preinscripcion`

**Respuesta corta:** el body es **JSON** con **exactamente 6 campos**, todos
**obligatorios (`NOT NULL`)**. Confirmados por el usuario: PD-01 cerrado,
P-09 resuelta, O-2 resuelta (`analisis.txt` §3.20 y §7; plan §6).

| # | Campo | Tipo y límite | Validación de contenido | Fuente |
|---|---|---|---|---|
| 1 | `nombre_alumno` | string, `varchar(150)` | No vacío tras recorte **(D)** | §3.20 |
| 2 | `documento` | string, `varchar(20)` | Hasta 20 caracteres. Formato exacto (¿sólo dígitos?) → **PENDIENTE** | §3.20 |
| 3 | `fecha_nacimiento` | string, fecha ISO 8601 `YYYY-MM-DD` **(D)**, columna `date` | Fecha válida **(D)**; ¿prohíbe fecha futura? → **PENDIENTE** | §3.20 |
| 4 | `orientacion` | string, `varchar(150)` | Texto libre, **sin catálogo ni FK**. ¿Debe coincidir con `es_orientacion.descripcion`? → **PENDIENTE** | §3.20 |
| 5 | `nombre_tutor` | string, `varchar(150)` | No vacío **(D)**. **Obligatorio siempre**, con independencia de la edad del postulante | §3.20; O-2 |
| 6 | `email` | string, `varchar(150)` | Formato de email válido **(D)**, Pydantic v2 (§0) | §3.20; §0 |

**Reglas del payload:**

- **Los 6 son obligatorios**, incluido `nombre_tutor` (O-2; §3.20): faltante o
  `null` → `422`.
- **No se envía `anio_lectivo`**: lo deriva el backend de la única ventana de
  preinscripción vigente (O-3; §3.20, §3.21).
- **No hay campo de consentimiento** (ver más abajo).
- Los campos del lado servidor — `ip`, `user_agent`, `utm_*`, `estado`,
  `created_at`, `updated_at` — **no vienen en el body** (§3.20, secciones
  CLIENTE / SERVIDOR).
- Tratamiento de campos **extra** en el body (¿ignorar vs `422`?) →
  **PENDIENTE**; el contrato sólo define los 6.

**Ejemplo de request (copy-paste):**

```http
POST /api/v1/landing/preinscripcion HTTP/1.1
Host: TU-DOMINIO-BACKEND
Content-Type: application/json; charset=utf-8
Origin: https://TU-ORIGEN-DE-LA-LANDING

{
  "nombre_alumno": "María Belén Rodríguez",
  "documento": "41234567",
  "fecha_nacimiento": "2012-04-18",
  "orientacion": "Tecnicatura en Gestión y Administración de las Organizaciones",
  "nombre_tutor": "Carlos Rodríguez",
  "email": "carlos.rodriguez@example.com"
}
```

> `Host` y `Origin` son de ejemplo: el dominio real del backend y el origen
> exacto de la landing son configuración (**PENDIENTE**, ver 11.6).

### Consentimiento (Ley 25.326) — fuera del sistema

- **Art. 5 (consentimiento):** proceso **físico externo posterior**, en
  formulario en papel. **No existe columna `consentimiento` ni
  `consentimiento_en`**; el contrato no tiene ningún campo de consentimiento
  (O-1; §3.20).
- **Art. 6 (aviso previo):** requisito **heredado a la landing** (para el
  proyecto futuro de landing, no para el backend) (O-1; plan §3, 11.3).
- Nota sobre §2.9: esa sección pedía un "checkbox de consentimiento" y
  "guardar fecha de otorgamiento e IP". O-1 (§3.20) cerró que **no hay columna
  de consentimiento** en el backend; lo que queda aquí es la **IP de
  trazabilidad** (11.6), no una fecha de otorgamiento. La existencia de un
  checkbox en el formulario es asunto de la landing, fuera del alcance de este
  contrato.
- Art. 9, 14 y 16 (seguridad, acceso, rectificación) son del backend y se
  documentan en el doc 09 (§3.20).

---

## 11.4 Reglas y respuestas — contrato HTTP

### 11.4.1 Reglas que gobiernan el POST

| Regla | Enunciado | Fuente |
|---|---|---|
| Upsert, nunca duplicado | Repetir el formulario **no es error**: identidad `(anio_lectivo, documento)` inexistente → INSERT con `201`; existente → UPDATE de los campos mutables con `200`. **Nunca `409` por documento repetido.** | RB-13; O-4; §6 |
| Campos mutables | Se sobrescriben en cada reenvío: `nombre_alumno`, `fecha_nacimiento`, `orientacion`, `nombre_tutor`, `email`. | O-4; §3.20 |
| Campos identitarios | **No cambian**: `anio_lectivo`, `documento`. | O-4; §3.20 |
| Auditoría en reenvío | `created_at` se conserva; `updated_at` se refresca (trigger, §1.6). `estado` **no** está en la lista de mutables: un reenvío no lo altera. | O-4; §3.20; §1.6 |
| Ventana de preinscripción única | Sólo se acepta dentro de la **ventana de preinscripción** vigente; fuera → `409 ventana-cerrada`. | RB-14; §3.21 |
| Límite inclusivo | La ventana de preinscripción se respeta **hasta las 23:59:59** de `fecha_hasta` inclusive; a las 00:00:00 del día siguiente ya está cerrada. Se compara por fecha de calendario en `America/Argentina/Buenos_Aires`, con el reloj del backend — nunca con el reloj del cliente. Vale igual para `fecha_desde`. | RB-23; §4 (RB-23 menciona `pr_ventana` explícitamente) |
| Validación previa | El resumen y la doble confirmación de los datos **antes** de enviar los hace la landing, no el backend. | RB-13; §3.20 (O-4) |
| Idempotencia | El upsert vuelve seguro el reintento de red: reenviar los mismos datos produce `200`, nunca un error ni un duplicado (01 §1.2.4). | RB-13 |
| Concurrencia | Dos envíos simultáneos con el mismo documento no deben producir un `500`: el índice `uq_preinscripcion_unica` garantiza una sola fila (§3.20). El tratamiento exacto es detalle de implementación (plan §3, 7.4). | §3.20; RB-13 |

### 11.4.2 Los 5 códigos de respuesta

| Código | Cuándo dispara | Cuerpo | Fuente |
|---|---|---|---|
| `201 Created` | Primera vez que se recibe ese `(anio_lectivo, documento)` dentro de la ventana de preinscripción → INSERT | `{ "accion": "creada" }` | §6; RB-13 |
| `200 OK` | La identidad ya existía → UPDATE de los campos mutables (reenvío) | `{ "accion": "actualizada" }` | §6; RB-13 |
| `409 Conflict` | **Sólo** por ventana de preinscripción cerrada: no hay fila en `vw_ventana_vigente` | `{ "code": "ventana-cerrada" }` | §6; RB-14 |
| `422 Unprocessable Entity` | Payload inválido: falta un campo, `null`, largo excedido o formato inválido | `{ "code": "validacion", "errors": [ … ] }` | §6 |
| `429 Too Many Requests` | Rate limit estricto anti-bots (§2.9) | `{ "code": "rate-limit" }` **(D) — PROVISIONAL** | §6 (el `429` está listado sin cuerpo); §2.9 |

> **Regla de oro:** el `409` de este endpoint significa **ventana de
> preinscripción cerrada** y
> nada más. Un documento repetido jamás devuelve `409` (RB-13, §6).

### 11.4.3 Respuestas — copy-paste

**201 — creada:**

```http
HTTP/1.1 201 Created
Content-Type: application/json; charset=utf-8

{
  "accion": "creada"
}
```

**200 — actualizada (reenvío dentro de la ventana de preinscripción):**

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{
  "accion": "actualizada"
}
```

**409 — ventana de preinscripción cerrada (no hay ventana vigente):**

```http
HTTP/1.1 409 Conflict
Content-Type: application/json; charset=utf-8

{
  "code": "ventana-cerrada"
}
```

**422 — validación (falta `nombre_tutor`, por ejemplo):**

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json; charset=utf-8

{
  "code": "validacion",
  "errors": [
    { "campo": "nombre_tutor", "mensaje": "campo obligatorio" },
    { "campo": "email", "mensaje": "formato de email inválido" }
  ]
}
```

> §6 sólo fija `errors[]`, sin definir el item. La forma
> `{ "campo", "mensaje" }` es **(D) derivada** y queda **PROVISIONAL**.

**429 — rate limit:**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json; charset=utf-8
Retry-After: 60

{
  "code": "rate-limit"
}
```

> Cuerpo y cabecera `Retry-After` son **(D) derivados** del patrón `code` de
> §6: **PROVISIONAL**. El umbral numérico del rate limit está **PENDIENTE**
> (11.6).

### 11.4.4 Orden de evaluación

Propuesta **(D) — PROVISIONAL** (el orden no está fijado por ninguna fuente):

1. CORS (middleware, previo al handler) → 11.6
2. Rate limit → `429`
3. Tamaño máximo del body → **PENDIENTE** (el código de respuesta para body
   excedido no está definido; las 5 respuestas del contrato no lo contemplan)
4. Validación de esquema → `422`
5. Ventana de preinscripción vigente → `409`
6. Upsert → `201` / `200`

La precedencia **`422` vs `409`** (¿payload inválido y ventana de
preinscripción cerrada a la vez?) queda **PENDIENTE** de confirmación.

### 11.4.5 Acuse por email (consecuencia posible, no parte del contrato)

RB-24 incluye el **acuse de preinscripción** entre los emails, sólo por
eventos de usuario, y RB-25 declara la cola de email **obligatoria desde v1**.
Si el acuse se envía al recibir este POST es **PENDIENTE**: ninguna fuente fija
el instante de disparo. El backend no debe bloquear la respuesta `201`/`200`
por el envío de email (la cola es asíncrona, RB-25). **(D)**

---

## 11.5 `pr_ventana` y `vw_ventana_vigente`

**Respuesta corta:** una sola **ventana de preinscripción** vigente a la vez;
fuera de ella el POST responde `409 ventana-cerrada` (RB-14; §3.21). Motivo
del usuario: "para que no estén jugando con el formulario todo el año"
(§3.21).

| Pieza | Definición | Fuente |
|---|---|---|
| `pr_ventana` | `anio_lectivo`, `descripcion`, `fecha_desde` / `fecha_hasta` (ambas **inclusivas**), `activa`. Check `ck_ventana`: `fecha_desde <= fecha_hasta`. `uq_ventana_anio`: un registro por año lectivo. | §3.21 |
| `vw_ventana_vigente` | `activa AND deleted_at IS NULL AND current_date BETWEEN fecha_desde AND fecha_hasta`. | §3.21 |
| Uso en el POST | Si `vw_ventana_vigente` devuelve fila → el backend toma `anio_lectivo` de ahí y procesa; si no devuelve fila → `409 { "code": "ventana-cerrada" }`. | RB-14; §3.20 (O-3); §6 |
| Reloj | `current_date` en la timezone del backend (`America/Argentina/Buenos_Aires`); inclusivo hasta 23:59:59. | RB-23 |
| Quién gestiona la ventana de preinscripción | Desde SIGME (Administrador/Superadmin), **nunca** desde la landing: `GET\|POST /ventanas-preinscripcion` (E-05 en `03`). | §3.21; §6 |

**PENDIENTE:** `uq_ventana_anio` sólo impide dos filas para el **mismo** año;
el DDL **no impide el solape de fechas entre ventanas de años distintos**. Si
dos ventanas se solaparan, `vw_ventana_vigente` devolvería dos filas y el
`anio_lectivo` sería ambiguo. La regla "sólo una vigente a la vez" (§3.21)
queda garantizada por la gestión en SIGME; una validación de solape **no está
especificada** en ninguna fuente.

---

## 11.6 Endpoint anónimo, rate limit, CORS y trazabilidad

**Respuesta corta:** sin JWT, sin roles; sólo **rate limit estricto**,
**CORS restringido** al origen de la landing, validación estricta y tamaño
máximo de body (§2.9). La ventana de preinscripción la gestiona SIGME, no la
landing (§3.21).

| Control | Requisito | Fuente |
|---|---|---|
| Autenticación | **Ninguna**: endpoint público, anónimo. Sin headers de Authorization. | §2.9; RB-10; §3.20 |
| Roles / permisos | El endpoint **no** pasa por RBAC. El catálogo §2.7 tiene `preinscripcion.crear` y `preinscripcion.listar`: `listar` corresponde a la consulta desde SIGME (§6); el dueño de `crear` sigue **PENDIENTE** (G-02 en `01`; PD-03, cerrado 2026-10-06, fijó el reparto de la matriz de `02` §2.4 sin resolver este dueño). | §2.7; §6; `01` §1.5.2 |
| Rate limit | "Estricto (anti-bots)". **El umbral numérico es PENDIENTE** (§2.9 no da número; el de 5 intentos/15 min de §2.4 es de `/auth/login`, no de la landing). Respuesta `429`. | §2.9; §2.4 |
| Tamaño de body | Validación estricta y **tamaño máximo de body**. **El número y el código de respuesta son PENDIENTE**. | §2.9 |
| CORS | Origen **exclusivamente** el de la landing. **Nunca `allow_origins=["*"]`** en producción. El valor exacto es configuración → **PENDIENTE** (PD-06, cerrado 2026-10-06, fijó Vercel + CORS obligatorio, no el valor del origen). | §2.9 |
| Lectura pública | **No existe**: la landing sólo escribe. | RB-10; §2.9 |
| Ventana de preinscripción | Se gestiona desde SIGME con sesión válida; la landing no la ve ni la toca. | §3.21 |

### Trazabilidad (IP, user agent, UTM)

**Nota local de vocabulario — trazabilidad:** registro de los datos del
request que permiten auditar el origen del envío sin identificar ni
autenticar al usuario. Columnas servidor en `pr_preinscripcion`: `ip`
(`inet`), `user_agent` (`varchar(300)`), `utm_source`, `utm_medium`,
`utm_campaign` (`varchar(100)`, todas anulables) (§3.20).

| Dato | Cómo se obtiene | Estado |
|---|---|---|
| `ip` | Del request entrante, detrás del proxy del despliegue (Vercel): del header de proxy confiable (por ejemplo `X-Forwarded-For`), nunca de la dirección de conexión entrante. | **Definido** (PD-06, cerrado 2026-10-06; NFR-042) |
| `user_agent` | Cabecera `User-Agent` del request. | Definido (§3.20) |
| `utm_source` / `utm_medium` / `utm_campaign` | **No pueden ir en el body**: el payload es exactamente 6 campos (11.3). Candidato: query string del propio `POST` (`?utm_source=…`). | **PENDIENTE** — el mecanismo no está especificado en ninguna fuente |

La trazabilidad es **del lado servidor**: el backend completa esas columnas;
el cliente no las envía como campos del payload (§3.20, sección SERVIDOR).

---

## 11.7 Estrategia de migración futura a `pe_persona`

**Respuesta corta:** hoy **no hay ninguna FK ni propagación de ids** entre
`pr_*` y `pe_*`/`es_*` (11.2). La migración es un **proceso de datos futuro**
que la misma base de datos debe facilitar (`analisis.txt` §3.20; plan §3,
11.7).

**Objetivo:** al momento de convertir una preinscripción en persona real del
sistema, alinear los nombres del payload con el modelo `pe_*` / `es_*` sin
reescrituras forzadas.

| Campo de `pr_preinscripcion` | Destino tentativo | Obstáculo a resolver | Estado |
|---|---|---|---|
| `nombre_alumno` | `pe_persona.apellido` + `pe_persona.nombre` (§3.2) | `pe_persona` separa apellido y nombre; el payload trae **un solo campo**. ¿Cómo se parte? | **PENDIENTE** |
| `documento` | `pe_persona.documento` + `pe_documento_tipo` (se asume DNI, §3.1) | Requiere resolver el `documento_tipo_id` de `pe_documento_tipo` en el momento de migrar | Derivado de §3.1/§3.2 |
| `fecha_nacimiento` | `pe_persona.fecha_nacimiento` (nullable en `pe_persona`) | Sin obstáculo | Derivado de §3.2 |
| `orientacion` | `es_orientacion` (FK, §3.13) | Texto libre → catálogo con FK: requiere match exacto o tabla de equivalencias; **no especificado** | **PENDIENTE** |
| `email` | `pe_contacto` con `pe_contacto_tipo` = Email (§3.3, §3.4) | Requiere crear o buscar la persona primero | Derivado de §3.3/§3.4 |
| `nombre_tutor` | Persona de contacto del alumno o fila propia | **No está determinado** por ninguna fuente | **PENDIENTE** |
| `anio_lectivo`, `estado`, `ip`, `user_agent`, `utm_*` | Sin destino en `pe_*` | Quedan como histórico en `pr_preinscripcion`; la preinscripción **no se borra** al migrar (soft delete, §1.7) | **PENDIENTE** (política exacta) |

**PENDIENTE (pregunta madre):** **cuándo** ocurre la migración — quién dispara
que una preinscripción pase a `pe_persona` y con qué permiso. Ninguna fuente
lo define; es tema del doc de casos de uso / estados (plan §3, 04–05).

---

## PENDIENTE consolidados

| # | PENDIENTE | Bloquea / afecta | Fuente del hueco |
|---|---|---|---|
| 1 | Umbral numérico del rate limit de la landing | 11.4 (429), 11.6 | §2.9 (sin número) |
| 2 | Tamaño máximo de body **y** su código de respuesta | 11.4.4 | §2.9 / §6 (no contemplado entre los 5) |
| 3 | Valor exacto del origen CORS de la landing | 11.6 | §2.9 (configuración); PD-06 cerró 2026-10-06 la estrategia (Vercel, CORS obligatorio), no el valor |
| 4 | Mecanismo de captura de UTM (no puede ir en el body) | 11.6 | §3.20 vs 11.3 |
| 5 | ~~Obtención de `ip` detrás de proxy (`X-Forwarded-For`)~~ **[RESUELTO — 2026-10-06]**: header de proxy confiable, con el despliegue fijado en Vercel (PD-06; NFR-042) | — (ya no bloquea) | PD-06 (cerrado 2026-10-06) |
| 6 | Formato de `documento` (¿sólo dígitos?) | 11.3 | §3.20 (sólo `varchar(20)`) |
| 7 | Rango de `fecha_nacimiento` (¿no futura?) | 11.3 | Sin fuente |
| 8 | ¿`orientacion` debe coincidir con `es_orientacion.descripcion`? | 11.3, 11.7 | §3.20 (texto sin catálogo) |
| 9 | Tratamiento de campos extra del body (ignorar vs `422`) | 11.3 | Sin fuente |
| 10 | Forma del item en `errors[]` y cuerpo del `429` | 11.4.3 | §6 (parcial) — **(D), PROVISIONAL** |
| 11 | Orden `422` vs `409` | 11.4.4 | Sin fuente — **(D), PROVISIONAL** |
| 12 | Instante del acuse de preinscripción por email | 11.4.5 | RB-24 / RB-25 (canal sí, disparo no) |
| 13 | Validación de no-solape entre ventanas de años distintos | 11.5 | §3.21 vs DDL (`uq_ventana_anio`) |
| 14 | Migración a `pe_persona`: disparador, `nombre_tutor`, destino de `anio_lectivo`/`estado` | 11.7 | §3.20, plan §3 (11.7) |
| 15 | Dueño del permiso `preinscripcion.crear` | 11.6 | §2.7; `01` G-02 (PD-03 cerró 2026-10-06 sin fijar este dueño) |
| 16 | ~~Payload real que envía la landing (verificación de mañana)~~ **[RESUELTO — 2026-10-04]**: payload verificado con el usuario, coincide con 11.3 | — (ya no bloquea) | plan §3 (11), estado `[PROVISIONAL]` |

---

## Checklist de cierre (11 · Landing — contrato de preinscripción)

- [x] El payload lista **exactamente** los 6 campos de PD-01 (§7), P-09
      (plan §6) y las columnas CLIENTE de §3.20: `nombre_alumno`, `documento`,
      `fecha_nacimiento`, `orientacion`, `nombre_tutor`, `email`.
- [x] Los 6 aparecen como obligatorios (`NOT NULL`), incluido `nombre_tutor`
      (O-2; §3.20).
- [x] `anio_lectivo` **no** está en el payload: se deriva de
      `vw_ventana_vigente` (O-3; §3.20, §3.21).
- [x] Las 5 respuestas son `201`, `200`, `409 ventana-cerrada`, `422` y `429`
      (§6); **nunca `409` por duplicado** (RB-13).
- [x] Cuerpos de `201`/`200`/`409`/`422` coinciden con el croquis de §6; los
      dos cuerpos derivados quedan marcados **(D) / PROVISIONAL**.
- [x] Ninguna foreign key hacia `pe_*` ni `es_*` se propone en este documento
      (§3.20; plan §3, 11.2).
- [x] Sin columna de consentimiento: art. 5 externo (físico), art. 6 heredado
      a la landing (O-1; §3.20; plan §3, 11.3).
- [x] Endpoint anónimo: sin JWT, sin roles, con rate limit y CORS restringido
      (§2.9); ventana de preinscripción gestionada desde SIGME (§3.21).
- [x] Trazabilidad IP / user agent / UTM referida a columnas servidor de
      §3.20, sin campos extra en el payload.
- [x] Toda cita `RB-xx` / `PD-xx` / `O-x` / `P-xx` existe en su fuente
      (RB-10, RB-13, RB-14, RB-23, RB-24, RB-25; PD-01, PD-03, PD-06;
      O-1…O-4, §3.20; P-09, plan §6). No se creó ningún ID nuevo.
- [x] Vocabulario conforme a `01` §1.2.2 (preinscripción, ventana de
      preinscripción, año lectivo, upsert) y §1.3 (sin "inscribirse a la
      escuela", sin "matrícula", "ventana" siempre calificada).
- [x] **Criterio del plan** (plan §3, 11): la landing puede implementar el
      POST contra este contrato **sin preguntar nada** — la verificación del
      payload real se cerró el **2026-10-04**.
- [ ] Verificación conjunta con el usuario (payload real aprobado
      **2026-10-04**; siguen (b), (c) y (d)) → actualizar 11.3, 11.4 y el
      estado `[PROVISIONAL]` → `[VERIFICADO]`.

## Siguiente paso

Verificación conjunta con el usuario: contrastar la tabla de 11.3 contra los
datos reales que la landing envía, resolver los PENDIENTE 1…16 que correspondan
y quitar el estado `[PROVISIONAL]`. En paralelo, según `odd/tasks`, el
siguiente documento de la serie es `04-maquinas-de-estados.md` (Fase 2), que
absorbe los PENDIENTE 11, 12 y 13.
