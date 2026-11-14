# 07 · Estados críticos y excepciones — Backend EPET36

**Respuesta corta:** este documento cataloga **23 estados críticos**
(`EX-01`…`EX-23`): todo aquello en lo que el backend puede recibir una
petición que no puede satisfacer de forma obvia — ventanas vencidas,
inscripciones duplicadas, límites de condición, tokens caídos, mesas que
desaparecen de los listados, colas de notificación con fallo y operaciones
sin red. Para cada uno declara el **disparador**, el **dueño** de la regla,
la **respuesta HTTP** (sólo si alguna fuente la declara), qué **se pierde**,
la **mitigación** y quién la **verifica**, y cierra con un escenario
**Given/When/Then** ejecutable. Los códigos que ninguna fuente fija quedan
**PENDIENTE** en **7.7** y **7.8** con el hueco exacto que los mantiene
abiertos; en este documento **no se cierra ningún `PD-xx` ni `G-xx`**.

Vocabulario: se usan los términos de `01-glosario-y-alcance.md` (1.2) y se
respeta su vocabulario prohibido y retirado (1.3); las lesiones de cada
consumidor salen de `02-actores-y-consumidores.md` (2.1, 2.4); los eventos y
gatillos, de `03-eventos-y-gatillos.md` (3.1–3.4); las transiciones de
`04-maquinas-de-estados.md` (4.6); los casos de uso afectados, de
`05-casos-de-uso-sigme.md` (`CU-01`…`CU-30`) y
`06-casos-de-uso-sigme-m.md` (`CU-31`…`CU-42`); el contrato de la landing,
de `11-landing-preinscripcion.md`. Toda cita `RB-xx` y `PD-xx` remite a
`analisis.txt` (§4 y §7); `§n.m` remite a la sección de ese archivo;
`E-xx`, `S-xx` y `T-xx` remiten a doc 03; `G-xx` a doc 01 §1.5.2;
`C-xx`, `ME-xx`, `INS-xx`, `US-xx`, `SES-xx` y `GR-xx` a doc 04.

## Rápido recorrido

1. **7.1** — el catálogo completo de los 23 estados, con su respuesta HTTP
   declarada.
2. **7.2** — el detalle de cada uno: disparador → qué se pierde →
   mitigación → quién verifica → escenario Given/When/Then, agrupado en cinco
   dominios.
3. **7.3** — la ventana temporal: límite inclusivo, reloj autoritativo y
   desfasaje del dispositivo (RB-23).
4. **7.4** — concurrencia: semántica de reintento por operación (E-13) e
   índices únicos que absorben el choque.
5. **7.5** — integridad de los datos históricos: snapshot, ciclo de
   convocatorias y soft delete.
6. **7.6** — degradación y recuperación: qué sigue funcionando cuando algo
   se cae, y cómo se vuelve.
7. **7.7** — consolidado de códigos HTTP: declarados con su fuente, y
   pendientes con su hueco.
8. **7.8** — consolidado de pendientes que este documento hereda y no cierra.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Alcance** | Los tres consumidores del backend (SIGME web, SIGME-M y landing) y todas las operaciones de `analisis.txt` §6. Los casos de uso de los docs 05 y 06 referencian los códigos de acá; **los códigos y los estados críticos se definen en este documento**. | plan §3 (07); doc 02 §2.1; doc 05 §5.1, doc 06 §6.8 |
| **Identificadores** | `EX-xx` es una **serie local** de este documento: son los estados críticos del catálogo de 7.1. No se reutiliza la serie `E-xx` de doc 03 (son eventos) ni ninguna otra. `RB-xx`/`PD-xx` → `analisis.txt` (§4, §7); `E-xx`/`S-xx`/`T-xx` → doc 03; `G-xx` → doc 01 §1.5.2; `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` → doc 04; `CU-01`…`CU-42` → docs 05 y 06; `O-x` → `analisis.txt` §3.20. | doc 03 §3.4; plan §3 (07) |
| **Códigos HTTP** | Un código se afirma **sólo** si alguna fuente lo declara. Si ninguna lo declara, la fila dice **ninguno declarado → PENDIENTE** y nombra el hueco (`PD-xx` o `G-xx`). Cuando la fuente lista candidatos sin elegir —como **PD-19** con `404, 409, 422`— se citan **como candidatos**, nunca como contrato. | `analisis.txt` §6, §7; doc 01 §1.1 (códigos de respuesta en alcance); doc 06 §6.8 |
| **PENDIENTE** | Este documento **no cierra** ningún `PD-xx` ni `G-xx`: los hereda visibles en 7.8. Los casos que no tenían ID hoy están anclados a `PD-23`…`PD-28` en `analisis.txt` §7. | doc 05 §5.11; doc 06 §6.8; `analisis.txt` §7 |
| **Ventana y reloj** | Toda ventana se **constata** en cada request por fecha de calendario en `America/Argentina/Buenos_Aires`, inclusive hasta las 23:59:59; el reloj autoritativo es el del backend, nunca el del dispositivo; no hay ningún job programado en v1. | RB-23, RB-24; doc 03 §3.2; doc 02 §2.1.2 |
| **Idempotencia** | Toda escritura que un cliente puede reintentar (E-13) se analiza en 7.4.1 con la semántica que ya declararon los docs 06 y 11; aquí se agregan los casos que quedaron sin código. | plan §3 (06.6, 07); doc 06 §6.6; doc 11 §11.4.1 |
| **Vocabulario** | Se respetan los términos de doc 01 §1.2 y la lista de vocabulario prohibido y retirado de §1.3: convocatoria ≠ mesa, preinscripción ≠ inscripción, grupo de mesas = fecha + hora. | doc 01 §1.2, §1.3; RB-27, RB-16 |
| **Verificación** | Cada estado declara **quién verifica** la mitigación: el backend en cada request, el cliente en su interfaz, o una prueba de integración sobre el service. Donde la verificación depende de una decisión abierta, se marca bloqueada hasta ese PD. | plan §3 (07, criterio de cierre) |

---

## 7.1 Catálogo de estados críticos

Los 23 estados, agrupados por dominio. La columna "Respuesta HTTP declarada"
resume 7.2 y se detalla en 7.7.

| EX | Estado crítico | Dominio | Respuesta HTTP declarada | Fuente |
|---|---|---|---|---|
| EX-01 | Ventana de inscripción cerrada al inscribir o anular | Ventanas | `409` en `POST /inscripciones`; **ninguno declarado** para el `DELETE` | RB-07, RB-17, RB-23; §6; T-03 |
| EX-02 | Ventana de preinscripción de la landing cerrada | Ventanas | `409 { code: "ventana-cerrada" }` | RB-14, RB-23; §6; T-04 |
| EX-03 | Payload inválido o ráfaga de envíos en el endpoint anónimo | Ventanas | `422`, `429` — y nunca `409` por documento repetido | RB-13; §6, §2.9 |
| EX-04 | Convocatoria inactiva o fuera de su ventana | Convocatoria | **ninguno declarado** → PENDIENTE | RB-09; S-07 |
| EX-05 | Campaña terminada: cierre de la convocatoria por calendario | Convocatoria | sin request: constatación de calendario (**G-05**, **[RESUELTA — 2026-10-06]**) | RB-16; T-06; G-05 |
| EX-06 | Inscripción duplicada a la misma materia en la misma convocatoria | Inscripción | `409` | RB-08; §6; S-06 |
| EX-07 | Combinación materia × condición sin mesa | Inscripción | **PENDIENTE (PD-19)** | RB-31, RB-28; §7 |
| EX-08 | Límite de materias por condición alcanzado | Inscripción | **ninguno declarado** → PENDIENTE | RB-03, RB-08c; S-05; PD-02 (cerrado 2026-10-06) |
| EX-09 | Anulación fuera de la ventana de inscripción | Inscripción | **ninguno declarado** → PENDIENTE | RB-08b, RB-07; INS-02 |
| EX-10 | Anulación repetida (reintento del `DELETE`) | Inscripción | efecto nulo declarado; **código PENDIENTE** | RB-08b; INS-02; doc 06 §6.8 |
| EX-11 | Access token vencido sobre una acción protegida | Sesión | `401` | T-07; §2.1; doc 02 §2.1.2 |
| EX-12 | Refresh vencido o reutilizado | Sesión | `401` (citado desde T-07) | §2.2; T-08, S-14; doc 05 §5.1 |
| EX-13 | Rate limit de login y bloqueo temporal | Sesión | `429` **o** bloqueo temporal; elección **PENDIENTE** | §2.4; E-14; US-02, US-03 |
| EX-14 | Invalidación global por `token_version` | Sesión | **ninguno declarado** → PENDIENTE | §2.6; S-15 |
| EX-15 | Usuario sin el permiso del endpoint | Autorización | **ninguno declarado** → PENDIENTE | §2.7; doc 02 §2.1.1; PD-03 (cerrado 2026-10-06) |
| EX-16 | Mesa que quedó sin inscripciones activas | Listados | sin error: es un **filtrado**; su alcance está **PENDIENTE** | RB-22; S-03; §3.18 |
| EX-17 | Edición de un grupo con la ventana de inscripción abierta | Grupos | sin código declarado; el permiso de hacerlo es **PD-12** | RB-29; PD-12 |
| EX-18 | Choque de unicidad al crear grupos o mesas | Grupos | **ninguno declarado** para `uq_mesa_unica`; colisión de `uq_grupo_unico` → `409` | §3.18, §3.22; PD-13, PD-16 (cerrados 2026-10-06) |
| EX-19 | Grupo borrado con mesas vivas que lo referencian | Grupos | sin endpoint de baja en §6 → PENDIENTE | PD-18 (cerrado 2026-10-06); GR-02; §1.8 |
| EX-20 | Estados de la mesa sin disparador declarado | Mesas | sin operación: el estado se constata al leer (**G-05**, **[RESUELTA — 2026-10-06]**) | G-05; ME-03, ME-04, ME-05; RB-21 |
| EX-21 | Cola de email con fallo de envío | Notificaciones | sin código: el envío es posterior a la respuesta | RB-25, RB-24; S-20 |
| EX-22 | Registro del token de push sin endpoint | Notificaciones | sin endpoint en §6 → PENDIENTE | RB-24; doc 06 §6.8 |
| EX-23 | Operación sin conexión (RB-26) | Degradación | sin request; `401` si hay red y la sesión venció | RB-26; T-07; doc 02 §2.1.2 |

**Cómo leer la tercera columna.** De los 23 estados, **5** tienen respuesta
declarada sin fisuras (EX-02, EX-03, EX-06, EX-11 y EX-16, este último por
ser un filtrado que no responde con error); **4** están declarados sólo en
parte, porque algún caso de uso dentro del mismo estado sigue sin código
(EX-01 con el `DELETE`, EX-12 y EX-13 con el detalle de la respuesta, EX-23
con la escritura sin red); **1** no aplica porque no hay request de por medio
(EX-05, el cierre por calendario); y los **13** restantes — EX-04, EX-07,
EX-08, EX-09, EX-10, EX-14, EX-15, EX-17, EX-18, EX-19, EX-20, EX-21 y
EX-22 — **no tienen contrato de respuesta** y por eso aparecen en 7.7.2 como
pendientes. Un estado crítico sin código no es un estado resuelto: es un
hueco visible.

---

## 7.2 Detalle de cada estado crítico

Cada bloque usa la misma tabla de siete campos. La fila **Escenario** es
ejecutable en lenguaje Given/When/Then y es el criterio de cierre del plan
§3.07.

### 7.2.1 Ventanas y convocatoria

**EX-01 — Ventana de inscripción cerrada al inscribir o anular**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | T-03 / C-04 — cambia la fecha de calendario a 00:00:00 posterior a `fecha_fin_inscripcion`; el alumno todavía envía `POST /inscripciones` o `DELETE /mis-inscripciones/{id}` | doc 03 §3.2; doc 04 C-04; RB-23, RB-17 |
| Dueño | La regla la gobierna el calendario, no un usuario: la constatación ocurre en cada request. No hay ningún job programado en v1, así que el cierre no se "dispara" a una hora fija. | RB-23, RB-24; doc 03 §3.2; doc 04 §4.6.1 |
| Respuesta HTTP declarada | `409` para `POST /inscripciones` (§6: "409 si ya inscripto a esa MATERIA en esta convocatoria, o ventana cerrada"). Para `DELETE /mis-inscripciones/{id}` **ninguna fuente declara el código** → PENDIENTE. | §6; doc 06 CU-37, CU-39 |
| CU y transiciones afectados | CU-37, CU-39, CU-40, CU-41; transiciones C-04 e INS-02; evento T-03 | doc 06 §6.3, §6.5; doc 04 C-04, INS-02 |
| Qué se pierde | La posibilidad de inscribirse o anular: la lista queda **fija** en `fecha_fin_inscripcion` y no se revalida nada el día de rendir. El alumno que no llegó a tiempo pierde la oportunidad de esa convocatoria; sólo le queda consultar la fecha de rendir. | RB-17, RB-18, RB-07 |
| Mitigación y quién la verifica | El backend compara `current_date` en `America/Argentina/Buenos_Aires` contra la columna `date`, sin usar timestamps crudos de UTC ni sumar horas; el reloj del dispositivo nunca decide. **Quién verifica:** el backend en cada request; el alumno lo comprueba al ver que, tras el cierre, las pantallas de escritura desaparecen y sólo queda la consulta. | RB-23; doc 02 §2.1.2; doc 06 §6.6 |
| Escenario (Given/When/Then) | **Given** una convocatoria `activa` cuya `fecha_fin_inscripcion` ya pasó; **When** el alumno envía `POST /inscripciones` para una materia de esa convocatoria; **Then** el backend responde `409`, no se crea ninguna fila en `es_mesa_inscripcion` y `GET /mis-inscripciones` sigue devolviendo exactamente las inscripciones previas (§6, RB-17, RB-08). | §6; RB-17, RB-08, RB-23 |

**EX-02 — Ventana de preinscripción de la landing cerrada**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | T-04 — se cumple `fecha_hasta` de `pr_ventana` (o no hay fila vigente en `vw_ventana_vigente`) y una persona envía el formulario | doc 03 §3.2; RB-14, RB-23 |
| Dueño | RB-14: existe **una sola** ventana vigente por año (`uq_ventana_anio`); quien la abre y cierra es la administración desde SIGME, nunca la landing anónima | RB-14; §3.21; E-05 |
| Respuesta HTTP declarada | `409 Conflict` con cuerpo `{ "code": "ventana-cerrada" }`. **Regla de oro:** en este endpoint el `409` significa ventana cerrada y nada más; un documento repetido jamás devuelve `409`. | §6; RB-14; doc 11 §11.4.2 |
| CU y transiciones afectados | CU-14, CU-26, CU-42 (acuse); eventos T-04, T-05, S-19 | doc 05 §5.5; doc 11 §11.4; doc 03 §3.2 |
| Qué se pierde | La posibilidad de preinscribirse por la web: la solicitud queda fuera del sistema y el consentimiento se recoge en el formulario físico posterior. No se pierde ningún dato ya enviado. | RB-14, RB-10; doc 11 §11.1 |
| Mitigación y quién la verifica | La ventana se lee desde `vw_ventana_vigente` con el reloj del backend; el reenvío de los mismos datos sigue siendo seguro porque el upsert es idempotente (RB-13). **Quién verifica:** la administración al abrir y cerrar `pr_ventana` desde SIGME, y el visitante al reenviar el formulario. | RB-13, RB-14, RB-23; doc 11 §11.4.1 |
| Escenario (Given/When/Then) | **Given** que hoy no hay fila vigente en `vw_ventana_vigente`; **When** un visitante envía `POST /landing/preinscripcion` con los 6 campos obligatorios bien formados; **Then** el backend responde `409 { "code": "ventana-cerrada" }` y no se inserta ni actualiza ninguna fila de `pr_preinscripcion` (§6, RB-14, RB-10). | §6; RB-14, RB-10; doc 11 §11.4.2 |

**EX-03 — Payload inválido o ráfaga de envíos en el endpoint anónimo**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-04 con un payload incompleto o mal formado; E-14 con una ráfaga de envíos que supera el rate limit estricto anti-bots | doc 03 §3.1; §2.9 |
| Dueño | La validación estricta es del backend; el resumen y la doble confirmación de los datos **antes** de enviar los los hace la landing, no el backend | RB-13; §2.9; doc 11 §11.4.1 |
| Respuesta HTTP declarada | `422 { code: "validacion", errors[] }` para payload inválido y `429` para la ráfaga. Nunca `409` por documento repetido: repetir produce `201` (creada) o `200` (actualizada). | §6; RB-13; doc 11 §11.4.2 |
| CU y transiciones afectados | CU-26; eventos E-04, E-14; filas de doc 03 §3.4 "Preinscripción de la landing" | doc 05 §5.5; doc 03 §3.4 |
| Qué se pierde | Un envío legítimo que pega la ráfaga no completa el formulario en ese intento; un body que supera el tamaño máximo se descarta entero. Ninguna fila ya escrita se pierde: el upsert sobrescribe en el siguiente intento. | §2.9; RB-13; O-4 |
| Mitigación y quién la verifica | Rate limit estricto, límite de tamaño de body y CORS restringido exclusivamente al origen de la landing (nunca `*`); el reintento manual es seguro porque repetir no es error. **Quién verifica:** el backend en cada request; el equipo de la landing con las pruebas de integración del contrato. | §2.9; RB-13; doc 11 §11.4.2 |
| Escenario (Given/When/Then) | **Given** una ventana de preinscripción vigente; **When** llega un `POST /landing/preinscripcion` con `email` en `null`; **Then** el backend responde `422 { "code": "validacion", "errors": [ … ] }` y `pr_preinscripcion` queda intacta (§6, O-2). | §6; O-2 |

**EX-04 — Convocatoria inactiva o fuera de su ventana**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-07 / C-05 / E-06 — la convocatoria tiene `activa = false`, o el `hoy` del backend cae fuera de `fecha_inicio_inscripcion`…`fecha_fin_inscripcion`, y un alumno intenta inscribirse | doc 03 §3.3; doc 04 C-05, INS-01; RB-09 |
| Dueño | `activa` la cambia la administración desde SIGME (E-06); la ventana la gobierna el calendario (C-02, C-04). El catálogo §2.7 **no tiene** ningún código `convocatoria.*`, así que el permiso de esa edición sigue en hueco de la matriz — **PD-03** se cerró el 2026-10-06 con el reparto de doc 02 §2.4, sin crear el código. | E-06; doc 04 §4.6.1; PD-03 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** §6 sólo anota `409` para duplicado y para ventana cerrada en `POST /inscripciones`; el rechazo de RB-09 se describe como "Rechazo: no se inscribe" sin código. | §6; RB-09; S-07 |
| CU y transiciones afectados | CU-11, CU-12, CU-37, CU-40; transiciones C-05 e INS-01 | doc 05 §5.4; doc 06 CU-37 |
| Qué se pierde | Toda posibilidad de inscribir o anular en esa convocatoria. El caso más delicado es una convocatoria desactivada **con la ventana de fechas todavía vigente**: el alumno ve la ventana abierta y aun así no puede completar la operación. | RB-09, RB-07 |
| Mitigación y quién la verifica | `activa` y la ventana se evalúan en el mismo request, de modo que ninguna de las dos depende de una comprobación previa; el cliente debe leer `GET /convocatoria-vigente` antes de ofrecer la acción. **Quién verifica:** el backend al rechazar la escritura; el alumno al consultar la convocatoria vigente. | RB-09; doc 06 CU-34; doc 04 INS-01 |
| Escenario (Given/When/Then) | **Given** una convocatoria con la ventana de fechas vigente hoy pero con `activa = false`; **When** el alumno envía `POST /inscripciones`; **Then** no se crea ninguna fila en `es_mesa_inscripcion` y el código HTTP devuelto es **PENDIENTE** — ninguna fuente lo declara (RB-09, S-07, doc 04 INS-01). | RB-09; S-07; doc 04 INS-01 |

**EX-05 — Campaña terminada: cierre de la convocatoria por calendario**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | T-06 — pasa el último día de rendir de la convocatoria, que es la **última fecha de sus grupos** (RB-27) | doc 03 §3.2; RB-16, RB-27 |
| Dueño | **G-05 [RESUELTA — 2026-10-06].** El cierre no lo dispara nadie: es una constatación del calendario (C-04), igual que la ventana; la campaña siguiente se abre de forma explícita (RB-16). Sigue en hueco el permiso de la edición manual de `activa` (código `convocatoria.*` de §2.7). | RB-16; doc 01 §1.5.2; doc 04 §4.6.2; G-05 |
| Respuesta HTTP declarada | Ninguna: es una constatación de calendario, no una operación. Lo que sí afecta al cliente es que, a partir de ese día, las escrituras de EX-01 dejan de servir. | RB-16, RB-23; doc 04 C-04 |
| CU y transiciones afectados | CU-13, CU-34; transiciones C-04 y C-07; eventos T-06 y S-10 | doc 05 §5.4; doc 04 C-07 |
| Qué se pierde | Sin escritura de cierre, la campaña rendida queda navegable como consulta y el alumno no puede distinguir una convocatoria vigente de una terminada más allá de las fechas. | RB-16; G-05 |
| Mitigación y quién la verifica | **[CERRADO — 2026-10-06]** (G-05): el estado se deriva al leer y nunca se escribe; la convocatoria siguiente se **abre de forma explícita** (RB-16), así que el alumno no depende de un cierre automático. **Quién verifica:** la administración al abrir la campaña siguiente; el alumno con `GET /convocatoria-vigente`, que devuelve el estado derivado. | RB-16; doc 06 CU-34; G-05 |
| Escenario (Given/When/Then) | **Given** una convocatoria cuya última fecha de grupo fue ayer y que sigue con `activa = true`; **When** el alumno consulta `GET /convocatoria-vigente` hoy; **Then** el backend devuelve la convocatoria con estado derivado `cerrada`, calculado por calendario en cada lectura y sin que nadie haya escrito ese estado (G-05, 2026-10-06; RB-16, doc 04 §4.6.2). | RB-16; G-05 |

### 7.2.2 Inscripción

**EX-06 — Inscripción duplicada a la misma materia en la misma convocatoria**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-06 / E-13 — un segundo `POST /inscripciones` para la misma materia y convocatoria, ya sea un reintento del propio alumno tras un timeout o un intento deliberado de repetir | doc 03 §3.3, §3.4; RB-08 |
| Dueño | El índice único de la base, no el código de aplicación: `uq_inscripcion_unica (convocatoria_id, usuario_id, materia_id) WHERE deleted_at IS NULL AND estado <> 'anulado'` | §3.19; RB-08 |
| Respuesta HTTP declarada | `409` y no se crea fila. Es además la garantía de idempotencia de esta operación: el reintento devuelve la misma respuesta sin duplicar. | §6; S-06; doc 06 §6.6 |
| CU y transiciones afectados | CU-37, CU-40, CU-25 (pendiente); transiciones INS-01 e INS-04 | doc 06 §6.3; doc 05 CU-25 |
| Qué se pierde | Nada de datos: éste es el estado en que la pérdida se previene. Lo que se pierde es **información para el cliente**: un reintento tras un timeout y un intento legítimo de duplicar reciben la misma respuesta, y el cliente sólo puede distinguirlos consultando `GET /mis-inscripciones`. | RB-08, RB-26 |
| Mitigación y quién la verifica | La unicidad vive en la base y la fila `anulado` queda fuera del índice, así que anular libera la materia sin borrar la historia. **Quién verifica:** el backend al recibir el choque; una prueba de integración que dispara dos `POST` consecutivos y dos concurrentes. | §3.19; RB-08b; plan §3 (07) |
| Escenario (Given/When/Then) | **Given** un alumno con una inscripción `inscripto` a la materia M de la convocatoria C; **When** repite `POST /inscripciones` para la misma materia y convocatoria (reintento E-13); **Then** el backend responde `409`, `es_mesa_inscripcion` conserva exactamente una fila activa para ese par y ninguna mesa nueva se creó (RB-08, §3.19, §6). | RB-08; §3.19; §6 |

**EX-07 — Combinación materia × condición sin mesa**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-01 sobre una combinación para la que el secretario nunca creó mesa en la convocatoria | RB-31, RB-28; doc 03 §3.4 |
| Dueño | RB-31: "si una combinación materia × condición no tiene mesa, el alumno simplemente no puede inscribirse y **NADA falla de forma ruidosa**". La creación de mesas es exclusiva del secretario, en bloque. | RB-31, RB-28 |
| Respuesta HTTP declarada | **PENDIENTE (PD-19).** La fuente sólo dice "Rechazo" y lista `404, 409, 422` como candidatos sin elegir uno. | §7 PD-19; RB-31 |
| CU y transiciones afectados | CU-37, CU-40, CU-21 (cobertura); transición INS-01 | doc 06 CU-37; doc 05 CU-21 |
| Qué se pierde | La posibilidad de rendir esa materia en esa convocatoria. Si el alumno no revisó la cobertura antes de que se abra la ventana, descubre el hueco recién al intentar inscribirse. | RB-31; PD-15 |
| Mitigación y quién la verifica | `GET /cobertura-mesas?convocatoria_id=` expone las materias × condiciones sin mesa y está pensada para consultarse **antes** de abrir la ventana; RB-31 prohíbe resolverlo creando la mesa en el momento. **Quién verifica:** el secretario con la cobertura antes de abrir; el backend al no insertar nada. | §6; RB-31; doc 05 CU-21 |
| Escenario (Given/When/Then) | **Given** una convocatoria con la ventana abierta y sin mesa para la materia M en la condición Previa; **When** el alumno envía `POST /inscripciones` para esa combinación; **Then** no se crea ninguna `es_mesa_examen` ni ninguna inscripción, y el código HTTP del rechazo queda **PENDIENTE (PD-19)** (RB-31, RB-28, §7). | RB-31, RB-28; §7 |

**EX-08 — Límite de materias por condición alcanzado**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-05 / RB-08c — se intenta una inscripción, o una reinscripción tras anular, que superaría `es_condicion.limite_materias` | doc 03 §3.3; RB-03, RB-08c |
| Dueño | RB-03, validado **sólo** al momento de inscribirse (o de anular y reinscribir). Nunca se revalida el día de la mesa. | RB-03, RB-17, RB-18 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** Ninguna fuente fija el código del rechazo por límite; **PD-02** se cerró el 2026-10-06 con los valores de la condición, no con el código. | RB-03; §7 PD-02 |
| CU y transiciones afectados | CU-37, CU-40; transiciones INS-01 e INS-04; evento S-05 | doc 06 §6.3, §6.5; doc 04 INS-04 |
| Qué se pierde | La inscripción a esa materia en esa convocatoria. RB-01 no interviene: no hay límite de cantidad por mesa, el límite es de la **condición** y cuenta inscripciones, no lugares. | RB-01, RB-03 |
| Mitigación y quién la verifica | **[CERRADO — 2026-10-06]**, PD-02: los valores se siembran como `DEFAULT` (Previa hasta 3, Regular hasta 8, Libre sin límite) con unidad de conteo **por convocatoria** y son editables desde SIGME; el límite sólo se evalúa al inscribirse (RB-03). **Quién verifica:** una prueba unitaria del service con esos valores cargados. El código HTTP del rechazo sigue **PENDIENTE**. | §7 PD-02; RB-03 |
| Escenario (Given/When/Then) | **Given** `es_condicion.limite_materias = 3` para Previa y un alumno con 3 inscripciones activas en Previa dentro de la convocatoria; **When** envía `POST /inscripciones` para una cuarta materia en Previa; **Then** no se crea la fila, el límite no se revalida después de cerrada la ventana (RB-17) y el código HTTP del rechazo sigue **PENDIENTE** (RB-03; PD-02 cerrado 2026-10-06 sólo fijó los valores). | RB-03, RB-17; PD-02 |

**EX-09 — Anulación fuera de la ventana de inscripción**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-02 con `hoy` fuera de la ventana (T-03): el alumno toca "anular" después de `fecha_fin_inscripcion` | doc 03 §3.1, §3.4; RB-08b |
| Dueño | El calendario, con el mismo límite inclusivo de EX-01: RB-08b sólo habilita la anulación **durante** la ventana de la convocatoria | RB-08b, RB-07, RB-23 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** §6 sólo anota la restricción "sólo dentro de la ventana (RB-08b)" sin fijar código. | §6; RB-08b |
| CU y transiciones afectados | CU-39; transición INS-02; evento E-02 | doc 06 §6.5; doc 04 INS-02 |
| Qué se pierde | La oportunidad de corregir un error de elección: a partir del cierre, la inscripción errónea queda definitiva en la lista fija. No se pierde la fila ni su auditoría. | RB-17, RB-08b |
| Mitigación y quién la verifica | El backend evalúa la ventana en el mismo request que ejecuta la transición, así que la precondición no depende del cliente; el alumno sólo ve la opción de anular mientras la convocatoria vigente muestra la ventana abierta. **Quién verifica:** el backend al rechazar; el alumno al comprobar que la opción desapareció. | RB-23, RB-08b; doc 06 CU-34 |
| Escenario (Given/When/Then) | **Given** una inscripción en estado `inscripto` y una convocatoria cuya `fecha_fin_inscripcion` ya pasó; **When** el alumno envía `DELETE /mis-inscripciones/{id}`; **Then** la fila sigue en `inscripto`, no se aplica la transición INS-02 y el código HTTP del rechazo es **PENDIENTE** (RB-08b, RB-07, doc 04 INS-02). | RB-08b, RB-07; doc 04 INS-02 |

**EX-10 — Anulación repetida (reintento del `DELETE`)**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-13 sobre `DELETE /mis-inscripciones/{id}` cuando la fila ya está en estado `anulado` (típicamente: la respuesta del primer intento se perdió en la red) | doc 03 §3.1; RB-08b |
| Dueño | INS-02: la transición exige estado `inscripto`. Sobre una fila `anulado` no hay transición de salida, así que el **efecto** del reintento es nulo. | doc 04 §4.3, INS-02 |
| Respuesta HTTP declarada | Efecto nulo declarado y **código también declarado: `204 No Content`**, idempotente y sin cuerpo, igual que la primera llamada — **PD-25 cerrado** en `analisis.txt` §6. Doc 06 §6.8 derivó la pregunta a este documento; hoy la respuesta es observable con `GET /mis-inscripciones`. | doc 06 §6.8, §6.6; RB-08b; doc 04 INS-02; PD-25; `analisis.txt` §6 |
| CU y transiciones afectados | CU-39; transición INS-02; evento E-13 | doc 06 §6.5, §6.6 |
| Qué se pierde | Ningún dato: no se duplica ni se corrompe nada. Lo que se pierde es la **distinción en la respuesta**: el `204` idéntico de la primera y de la repetida no dice cuál de las dos ejecutó el cambio — el cliente las observa con `GET /mis-inscripciones`. | RB-08b, RB-26 |
| Mitigación y quién la verifica | El índice único excluye las filas `anulado`, de modo que un reintento no altera la unicidad ni bloquea la materia; el estado real se observa con `GET /mis-inscripciones`. **Quién verifica:** el backend al no crear ni modificar filas; una prueba de integración con dos `DELETE` consecutivos. | §3.19; RB-08b; doc 06 §6.6 |
| Escenario (Given/When/Then) | **Given** una inscripción ya en estado `anulado`; **When** el cliente reintenta `DELETE /mis-inscripciones/{id}` tras un timeout (E-13); **Then** la fila permanece `anulado`, no se crea ninguna fila nueva, `uq_inscripcion_unica` no cambia, la materia sigue libre para reinscribirse y la respuesta es `204 No Content`, igual que la primera (RB-08b, §3.19, §6). | RB-08b; §3.19; doc 06 §6.8; PD-25 |

### 7.2.3 Sesión, tokens y autorización

**EX-11 — Access token vencido sobre una acción protegida**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | T-07 — el access token cumplió su TTL de 15 minutos (máximo 30) mientras el alumno o el personal seguía navegando | doc 03 §3.2; §2.1 |
| Dueño | `analisis.txt` §2.1: el cliente rota con `POST /auth/refresh`; el backend sólo valida, no renueva por su cuenta | §2.1; doc 04 SES-01 |
| Respuesta HTTP declarada | `401` en la acción protegida | T-07; doc 02 §2.1.2 |
| CU y transiciones afectados | CU-02, CU-32 y toda escritura de CU-37, CU-39, CU-40; transición SES-01 | doc 05 §5.1; doc 06 §6.1 |
| Qué se pierde | La acción en curso, no los datos. **No** se pierde la lectura: la caché local del alumno sigue funcionando sin red ni token, así que la pantalla no queda vacía. | RB-26; doc 02 §2.1.2 |
| Mitigación y quién la verifica | Rotación de tokens en `/auth/refresh` y reintento de la operación después de renovar; el access token lleva los roles y permisos, así que la autorización no depende de una consulta previa. **Quién verifica:** el backend al rechazar; el cliente al renovar y reintentar. | §2.1, §2.2; doc 06 §6.6 |
| Escenario (Given/When/Then) | **Given** un access token emitido hace 16 minutos; **When** el alumno envía `POST /inscripciones`; **Then** el backend responde `401`, no se crea ninguna fila y, después de `POST /auth/refresh`, el mismo reintento se evalúa contra las reglas normales de ventana, unicidad y límite (T-07, RB-26). | T-07; RB-26 |

**EX-12 — Refresh vencido o reutilizado**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | T-08 — vencen los 7 días de `us_sesion.expires_at`; o S-14 — llega un refresh token **ya consumido** (reintento con respuesta perdida o intento de robo) | doc 03 §3.2, §3.3; §2.2 |
| Dueño | §2.2: rotación en cada uso y **reuse detection**; SES-04 revoca toda la familia (`familia_id`) | §2.2; doc 04 SES-04 |
| Respuesta HTTP declarada | `401`, citado desde **T-07** como la respuesta ante una sesión que ya no rota; doc 05 §5.1 lo invoca para T-08 y S-14. T-08 y S-14 **no declaran código por su cuenta**. | T-07; doc 05 §5.1 |
| CU y transiciones afectados | CU-02, CU-32; transiciones SES-04 y SES-05; eventos T-08 y S-14 | doc 06 §6.1; doc 04 SES-04 |
| Qué se pierde | La sesión completa de ese dispositivo: toda la familia de tokens queda revocada y hay que volver a autenticarse. En red móvil inestable, una respuesta perdida del refresh expulsa al usuario aunque no haya ningún robo. | §2.2, S-14 |
| Mitigación y quién la verifica | La reutilización sólo puede venir de un reintento o de un robo, así que revocar la familia es la respuesta deliberada; en base de datos se guarda sólo el hash SHA-256 del refresh, nunca el token crudo. **Quién verifica:** el backend en la reuse detection; una prueba de integración que envía dos veces el mismo refresh. | §2.2; doc 04 SES-04 |
| Escenario (Given/When/Then) | **Given** una familia de sesión cuyo refresh token ya fue consumido; **When** el cliente reintenta `POST /auth/refresh` con ese token; **Then** toda la familia pasa a `revocado` (SES-04), no se emite ningún par nuevo y se exige un login nuevo (§2.2, S-14). | §2.2; S-14; doc 04 SES-04 |

**EX-13 — Rate limit de login y bloqueo temporal**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-14 / S-16 — 5 intentos de login fallidos por usuario o IP dentro de 15 minutos | doc 03 §3.1; §2.4 |
| Dueño | §2.4: el backend suma `intentos_fallidos`, setea `bloqueado_hasta` y sube `token_version`; la transición US-02 no tiene dueño humano porque es una consecuencia, no una autorización | §2.4; doc 04 US-02 |
| Respuesta HTTP declarada | **Las dos cosas de la alternativa E-14:** `429 Too Many Requests` con cabecera `Retry-After` (segundos) **y** cuenta bloqueada 15 minutos (`bloqueado_hasta = now + 15 min`, la ventana de §2.4); al levantarse el bloqueo `intentos_fallidos` vuelve a 0 — **PD-27 cerrado** (señalado además en doc 04 US-03). | E-14; §2.4; doc 04 US-03; PD-27 |
| CU y transiciones afectados | CU-01, CU-31; transiciones US-02 y US-03; eventos T-09 y E-14 | doc 05 §5.1; doc 06 §6.1 |
| Qué se pierde | El acceso temporal de la cuenta: un usuario legítimo que se equivoca cinco veces queda bloqueado. No se pierde ninguna sesión ya abierta salvo por el `token_version` que sube con el bloqueo. | §2.4, §2.6 |
| Mitigación y quién la verifica | El bloqueo se levanta solo al vencer `bloqueado_hasta` (T-09 / US-03) y el subir `token_version` hace que los tokens viejos dejen de servir (S-15). **Quién verifica:** el backend al contar los intentos; una prueba de integración con seis logins fallidos y el reloj adelantado hasta el vencimiento. Duración fijada en 15 minutos con `429` + `Retry-After` (PD-27, `analisis.txt` §6). | §2.4, §2.6; doc 04 US-02, US-03 |
| Escenario (Given/When/Then) | **Given** una cuenta `activo` con 4 intentos fallidos en los últimos 10 minutos; **When** llega el quinto intento fallido; **Then** `intentos_fallidos` alcanza 5, se setea `bloqueado_hasta = now + 15 min`, la cuenta pasa a `bloqueado` (US-02), la respuesta es `429` con `Retry-After` y los intentos siguientes son rechazados; al vencer el bloqueo `intentos_fallidos` vuelve a 0 (§2.4, S-16, E-14, PD-27). | §2.4; S-16; E-14; PD-27 |

**EX-14 — Invalidación global por `token_version`**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-15 — cambio de clave (`POST /auth/cambiar-clave`), cambio de rol o bloqueo de cuenta | doc 03 §3.3; §2.6 |
| Dueño | §2.6: el entero `us_usuario.token_version` sube y los access tokens emitidos con la versión vieja **dejan de servir**; lo disparan la gestión de usuarios (US-04) o el propio usuario | §2.6; doc 04 US-04 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** T-07 declara `401` para el token **vencido** por tiempo; ninguna fuente declara el código para un token con `ver` vencido. | §2.6; T-07; S-15 |
| CU y transiciones afectados | CU-04, CU-09, CU-10; transiciones US-02 y US-04; evento S-15 | doc 05 §5.1, §5.3; doc 04 US-04 |
| Qué se pierde | Todas las sesiones activas del usuario en todos los dispositivos a la vez, sin aviso previo: cualquier operación en vuelo queda interrumpida. | §2.6 |
| Mitigación y quién la verifica | El cliente debe tratar el rechazo renovando o volviendo a autenticarse; subir `token_version` es además precondición del bloqueo por rate limit. **Quién verifica:** el backend al rechazar el token viejo; una prueba de integración que cambia la clave y reutiliza el token emitido antes del cambio. | §2.6, §2.4; doc 04 US-02 |
| Escenario (Given/When/Then) | **Given** un access token emitido con `ver = 1`; **When** un administrador cambia la clave del usuario (S-15) y luego el cliente usa ese token; **Then** el token deja de servir (§2.6) y el código HTTP devuelto es **PENDIENTE** — ninguna fuente lo declara. | §2.6; S-15 |

**EX-15 — Usuario sin el permiso del endpoint**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | Un request autenticado hacia un endpoint cuyo código de permiso el rol invocado no tiene | §2.7; doc 02 §2.1.1 |
| Dueño | La dependencia `require_permiso()` en cada endpoint protegido (checklist de calidad antes de codificar) | §2.7; doc 02 §2.1.1 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** Doc 02 §2.1.1 la llama "respuesta de prohibición" sin fijar el código; el mapeo endpoint → permiso sale de la matriz de doc 02 §2.4 desde el cierre de **PD-03** (2026-10-06), pero el código de la respuesta sigue sin fijar. | doc 02 §2.1.1; §2.7; PD-03 |
| CU y transiciones afectados | Todos los CU con fila de permiso de los docs 05 (5.1–5.10) y 06 (6.1–6.5) | doc 02 §2.4; doc 05 §5.11 |
| Qué se pierde | La operación solicitada y, si la interfaz no explica el motivo, la salida para el usuario. No se pierden datos ni se ejecuta el service. | §2.7 |
| Mitigación y quién la verifica | Los permisos viajan en el payload del access token, así que la verificación es local al backend y no depende de una consulta; el reparto rol × permiso de doc 02 §2.4 es la matriz **definitiva** desde el cierre de **PD-03** (2026-10-06). **Quién verifica:** el backend antes de delegar al service; una prueba de integración por cada par (rol, endpoint) de la matriz. El código de la respuesta sigue **PENDIENTE**. | §2.1; doc 02 §2.4; PD-03 |
| Escenario (Given/When/Then) | **Given** un Alumno autenticado con el módulo `sigme_mobile` asignado; **When** llama un endpoint de `/api/v1/sigme` protegido por `mesa.crear`; **Then** `require_permiso()` rechaza la operación sin ejecutar el service y sin modificar ninguna fila, y el código HTTP devuelto es **PENDIENTE** (§2.7, doc 02 §2.1.1; el cierre de PD-03 2026-10-06 no fijó código). | §2.7; doc 02 §2.1.1; PD-03 |

### 7.2.4 Grupos, mesas y listados

**EX-16 — Mesa que quedó sin inscripciones activas**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-03 / S-11 — la última inscripción activa de una mesa pasa a `anulado` | doc 03 §3.3; RB-22 |
| Dueño | RB-22: todo listado y toda impresión devuelven únicamente las mesas con al menos una inscripción activa; el filtro está materializado en la vista `vw_mesa_con_alumnos`, que exige `EXISTS` de una inscripción con `estado = 'inscripto'` | RB-22; §3.18 |
| Respuesta HTTP declarada | Ninguna: es un **filtrado**, no una excepción. Ninguna respuesta 4xx ni 5xx. | RB-22; doc 04 §4.3 |
| CU y transiciones afectados | CU-19, CU-21, CU-23, CU-27, CU-28, CU-30, CU-34, CU-35, CU-36; evento S-03 | doc 05 §5.7, §5.10; doc 06 §6.2 |
| Qué se pierde | La mesa desaparece de la consulta y de la impresión, pero **no se borra ni cambia de estado**: queda ignorada. Si un listado la mostrara, el alumno creería que puede inscribirse en una mesa que ya nadie sostiene. | RB-22; doc 04 §4.3 |
| Mitigación y quién la verifica | El filtro vive en la vista y no en cada endpoint, así que se aplica también a la impresión masiva; la fila se conserva para auditoría. **Quién verifica:** el backend al excluir la mesa; el secretario al imprimir los reportes de cierre. | RB-22, RB-19; §3.18 |
| Escenario (Given/When/Then) | **Given** una mesa creada en un grupo cuya única inscripción activa fue anulada; **When** se consulta cualquier listado o se emite cualquier impresión; **Then** la mesa no aparece en la respuesta y la fila de `es_mesa_examen` sigue intacta (RB-22, S-03). | RB-22; S-03 |

**Pendiente propio de EX-16 — alcance de RB-22 en `GET /mesas-disponibles`.**
RB-22 dice "todo listado", pero su cláusula operativa describe las mesas
que **quedaron** con 0 alumnos (S-03). La vista `vw_mesa_con_alumnos` exige
al menos una inscripción activa, por lo que una mesa **recién creada** por
el secretario tampoco pasa ese filtro; si el endpoint de la ventana
aplicara RB-22 literalmente, ninguna inscripción podría iniciarse en las
mesas nuevas (RB-28, RB-31). **PENDIENTE (PD-23)**, heredado de doc 06 §6.8.

**EX-17 — Edición de un grupo con la ventana de inscripción abierta**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-16 / S-21 — `PATCH /grupos/{id}` cambia la `fecha` o la `hora` de un grupo | doc 03 §3.1, §3.3; RB-29 |
| Dueño | Rol con `mesa.modificar` (Secretario, Administrador, Superadmin); el grupo es la fuente de verdad del horario y todas sus mesas se mueven en la misma transacción | §6; RB-29; doc 04 GR-01 |
| Respuesta HTTP declarada | Ninguno para la operación en sí. Lo que **no** está declarado es si se **permite** hacerlo con la ventana abierta: **PD-12 PENDIENTE**. | RB-29; §7 PD-12 |
| CU y transiciones afectados | CU-15, CU-16, CU-35, CU-38; transiciones GR-01 y ME-01; eventos E-16 y S-21 | doc 05 §5.6; doc 06 §6.2, §6.4 |
| Qué se pierde | La fecha y la hora que el alumno ve cambian sin ninguna intervención suya: una inscripción tomada confiando en ese horario queda desactualizada. No hay ninguna notificación que lo avise, porque todos los envíos nacen de una acción de usuario y en v1 no hay job programado. | RB-29, RB-24; PD-12 |
| Mitigación y quién la verifica | La única mitigación declarada es la transacción única: grupo y mesas nunca quedan desfasados entre sí (RB-29). Sobre el efecto hacia los alumnos ya inscriptos **no hay mitigación declarada** hasta cerrar PD-12. **Quién verifica:** el secretario revisando la convocatoria; **bloqueada** hasta que el usuario decida PD-12. | RB-29; §7 PD-12 |
| Escenario (Given/When/Then) | **Given** una convocatoria con la ventana de inscripción abierta y un grupo con 3 mesas, algunas con inscripciones activas; **When** el secretario cambia la `hora` del grupo; **Then** las 3 mesas quedan con la nueva hora en la misma transacción (RB-29) y qué les ocurre a los alumnos ya inscriptos sigue **PENDIENTE (PD-12)**. | RB-29; PD-12 |

**EX-18 — Choque de unicidad al crear grupos o mesas**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | E-15 / S-01 — `POST /grupos` o `POST /mesas` traen una combinación que ya existe: `uq_mesa_unica` con `deleted_at IS NULL`, cuya composición **[CERRADA — 2026-10-06]** es `(convocatoria_id, materia_id, condicion_id, fecha)` (PD-13, con migración del índice) | §3.18; doc 03 §3.1; doc 04 ME-01 |
| Dueño | El índice único de la base y la transacción única del alta masiva; la creación es exclusiva del secretario con `mesa.crear` | §3.18, §3.22; RB-28; doc 04 ME-01 |
| Respuesta HTTP declarada | Mesas: **ninguno declarado → PENDIENTE** (§6 no anota código para el choque de `uq_mesa_unica`). Grupos: colisión de `uq_grupo_unico` → `409` (**PD-16**, cerrado 2026-10-06). | §6; §3.18; PD-16 |
| CU y transiciones afectados | CU-15, CU-16, CU-30; transiciones GR-01 y ME-01; evento S-01 | doc 05 §5.6; doc 04 ME-01 |
| Qué se pierde | La creación completa del grupo. El riesgo real no es el dato sino la **atomicidad**: si la validación y la inserción de las N mesas no están en la misma transacción, podría quedar un grupo con un subconjunto de sus mesas. | RB-28, S-01 |
| Mitigación y quién la verifica | El índice rechaza la fila duplicada y el alta se declara en una sola transacción; las dos preguntas están **[CERRADAS — 2026-10-06]**: `uq_mesa_unica` gana `convocatoria_id` y sigue **sin** `hora` (PD-13), y `es_grupo_horario` pasa a `uq_grupo_unico (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` con colisión → `409` (PD-16), ambas con migración. **Quién verifica:** el backend al abortar la transacción; una prueba de integración que envía dos altas idénticas. El código del choque de `uq_mesa_unica` sigue **PENDIENTE**. | §3.18, §3.22; PD-13, PD-16 |
| Escenario (Given/When/Then) | **Given** una convocatoria con un grupo de la fecha F que ya incluye la mesa Materia M × Condición Previa; **When** el secretario envía otro `POST /grupos` que vuelve a incluir esa misma combinación para la fecha F; **Then** `uq_mesa_unica` rechaza la inserción, no queda ningún grupo a medias y el código HTTP del rechazo sigue **PENDIENTE**; si la única diferencia está en la `hora`, la combinación ya no colisiona (PD-13, 2026-10-06: `hora` queda fuera de la clave) y dos grupos con la misma convocatoria, fecha y hora chocan en `uq_grupo_unico` con `409` (PD-16). | §3.18; PD-13, PD-16 |

**EX-19 — Grupo borrado con mesas vivas que lo referencian**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | GR-02 — se marca `deleted_at` en `es_grupo_horario` mientras existen mesas con `grupo_id` NOT NULL | doc 04 GR-02; §3.22 |
| Dueño | **PENDIENTE** para el permiso `mesa.eliminar` (Secretario está en celda `PENDIENTE` de doc 02 §2.4; **PD-03** se cerró el 2026-10-06 sin cubrir ese hueco); §6 **no expone** operación de baja de grupos: sólo `POST`, `PATCH` y `GET` | §6; doc 04 GR-02; PD-03 |
| Respuesta HTTP declarada | Ninguno: no hay endpoint de baja declarado en §6. **PENDIENTE** | §6; doc 05 CU-18 |
| CU y transiciones afectados | CU-17, CU-18 (pendiente sin endpoint), CU-30; transición GR-02 | doc 05 §5.6 |
| Qué se pierde | **[CERRADO — 2026-10-06]**, PD-18: el borrado lógico del grupo arrastra en la misma transacción el borrado lógico de todas sus mesas, así que ninguna mesa queda apuntando a un grupo borrado. Lo que ninguna fuente declara es si `vw_mesa_con_alumnos` mira también el `deleted_at` del grupo. | PD-18, RB-22 |
| Mitigación y quién la verifica | El **borrado físico** está impedido por `ON DELETE RESTRICT` mientras haya mesas (y el error 23503 se evita por diseño); el **lógico** resuelve PD-18 con cascada lógica transaccional: si alguna mesa tiene inscripciones activas, la operación entera falla y no se borra nada. **Quién verifica:** el backend al rechazar el borrado físico y al abortar la cascada lógica; una prueba de integración sobre ambas rutas. El permiso `mesa.eliminar` y su endpoint siguen **PENDIENTES**. | §1.8, §3.18, §3.22; S-17; PD-18 |
| Escenario (Given/When/Then) | **Given** un grupo `vigente` con 5 mesas, tres de ellas con inscripciones activas; **When** alguien intenta borrar el grupo; **Then** el borrado físico está impedido por `ON DELETE RESTRICT` (§1.8) y, con el borrado lógico, la cascada transaccional **falla entera** porque las tres mesas tienen inscripciones activas — no se borra nada (PD-18, 2026-10-06). | §1.8, §3.22; PD-18 |

**EX-20 — Estados de la mesa sin disparador declarado**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-10 — con la regla temporal **[CERRADA — 2026-10-06]**, el paso de la jornada de rendición no escribe nada: `planificada → cerrada → realizada` se **constata al leer** cuando la `fecha`/`hora` de la mesa pasó; el valor `acta_cerrada` ni siquiera existe en el `CHECK` de §3.18 | doc 03 §3.3; §3.18; G-05 |
| Dueño | **G-05 [RESUELTA — 2026-10-06].** ME-03 y ME-04 no tienen dueño ni permiso porque nadie escribe el estado: la constatación es del calendario (RN-005, sin job); ME-05 arranca desde un valor fuera del `CHECK` (opciones (i)/(ii) de doc 04 §4.2). | doc 04 ME-03, ME-04, ME-05; doc 01 §1.5.2 |
| Respuesta HTTP declarada | Ninguna: ninguna ruta de §6 cambia el estado de la mesa. El `PATCH /mesas/{id}` sólo actualiza la **asignación** (materia o condición) y con ella los snapshot. | §6; RB-11 |
| CU y transiciones afectados | CU-22 (cerrado 2026-10-06: constatación sin escritura), CU-20, CU-29; transiciones ME-03, ME-04, ME-05 | doc 05 §5.7; doc 04 §4.2 |
| Qué se pierde | Las mesas cuya `fecha`/`hora` pasó dejan de listarse y los reportes leen el estado derivado, no una marca escrita. Lo que **no** se pierde es el resultado: el acta es papel y el sistema no guarda notas ni asistencia. Queda sin declarar la frontera entre `cerrada` y `realizada`. | G-05, RB-19, RB-21, RB-18 |
| Mitigación y quién la verifica | **[CERRADA — 2026-10-06]**, G-05: la constatación se calcula **al leer** en `America/Argentina/Buenos_Aires`, sin escritura ni job (RN-005). **Quién verifica:** el backend en cada lectura de listado; una prueba que avanza el reloj hasta la `fecha`/`hora` de la mesa y comprueba que desaparece del listado. ME-05 sigue dependiendo de las opciones (i)/(ii) del estado de acta. | G-05; RN-005; doc 04 §4.2 |
| Escenario (Given/When/Then) | **Given** una mesa `planificada` en la fecha que copió de su grupo; **When** llega el cierre de la jornada; **Then** el estado almacenado no cambia (`planificada` en `es_mesa_examen`) pero la lectura deriva el estado según la fecha y la mesa vencida deja de listarse (G-05, 2026-10-06; RB-21, doc 04 ME-03, ME-04). | G-05; RB-21 |

### 7.2.5 Notificación y degradación

**EX-21 — Cola de email con fallo de envío**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | S-20 — un evento de usuario (confirmación de inscripción con fecha y hora, acuse de preinscripción, password reset) encola un email y el proveedor falla **después** de la respuesta HTTP | doc 03 §3.3; RB-24, RB-25 |
| Dueño | RB-25: la cola de email es **obligatoria desde v1**, con reintento y registro del estado de envío. No es una decisión opcional: sin ella no funciona el password reset (**[CERRADO — 2026-10-06]**, PD-04: `us_password_reset` desde v1, email por la cola). El contrato de reintento de la cola no queda resuelto en PD-04. | RB-25, PD-04 |
| Respuesta HTTP declarada | **Ninguno declarado → PENDIENTE.** RB-25 habla de estado de envío y reintento **en la cola**, no de una respuesta; ninguna fuente fija un código para un fallo de entrega. | RB-25; S-20 |
| CU y transiciones afectados | CU-42, CU-37, CU-26; evento S-20 | doc 06 §6.7; doc 03 §3.4 |
| Qué se pierde | Un email de password reset perdido deja al usuario sin recuperación posible — ése es el motivo de que la cola sea obligatoria. Un email de confirmación perdido deja al alumno sin constancia escrita de su fecha y hora de rendir. | RB-25, RB-24, PD-04 |
| Mitigación y quién la verifica | Reintento y registro de estado exigidos por RB-25; además, la información de la inscripción es observable dentro del sistema (`GET /mis-inscripciones`) y la ventana, con `GET /convocatoria-vigente` — el email no es la única vía para enterarse. **Quién verifica:** el backend al registrar el estado del envío; una prueba de integración con un proveedor que falla el primer intento. | RB-25, RB-26; doc 06 CU-38 |
| Escenario (Given/When/Then) | **Given** un `POST /inscripciones` exitoso que dispara el email de confirmación con fecha y hora (S-20); **When** el proveedor de email rechaza el primer intento; **Then** la cola registra el estado y reintenta (RB-25), la respuesta HTTP de la inscripción ya se había devuelto con éxito y ninguna fila de `es_mesa_inscripcion` cambia por el fallo del envío. | RB-25; S-20 |

**EX-22 — Registro del token de push**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | El alumno instala o renueva SIGME-M y el cliente necesita dar de alta o dar de baja el token en `us_dispositivo` | §6, §4; RB-24 |
| Dueño | RB-24 declara la infraestructura (alta, refresco y purga de caducos); los endpoints de alta y baja ya están en §6 y sólo alcanzan al **dispositivo propio** del alumno autenticado — sin permiso nuevo | RB-24; §6; PD-26 |
| Respuesta HTTP declarada | **Declarado:** `POST /dispositivos` → `201 { id }` y `DELETE /dispositivos/{id}` bajo `/api/v1/sigme-mobile` — **PD-26 cerrado** en `analisis.txt` §6 (heredado de doc 06 §6.8). La purga de caducos sigue siendo infraestructura del backend. | §6; doc 06 §6.8; PD-26 |
| CU y transiciones afectados | CU-42 | doc 06 §6.7 |
| Qué se pierde | Sin tokens registrados no puede entregarse ninguna push de apertura o cierre de ventanas: el alumno se entera sólo al entrar a la app, que es justamente lo que RB-24 quería evitar. | RB-24 |
| Mitigación y quién la verifica | Las otras dos notificaciones de RB-24 (email y campanita in-app) no dependen de `us_dispositivo`, así que el sistema no queda sin canal; la purga de tokens caducos está prevista en la propia infraestructura. **Quién verifica:** el backend al persistir el alta o la baja del token del alumno autenticado; una prueba que registra y da de baja el mismo dispositivo. | RB-24, RB-25; §6 |
| Escenario (Given/When/Then) | **Given** un alumno con la app instalada que registró su token con `POST /dispositivos` y el backend emitiendo la notificación de cierre de ventanas (S-20); **When** intenta entregar el push; **Then** sólo llega a los dispositivos cuyo token ya está en `us_dispositivo`, y `DELETE /dispositivos/{id}` retira el propio sin tocar los demás (RB-24, §6). | RB-24; doc 06 §6.8; PD-26 |

**EX-23 — Operación sin conexión (RB-26)**

| Campo | Contenido | Fuente |
|---|---|---|
| Disparador | El alumno intenta inscribir o anular con el teléfono sin datos, o con la sesión ya vencida | RB-26; doc 02 §2.1.2 |
| Dueño | RB-26: lectura con caché sin red ni token, escritura siempre online y **ninguna cola de acciones offline** | RB-26; plan P-07 (resuelta) |
| Respuesta HTTP declarada | **Sin request:** la falla ocurre en el cliente y nada llega al backend. Cuando **hay** red pero la sesión venció, la escritura recibe `401` (EX-11). | RB-26; T-07; doc 06 §6.6 |
| CU y transiciones afectados | CU-37, CU-39, CU-40, CU-41 | doc 06 §6.6 |
| Qué se pierde | La oportunidad de inscribirse si el cierre de ventana ocurre mientras el alumno está sin red: RB-17 y RB-23 no esperan a nadie, y no hay ninguna cola que lo resuelva. Ése es exactamente el motivo por el que RB-26 prohíbe la cola offline. | RB-26, RB-17, RB-23 |
| Mitigación y quién la verifica | La caché sirve las tres lecturas con su "última actualización" y **nunca** decide ventana, unicidad ni límite de condición; el aviso de apertura y cierre de ventanas llega por push (RB-24). **Quién verifica:** el backend al exigir sesión válida en toda escritura; el alumno al ver la marca de desactualización en pantalla. | RB-26, RB-23, RB-08, RB-03; doc 06 CU-41 |
| Escenario (Given/When/Then) | **Given** un alumno con la última respuesta de `GET /mesas-disponibles` en caché y el teléfono sin datos; **When** abre la pantalla de mesas, y luego toca "inscribirse"; **Then** la lectura se muestra con su fecha de "última actualización" sin llamar al backend y sin exigir token, mientras que la escritura falla en el cliente, no se encola ninguna operación offline y debe reintentarse con red y sesión válidas (RB-26). | RB-26; doc 06 CU-41 |

---

## 7.3 Ventana temporal: semántica de cierre, reloj y desfasaje

Tres constantes gobiernan todos los estados de 7.2.1 y se repiten aquí porque
son la base de EX-01, EX-02, EX-04, EX-05 y EX-09.

| Constante | Qué obliga | Fuente |
|---|---|---|
| **Límite inclusivo** | `fecha_fin_inscripcion` se respeta hasta las **23:59:59** de ese día inclusive; a las 00:00:00 del día siguiente ya cambió de fecha y la operación está cerrada. Vale igual para `fecha_inicio_inscripcion` y para `pr_ventana`. | RB-23; doc 03 §3.2 |
| **Comparación por fecha de calendario** | Se compara `current_date` (con la zona del backend, `America/Argentina/Buenos_Aires`) contra la columna `date`; **no** se usa un timestamp crudo de UTC ni se suman horas. | RB-23; doc 06 §6.6 |
| **Reloj autoritativo** | Decide el backend, nunca el dispositivo: el alumno con el celular desfasado no adelanta ni atrasa la ventana. | RB-23; doc 02 §2.1.2 |
| **Sin scheduler en v1** | Ningún cierre se dispara a una hora fija: se **constata** en cada request. RB-24 declara que todos los envíos nacen de una acción de usuario y PD-11 deja el recordatorio de 48 h fuera de v1. | RB-24, PD-11; doc 03 §3.2 |
| **Identidad de la ventana de la landing** | Una sola ventana vigente por año (`uq_ventana_anio`), leída desde `vw_ventana_vigente` (`activa`, sin `deleted_at` y cuyo rango contiene `current_date`). | §3.21; RB-14 |

| Instante | Ventana de inscripción (convocatoria) | Ventana de preinscripción (landing) | Fuente |
|---|---|---|---|
| 23:59:59 de la última fecha | Inscripción y anulación **permitidas** (EX-01 no aplica) | `POST /landing/preinscripcion` aceptado | RB-23, RB-08b; RB-14 |
| 00:00:00 del día siguiente | Cerrada: sólo consulta de la fecha de rendir; `POST /inscripciones` → `409`, `DELETE` → **PENDIENTE** | `409 { code: "ventana-cerrada" }` | RB-07, RB-17; §6; RB-14 |
| Reloj del dispositivo desfasado | **Sin efecto:** la decisión es del backend | **Sin efecto** | RB-23; doc 02 §2.1.2 |

**Abierto en este dominio: PD-17.** `grupo.hora` es una columna `time` **sin
zona horaria** y RB-23 evalúa por fecha de calendario; cómo se interpreta
`hora` al combinarse con `fecha` sigue sin declararse, y por lo tanto el
límite de EX-01 para una mesa de la última franja horaria del día queda
también sin cerrar. No se resuelve en este documento.

---

## 7.4 Concurrencia: unicidad, bloqueos e idempotencia

### 7.4.1 Semántica de reintento por operación (E-13)

Los docs 06 §6.6 y 11 §11.4.1 ya declararon la semántica de las operaciones
que un cliente reintenta. Esta tabla la consolida y agrega las que seguían
sin declaración.

| Operación | Efecto de un reintento | Garantía | Fuente |
|---|---|---|---|
| `POST /auth/login` | No idempotente pero inocuo para los datos de negocio: crea su propia fila de sesión o suma al rate limit (EX-13) | Cada intento es independiente; 5 fallos en 15 minutos → `429` + `Retry-After` y bloqueo de 15 minutos (PD-27) | §2.4; §6; doc 06 §6.6 |
| `POST /auth/refresh` | **No idempotente**: la rotación revoca el refresh anterior; un reintento con la respuesta perdida dispara la reuse detection (EX-12) | Revoca toda la familia y exige login nuevo | §2.2; doc 06 §6.6 |
| `GET /convocatoria-vigente`, `GET /mesas-disponibles`, `GET /mis-inscripciones` | Idempotentes: misma respuesta; sin red, el cliente sirve su caché sin llamar al backend (EX-23) | Reintento seguro | RB-26; doc 06 §6.6 |
| `POST /inscripciones` | Reintento seguro **sin duplicar**: si la fila ya existe, `uq_inscripcion_unica` responde `409` y no se crea otra (EX-06) | Índice único por convocatoria × alumno × materia | RB-08, §6; doc 06 §6.6 |
| `DELETE /mis-inscripciones/{id}` | El **efecto** es nulo: la fila ya está `anulado` y sigue `anulado` (EX-10); la respuesta repetida devuelve `204 No Content`, igual que la primera (PD-25) | Fila fuera del índice único; no altera la unicidad | RB-08b, §3.19; §6; doc 06 §6.8 |
| `POST /landing/preinscripcion` | Upsert sobre `(anio_lectivo, documento)`: `201` la primera vez, `200` en reenvíos; **nunca** `409` ni error por duplicado (EX-03) | `uq_preinscripcion_unica`; dos envíos simultáneos **no deben producir `500`** | RB-13, §3.20; doc 11 §11.4.1 |
| `POST /grupos`, `POST /mesas` | Mesas: **sin declaración** para el choque de `uq_mesa_unica` (EX-18); grupos: la colisión de `uq_grupo_unico` responde `409` (PD-16) | Índice único + alta en una sola transacción | §3.18; PD-13, PD-16 (cerrados 2026-10-06) |

### 7.4.2 Índices únicos y bloqueos

| Mecanismo | Qué impone | Estado | Fuente |
|---|---|---|---|
| `uq_inscripcion_unica (convocatoria_id, usuario_id, materia_id) WHERE deleted_at IS NULL AND estado <> 'anulado'` | La unicidad es por **materia × convocatoria**, no por mesa; la fila `anulado` no ocupa y libera la materia para reinscribirse | Declarado | §3.19; RB-08, RB-08b |
| `uq_mesa_unica (convocatoria_id, materia_id, condicion_id, fecha) WHERE deleted_at IS NULL` | Impide dos mesas de la misma materia y condición en la misma fecha **y convocatoria** | **[CERRADO — 2026-10-06]** (PD-13): gana `convocatoria_id`, sigue **sin** `hora`; migración del índice | §3.18 |
| `uq_preinscripcion_unica (anio_lectivo, documento)` | Una sola fila por identidad y por año lectivo; hace seguro el reintento de la landing | Declarado | §3.20; RB-13 |
| `uq_ventana_anio (anio_lectivo)` | Una sola ventana de preinscripción por año | Declarado | §3.21; RB-14 |
| `uq_usuario_username`, `uq_usuario_email` (parciales) | Username y email únicos entre filas no borradas, de modo que el soft delete deja el valor libre | Declarado | §3.5, §1.7 |
| `uq_grupo_unico (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` | Impide grupos duplicados idénticos en la misma convocatoria; la colisión responde `409` | **[CERRADO — 2026-10-06]** (PD-16); migración del índice | §3.22 |
| `require_permiso()` antes del service | Rechaza la operación sin ejecutar la lógica de negocio (EX-15) | Declarado, código **PENDIENTE** | §2.7 |
| Bloqueo temporal (`bloqueado_hasta`) | Cinco fallos de login en 15 minutos bloquean la cuenta (EX-13) | Declarado, duración **15 minutos** con `429` + `Retry-After` (PD-27) | §2.4; §6 |
| Reuse detection del refresh | Revoca toda la familia de tokens ante un refresh reutilizado (EX-12) | Declarado | §2.2 |
| `token_version` | Invalida de golpe todos los access tokens emitidos (EX-14) | Declarado, código **PENDIENTE** | §2.6 |
| Recálculo del snapshot en la misma transacción | Ante una edición concurrente de la asignación de la mesa, el snapshot no queda a medio actualizar | Declarado | RB-11; doc 02 §2.1.1 |
| `ON DELETE RESTRICT` explícito en cada FK | Impide perder referencias: el borrado se rechaza antes de producir el error 23503 | Declarado | §1.8; S-17 |

**Observación de índice, ya resuelta.** `uq_mesa_unica` no incluía
`convocatoria_id`: sólo cubría materia, condición y fecha, de modo que
rechazaba una mesa válida de la convocatoria B por existir una de la A,
contra RN-007. **PD-13** lo cerró el 2026-10-06 agregando `convocatoria_id`
(con migración del índice) y manteniendo `hora` fuera de la clave.

---

## 7.5 Integridad de los datos históricos

El riesgo estructural: los nombres que el usuario ve hoy no son los que
estaban cuando se creó la fila. La respuesta del modelo es el **snapshot**
más la **convención de ciclo**.

| Riesgo | Qué se pierde si no se mitiga | Mitigación declarada | Fuente |
|---|---|---|---|
| Renombrar una materia, curso, orientación o condición | Las mesas históricas dejarían de mostrar el nombre con el que fueron creadas y los reportes impresos cambiarían retroactivamente | Los 4 snapshot (`orientacion_nombre`, `curso_nombre`, `materia_nombre`, `condicion_nombre`) se recalculan **sólo** al editar la asignación de la mesa, en la misma transacción; **nunca** por un renombre de la tabla origen | RB-11, RB-12; §3.18 |
| Leer el catálogo en lugar del snapshot | Los reportes dependerían del nombre vigente y no del nombre de la época | No existe vista `v_mesa_examen`: los reportes leen directamente las columnas snapshot y usan las FK sólo para filtrar y navegar | RB-12 |
| Renombrar el catálogo sin endpoint declarado | El renombre quedaría fuera de contrato mientras el efecto se materializa como `PATCH` | **PENDIENTE (PD-21):** §6 declara sólo `GET` y `POST` en esas colecciones | §6; PD-21; doc 03 S-09 |
| Reutilizar filas entre campañas | Los datos de una convocatoria se mezclarían con los de la siguiente | Convención de ciclo: cada convocatoria nueva nace con grupo, mesas e inscripciones **nuevas**; las filas viejas quedan intactas (RB-16) | RB-16; doc 04 ME-06 |
| Revalidar después del cierre | Se modificaría una lista que ya se había declarado definitiva | Lista fija al cerrar la ventana: no se revalida nada el día de rendir y no se registra asistencia | RB-17, RB-18 |
| Guardar el resultado de la mesa | Aparecerían estados de nota o de aprobación que el sistema no modela | `es_mesa_inscripcion` sólo admite `inscripto` y `anulado`; el resultado vive en el acta en papel | RB-21; §3.19 |
| Borrar filas referenciadas | Se perderían personas o materias de las que dependen inscripciones y mesas | FK con `ON DELETE` explícito y `RESTRICT` en las referencias que no se pueden perder; soft delete con índices parciales para poder reinsertar | §1.8, §1.7, §1.5; S-17 |
| Columna de fecha común retirada del modelo | Se reintroduciría un atributo que ya no existe | **PD-14 resuelto:** la columna se elimina; cada grupo declara su `fecha` y su `hora` y la mesa copia ese par | PD-14; RB-27, RB-29 |

---

## 7.6 Degradación y recuperación

Qué sigue funcionando cuando algo no está disponible, y cómo se vuelve a
operar. Reproduce lo declarado en RB-26, RB-25 y en los estados de sesión de
7.2.3.

| Fallo | Qué sigue funcionando | Recuperación declarada | Fuente |
|---|---|---|---|
| **Sin red** | Las tres lecturas de SIGME-M desde la caché local, con su "última actualización" | Reintento online de la escritura; **no** hay cola de acciones offline que reconciliar | RB-26; doc 06 CU-41 |
| **Access token vencido** | La lectura en caché del cliente, sin llamar al backend | `POST /auth/refresh` y reintento de la operación (EX-11) | T-07; RB-26 |
| **Refresh vencido o reutilizado** | Ninguna operación autenticada | Login nuevo: la familia entera quedó revocada (EX-12) | §2.2; doc 04 SES-04 |
| **Cuenta bloqueada por rate limit** | La caché local; ninguna escritura | Esperar el vencimiento de `bloqueado_hasta` (T-09 / US-03); duración fijada en 15 minutos y `429` + `Retry-After` en la respuesta (PD-27) | §2.4; §6; doc 04 US-03 |
| **Proveedor de email caído** | Todo el resto del sistema: la respuesta HTTP de la operación que disparó la notificación ya se devolvió | Reintento y registro de estado en la cola, obligatorios desde v1 (EX-21) | RB-25 |
| **Servicio push caído o token caducado** | Email y campanita in-app, que no dependen de `us_dispositivo` | Refresco y purga de tokens caducos; alta y baja de tokens declaradas en §6 (PD-26, EX-22) | RB-24; §6; doc 02 §2.1.2 |
| **Tabla o consulta de catálogo incompleta** | Las escrituras ya existentes; las mesas creadas conservan su snapshot | Ninguna: es un hueco de datos, no de servicio — la cobertura RB-31 y su origen de pares siguen **PENDIENTE (PD-15)** | RB-31; PD-15, PD-20 |
| **Job programado inexistente (v1)** | Nada se atrasa: no hay tareas pendientes que se caigan | El recordatorio de 48 h está **deferido a v2 (PD-11)**; todos los envíos nacen de una acción de usuario | RB-24, PD-11 |

**Lo que la degradación nunca habilita.** RB-26 prohíbe de forma explícita
que la caché sirva para decidir ventana, unicidad o límite de condición: un
cliente desactualizado no puede validar ninguna de esas tres reglas. Ésa es
la frontera entre operar degradado y operar mal.

---

## 7.7 Consolidado de códigos HTTP

### 7.7.1 Códigos declarados por alguna fuente

| Código | Cuándo dispara | Endpoint | Fuente |
|---|---|---|---|
| `201 Created` | Identidad `(anio_lectivo, documento)` inexistente dentro de la ventana de preinscripción → INSERT | `POST /landing/preinscripcion` | §6; RB-13 |
| `200 OK` | La identidad ya existía → UPDATE de los campos mutables | `POST /landing/preinscripcion` | §6; RB-13 |
| `409 Conflict` `{ code: "ventana-cerrada" }` | Fuera de la ventana de preinscripción; y **sólo** eso en este endpoint | `POST /landing/preinscripcion` | §6; RB-14 |
| `422 Unprocessable Entity` `{ code: "validacion", errors[] }` | Payload inválido (falta un campo, `null`, formato inválido) | `POST /landing/preinscripcion` | §6; O-2 |
| `429 Too Many Requests` | Ráfaga de envíos (rate limit estricto anti-bots); el cuerpo es la envolvente única de `analisis.txt` §6 (PD-24) | `POST /landing/preinscripcion` | §6, §2.9; doc 11 §11.4.2 |
| `409 Conflict` | Materia ya inscripta en la convocatoria, **o** ventana de inscripción cerrada | `POST /inscripciones` | §6; S-06; RB-08 |
| `409 Conflict` | Choque de `uq_grupo_unico` al crear grupos idénticos (misma convocatoria, fecha y hora) | `POST /grupos` | §7 PD-16 (cerrado 2026-10-06) |
| `204 No Content` | `DELETE` exitoso **y** su repetición sobre una fila ya `anulado`: idempotente y sin cuerpo (PD-25) | `DELETE /mis-inscripciones/{id}` | §6; RB-08b; doc 04 INS-02 |
| `401 Unauthorized` | Access token vencido en una acción protegida; citado también ante T-08 y S-14 | Cualquier endpoint protegido | T-07; doc 02 §2.1.2; doc 05 §5.1 |
| `429 Too Many Requests` **y** bloqueo temporal | Rate limit de login (5 fallos en 15 minutos): **ambos**, no uno u otro — `Retry-After` con los segundos y bloqueo de 15 minutos (PD-27) | `POST /auth/login` | E-14; §2.4; §6 |
| `500` | **Sólo como prohibición explícita:** dos envíos simultáneos de la landing con el mismo documento no deben producirlo | `POST /landing/preinscripcion` | doc 11 §11.4.1; §3.20 |

> **Nota de verificación.** Fuera de esta tabla, `analisis.txt` y los
> documentos 01–06 y 11 **no citan** `400`, `403`, `405`, `410` ni `202`
> en ninguna respuesta (el `204` sólo lo declara §6, PD-25). El único
> `404` que aparece en toda la fuente es como **candidato sin elegir**
> dentro de PD-19. No se usan hasta que un contrato los declare.

### 7.7.2 Casos sin código declarado → PENDIENTE

| Caso | Qué dice la fuente | Hueco que lo mantiene abierto | Fuente |
|---|---|---|---|
| Convocatoria inactiva o fuera de su ventana | "Rechazo: no se inscribe" | Sin código en §6 | RB-09, S-07 |
| Límite de materias por condición | "Rechazo de la inscripción" | Sin código en ninguna fuente; PD-02 (cerrado 2026-10-06) fijó los valores, no el código | RB-03, S-05; PD-02 |
| Anulación fuera de la ventana | "Rechazo; sólo consulta" | Sin código en §6 | RB-07, RB-08b |
| Combinación materia × condición sin mesa | "Rechazo" sin código; candidatos `404, 409, 422` | **PD-19** | §7; RB-31 |
| Usuario sin el permiso del endpoint | "Respuesta de prohibición" sin código | El mapeo endpoint → permiso ya sale de la matriz de doc 02 §2.4 (PD-03 cerrado 2026-10-06); ninguna fuente fija el código | doc 02 §2.1.1; §2.7; PD-03 |
| Access token con `ver` vencido | El token "deja de servir"; sin código | **S-15 / §2.6** no fijan respuesta | §2.6; S-15 |
| Refresh vencido o reutilizado | "Se exige login nuevo" (código citado desde T-07) | T-08 y S-14 no declaran código por su cuenta | §2.2; T-08, S-14 |
| Choque de `uq_mesa_unica` | Sin anotación en §6 | Sigue sin código: PD-13 (2026-10-06) definió la clave, no el código | §3.18; PD-13 |
| Baja de un grupo con mesas vivas | Sin endpoint en §6 | PD-18 cerró el 2026-10-06 la cascada lógica; el endpoint y el permiso `mesa.eliminar` siguen sin declarar | §6; PD-18, PD-03 |
| Estados de la mesa (`planificada → cerrada → realizar`) | Sin operación declarada en §6 | **Sin hueco:** G-05 resuelta 2026-10-06 — la constatación es al leer, no hay operación ni código | §3.18; doc 04 ME-03…ME-05 |
| Alcance de RB-22 en `GET /mesas-disponibles` | "Todo listado" vs. la cláusula de mesas que quedaron con 0 alumnos | **PD-23** (doc 06 §6.8) | RB-22; S-03 |

---

## 7.8 Consolidado de pendientes heredados

Ninguno de estos identificadores se cierra en este documento. Se listan con
el estado crítico que los hace visibles, para que los documentos 08, 09 y 10
los hereden trazados; los que ya tienen decisión en `analisis.txt` §7 se
conservan marcados **[CERRADO — 2026-10-06]** (o **[RESUELTA]** para G-05)
sin renumerar.

| ID | Pregunta abierta | Estado que la hace visible | Fuente |
|---|---|---|---|
| **PD-02** | **[CERRADO — 2026-10-06]** — Valores de `es_condicion.limite_materias` (Previa 3, Regular 8, Libre sin límite; por convocatoria, editables desde SIGME) | EX-08 | `analisis.txt` §7; RB-03 |
| **PD-03** | **[CERRADO — 2026-10-06]** — Semilla de roles, permisos y usuarios en la migración inicial, con el reparto rol × permiso de la matriz doc 02 §2.4 | EX-04, EX-15, EX-19, EX-22 | `analisis.txt` §7; doc 02 §2.4 |
| **PD-04** | **[CERRADO — 2026-10-06]** — Reseteo de contraseña por email: `us_password_reset` desde v1, email por la cola obligatoria | EX-21 | `analisis.txt` §7; RB-25 |
| **PD-10** | Conjunto exacto de notificaciones in-app por rol | EX-21, EX-22 | `analisis.txt` §7; RB-24 |
| **PD-11** | Recordatorio de 48 h (deferido a v2; exige un job que v1 no tiene) | EX-21, 7.3, 7.6 | `analisis.txt` §7; RB-24 |
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana abierta? ¿qué efecto tiene sobre alumnos ya inscriptos? | EX-17 | `analisis.txt` §7; RB-29 |
| **PD-13** | **[CERRADO — 2026-10-06]** — `uq_mesa_unica` gana `convocatoria_id` y sigue sin `hora` | EX-18 | `analisis.txt` §7; §3.18 |
| **PD-15** | De dónde sale el conjunto esperado de pares materia × condición para la cobertura | 7.6 | `analisis.txt` §7; RB-31 |
| **PD-16** | **[CERRADO — 2026-10-06]** — `uq_grupo_unico (convocatoria_id, fecha, hora)` en `es_grupo_horario`, colisión → `409` | EX-18, 7.4.2 | `analisis.txt` §7; §3.22 |
| **PD-17** | Cómo se interpreta `grupo.hora` (`time` sin zona) al combinarse con `fecha` frente a RB-23 | 7.3 | `analisis.txt` §7; RB-23 |
| **PD-18** | **[CERRADO — 2026-10-06]** — Borrado lógico de grupo con cascada lógica transaccional; falla si alguna mesa tiene inscripciones activas | EX-19 | `analisis.txt` §7; doc 04 GR-02 |
| **PD-19** | Código HTTP del rechazo de `POST /inscripciones` sin mesa | EX-07, 7.7.2 | `analisis.txt` §7; RB-31 |
| **PD-21** | Renombrado de catálogo sin endpoint declarado | 7.5 | `analisis.txt` §7; doc 03 S-09 |
| **PD-22** | Efecto del `PATCH /preinscripciones` | 7.5, 7.7.2 | `analisis.txt` §7; doc 02 §2.1.1 |
| **PD-23** | Alcance de RB-22 sobre `GET /mesas-disponibles` | EX-16, 7.7.2 | `analisis.txt` §7; doc 06 §6.8 |
| **PD-28** | Paginación de `GET /mis-inscripciones` | 7.6, 7.7.2 | `analisis.txt` §7; plan §3.06 |
| **G-05** | **[RESUELTA — 2026-10-06]** — Nadie dispara el cambio de estado: es una constatación de calendario al leer | EX-05, EX-20 | doc 01 §1.5.2; doc 04 §4.6.2 |

---

## Checklist de cierre (7 · Estados críticos y excepciones)

- [x] **23 estados críticos con ID estable** (`EX-01`…`EX-23`), agrupados en
      cinco dominios que reproducen el plan §3.07: ventanas y convocatoria,
      inscripción, sesión y autorización, grupos y listados, notificación y
      degradación.
- [x] **Cada estado declara** las siete filas pedidas por el plan §3.07:
      disparador, dueño de la regla, respuesta HTTP, casos de uso y
      transiciones afectados, qué se pierde, mitigación con quién la verifica
      y escenario Given/When/Then.
- [x] **Cada estado tiene al menos un escenario Given/When/Then ejecutable**
      — criterio de cierre del plan §3.07; los que dependen de una decisión
      abierta declaran en el propio escenario qué condición falta.
- [x] **Ningún código HTTP inventado:** 7.7.1 lista los códigos que alguna
      fuente declara, con su endpoint y su fuente; 7.7.2 lista los casos sin
      declaración con el hueco que los mantiene abiertos. Verificado contra
      `analisis.txt` y los docs 01–06 y 11: `400`, `403`, `405`, `410` y
      `202` no aparecen en ninguna de esas fuentes (el `204` entra sólo con
      el cierre de PD-25 en §6; el único `404` es PD-19 sin elegir).
- [x] **Ventana temporal conforme a RB-23** (7.3): límite inclusivo hasta las
      23:59:59, comparación por fecha de calendario en
      `America/Argentina/Buenos_Aires`, reloj del backend por encima del del
      dispositivo, y sin job programado en v1.
- [x] **Concurrencia e idempotencia consolidadas** (7.4): semántica de
      reintento por operación para E-13 — con el `DELETE` repetido cerrado
      en `204` (PD-25) —, índice por índice con su estado — con PD-13 y
      PD-16 cerrados el 2026-10-06 (claves de unicidad) y el código del
      choque de `uq_mesa_unica` declarado como pendiente —, y los huecos
      restantes expuestos en lugar de suponerse.
- [x] **Integridad histórica y degradación cubiertas** (7.5 y 7.6):
      snapshot frente a renombre (RB-11, RB-12), convención de ciclo
      (RB-16), soft delete, y la frontera de RB-26 entre operar degradado y
      operar mal.
- [x] **Ningún `PD-xx` ni `G-xx` cerrado en este documento:** 7.8 lista los
      **17** pendientes heredados — los 15 previos más **PD-23** y **PD-28**,
      los dos huecos que este documento hace visibles—, cada uno con su
      estado; **7** de ellos (PD-02, PD-03, PD-04, PD-13, PD-16, PD-18 y
      G-05) se cerraron en `analisis.txt` §7 el 2026-10-06 y se conservan
      marcados sin renumerar; PD-24…PD-27 se cerraron en `analisis.txt`
      §6/§7.

## Siguiente paso

`08-reglas-de-negocio.md`: de aquí salen los invariants `RN-001…` con
identificador estable — cada regla que este documento usó para rechazar una
operación (ventana, unicidad por materia × convocatoria, límite de la
condición, lista fija, snapshot y cola de email) se formula allí con su
entidad afectada, su forma de violación y su forma de prevención; y cada
hueco marcado **PENDIENTE** en 7.7 y 7.8 queda expuesto para que la matriz
del doc 10 lo traze sin rebuscarlo.
