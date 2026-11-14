# SDD-3 — Mesas y convocatorias

Objetivo: implementar bajo `/api/v1/sigme` convocatorias, ventanas-preinscripcion,
grupos (alta masiva + mover fecha/hora), mesas (lectura filtrada RB-22 + edición)
y cobertura-mesas, sobre los modelos SDD-0 ya existentes.
Rama: `feat/sdd-3-mesas` desde `origin/main` (`6018204`). Runner: `python -m pytest tests -q` (+ `python -m ruff check .`).
Estrategia de entrega: `single-pr` (precedente aceptado del PR #4 de SDD-2; pronóstico ~1400 líneas autorizadas entre implementación y tests).

## Specs

### S1 — Convocatorias (GET|POST|PATCH)

§6 (`analisis.txt:1093`): `GET|POST /convocatorias` (+ `PATCH /convocatorias/{id}`,
CU-11..CU-13). Campos (§3.17): `descripcion varchar(100) NN`,
`fecha_inicio_inscripcion date NN`, `fecha_fin_inscripcion date NN`,
`activa boolean DEFAULT true`; `CONSTRAINT ck_convocatoria_ventana CHECK
(fecha_inicio_inscripcion <= fecha_fin_inscripcion)` — la violación responde
`422` con `errors[]` (PD-24). `GET` devuelve las columnas de negocio más
`estado` derivado según doc 04 §4.1: `borrador` (`activa=false`),
`abierta` (`activa=true` e `hoy` entre fechas, límite inclusive RB-23),
`cerrada` (`hoy > fecha_fin_inscripcion`), `archivada` (`deleted_at` no nulo
no se lista; archivado = soft delete, CU-13). RB-16: "LA CONVOCATORIA DELIMITA
TODO". RB-17: "LISTA FIJA AL CERRAR LA VENTANA". RB-23: límite inclusive por
fecha de calendario en `America/Argentina/Buenos_Aires`.
`POST` crea (`activa` nace `true` por defecto, C-01); `PATCH` permite editar
`descripcion`, las dos fechas (respetando el CHECK) y `activa` (C-05).
Permisos: códigos `convocatoria.*` PENDIENTE en los docs (CU-11 propone
`convocatoria.gestionar`) → gate temporal patrón SDD-2: lectura
`require_modulo("sigme_web")`, escritura `require_permiso("usuario.gestionar")`
mismo placeholder que catálogo; se cambia cuando el cliente confirme el código.
Fuera de SDD-3: archivar/restaurar como endpoints dedicados (CU-13 sin ruta
declarada en §6; se usa `deleted_at` vía soft delete sólo si CU-13 lo exige —
decisión de implementación en T1, preferencia: sin endpoint de archivado,
documentado).

### S2 — Ventanas-preinscripcion (GET|POST de `pr_ventana`)

§6 (`analisis.txt:1094`): `GET|POST /ventanas-preinscripcion (gestiona
pr_ventana)` — **sin `PATCH`** (corrección L6: la primera versión de este doc
declaraba `PATCH /{id}`, que no está en ninguna fuente). CU-14: "POST
/ventanas-preinscripcion para abrir o cerrar la ventana vigente" → el POST es
un **upsert por `anio_lectivo`** (única clave natural por `uq_ventana_anio`):
crea la ventana si el año no existe; si existe, actualiza fechas, descripción
y `activa` (cerrar = `activa=false`). §3.21: `anio_lectivo int NN`,
`descripcion varchar(100) NN`, `fecha_desde date NN` (inclusive),
`fecha_hasta date NN` (inclusive), `activa boolean DEFAULT true`,
`CONSTRAINT ck_ventana CHECK (fecha_desde <= fecha_hasta)` → `422` con
`errors[]` (PD-24), `CONSTRAINT uq_ventana_anio UNIQUE (anio_lectivo)` (año
registrado en una fila soft-deleted → `409 ventana-anio-existente`). RN-035
"Nunca dos ventanas vigentes a la vez": el POST responde `409
ventana-solapada` si el resultado quedaría `activa` con rango que se solapa
con otra ventana `activa` no borrada — garantiza que `vw_ventana_vigente`
nunca devuelva 2 filas (el nombre del código y la validación son asunción
A-SDD3-4: ninguna fuente los nombra; el DDL no la garantiza porque
`uq_ventana_anio` sólo cubre el mismo año). `GET` lista todas (no borradas,
`anio_lectivo` desc) con `vigente: bool` derivado (`activa AND hoy_BA BETWEEN
fechas`, doc 11 §11.5). RB-23 aplica igual a `pr_ventana`. Permisos: patrón
SDD-2 temporal (lectura módulo `sigme_web`, escritura `usuario.gestionar`)
mientras `ventana.*` siga PENDIENTE. Además T2 corrige `_ventana_activa` del
landing para usar `hoy_buenos_aires()` (RB-23) en lugar de `date.today()` del
servidor; el helper se mueve a `app/core/fechas.py` compartido.

### S3 — Grupos (POST alta masiva, PATCH mover, GET por convocatoria)

§6 (`analisis.txt:1101-1112`): "Crear un grupo exige `mesa.crear`; mover la
fecha/hora de un grupo exige `mesa.modificar` (§2.7 — códigos ya existentes;
no se agregan permisos nuevos)". `POST /grupos`: "crea el grupo y N mesas de
una (materias[] × condiciones[] × fecha × hora) — RB-28. Colisión de
`uq_grupo_unico` (§3.22, PD-16) → 409". `PATCH /grupos/{id}`: "cambia
fecha/hora: mueve TODAS sus mesas en la misma transacción (RB-29) — con
ventana abierta: PD-12". `GET /grupos?convocatoria_id=` (RB-27).
RB-28: "el secretario elige materias y condiciones, les asigna una fecha y una
hora, y el backend crea N mesas de una (materias[] × condiciones[] × fecha ×
hora)"; permiso `mesa.crear` (Secretario, Administrador, Superadmin).
RB-29: "`es_mesa_examen.grupo_id` es NOT NULL. La `fecha` y la `hora` de la
mesa son una COPIA del grupo, sincronizada en la MISMA transacción".
Las mesas creadas nacen `estado='planificada'` con los 4 snapshots rellenos
desde el catálogo (ME-01/GR-01).
**PD-12 CERRADO por el cliente (2026-10-22): "Crear sí, mover no"** —
`POST /grupos` con ventana de inscripción abierta de la convocatoria
(`activa=true` y `fecha_inicio <= hoy_BA <= fecha_fin`, RB-23) está
PERMITIDO (alta aditiva; no invalida inscripciones existentes);
`PATCH /grupos/{id}` con ventana abierta responde `409 ventana-abierta`
hasta que cierre la ventana (las fechas nunca cambian bajo alumnos ya
inscriptos; RB-17). La ventana abierta se evalúa por convocatoria, no por
`pr_ventana` (esa es la del landing).

### S4 — Mesas (GET listado y detalle RB-22, PATCH asignación)

§6 (`analisis.txt:1096-1098`): `GET /mesas # filtra RB-22: sólo con >=1 activa`,
`GET /mesas/{id}`, `PATCH /mesas/{id}` (CU-19, CU-20), `GET
/mesas/por-fecha?desde=&hasta= # filtra RB-22`. RB-22: "Todo listado y toda
impresión devuelven únicamente las mesas con AL MENOS UNA INSCRIPCIÓN ACTIVA
(estado = 'inscripto')" — implementado como el EXISTS de
`vw_mesa_con_alumnos` (`analisis.txt:546-555`: EXISTS contra
`es_mesa_inscripcion` con `estado='inscripto'` y `deleted_at IS NULL`).
**Alcance (corrección T4, ver L11):** CU-19 declara las TRES operaciones de
lectura (incluye `GET /mesas/{id}`) y su resultado "el backend devuelve sólo
mesas con al menos una inscripción activa" → RB-22 también en el detalle
(mesa sin inscripción activa → 404 `mesa-no-encontrada`; S-03: "no aparece,
pero no se borra"). **Exclusión temporal (incorporada en T4, ver L11):** las
mesas VENCIDAS (fecha/hora pasada en `America/Argentina/Buenos_Aires`, RB-23)
dejan de listarse en SIGME — 7 fuentes concordantes (`analisis.txt:572`
comentario DDL, doc 01 G-05, doc 04 §4.2/§4.6.2, doc 05 CU-22, doc 07) — por
lo que `GET /mesas` y `por-fecha` excluyen vencidas; el detalle por id NO se
excluye (es la única lectura donde el estado derivado resulta observable —
CU-22: "la constatación ocurre en toda lectura"). Filtros query opcionales en
ambos listados: `convocatoria_id` (inexistente → 404
`convocatoria-no-encontrada`, patrón T1/T3), `materia_id`, `condicion_id`;
orden por `fecha` y `hora`. `por-fecha` exige `desde` y `hasta` (faltan o
`desde > hasta` → 422 `validacion` con `errors[]`), rango inclusive sobre
`fecha` (RB-23), y aplica RB-22 + exclusión de vencidas. `GET /mesas/{id}`
devuelve la mesa con sus 4 snapshots y `estado` DERIVADO (ME-03/ME-04
constatan al leer, sin escritura): A-SDD3-6 — vencida → `cerrada` (la
transición mínima desde el almacenado `planificada`); la frontera
`cerrada`/`realizada` queda PENDIENTE por falta de fuente (doc 04 ME-03/ME-04:
mismo disparador, ninguna fuente los separa) y `realizada` no se deriva en v1.
`PATCH /mesas/{id}` (CU-20: "Editar la asignación de una mesa"): permite
cambiar `condicion_id` y/o `materia_id` — al menos uno, `422 validacion` si
ninguno, `extra="forbid"` (fecha/hora pertenecen al grupo, RB-29) — rellenando
los 4 snapshots desde el catálogo en la MISMA transacción, respetando
`uq_mesa_unica` (convocatoria, materia, condición, fecha) → colisión `409
mesa-duplicada` con cierre de carrera NFR-029; catálogo inexistente/inactivo →
404 `materia-no-encontrada`/`condicion-no-encontrada`; el `estado` NO cambia
(CU-20) y NO hay gate temporal (CU-20 no declara ventana; PD-12 es sólo de
grupos) ni filtro RB-22 (escritura sobre fila existente: "mesa existente y no
borrada"). Permisos: `mesa.listar` (los 3 reads), `mesa.modificar` (PATCH).
PD-29 CERRADO: `POST /mesas` (mesa suelta) queda FUERA de la primera entrega —
el alta es sólo masiva vía `POST /grupos` (RB-28; "mesa suelta" choca con
`grupo_id NOT NULL` RB-29).

### S5 — Cobertura-mesas (GET)

§6 (`analisis.txt:1114-1116`): "Cobertura de mesas (RB-31): materias ×
condiciones SIN mesa en la convocatoria. Se consulta ANTES de abrir la ventana
de inscripción. `GET /cobertura-mesas?convocatoria_id=`". RB-31: "el backend
debe poder exponer qué materias × condiciones de una convocatoria quedan SIN
mesa, en una consulta utilizable ANTES de abrir la ventana de inscripción".
PD-15 CERRADO (asunción A-SDD3-1): el conjunto esperado de pares se deriva
del catálogo ACTIVO completo — `es_materia` activas × `es_condicion` activas
(excluyendo la condición de la propia convocatoria si aplicara; la
convocatoria no tiene FK al catálogo). La respuesta lista los pares SIN mesa
activa en la convocatoria (mesa con `deleted_at IS NULL`, cualquier grupo,
cualquier fecha). Es un reporte de consulta (advisory), no un gate: nada lo
usa para rechazar operaciones. Permisos: `mesa.listar`.

### S6 — README y cierre

README: secciones nuevas de SIGME para convocatorias, ventanas, grupos, mesas
y cobertura (tabla de endpoints + notas de reglas clave RB-22/RB-27/RB-28/
RB-29/RB-31 y PD-12). Actualizar la sección de superficie pública si el
esquema cambia (no debería: todos los nuevos exigen JWT). Cerrar Log con
evidencia de commits y resultados de test.

## Tasks

| ID  | Specs      | Ruta            | Estado     | Commit / evidencia |
|-----|------------|-----------------|------------|--------------------|
| T1  | S1         | inline          | completado | `16bfea9` (RED 404→401, GREEN 6/6, suite 126, ruff ok) |
| T2  | S2         | inline          | completado | `652102c` (RED 10/10, GREEN 10/10, suite 136, ruff ok) |
| T3  | S3         | inline          | completado | `47c3dbc` (RED 14/14, GREEN 14/14, suite 150, ruff ok) |
| T4  | S4         | inline          | completado | `283d663` (RED 17 escrito → GREEN 17/17, suite 167, ruff ok) |
| T5  | S5         | inline          | completado | `c303a31` (RED 8/8 → GREEN 8/8, suite 175, ruff ok) |
| T6  | S6         | inline          | completado | README SDD-3 (readback estructural; docs pasivas) |

Rutas: ninguna task dispara Writer trigger (cambios secuenciales en la misma
área, superficies solapadas en `app/features/mesas/` y
`app/features/preinscripcion/` — un solo escritor, el padre).

## Log

- **L1 (2026-10-22)** — Petición original del usuario (verbatim): "has el merge y continua" — continúa SDD-3 — Mesas y convocatorias desde `analisis.txt`, tras merge de SDD-2 (PR #4 → main `6018204`).
- **L2 (2026-10-22)** — PD-12 CERRADO por decisión explícita del cliente. El usuario eligió la opción "Crear sí, mover no (Recomendada)": "`POST /grupos` con ventana abierta: permitido (aditivo, permite tapar un hueco de cobertura en caliente sin invalidar inscripciones existentes). `PATCH /grupos/{id}`: 409 ventana-abierta hasta que cierre la ventana — las fechas nunca cambian bajo alumnos ya inscriptos."
- **L3 (2026-10-22)** — Asunciones del asistente (A-SDD3-1..3), aceptadas por delegación del usuario ("por lo que creas mejor, te dejo la decisión"): A-SDD3-1 (PD-15) conjunto esperado de cobertura = catálogo activo completo materia×condición; A-SDD3-2 (PD-17) `grupo.hora` es hora local Argentina (BA) combinada con `fecha` (RB-23; sin DST en AR desde 2009); A-SDD3-3 (PD-29) `POST /mesas` sueltas fuera de la primera entrega. PD-19 y PD-23 pertenecen a SDD-4 (inscripciones), no bloquean.
- **L4 (2026-10-22)** — Permisos: §6 declara `mesa.crear`/`mesa.modificar`/`mesa.listar` existentes (sin permisos nuevos) para grupos y mesas; `convocatoria.*` y `ventana.*` siguen PENDIENTE en docs → gates temporales patrón SDD-2 (`require_modulo("sigme_web")` lectura, `require_permiso("usuario.gestionar")` escritura), igual que catálogo en SDD-2.
- **L5 (2026-10-22)** — T1 completado: RED observado (`GET /sigme/convocatorias` → 404 donde corresponde 401), GREEN 6/6 en `tests/unit/test_convocatorias.py`, suite 126 passed, ruff limpio. Commit `16bfea9` en `feat/sdd-3-mesas`. Detalles de implementación: `hash_password` importado de `app.core.security`; tests de escritura requieren `permisos=("usuario.gestionar",)`; el CHECK de ventana se valida también sobre valores RESULTANTES en PATCH (422 con `errors[]`).
- **L6 (2026-10-22)** — Corrección de spec de S2 antes de implementar T2 (verificación contra fuentes, no inventiva): (a) la primera versión del doc declaraba `PATCH /ventanas-preinscripcion/{id}` — `analisis.txt:1094` sólo declara `GET|POST` y CU-14 dice "POST para abrir o cerrar la ventana vigente"; se elimina el `PATCH` y el POST queda como upsert por `anio_lectivo`. (b) A-SDD3-4 (asunción): código `ventana-solapada` para el choque de dos ventanas activas con rangos solapados — RN-035 ("Nunca dos ventanas vigentes a la vez") está especificado pero ninguna fuente nombra el código ni la validación de solape (doc 11, PENDIENTE 13); sin ella `vw_ventana_vigente` devolvería 2 filas y el `anio_lectivo` del landing sería ambiguo. (c) A-SDD3-5 (asunción): `GET` devuelve todas las ventanas con `vigente` derivado en lugar de sólo la vigente, para que el operador vea el histórico por año (§6 no especifica la forma de la respuesta; sólo "gestiona pr_ventana").
- **L7 (2026-10-22)** — T2 completado: RED observado (10 tests fallan con 404 donde corresponde 401/200/201; el monkeypatch de `hoy_buenos_aires` no encontraba el atributo en el router de landing), GREEN 10/10 en `tests/unit/test_ventanas_preinscripcion.py`, suite 136 passed, ruff limpio. Commit `652102c` en `feat/sdd-3-mesas`. Detalles: helper `hoy_buenos_aires()` movido a `app/core/fechas.py` (re-export desde `service_convocatoria` para no romper el router de mesas); `upsert_ventana` devuelve `(fila, creada)` para que el router responda 201/200 dinámicamente; el fix RB-23 del landing importa `hoy_buenos_aires` directamente al namespace del router (el monkeypatch del test depende de eso).
- **L8 (2026-10-22)** — Pausa acordada del usuario ("vamos cortando"). Estado de T3: escrito el archivo RED `tests/unit/test_grupos.py` (14 tests: RB-28 bulk, PD-12 crear-sí/mover-no, uq_grupo_unico → 409 grupo-duplicado, uq_mesa_unica → 409 mesa-duplicada, 404 convocatoria/materia, 422 listas vacías, RB-29 sync en PATCH, CU-17 listado) pero **SIN ejecutar aún** y **sin implementación** (`router_grupos`/`service_grupos` no existen). El archivo queda sin commitear en el árbol de trabajo: la próxima sesión arranca ejecutando el RED, luego implementa y cierra GREEN. Harness T3 usa los permisos REALES `mesa.crear`/`mesa.modificar`/`mesa.listar` (existen en el seed §2.7, a diferencia de los gates temporales de T1/T2).
- **L9 (2026-10-26)** — Intercalado: tarea del usuario sobre el informe del colega de la landing (reporte de 3 hallazgos contra `POST /preinscripcion`, auditado sobre `8c3cd1f`). F1 (crítico, 409 por reenvío) y F2 (`code` 422 `error-validacion` → `validacion`) verificados y corregidos en `7a1370d` (upsert RB-13 con cierre de carrera NFR-029; rename API-wide). F3 (rate limit) verificado como obligación del contrato pero **decidido pendiente** por el usuario (2026-10-28): la regla previa "no per-IP" cierra la propuesta del informe; queda documentado como gap (NFR-008 umbral [POR DEFINIR]); guardado en Engram (`landing/rate-limit`). Revisión RDD del slice `origin/main..7a1370d` **declinada por el usuario** ("Omitir esta vez"); RDD sigue activo. Devolución al colega entregada como PDF.
- **L10 (2026-10-28)** — T3 completado. RED observado: 14/14 fallan (rutas 404) + 2 bugs del harness descubiertos al correrlo (`es_taller` NOT NULL en `crear_catalogo`). GREEN 14/14, suite 150 passed, ruff limpio. Archivos: `schemas_grupo.py`, `service_grupos.py`, `router_grupos.py` + registro en `api.py`. Detalles: permisos REALES `mesa.crear`/`mesa.modificar`/`mesa.listar` (§2.7, sin gates temporales); pre-chequeo de `uq_grupo_unico` y `uq_mesa_unica` + cierre de carrera por `IntegrityError` → relectura → 409 (patrón NFR-029 del landing); PD-12 materializado (`crear` sin check de ventana, `mover` → 409 `ventana-abierta` vía `ventana_inscripcion_abierta` de T1); RB-29: grupo y mesas se actualizan en la misma transacción. Dos ajustes del harness durante el GREEN: (a) `test_patch_grupo_duplicado_es_409` creaba los dos grupos con las MISMAS materias/condiciones en la MISMA fecha — `uq_mesa_unica` sin hora (PD-13) lo rechaza correctamente, así que el segundo grupo usa materias distintas (franjas del mismo día con materias distintas, caso de negocio real); (b) `test_get_grupos_por_convocatoria` necesitaba `mesa.crear además de`mesa.listar` porque su setup hace un POST.
- **L11 (2026-10-28)** — T4: verificación de la spec S4 contra las fuentes ANTES del RED (patrón L6). (a) Exclusión temporal incorporada a S4: "las mesas vencidas dejan de listarse en SIGME" — 7 fuentes concordantes (`analisis.txt:572` comentario del DDL, doc 01 G-05, doc 04 §4.2/§4.6.2, doc 05 CU-22, doc 07) — aplica a `GET /mesas` y `por-fecha`; el detalle por id NO se excluye (es la única lectura donde el estado derivado es observable — CU-22: "la constatación ocurre en toda lectura"). (b) RB-22 también en `GET /mesas/{id}`: el flujo de CU-19 declara las 3 operaciones de lectura y su resultado "sólo mesas con al menos una inscripción activa" (extiende el alcance textual de RB-22 — "todo listado y toda impresión" — a la lectura puntual; el borrador §6 sólo anota el comentario en los dos listados). (c) A-SDD3-6: estado derivado de vencida = `cerrada` (ME-03: transición mínima desde el estado almacenado `planificada`); la frontera `cerrada`/`realizada` queda PENDIENTE por falta de fuente (doc 04 ME-03/ME-04 comparten disparador sin frontera declarada) y `realizada` no se deriva en v1. (d) `por-fecha` exige `desde` y `hasta` — faltan o `desde > hasta` → 422 `validacion` (rango inclusive de fecha, RB-23). (e) `convocatoria_id` desconocido en los filtros → 404 `convocatoria-no-encontrada` (patrón T1/T3). (f) `PATCH /mesas/{id}`: `extra="forbid"` (fecha/hora pertenecen al grupo, RB-29), al menos una asignación (422 `validacion`), 409 `mesa-duplicada` con cierre de carrera NFR-029, SIN gate temporal (CU-20 no declara ventana; PD-12 es sólo de grupos) y SIN filtro RB-22 (escritura sobre fila existente; precondiciones CU-20: "mesa existente y no borrada"). La revisión RDD del slice T1–T3 quedó detenida por `operation_timeout` de gentle-ai (linaje `review-1b5dd17ce19b283f`, consentimiento consumido; decisión del usuario: continuar sin reportar).
- **L12 (2026-10-30)** — T4 completado. RED observado: 17 tests escritos (14 fallan como corresponde: rutas aún inexistentes; 3 pasan por coincidencia de FastAPI que igual fija contrato PD-24). GREEN 17/17, suite 167 passed, ruff limpio. Archivos: `schemas_mesas.py`, `service_mesas.py`, `router_mesas.py` + registro `examenes_router` en `api.py` (orden importa: `/mesas` y `/mesas/por-fecha` ANTES de `/mesas/{mesa_id}`). Implementación: RB-22 vía `exists()` sobre `es_mesa_inscripcion` activa (`estado='inscripto'`, `deleted_at IS NULL`) en las 3 lecturas; mesas vencidas (fecha/hora BA, UTC-3 fijo sin DST) excluidas de los dos listados y con estado DERIVADO `cerrada` sólo en el detalle (sin escritura de la columna, CU-22); `por-fecha` exige `desde`/`hasta` (faltan → 422 del parser FastAPI; invertidos → `DomainValidationError` con `errors[]`, PD-24) con rango inclusive; el PATCH reutiliza `_cargar_materias`/`_cargar_condiciones` de T3 (404 de catálogo), pre-chequeo `_ocupada` sobre `uq_mesa_unica` (PD-13: sin hora) + `IntegrityError` → 409 `mesa-duplicada` (cierre NFR-029), snapshots RB-11 en la misma transacción, sin gate temporal. Cuatro bugs del HARNESS del test corregidos durante el GREEN (del test, no de la spec): (a) `inscripto_en` NOT NULL sin default usable en SQLite — la corrección previa NO se había aplicado de hecho (la edición reportó éxito sin escribir; verificar toda escritura por shell es obligatorio en esta sesión); (b) 4 tests usaban `POST /grupos` como setup sin `mesa.crear`; (c) dos asserts comparaban id de MESA con id de GRUPO (`creada.json()["id"]` es el grupo); (d) `expire_all()` + acceso a atributos de ORM vencido en test async → `MissingGreenlet` (capturar UUIDs antes de expirar; `expire_on_commit=False` en el conftest).
- **L13 (2026-10-30)** — T5 completado. RED observado: 8/8 fallan (ruta aún inexistente). GREEN 8/8, suite 175 passed, ruff limpio. `GET /sigme/cobertura-mesas?convocatoria_id=` agregado a `router_mesas.py` (permiso `mesa.listar`; el path es raíz bajo `/sigme`, sin prefijo `/mesas` — §6 lo declara como `GET /cobertura-mesas?convocatoria_id=`). Implementación: `NOT EXISTS` correlacionado sobre `es_mesa_examen` — cualquier mesa viva (`deleted_at IS NULL`) del par cuenta como cubierta, sin filtros de fecha/vencidas/vida (es cobertura de CREACIÓN, distinto al listado RB-22) — sobre cross join de catálogo ACTIVO materia × condición (PD-15/A-SDD3-1) con los 4 nombres para lectura directa; schema `CoberturaPar`; 404 `convocatoria-no-encontrada` (patrón T1/T3); parámetro ausente → 422 del parser (PD-24). Un bug del harness del RED: falta `from sqlalchemy import select` en `test_cobertura_mesas.py`.
- **L14 (2026-10-30)** — T6 completado (documentación pasiva: verificación = readback estructural, sin RED/GREEN). README: sección nueva `SIGME — mesas y convocatorias (SDD-3, analisis.txt 6)` con la tabla de los 10 endpoints SDD-3 (rutas y permisos extraídos de los routers con evidencia, no de memoria) y notas de RB-22/RB-28/RB-29/RB-31, PD-12/PD-13/PD-15 y A-SDD3-6. Superficie pública: el README no la menciona (el contrato vive en `tests/unit/test_superficie_publica.py`) — sin cambios, como anticipó S6. Evidencia de cierre de SDD-3: T1 `16bfea9`, T2 `652102c`, T3 `47c3dbc`, T4 `283d663`, T5 `c303a31`; suite 175 passed y ruff limpio al cierre. Los slices T4 y T5 quedaron `medium`/`under_budget` en el assess de RDD (review pendiente en el slice; el slice T1–T3 sigue con su linaje congelado por el timeout).
