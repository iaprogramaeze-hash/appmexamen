# 09 · Requisitos no funcionales — Backend EPET36

**Respuesta corta:** este documento fija **54 requisitos no funcionales** con
identificador estable (`NFR-001`…`NFR-054`) para la API del backend: 12 en
rendimiento y disponibilidad, 15 en seguridad y privacidad, 11 en resiliencia,
9 en auditoría, trazabilidad e integridad y 7 en mantenibilidad y flexibilidad.
Cada fila es una **afirmación comprobable** con su método de verificación, su
fuente y uno de tres estados: **Medible** (la fuente ya da un número o una
condición comprobable), **`[POR DEFINIR]`** (el requisito existe pero ningún
número lo cierra) o **Propuesta** (número propuesto por este documento, todavía
no decidido por nadie; hoy ninguna fila está en este estado: las siete que lo
estuvieron fueron aprobadas por el mantenedor el 2026-10-05). Aplica la
taxonomía ISO/IEC 25010:2023 —nueve características— al **API**, no a las
interfaces: lo que corresponde a la pantalla queda separado en 9.6 como
requisito heredado a los proyectos futuros. **No se cierra ningún `PD-xx`
ni ningún `G-xx`** heredado de los docs 01, 06, 07, 08 y 11 (9.8).

Vocabulario: se respetan los términos de `01-glosario-y-alcance.md` (1.2 y
1.3, incluido el vocabulario prohibido y retirado), los actores y consumidores
de `02-actores-y-consumidores.md`, las reglas de `08-reglas-de-negocio.md`
(`RN-001`…`RN-059`), los estados críticos de
`07-estados-criticos-y-excepciones.md` (`EX-01`…`EX-23`) y el contrato de la
landing de `11-landing-preinscripcion.md`. Toda cita `RB-xx` y `PD-xx`
remite a `analisis.txt` (§4 y §7); `§n.m` remite a la sección de ese archivo;
`E-xx`, `S-xx` y `T-xx` remiten a doc 03; `G-xx` a doc 01 §1.5.2; `C-xx`,
`ME-xx`, `INS-xx`, `US-xx`, `SES-xx` y `GR-xx` a doc 04; `CU-xx` a los docs
05 y 06; `EX-xx` a doc 07; `RN-xxx` a doc 08; `O-x` a `analisis.txt` §3.20.

## Rápido recorrido

1. **9.1** — las nueve características de ISO/IEC 25010:2023 y cómo se aplican
   **al API**, con la sección y los `NFR-xxx` donde cada una se mide.
2. **9.2** — rendimiento y disponibilidad **con números**: latencia p95,
   concurrencia, presupuesto de errores, disponibilidad y límites de tasa.
3. **9.3** — seguridad y privacidad, con los plazos de la Ley 25.326 ya
   fijados por la fuente (10 días corridos, 5 días hábiles, log de accesos
   ≥ 3 años) y el reparto de art. 5, art. 6, art. 9, art. 14 y art. 16.
4. **9.4** — resiliencia: idempotencia por operación, backoff con jitter,
   reintentos, degradación controlada y reloj autoritativo.
5. **9.5** — auditoría, trazabilidad e integridad: qué queda registrado, en
   qué columnas y con qué retención.
6. **9.6** — requisitos heredados a los clientes (WCAG 2.2, WCAG2Mobile, UX de
   carga offline y los dos artículos de la Ley que quedaron en la interfaz),
   **en tabla propia** y marcados como obligación de proyectos futuros.
7. **9.7** — mantenibilidad y flexibilidad: estructura por dominio, análisis
   estático, tests, migraciones y configuración.
8. **9.8** — pendientes heredados: todo lo que sigue abierto, con el hueco que
   lo mantiene así.
9. **Checklist** — incluye la verificación del criterio de cierre del plan
   (plan §3, 09): ningún NFR queda sin número ni sin marcador, y los
   heredados están separados de los del backend.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Alcance** | Los requisitos del **backend**: la API, su configuración, su base de datos y su operación. Los tres consumidores (SIGME web, SIGME-M, landing) aparecen sólo como fuente de restricciones que el backend debe satisfacer. | plan §3 (09); doc 01 §1.1 |
| **Identificadores** | `NFR-001…` es una **serie local** de tres dígitos, **sin huecos y sin duplicados**, con **un requisito por fila**; empieza en `NFR-001` y no reutiliza ninguna serie ajena. Toda otra serie citada existe en su fuente: `RB-xx`/`PD-xx`/`§n.m`/`O-x` → `analisis.txt`; `E-xx`/`S-xx`/`T-xx` → doc 03; `G-xx` → doc 01 §1.5.2; `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` → doc 04; `CU-xx` → docs 05 y 06; `EX-xx` → doc 07; `RN-xxx` → doc 08. | plan §3 (09.1); doc 08 Convenciones |
| **Estado de una fila** | Tres valores posibles y ninguno más. **Medible**: la fuente declara un número o una condición comprobable. **`[POR DEFINIR]`**: el requisito es real y verificable, pero el número o el mecanismo no lo cierra ninguna fuente, y la fila nombra el hueco. **Propuesta**: el número lo sugiere este documento; no está decidido y debe tratarse como hipótesis hasta que alguien lo apruebe. | plan §3 (09.2, criterio de cierre); doc 01 §1.5.1 |
| **Números** | Un adjetivo sin número no es un requisito: por eso 9.2 no admite filas como "rápido" o "disponible". Donde la fuente no da número, la fila dice `[POR DEFINIR]`; donde el número es una sugerencia de este documento, dice **Propuesta**. | plan §3 (09.2) |
| **PENDIENTE** | Este documento **no cierra** ningún `PD-xx` ni ningún `G-xx`: los hereda visibles en 9.8. Los casos que no tenían ID hoy están anclados a `PD-23`…`PD-29` en `analisis.txt` §7. | doc 06 §6.8; doc 07 §7.8; doc 08 §8.5; `analisis.txt` §7 |
| **ISO/IEC 25010:2023** | Se aplica la edición **2023**, con **nueve** características: `Usability` y `Portability` de la edición 2011 fueron reemplazadas por `Interaction Capability` y `Flexibility`, y se agregó `Safety`. De las nueve, ocho se aplican **al API**; `Interaction Capability` mide la relación persona–sistema, así que se traslada a 9.6. | plan §3 (09.1); doc 01 §1.1 |
| **Vocabulario** | Se respetan los términos de doc 01 §1.2 y el vocabulario prohibido y retirado de §1.3: convocatoria ≠ mesa, preinscripción ≠ inscripción, grupo de mesas = fecha + hora, el alumno elige sólo materia + condición, sin "cupo", sin "matrícula", sin resultados ni asistencia. | doc 01 §1.2, §1.3; RB-01, RB-18, RB-21, RB-27 |
| **Verificación** | Cada fila declara **cómo se comprueba**: prueba de carga, prueba de integración contra la base real, consulta SQL sobre `information_schema`, inspección de configuración o revisión de código en CI. | plan §3 (09.2); `analisis.txt` §8 |

---

## 9.1 Taxonomía ISO/IEC 25010:2023 aplicada al API

Nueve características, aplicadas al API y no a las interfaces. La columna
"Dónde se mide" apunta a los `NFR-xxx` de este documento; las características
que no miden el API se trasladan a 9.6 para no perderlas.

| Característica (edición 2023) | Cómo se aplica al API | Dónde se mide | Fuente |
|---|---|---|---|
| **Adecuación funcional** (`Functional Suitability`) | El API hace exactamente lo que `analisis.txt` §6 declara: los mismos endpoints, los mismos códigos, y ninguna operación pública que la fuente no nombra. | NFR-024, NFR-028, NFR-029, NFR-036 | §6; RB-10, RB-13 |
| **Eficiencia de desempeño** (`Performance Efficiency`) | Tiempos de respuesta, tamaño de los payloads y concurrencia soportada, medidos sobre el API y no sobre la pantalla. | 9.2 — NFR-001…NFR-007 | plan §3 (09.2) |
| **Compatibilidad** (`Compatibility`) | Interoperabilidad con los tres consumidores: JSON y los códigos HTTP de §6, CORS con orígenes explícitos, y coexistencia de `pr_*` con el resto del esquema sin foreign keys. | NFR-012, NFR-022, NFR-023, NFR-025 | §2.9, §3.20, §1.1; plan §3 (11.2) |
| **Capacidad de interacción** (`Interaction Capability`) | **No aplica al API**: mide la relación persona–sistema, que sólo existe en las interfaces. Se traslada íntegra a 9.6 para que no se pierda. | 9.6, filas 1–3 | plan §3 (09.6); doc 01 §1.1 |
| **Confiabilidad** (`Reliability`) | Disponibilidad, presupuesto de errores y comportamiento ante fallos del proveedor de email o del cliente móvil. | NFR-004, NFR-005, NFR-033, NFR-034, NFR-035 | plan §3 (09.2); RB-25, RB-26 |
| **Seguridad** (`Security`) | Autenticación, autorización, manejo de secretos, límite de tasa, CORS y las obligaciones de la Ley 25.326 que recaen en el backend. | NFR-009, NFR-013…NFR-027, NFR-040 | `analisis.txt` §2; §3.20 |
| **Mantenibilidad** (`Maintainability`) | Estructura por dominio, análisis estático, tests y migraciones versionadas: todo comprobable sobre el repositorio, no sobre el producto en ejecución. | 9.7 — NFR-048…NFR-052 | `analisis.txt` §5, §8 |
| **Flexibilidad** (`Flexibility`) | El mismo código atiende a los tres consumidores y se configura por entorno sin tocar la lógica de negocio. | NFR-051, NFR-053, NFR-054 | `analisis.txt` §2.8; PD-06 |
| **Inocuidad** (`Safety`) | Fallos que no deben dañar datos ni dejar el sistema en un estado peligroso: foreign keys con `ON DELETE` explícito, snapshot de `es_mesa_examen` que no se relee del catálogo, y el `500` que la landing tiene prohibido producir. | NFR-029, NFR-034, NFR-046 | §1.8, §3.18; RB-11, RB-12; doc 11 §11.4.1 |

> **Nota sobre `Safety`.** En la edición 2023 `Safety` es una característica
> **distinta** de `Security`: `Security` protege frente a agentes maliciosos,
> mientras que `Safety` evita que un fallo perjudique a las personas ni a los
> datos. Conviene no traducirlas ambas como "seguridad" al citar el estándar.

---

## 9.2 Rendimiento y disponibilidad

El plan pide **números, no adjetivos**. `analisis.txt` no declara ninguna
latencia, ninguna disponibilidad ni ningún límite de concurrencia: esos
valores los propuso este documento y el mantenedor los aprobó el
2026-10-05, así que las seis primeras filas hoy figuran **Medible** con su
anotación de aprobación. Las que dependen de una decisión abierta quedan
**`[POR DEFINIR]`** con el hueco nombrado.

| NFR | Requisito (afirmación comprobable) | Verificación | Fuente | Estado |
|---|---|---|---|---|
| NFR-001 | Latencia p95 de `GET /convocatoria-vigente`, `GET /mesas-disponibles` y `GET /mis-inscripciones` ≤ 300 ms bajo carga nominal. | Prueba de carga con 1000 requests sobre un entorno con datos; se calcula el percentil 95. | plan §3 (09.2); doc 06 §6.6 | **Medible** — aprobada por el mantenedor 2026-10-05 |
| NFR-002 | Latencia p95 de `POST /inscripciones`, `DELETE /mis-inscripciones/{id}` y `POST /landing/preinscripcion` ≤ 500 ms. | Prueba de carga con escrituras reales sobre la base. | plan §3 (09.2); §6 | **Medible** — aprobada por el mantenedor 2026-10-05 |
| NFR-003 | Latencia p95 de `GET /reportes/permiso-examen/{usuario_id}`, `GET /reportes/acta-volante/{mesa_id}` y `GET /reportes/planilla-grupos/{convocatoria_id}` ≤ 2000 ms. | Prueba de carga sobre los tres reportes con una convocatoria completa cargada. | plan §3 (09.2); RB-19, RB-32 | **Medible** — aprobada por el mantenedor 2026-10-05 |
| NFR-004 | Presupuesto de errores: ≤ 0,5 % de las respuestas `5xx` sobre el total de requests en una ventana móvil de 30 días. | Conteo de respuestas `5xx` por código, medido durante 30 días. | plan §3 (09.2) | **Medible** — aprobada por el mantenedor 2026-10-05 |
| NFR-005 | Disponibilidad del API ≥ 99,5 % mensual, es decir ≤ 3 h 36 min de indisponibilidad no planificada en un mes de 30 días. | Sondeo de `GET /convocatoria-vigente` cada minuto y cálculo mensual del porcentaje. | plan §3 (09.2) | **Medible** — aprobada por el mantenedor 2026-10-05 |
| NFR-006 | Límite de concurrencia: ≥ 20 requests simultáneas sobre el API sin que NFR-001 deje de cumplirse. | Prueba de carga escalonada hasta 20 conexiones concurrentes, midiendo el p95 de cada tramo. | plan §3 (09.2); PD-06 | **Medible** — aprobada por el mantenedor 2026-10-05; la estrategia que condicionaba la prueba está decidida (**[CERRADO — 2026-10-06]**, PD-06: Vercel + FastAPI zero-config) |
| NFR-007 | Tamaño máximo de body en `POST /landing/preinscripcion` y el código que responde cuando se lo supera. | Caso de prueba: body por encima del límite declarado. | §2.9; doc 11 §11.6 (PENDIENTE 2) | **`[POR DEFINIR]`** — §2.9 no da número |
| NFR-008 | Umbral numérico del rate limit estricto (anti-bots) de `POST /landing/preinscripcion`. | Prueba de ráfaga por encima del umbral: debe responder `429`. | §2.9; doc 11 §11.6 (PENDIENTE 1) | **`[POR DEFINIR]`** — §2.9 no da número; el de §2.4 es de `/auth/login` |
| NFR-009 | Rate limit de `POST /auth/login`: máximo 5 intentos fallidos por usuario o por IP en una ventana de 15 minutos; al superarlo se incrementa `intentos_fallidos`, se setea `bloqueado_hasta` y sube `token_version`. | Caso de prueba: 6 logins fallidos consecutivos con el mismo usuario o desde la misma IP; se comprueba la fila de `us_usuario`. | §2.4, §8; RN-044; E-14; doc 04 US-02 | **Medible** |
| NFR-010 | Bloqueo de login: duración de 15 minutos ante el quinto fallo en la ventana de §2.4; el intento dentro del bloqueo responde `429` con `Retry-After`. | Caso de prueba: quinto login fallido → `429` con `Retry-After`, cuenta bloqueada 15 minutos; al vencer, `intentos_fallidos` en 0. | §2.4; doc 04 US-03; doc 07 EX-13; PD-27 | **Medible** — 15 minutos, `analisis.txt` §6 |
| NFR-011 | Estrategia de despliegue — decidida: Vercel + FastAPI zero-config, CORS obligatorio, Neon por driver HTTP serverless (sin pool TCP), Alembic desde CI/local y variables de entorno en el panel de Vercel por entorno (**[CERRADO — 2026-10-06]**, PD-06) — y conjunto de variables de entorno por entorno (desarrollo, pruebas y producción). | Inspección del repositorio y del entorno desplegado: cada entorno declara sus variables. | PD-06 | **Medible** — **[CERRADO — 2026-10-06]** (PD-06) |
| NFR-012 | Pool de conexiones: `pool_pre_ping = True`, `pool_recycle` declarado por debajo del scale-to-zero de Neon, aplicación sobre la conexión pooled y migraciones de Alembic sobre la conexión directa (host sin sufijo `-pooler`). | Lectura de la configuración de SQLAlchemy y de la cadena de conexión que usa Alembic. | §0 | **Medible** |

---

## 9.3 Seguridad y privacidad (Ley 25.326)

Los tres plazos que la fuente ya fija van con su número: acceso en 10 días
corridos, rectificación o supresión en 5 días hábiles y log de accesos con
retención ≥ 3 años. El reparto de responsabilidades por artículo lo declara
`analisis.txt` §3.20: art. 9, art. 14 y art. 16 son del backend (este
documento), art. 5 queda como proceso físico externo y art. 6 queda heredado
a la landing (9.6).

| NFR | Requisito (afirmación comprobable) | Verificación | Fuente | Estado |
|---|---|---|---|---|
| NFR-013 | El derecho de acceso a los datos personales (Ley 25.326, art. 14) se atiende en ≤ 10 días corridos desde que se recibe el pedido. | Caso de prueba: pedido recibido el día D, respuesta completada a más tardar el día D + 10 sobre calendario corrido. | §3.20 (art. 14); plan §3 (09.3) | **Medible** |
| NFR-014 | La rectificación y la supresión de los datos (art. 16) se atienden en ≤ 5 días hábiles desde que se recibe el pedido. | Caso de prueba con conteo de días hábiles. | §3.20 (art. 16); plan §3 (09.3) | **Medible** |
| NFR-015 | Log de accesos con retención mínima de 3 años (1095 días). | Consulta sobre el log: ninguna entrada de los últimos 1095 días fue eliminada. | plan §3 (09.3) | **Medible** |
| NFR-016 | Medidas de seguridad técnicas (art. 9): Argon2id con `m=19456`, `t=2`, `p=1` y longitud mínima de 12 caracteres; `bcrypt` sólo como fallback legacy con cost ≥ 10; nunca SHA-256 ni MD5 puros ni texto plano. | Inspección de `security.py` y prueba de hashing sobre una clave conocida. | §2.5, §8; RN-042 | **Medible** |
| NFR-017 | Access token: TTL de 15 minutos (máximo 30), firma asimétrica RS256 o ES256 con `kid`, claims obligatorios `iss`, `aud`, `exp`, `nbf`, `iat`, `jti`, `sid`, `ver` y `sub`, y ningún dato sensible en el payload. | Decodificar un token emitido y verificar cada claim, la firma y la expiración. | §2.1 | **Medible** |
| NFR-018 | Refresh token: opaco de 32 bytes, TTL de 7 días, rotación en cada uso, hash SHA-256 guardado en `us_sesion.refresh_token_hash` (nunca el token en claro) y revocación de la familia entera ante un reuso. | Caso de prueba: usar dos veces el mismo refresh y comprobar que toda la `familia_id` queda revocada. | §2.2, §3.12; RN-039; doc 04 SES-04 | **Medible** |
| NFR-019 | Invalidación global: toda request autenticada exige `ver == us_usuario.token_version` vigente; subir la versión por cambio de clave, de rol o bloqueo deja sin efecto los tokens anteriores. | Caso de prueba: token emitido antes del cambio debe ser rechazado en la siguiente request. | §2.6; RN-040; doc 03 S-15 | **Medible** |
| NFR-020 | Autorización: toda escritura exige sesión activa y la dependencia `require_permiso()` **antes** de entrar al service; sin permiso no se ejecuta ninguna lógica de negocio ni hay efectos parciales. | Prueba de integración por endpoint con y sin el permiso, verificando que la base no cambió en el caso rechazado. | §2.7, §8; RN-041; doc 07 EX-15 | **Medible** |
| NFR-021 | Reparto rol × permiso, mapeo `endpoint → permiso` y dueño de `preinscripcion.crear`. | Revisión de la matriz contra el `require_permiso()` declarado en cada endpoint. | PD-03; G-02; doc 07 EX-04 | **`[POR DEFINIR]`** — **G-02** (dueño de `preinscripcion.crear`); el reparto y el mapeo ya son la matriz definitiva (**[CERRADO — 2026-10-06]**, PD-03) |
| NFR-022 | CORS con orígenes explícitos: `allow_origins = ["*"]` está prohibido en producción y cualquier origen no listado se rechaza en el preflight. | Prueba preflight desde un origen no listado (debe fallar) y desde el origen listado (debe pasar). | §2.9, §8; doc 11 §11.6 | **Medible** |
| NFR-023 | Valor exacto del origen CORS de la landing, único que debe figurar en la lista de orígenes permitidos. | Lectura de la configuración del entorno. | §2.9; doc 11 §11.6 (PENDIENTE 3); PD-06 | **`[POR DEFINIR]`** — **sigue abierto:** valor de configuración; PD-06 (cerrado 2026-10-06) fijó Vercel + CORS obligatorio, no el origen concreto |
| NFR-024 | La única superficie pública sin autenticación es `POST /landing/preinscripcion`: sin header `Authorization`, sin RBAC, y sin ningún `GET` público de preinscripciones. | Prueba: cada `GET` del API responde `401` sin token; el POST anónimo responde según §6. | §2.9, §6; RB-10; RN-036 | **Medible** |
| NFR-025 | Aislamiento de `pr_*`: ninguna foreign key entre `pr_preinscripcion` y las tablas `pe_*`, `us_*` o `es_*`, en ninguna de las dos direcciones. | Consulta sobre `information_schema` de foreign keys cruzando esos prefijos: debe devolver 0 filas. | §3.20, §1.1; plan §3 (11.2); RN-037 | **Medible** |
| NFR-026 | Consentimiento (art. 5): proceso físico externo; el esquema no declara columna de consentimiento ni fecha de otorgamiento en `pr_preinscripcion`, y el API no expone endpoint que lo recoja. | Inspección del DDL de `pr_preinscripcion` y de la lista de endpoints bajo `/api/v1/landing`. | §3.20 (O-1); RN-058; doc 11 §11.3 | **Medible** |
| NFR-027 | Aviso previo al titular (art. 6): el backend no expone ni persiste el aviso; el requisito queda heredado a la landing y figura en 9.6. | Inspección de endpoints y columnas: no hay rastro del aviso en el backend. | §3.20 (O-1); RN-059; doc 11 §11.3 | **Medible** |

---

## 9.4 Resiliencia

Idempotencia por operación, política de reintento, degradación y reloj. La
semántica de reintento de cada operación la definieron los docs 06 §6.6 y
07 §7.4; aquí se convierte en requisito medible del backend, sin redefinir
los `EX-xx`.

| NFR | Requisito (afirmación comprobable) | Verificación | Fuente | Estado |
|---|---|---|---|---|
| NFR-028 | Idempotencia de `POST /inscripciones`: un reintento tras un timeout no crea una segunda fila; `uq_inscripcion_unica` responde `409` con la materia ya inscripta en la convocatoria. | Caso de prueba: mismo payload enviado dos veces dentro de la ventana → una fila y un `409`. | E-13, RB-08, §6; RN-006; doc 07 EX-06 | **Medible** |
| NFR-029 | Idempotencia de `POST /landing/preinscripcion`: upsert sobre `(anio_lectivo, documento)` con `201` la primera vez y `200` en reenvíos, **nunca** `409` por duplicado, y dos envíos simultáneos con el mismo documento **no producen** `500`. | Caso de prueba: dos requests concurrentes con el mismo documento → una `201` y una `200`, ninguna `500`. | RB-13, §3.20, §8; doc 11 §11.4.1; doc 07 EX-03 | **Medible** |
| NFR-030 | `DELETE /mis-inscripciones/{id}` repetido: la fila permanece `anulado` y la segunda respuesta es `204 No Content`, idempotente y sin cuerpo, igual que la primera. | Caso de prueba: mismo `DELETE` ejecutado dos veces seguidas → ambas responden `204`. | RB-08b, §3.19; RN-012; doc 07 EX-10; PD-25 | **Medible** — `204` en ambas, `analisis.txt` §6 |
| NFR-031 | `POST /auth/refresh` no es idempotente por diseño: un reintento cuya respuesta se perdió dispara la reuse detection, revoca la familia completa y exige login nuevo (`401`). | Caso de prueba: dos refresh con el mismo token; el segundo debe revocar la `familia_id`. | §2.2; doc 07 EX-12; doc 04 SES-04; doc 03 T-07 | **Medible** |
| NFR-032 | Política de backoff con jitter para los reintentos del cliente sobre escrituras y para los reintentos de la cola de email: exponencial con base 500 ms, factor 2, tope de 5 intentos y jitter de ±20 %. | Prueba de reintentos: se mide la serie de espera y se comprueba que no quedan sincronizados (jitter). | plan §3 (09.4); RB-25 | **Medible** — aprobada por el mantenedor 2026-10-05 (ninguna fuente de la spec la fija) |
| NFR-033 | Cola de email obligatoria desde v1: todo envío queda registrado en `ntf_envio` con `estado` y `reintentos`, y reintenta hasta lograr la entrega. | Inspección de `ntf_envio` después de provocar un fallo del proveedor: el registro pasa a estado de reintento y sube el contador. | RB-25; RN-051; doc 07 EX-21 | **Medible** |
| NFR-034 | Caída del proveedor de email: ocurre **después** de la respuesta HTTP y no modifica esa respuesta ni ninguna fila de negocio. | Caso de prueba con el proveedor apagado: la operación responde igual y sólo cambia el registro de `ntf_envio`. | RB-25, RB-24; RN-051; doc 11 §11.4.5 | **Medible** |
| NFR-035 | Degradación controlada: las tres lecturas de SIGME-M se sirven desde la caché del cliente **sin red y sin token**; toda escritura exige conexión y sesión válida y se corta con `401` antes del service. | Caso de prueba sin red y con access vencido: lectura servida localmente, escritura rechazada. | RB-26; RN-053, RN-054; doc 06 §6.6; doc 07 EX-11, EX-23 | **Medible** |
| NFR-036 | Sin cola offline: el API no declara ni acepta ningún mecanismo de sincronización diferida, y la caché del cliente nunca decide ventana, unicidad ni límite de condición. | Revisión de la lista de endpoints (ninguna ruta de sincronización por lote) y de los contratos de escritura. | RB-26; RN-055; doc 06 §6.6 | **Medible** |
| NFR-037 | Reloj autoritativo: toda ventana se evalúa con `current_date` en `America/Argentina/Buenos_Aires`, inclusive hasta las 23:59:59; ningún parámetro de fecha del cliente ni reloj de dispositivo participa. | Caso de prueba con el dispositivo desfasado y con una request que envíe su propia fecha: ninguna de las dos cambia el resultado. | RB-23, RB-24; RN-002, RN-004; doc 07 §7.3 | **Medible** |
| NFR-038 | En v1 no existe ningún job programado: ninguna regla temporal depende de un scheduler y toda ventana se constata en cada request. | Revisión del repositorio y del proceso desplegado: no hay cron ni tarea programada. | RB-24, RB-23; PD-11; RN-005 | **Medible** |

---

## 9.5 Auditoría, trazabilidad e integridad de los datos

El plan agrupa auditoría y trazabilidad en 9.5; la integridad referencial
entra en esta sección porque sin foreign keys correctas la trazabilidad se
pierde: una referencia borrada arrastra la historia que el registro pretendía
conservar.

| NFR | Requisito (afirmación comprobable) | Verificación | Fuente | Estado |
|---|---|---|---|---|
| NFR-039 | Auditoría estándar en **toda** tabla: `created_at`, `updated_at` y `deleted_at` en `timestamptz`, con `updated_at` escrito por un trigger `BEFORE UPDATE` (nunca por un `DEFAULT`) y el índice parcial `idx_{tabla}_activa`. | Consulta sobre `information_schema` de columnas, triggers e índices: sin huecos entre las tablas. | §1.4, §1.5, §1.6, §8; RN-045, RN-047 | **Medible** |
| NFR-040 | Trazabilidad de la sesión: `us_sesion` registra `ip`, `user_agent`, `expires_at`, `familia_id`, `estado` y `rotated_at` para cada sesión emitida. | Consulta de una sesión usada y comparación con el request que la originó. | §3.12 | **Medible** |
| NFR-041 | Trazabilidad de la landing: el servidor completa `ip`, `user_agent`, `utm_source`, `utm_medium` y `utm_campaign` en `pr_preinscripcion`; el cliente no los envía en el body. | Inspección del payload (6 campos exactos) y de la fila insertada con las columnas de trazabilidad completas. | §3.20 (bloque SERVIDOR); doc 11 §11.6 | **Medible** |
| NFR-042 | Obtención de la `ip` detrás de un proxy: header de proxy confiable (por ejemplo `X-Forwarded-For`) en lugar de la dirección de conexión entrante. | Prueba con y sin proxy delante: en ambos casos la columna `ip` guarda la dirección del cliente. | PD-06; doc 11 §11.6 (PENDIENTE 5) | **Medible** — **[CERRADO — 2026-10-06]** (PD-06): el despliegue queda en Vercel, con el proxy siempre delante del API |
| NFR-043 | Mecanismo de captura de los UTM, que no puede ir en el body porque el payload de la landing es de exactamente 6 campos. | Caso de prueba con el mecanismo elegido: la fila queda con los tres UTM completos. | §3.20 vs doc 11 §11.3; doc 11 (PENDIENTE 4) | **`[POR DEFINIR]`** — ninguna fuente lo especifica |
| NFR-044 | Bitácora de auditoría de cambios: tabla `aud_evento` **append-only** con snapshot JSONB que registra quién modificó qué — alcance: escrituras exitosas, denegaciones `401`/`403` y descargas/impresiones de reportes; fuera de alcance las lecturas corrientes y `password_hash`, refresh tokens y hashes de sesión (**[CERRADO — 2026-10-06]**, PD-05). | Inspección del DDL y una modificación de cada endpoint de escritura, verificando la fila de bitácora. | PD-05; doc 01 §1.5.1; doc 08 §8.5 | **Medible** — **[CERRADO — 2026-10-06]** (PD-05); `analisis.txt` §3 no declara la tabla (sólo columnas por tabla, §1.4), la decisión vive en §7 |
| NFR-045 | Trazabilidad de la inscripción: `es_mesa_inscripcion` conserva `inscripto_en`, `created_at`, `updated_at` y `deleted_at`, y una anulación cambia el `estado` sin borrar la fila. | Consulta: la fila anulada sigue existiendo con `estado = 'anulado'` y su marca temporal original. | §3.19; RN-011; doc 04 INS-02 | **Medible** |
| NFR-046 | Integridad referencial: toda foreign key declara `ON DELETE` explícito, y las referencias que no se pueden perder (`pe_persona`, `es_materia`, `es_condicion`, `es_convocatoria`, `es_mesa_examen`, `es_grupo_horario`) son `RESTRICT`. | Consulta sobre `information_schema`: ninguna foreign key con `ON DELETE` sin declarar; ninguna de las referencias protegidas con `CASCADE`. | §1.8; RN-046; doc 03 S-17 | **Medible** |
| NFR-047 | Observabilidad: métricas del API, punto de salud y registro de errores con su causa. | Revisión del endpoint de salud y de la exposición de métricas en el entorno desplegado. | doc 08 §Siguiente paso; plan §3 (09.2) | **`[POR DEFINIR]`** — ninguna fuente declara métricas ni health check |

---

## 9.6 Requisitos heredados a los clientes

Los requisitos de pantalla **no son obligación de este proyecto**: las
interfaces son proyectos futuros separados y consumidoras del API. Se listan
aquí, en su propia tabla y fuera de la serie `NFR-xxx`, para que no se pierdan
y para que nadie los lea como alcance de este backend.

| # | Requisito heredado | Proyecto que lo asume | Por qué no es obligación de este proyecto | Fuente |
|---|---|---|---|---|
| 1 | Conformidad con **WCAG 2.2** en la interfaz web de SIGME. | SIGME web (proyecto futuro) | El backend no renderiza ninguna pantalla; sólo expone JSON. | plan §3 (09.6); doc 01 §1.1 |
| 2 | Conformidad con **WCAG2Mobile** en la aplicación móvil SIGME-M. | SIGME-M (proyecto futuro) | Mismo motivo: el requisito mide la relación persona–sistema (`Interaction Capability`), no el API. | plan §3 (09.6); doc 01 §1.1 |
| 3 | **UX de carga offline**: mostrar la última respuesta con su marca de "última actualización", marcarla como desactualizada y reintentar online. | SIGME-M (proyecto futuro) | El backend sólo cumple su parte —respuestas autosuficientes y sin cola offline (NFR-035, NFR-036)—; el resto es interfaz. | plan §3 (09.6) y plan §3 (06.6); RB-26 |
| 4 | **Aviso previo al titular (Ley 25.326, art. 6)**: informar para qué se usan los datos y de los derechos antes del envío. | Landing (proyecto futuro) | El backend no lo expone ni lo persiste: NFR-027 y RN-059 lo dejan fuera de su contrato. | §3.20 (O-1); RN-059; doc 11 §11.3; doc 01 §1.1 |
| 5 | **Checkbox de consentimiento** en el formulario de la landing, si ese proyecto decide mostrarlo. | Landing (proyecto futuro) | El art. 5 es proceso físico externo: el backend no guarda la marca ni la fecha de otorgamiento (NFR-026). La existencia del control en el formulario queda para la landing. | §2.9 vs §3.20 (O-1); doc 11 §11.3 |
| 6 | **Almacenamiento de los tokens** del cliente: access en memoria y refresh en Keychain o Keystore; prohibido `localStorage` y `AsyncStorage`. | SIGME web y SIGME-M (proyectos futuros) | El backend emite y valida los tokens; dónde y cómo se guardan en el dispositivo no puede decidirlo la API. | doc 06 §6.1; `analisis.txt` §2.1, §2.2 |

**Cómo leer esta tabla.** Ninguna de estas seis filas tiene identificador
`NFR-xxx` a propósito: no son requisitos de este backend y contarlas dentro de
la serie rompería el criterio de cierre del plan (plan §3, 09.6).

---

## 9.7 Mantenibilidad y flexibilidad

Comprobables sobre el repositorio y su configuración, no sobre el producto en
ejecución. Son los que la taxonomía exige para `Maintainability` y
`Flexibility` y que ningún otro apartado del plan cubre.

| NFR | Requisito (afirmación comprobable) | Verificación | Fuente | Estado |
|---|---|---|---|---|
| NFR-048 | Estructura por dominio: los routers manejan sólo HTTP, la lógica vive en `service.py` sin importar de FastAPI, un dominio nunca importa a otro y `app/api/v1/api.py` es el único punto que importa routers. | Test en CI que falle si un `service.py` importa `fastapi` o si un dominio importa a otro. | §5 | **Medible** |
| NFR-049 | `ruff` y `mypy` corren en pre-commit y en CI sin hallazgos. | Ejecución en CI: el job falla si hay algún hallazgo. | §8 | **Medible** |
| NFR-050 | Tests unitarios sobre los services y tests de integración contra una base real. | Ejecución de la suite completa en CI. | §8 | **Medible** |
| NFR-051 | Todo cambio de esquema se aplica con una migración versionada de Alembic, y el arranque desde cero (esquema vacío hasta el estado actual) es reproducible. | Ejecutar la cadena de migraciones completas sobre una base vacía, en CI. | §0, §8 | **Medible** |
| NFR-052 | Configuración por variables de entorno: `.env.example` commiteado, `.env` en `.gitignore` y ninguna credencial en el repositorio. | Inspección de archivos y de la configuración cargada al arrancar. | §0, §8 | **Medible** |
| NFR-053 | Convenciones de nombres: tablas en `snake_case` singular con uno de los cuatro prefijos de §1.1, columnas en `snake_case` sin camelCase, índices `idx_*`, `uq_*` y `ck_*`, y foreign keys con sufijo `_id`. | Consulta sobre `information_schema` contra cada regla de nomenclatura. | §1.1, §1.2, §8 | **Medible** |
| NFR-054 | Flexibilidad: el mismo código atiende a los tres consumidores; no hay rutas ni ramas de lógica por cliente, y el módulo operado se decide por `us_modulo` y no por bifurcaciones en el código. | Revisión de rutas y de la dependencia `require_modulo()` por endpoint. | §2.8; RN-043 | **Medible** |

---

## 9.8 Pendientes heredados

Ninguno de estos identificadores se cierra en este documento. Se listan con la
fila de este documento que los hace visibles, para que el documento 10 los
herede trazados; los que ya tienen decisión en `analisis.txt` §7 se conservan
marcados **[CERRADO — 2026-10-06]** (o **[RESUELTA]** para G-05) sin
renumerar.

| ID | Pregunta abierta | Qué toca en este documento | Fuente |
|---|---|---|---|
| **PD-02** | **[CERRADO — 2026-10-06]** — Valores de `es_condicion.limite_materias` (Previa 3, Regular 8, Libre sin límite) y unidad de conteo por convocatoria | **No es un NFR:** es una regla de negocio — RN-013 ya no está condicionada | `analisis.txt` §7; RB-03 |
| **PD-03** | **[CERRADO — 2026-10-06]** — Semilla de roles, permisos y usuarios en la migración inicial; reparto y mapeo de la matriz doc 02 §2.4 | **NFR-021** pasa a nombrar **G-02** como hueco restante (dueño de `preinscripcion.crear`) | `analisis.txt` §7; doc 02 §2.4 |
| **PD-04** | **[CERRADO — 2026-10-06]** — Reseteo de contraseña por email desde v1: tabla `us_password_reset`, email por la cola obligatoria | **No es un NFR:** es diseño de tabla — la tabla ya existe desde v1 y el canal está en NFR-033 | `analisis.txt` §7; RB-24, RB-25 |
| **PD-05** | **[CERRADO — 2026-10-06]** — Bitácora: `aud_evento` append-only con snapshot JSONB y alcance definido | **NFR-044** queda **Medible** | `analisis.txt` §7; doc 01 §1.5.1 |
| **PD-06** | **[CERRADO — 2026-10-06]** — Vercel + FastAPI zero-config; CORS obligatorio; Neon por driver HTTP serverless; Alembic desde CI/local; env vars por entorno en Vercel | **NFR-011** y **NFR-042** quedan **Medible**; NFR-006 pierde su condición; NFR-023 conserva **`[POR DEFINIR]`** por el valor del origen | `analisis.txt` §7; doc 08 §8.5 |
| **PD-10** | Conjunto exacto de notificaciones in-app por rol | **No es un NFR:** el canal ya está en NFR-033, el conjunto sigue abierto | `analisis.txt` §7; RB-24 |
| **PD-11** | Recordatorio de 48 horas antes de la mesa (**deferido a v2**) | NFR-038 sostiene que en v1 no hay job; el recordatorio queda fuera | `analisis.txt` §7; RB-24 |
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? | **No es un NFR:** toca precondiciones de negocio, no requisito no funcional | `analisis.txt` §7; RB-29 |
| **PD-13** | **[CERRADO — 2026-10-06]** — `uq_mesa_unica` gana `convocatoria_id` y sigue sin `hora` | **No es un NFR:** es una restricción de esquema | `analisis.txt` §7; §3.18 |
| **PD-15** | De dónde sale el conjunto esperado de pares materia × condición de la cobertura | **No es un NFR:** es un contrato de datos | `analisis.txt` §7; RB-31 |
| **PD-16** | **[CERRADO — 2026-10-06]** — Sí: `UNIQUE (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` (`uq_grupo_unico`); colisión → `409` | **No es un NFR:** NFR-046 cubre la parte de `ON DELETE`, no esta restricción | `analisis.txt` §7; §3.22 |
| **PD-17** | Interpretación de `grupo.hora` (`time` sin zona) frente a RB-23 | Toca **NFR-037**, que sostiene la fecha de calendario pero no la hora sin zona | `analisis.txt` §7; RB-23 |
| **PD-18** | **[CERRADO — 2026-10-06]** — Borrado lógico de grupo con cascada lógica transaccional; falla si alguna mesa tiene inscripciones activas | **No es un NFR:** toca RN-033 y la vista | `analisis.txt` §7; doc 04 GR-02 |
| **PD-19** | Código HTTP del rechazo de `POST /inscripciones` sin mesa | **No es un NFR:** es contrato de respuesta, abierto en doc 07 §7.7.2 | `analisis.txt` §7; RB-31 |
| **PD-20** | Formato canónico del catálogo de materias para validarlo programáticamente | **No es un NFR:** afecta a la semilla y a la cobertura | `analisis.txt` §7; RB-31 |
| **PD-21** | Renombrado o alta de catálogo sin endpoint declarado | **No es un NFR:** es contrato de endpoints | `analisis.txt` §7; doc 03 S-09 |
| **PD-22** | Efecto del `PATCH /preinscripciones` | **No es un NFR:** ninguna regla declara ese efecto | `analisis.txt` §7; doc 05 CU-26 |
| **PD-23** | Alcance de RB-22 sobre `GET /mesas-disponibles` | **No es un NFR:** es el alcance de una regla de negocio; RN-021 queda **condicionada** y NFR-001 sólo mide la latencia | `analisis.txt` §7; doc 06 §6.8; doc 07 EX-16 |
| **PD-24** | **[CERRADO — 2026-10-05]** Contrato de cuerpo de las respuestas de error fuera de `/landing/preinscripcion` | **No es un NFR:** es un contrato de respuesta — cerrado en `analisis.txt` §6 (sobre de error único) | `analisis.txt` §7; doc 07 §7.7.2 |
| **PD-25** | **[CERRADO — 2026-10-05]** Código HTTP de la respuesta repetida de `DELETE /mis-inscripciones/{id}` | **NFR-030** queda **Medible**: `204 No Content` en ambas (cerrado en `analisis.txt` §6) | `analisis.txt` §7; doc 06 §6.8; doc 07 §7.8 |
| **PD-26** | **[CERRADO — 2026-10-05]** Endpoint de alta y baja del token de push (`us_dispositivo`) | **No es un NFR:** endpoints `POST /dispositivos` y `DELETE /dispositivos/{id}` en §6 (NFR-038 sólo afirma que no hay jobs) | `analisis.txt` §7; doc 06 §6.8; doc 07 EX-22 |
| **PD-27** | **[CERRADO — 2026-10-05]** Duración exacta del bloqueo de login y el código de su respuesta | **NFR-010** queda **Medible**: `429` + `Retry-After`, bloqueo de 15 minutos (cerrado en `analisis.txt` §6) | `analisis.txt` §7; doc 04 US-03; doc 07 EX-13 |
| **PD-28** | Paginación de `GET /mis-inscripciones` | **No es un NFR:** es un contrato de lectura que §6 no declara; NFR-001 mide la latencia de esa ruta | `analisis.txt` §7; plan §3.06; doc 06 §6.6 |
| **PD-29** | Alcance de `POST /mesas` fuera de la alta masiva del grupo | **No es un NFR:** es regla de negocio sin dueño → doc 04 §4.6.4 | `analisis.txt` §7; doc 04 §4.6.4 |
| **G-01** | Qué significa "matrícula" para el cliente: la palabra no existe en `analisis.txt` | **No es un NFR:** es vocabulario; sigue PENDIENTE en doc 01 §1.3 | doc 01 §1.5.2 |
| **G-02** | Qué rol usa el permiso `preinscripcion.crear`, si la landing es anónima | Toca **NFR-021** (dueño del permiso) y la nota de 9.6 fila 5 | doc 01 §1.5.2; doc 02 §2.4 |
| **G-03** | Si existe el rol "docente", comentado en el DDL de `us_rol` | **No es un NFR:** es un dato de semilla; P-08 cerró la lista de roles | doc 01 §1.5.2; doc 04 §4.6.3 |
| **G-04** | Cómo obtiene SIGME-M las opciones de orientación, curso, materia y condición | **No es un NFR:** es un contrato sin endpoint; NFR-001 sólo fija la latencia de la lectura | doc 01 §1.5.2; doc 06 §6.8 |
| **G-05** | **[RESUELTA — 2026-10-06]** — Nadie cambia el estado: convocatoria y mesa se constatan al leer por calendario | **No es un NFR:** no hay escritura de estados que medir (NFR-038 sostiene además que no hay job) | doc 01 §1.5.2; doc 04 §4.6.2 |

---

## Checklist de cierre (9 · Requisitos no funcionales)

**Criterio de cierre del plan (plan §3, 09): *todo NFR de este backend es
medible o está marcado `[POR DEFINIR]`; los heredados están separados en su
propia tabla* — verificación:**

- [x] **54 requisitos con ID estable** (`NFR-001`…`NFR-054`), uno por fila, sin
      huecos ni duplicados: 12 en 9.2, 15 en 9.3, 11 en 9.4, 9 en 9.5 y 7 en
      9.7.
- [x] **Ninguna fila es un adjetivo sin número.** Reparto de estados: **48
      Medible**, **6 `[POR DEFINIR]`** y **0 Propuesta**. Las 6 filas
      `[POR DEFINIR]` nombran en su propia fila el hueco que las decide
      (los pendientes del doc 11 — NFR-007, NFR-008 y NFR-023—, **G-02** en
      NFR-021, y los dos huecos que quedan en 9.5 — NFR-043 y NFR-047—);
      NFR-011, NFR-042 y NFR-044 pasaron a **Medible** con los cierres de
      PD-05 y PD-06 del 2026-10-06, y las 7 filas que eran **Propuesta**
      fueron aprobadas por el mantenedor el 2026-10-05 y hoy cuentan como
      **Medible**.
- [x] **Taxonomía ISO/IEC 25010:2023 completa:** las **nueve** características
      de la edición 2023 figuran en 9.1, cada una con su aplicación al API y
      con la sección donde se mide; `Interaction Capability` apunta a 9.6 en
      lugar de fingir que el API tiene pantalla.
- [x] **Plazos de la Ley 25.326 con su número:** art. 14 en 10 días corridos
      (NFR-013), art. 16 en 5 días hábiles (NFR-014), log de accesos ≥ 3 años
      (NFR-015), art. 9 en NFR-016, art. 5 en NFR-026 y art. 6 en NFR-027 con
      su traslado a 9.6.
- [x] **9.6 existe como tabla propia:** los seis requisitos heredados (WCAG
      2.2, WCAG2Mobile, UX de carga offline, art. 6, checkbox de
      consentimiento y almacenamiento de tokens) están **fuera de la serie
      `NFR-xxx`** y marcados como obligación de los proyectos futuros, no de
      este backend.
- [x] **Los pendientes se heredan, no se cierran:** 9.8 lista los **24**
      `PD-xx` que hereda —11 abiertos, PD-11 deferido a v2, PD-24…PD-27
      cerrados el 2026-10-05 y **8** cerrados el 2026-10-06 (PD-02, PD-03,
      PD-04, PD-05, PD-06, PD-13, PD-16 y PD-18)— y los **5**
      `G-xx` (G-05 **[RESUELTA — 2026-10-06]**), cada uno con la fila que lo
      hace visible; ninguno se resuelve por suposición.
- [x] **Ningún requisito contradice a un documento anterior:** los códigos
      HTTP se citan sólo como los declararon los docs 07 §7.7.1 y 11 §11.4.2;
      los casos sin código declarado en doc 07 §7.7.2 siguen sin código aquí,
      porque este documento no se lo asigna por su cuenta.

## Siguiente paso

`10-matriz-de-trazabilidad.md`: cruzar `RN-xxx` ↔ `CU-xx` ↔ entidad ↔ estado
↔ criterio de aceptación, detectar huérfanos en ambos sentidos y consolidar
las listas de `[ABIERTA]` y `[POR DEFINIR]` — entre ellas las 6 filas
`[POR DEFINIR]` de este documento. El seguimiento en `odd/tasks/analisis-sigme.md`
llama a ese archivo `10-matriz-trazabilidad.md` (sin la segunda palabra
separada); se usa aquí el nombre del plan.
