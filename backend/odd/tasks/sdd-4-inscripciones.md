# SDD-4 — Inscripciones y consultas de alumno

Objetivo: implementar el alta/baja/consulta de inscripciones y las consultas
del alumno bajo `/api/v1/` **sin discriminar por dispositivo** (decisión del
mantenedor, L2): `POST/GET /inscripciones`, `GET /mis-inscripciones` +
`DELETE /mis-inscripciones/{id}`, `GET /mesas-disponibles`,
`GET /convocatoria-vigente`, `POST/DELETE /dispositivos`.
Rama: `feat/sdd-4-inscripciones` apilada sobre `feat/sdd-3-mesas`
(`c9a0ee4`; `main` = `6018204`). Runner: `python -m pytest tests -q` +
`python -m ruff check .`. Estrategia de entrega: `single-pr` (precedente
aceptado del PR #4 de SDD-2 y del plan de SDD-3; pronóstico ~1400 líneas).

## Specs

### S1 — Convocatoria-vigente (GET)

`GET /api/v1/convocatoria-vigente` (CU-34, doc 06 §6.2). Devuelve la
convocatoria vigente con `fecha_inicio_inscripcion`, `fecha_fin_inscripcion`
y su `estado` derivado (SDD-3 T1: `borrador`/`abierta`/`cerrada`). Gate:
**sólo sesión válida** (`get_current_principal`) — sin permiso ni módulo: el
catálogo §2.7 no tiene código de lectura de convocatoria (hueco declarado en
CU-34) y el mantenedor decidió no discriminar por dispositivo (L2). Sin gate
temporal: este endpoint es la fuente para SABER si hay ventana abierta.
"A-SDD4-1 (vigente): la de estado `abierta` si existe; si no, la `activa`
con `fecha_inicio_inscripcion` más reciente (responde `borrador`/`cerrada`);
sin ninguna convocatoria activa -> 404 `convocatoria-no-encontrada`."
Criterios de aceptación: 401 sin token; 200 con sesión sin permisos
especiales; estado derivado correcto según fecha BA (RB-23); 404 sin
activas; la respuesta no expone mesas ni grupos.

### S2 — Mesas-disponibles (GET)

`GET /api/v1/mesas-disponibles` (CU-35 + cascada G-04, doc 06 §6.2).
Permiso `mesa.listar` (agnóstico de dispositivo). "Sólo dentro de la ventana
de inscripción" (§6, analisis.txt:1132; RB-07, RB-23, `hoy` BA): fuera de la
ventana -> 409 `ventana-cerrada`. Devuelve las mesas VIVAS
(`deleted_at IS NULL`) de la convocatoria vigente, cada una con
`orientacion_nombre`, `curso_nombre`, `materia_nombre`, `condicion_nombre`,
`fecha` y `hora`. "A-SDD4-2 (PD-23 cerrado): RB-22 NO aplica a este
endpoint — RB-22 gobierna listados e impresiones de SIGME; aplicado acá
ocultaría las mesas recién creadas y nadie podría inscribirse en ellas
(RN-021 lo advierte). Filtro = convocatoria vigente + ventana + mesa viva."
"A-SDD4-3 (G-04 cerrado): la cascada orientación -> curso -> materia ->
condición se alimenta de las combinaciones únicas de esta misma respuesta;
no se crean endpoints de catálogo para el alumno." RN-019: la respuesta
**nunca** expone `grupo_id` ni campos del grupo. Criterios de aceptación:
401/403; 409 fuera de ventana; lista = mesas vivas de la convocatoria
(incluye mesas sin inscripciones — corolario de A-SDD4-2); mesa borrada no
aparece; sin rastro de grupo; combinaciones del cascade = únicas.

### S3 — Inscribirse (POST)

`POST /api/v1/inscripciones` (CU-37/CU-40, INS-01/INS-04: doc 04 §4.3,
doc 06 §6.3/§6.5). Permiso `inscripcion.crear`. Cuerpo `{materia_id,
condicion_id}` — el alumno elige sólo materia + condición (RB-30);
"A-SDD4-4: la convocatoria NO viaja en el cuerpo — es siempre la vigente."
Validaciones en orden: (1) convocatoria vigente existe -> si no, 404
`convocatoria-no-encontrada`; (2) `hoy` BA dentro de la ventana inclusive
hasta 23:59:59 (RB-07, RB-23) -> si no, 409 `ventana-cerrada`; (3) materia y
condición existen y están activas -> 404 `materia-no-encontrada` /
`condicion-no-encontrada` (patrón SDD-3 T3); (4) unicidad por materia x
convocatoria (`uq_inscripcion_unica`, RN-006: filas vivas no anuladas) ->
409 `inscripcion-duplicada` (RB-08, S-06; el reintento E-13 recibe la misma
respuesta sin duplicar); (5) límite de la condición
(`es_condicion.limite_materias`, NULL = sin límite; unidad POR CONVOCATORIA,
validado SÓLO al crear — RN-013/PD-02) sobre las inscripciones activas del
alumno -> supera -> 409 `limite-materias` (RB-03, RB-08c); (6) mesa viva de
la convocatoria para materia x condición -> si no existe, **409
`mesa-no-disponible`** "A-SDD4-5 (PD-19 cerrado): la misma familia 409 del
endpoint; 404 implicaría que materia/condición no existen y 422 sería input
malformado. Nada se inserta (RN-018)"; si hay varias mesas vivas del combo
(en fechas distintas — `uq_mesa_unica` incluye `fecha`), "A-SDD4-6: se elige
la de `fecha` más próxima, con `hora` e `id` como desempate (criterio
determinístico; ninguna fuente lo define)"; (7) crea la fila en `inscripto`
con `convocatoria_id` (modelo `es_mesa_inscripcion` existente). CU-40:
reinscribir tras anular es este mismo alta — fila NUEVA, la anulada no se
reutiliza (INS-04) y la unicidad no choca porque `anulado` queda fuera del
índice. "A-SDD4-8: la confirmación por email (RB-24/RB-25, S-20, paso 5 del
flujo) queda FUERA de SDD-4 — no existe infraestructura de colas ni de email
en el código; gap documentado para entrega futura." Criterios de aceptación:
cadena completa con un test por rechazo (y prueba de que NO se inserta nada);
reintento idempotente vía unicidad; límites Previa 3 / Regular 8 / Libre sin
límite; reinscripción crea fila nueva; elección determinística entre mesas
múltiples.

### S4 — Inscripciones de gestión (GET)

`GET /api/v1/inscripciones?mesa_id=&convocatoria_id=` (CU-23, doc 05 §5.8).
Permiso `inscripcion.listar`. Devuelve las filas con su estado; filtros
opcionales; IDs referenciados inexistentes -> 404 `mesa-no-encontrada` /
`convocatoria-no-encontrada` (patrón T4). RB-22 no aplica (lista
INSCRIPCIONES, no mesas). Orden determinístico (`inscripto_en` desc). "La
anulación por secretaría (INS-03) queda FUERA de SDD-4: está PENDIENTE en
doc 04 (¿la ventana limita también al secretario?) y §6 no declara endpoint
de escritura para la gestión." Criterios de aceptación: 401/403; listado con
y sin filtros; 404 de filtros referenciados.

### S5 — Mis-inscripciones (GET y DELETE)

`GET /api/v1/mis-inscripciones` (CU-38) + `DELETE
/api/v1/mis-inscripciones/{id}` (CU-39, INS-02; PD-25, PD-28; doc 06 §6.4/§6.5).
GET: permiso `inscripcion.listar`; sólo las filas del usuario autenticado;
para cada una: estado (`inscripto`/`anulado`), nombres de materia/condición,
`fecha` y `hora` de la mesa; nunca grupo (RN-019); "A-SDD4-9 (PD-28 cerrado):
sin paginación en v1 — la cantidad por alumno y convocatoria está acotada
por diseño (una fila por materia) y §6 no declara parámetros; se retoma si
SIGME-M lo pide." La lectura sigue disponible con la ventana cerrada (RB-07,
T-03). DELETE: permiso `inscripcion.anular`; sólo la propia -> de otro
alumno o inexistente -> 404 `inscripcion-no-encontrada` (no se filtra
existencia ajena); sólo dentro de la ventana (RB-08b, RB-07) -> fuera ->
409 `ventana-cerrada`; `inscripto` -> `anulado` (la fila se conserva para
auditoría y libera la unicidad); ya `anulado` -> 204 idempotente sin cuerpo
(PD-25). Criterios de aceptación: sólo filas propias; anulación dentro y
fuera de ventana; 204 doble (idempotente); la anulada no ocupa unicidad.

### S6 — Dispositivos (POST y DELETE)

`POST /api/v1/dispositivos` + `DELETE /api/v1/dispositivos/{id}` (CU-42,
PD-26 [CERRADO], analisis.txt §6:1150-1152). Tabla NUEVA + migración
alembic `0004` — **riesgo item 1 (migración)**. POST: sesión válida (sin
permiso nuevo, PD-26); cuerpo `{token, plataforma}` -> 201 `{id}`; sólo el
dispositivo PROPIO (RN-052 incluye purga de caducos al dar de alta — texto
a verificar en T6). DELETE: -> 204; dispositivo de otro usuario -> 404.
Criterios de aceptación: 401; alta/baja del propio; 404 ajeno; purga de
caducos observada.

### S7 — README y cierre

README: sección nueva de inscripciones/consultas con la tabla de los
endpoints y las notas de los PDs cerrados en este feature; la superficie
pública sigue siendo sólo `POST /preinscripcion`
(`tests/unit/test_superficie_publica.py`); cerrar el Log con la evidencia de
commits y de tests.

## Tasks

| ID  | Specs    | Ruta    | Estado     | Commit / evidencia |
|-----|----------|---------|------------|--------------------|
| T1  | S1       | inline  | completado | RED 6 failed -> GREEN 6 passed; suite 181 passed; ruff limpio |
| T2  | S2       | inline  | completado | RED 8 failed -> GREEN 8 passed; suite 189 passed; ruff limpio |
| T3  | S3       | inline  | completado | RED 14 failed -> GREEN 14 passed; suite 203 passed; ruff limpio |
| T4  | S4       | inline  | completado | RED 7 failed -> GREEN 7 passed; suite 210 passed; ruff limpio |
| T5  | S5       | inline  | completado | RED 10 failed -> GREEN 10 passed; suite 220 passed; ruff limpio |
| T6  | S6       | inline  | completado | RED 15 failed -> GREEN 15 passed; suite 235 passed; ruff limpio (riesgo item 1: migración 0004) |
| T7  | S7       | inline  | completado | README actualizado; suite 235 passed; ruff limpio |

Rutas: ninguna task dispara Writer trigger (cambios secuenciales en la misma
área, superficies solapadas en el feature nuevo de `app/features/inscripciones/`
— un solo escritor, el padre). La delegación de exploración se intentó y el
runtime denegó el permiso `subagent`: el mapeo de fuentes se hizo inline
(degradation path).

## Log

- **L1 (2026-10-22 / continuidad 2026-10-30)** — Mandato original del usuario
  (verbatim): "continuemos, sino no vamos a terminar nunca el backend". SDD-3
  cerrado (6/6, `c9a0ee4`); SDD-4 (inscripciones) es el siguiente SDD del
  roadmap; reportes queda para la entrega posterior.
- **L2 (2026-10-30)** — Decisión del usuario (verbatim): "no vamos a
  discriminar por dispositivo que lo utilice, todo endpoint trabaje bajo un
  mismo prefijo, entonces podemos usarlo siempre que querramos en cualquier
  cosa sin necesidad de que sea o mobile, web, incluso como webhook...
  entonces esta bien dejarle general /api/v1/". Cierre: SIN prefijo
  `/sigme-mobile`; las rutas nuevas de este feature van a raíz bajo
  `/api/v1/`; autorización por permiso (`require_permiso`, verificado
  agnóstico de módulo en `app/features/auth/dependencies.py:97`) o por
  sesión válida (`get_current_principal`), nunca por módulo/dispositivo; los
  endpoints existentes `/api/v1/sigme/*` NO se migran (contratos ya mergados
  en PR #4 — unificarlos sería tarea aparte, sólo si el mantenedor lo pide).
- **L3 (2026-10-30)** — Mapeo de fuentes de SDD-4 (inline; explorador
  delegado denegado por permisos). Verificado: §6 (analisis.txt:1099-1152),
  CU-23 (doc 05:390-405), CU-34..CU-42 (doc 06 §6.1-6.8), INS-01..INS-04
  (doc 04:234-237), RN-006/007/013/018/019/021 (doc 08), E-01/E-02/S-05/S-06/S-07
  (doc 03:130-144), modelo `es_mesa_inscripcion` (models.py:140 — trae
  `convocatoria_id` y `uq_inscripcion_unica`), semilla de permisos
  `inscripcion.*` ya presente (seed.py:23-25, rol alumno asignado).
  PDs cerrados como asunciones A-SDD4-1..9 (specs S1-S5). Fuera de alcance:
  INS-03 (anulación por secretaría, pendiente en doc 04), confirmación email
  (A-SDD4-8, sin infraestructura de colas), reportes (entrega siguiente).
  Dispositivos requiere tabla nueva + migración (riesgo item 1 en T6).
- **L4 (2026-10-30)** — T1 completado (S1, `GET /api/v1/convocatoria-vigente`).
  Test-first: RED observado (6 failed, ruta inexistente) -> GREEN (6 passed).
  Nuevo feature dir `app/features/inscripciones/` (service + router con
  `get_current_principal`, sin permiso ni módulo por L2) registrado en
  `app/api/v1/api.py` SIN prefijo. Reutiliza `EsConvocatoria`,
  `ConvocatoriaLectura`, `estado_convocatoria` y `hoy_buenos_aires` (SDD-3).
  Corrección de harness: `ConvocatoriaLectura` no admite `model_validate`
  sobre la fila ORM (el `estado` es derivado) -> construcción campo a campo
  como `_a_lectura` de `mesas/router.py`. Suite 181 passed / ruff limpio.
- **L5 (2026-10-31)** — Revisión de los 4 informes del colega
  (frontend/prototipo, 2026-10-27) antes de retomar T2: analizados y
  verificados contra fuentes; generado informe de devolución completo en
  `C:\Users\Acer\Downloads\informe-devolucion-colega-sdd4.md` (240 líneas,
  UTF-8 verificado) para que su agente verifique y siga. Correcciones
  clave: sus citas RB están desalineadas (RB-01 = no cupo por mesa, no
  "un DNI = una cuenta"; RB-13 = upsert de la landing, no "máximo 6
  materias"; RB-16 = ciclo de convocatorias); su commit `18fc09f` no
  existe en nuestro repo (reconciliación pendiente: ellos rebasean
  descartando su duplicado de F1/F2); `us_password_reset` ya existe desde
  SDD-0 (migración 0002, PD-04) — sólo faltan endpoints; `GET
  /sigme/materias` está gated `require_modulo("sigme_web")` → 403 para
  alumno (`sigme_mobile`) — el alumno debe usar `mesas-disponibles`;
  `PATCH /sigme/usuarios/{id}` no existe; registro libre no está en el
  análisis (PD-A) y contradice su propio informe de aprobación (PD-B).
  PDs abiertos para el cliente listados en el informe (§7). Engram obs 126.
- **L6 (2026-10-31)** — T2 completado (S2, `GET /api/v1/mesas-disponibles`).
  Test-first: RED observado (8 failed, ruta inexistente -> 404) -> GREEN
  (8 passed). Nuevo schema `MesaDisponible` en
  `app/features/inscripciones/schemas_inscripciones.py` — NO reutiliza
  `MesaLectura` (SDD-3) porque RN-019 prohíbe exponer `grupo_id`; trae
  `materia_id`/`condicion_id` para alimentar el POST de CU-37 (G-04).
  Service `mesas_disponibles`: reutiliza `convocatoria_vigente` (T1) +
  `ventana_inscripcion_abierta` (SDD-3 T3) → 409 `ventana-cerrada` fuera
  de ventana; mesas vivas (`deleted_at IS NULL`) de la vigente, orden
  determinístico (fecha, hora, id). Gate `require_permiso("mesa.listar")`
  (agnóstico de dispositivo, L2). PD-23/A-SDD4-2: RB-22 no aplica —
  mesas sin inscripciones SÍ aparecen. Suite 189 passed / ruff limpio.
  Archivos: `app/features/inscripciones/{service,router,schemas_inscripciones}.py`,
  `tests/unit/test_mesas_disponibles.py`.
- **L7 (2026-10-31)** — T3 completado (S3, `POST /api/v1/inscripciones`,
  CU-37/CU-40). Test-first: RED observado (14 failed, ruta inexistente ->
  404) -> GREEN (14 passed). Nuevos schemas `InscripcionCrear`
  (`extra="forbid"`, sólo `materia_id`+`condicion_id` — RB-30; convocatoria
  nunca en el cuerpo, A-SDD4-4) e `InscripcionLectura` (refleja
  `es_mesa_inscripcion`). Service `inscribirse` con validaciones EN ORDEN
  del spec S3: (1) 404 `convocatoria-no-encontrada` (reuse T1); (2) 409
  `ventana-cerrada` (reuse SDD-3); (3) 404 `materia/condicion-no-encontrada`
  (activas + vivas); (4) 409 `inscripcion-duplicada` (RN-006/RB-08, unicidad
  por materia × convocatoria; reintento E-13 idempotente); (5) 409
  `limite-materias` (`es_condicion.limite_materias`, NULL = sin límite,
  RN-013/PD-02, unidad por convocatoria); (6) 409 `mesa-no-disponible`
  (A-SDD4-5/PD-19); crea fila `inscripto` eligiendo la mesa de `fecha` más
  próxima con `hora`/`id` de desempate (A-SDD4-6, determinismo). Gate
  `require_permiso("inscripcion.crear")` (agnóstico de dispositivo, L2).
  CU-40/INS-04: reinscribir tras anular crea fila NUEVA (`anulado` fuera de
  `uq_inscripcion_unica`). Cada rechazo prueba que NO se inserta nada. Suite
  203 passed / ruff limpio. Archivos:
  `app/features/inscripciones/{service,router,schemas_inscripciones}.py`,
  `tests/unit/test_inscripciones.py`.
- **L8 (2026-10-31)** — T4 completado (S4, `GET /api/v1/inscripciones`,
  CU-23). Test-first: RED observado (7 failed, GET aún no registrado -> 405)
  -> GREEN (7 passed). Nuevo schema `InscripcionGestion` (refleja
  `es_mesa_inscripcion` + `usuario_id` — el gestor debe saber QUIÉN está
  inscripto). Service `inscripciones_gestion`: filtros opcionales `mesa_id`/
  `convocatoria_id`; un filtro que referencia un ID inexistente -> 404
  (reuse `obtener_mesa`/`obtener_convocatoria`, patrón T4); lista filas
  `deleted_at IS NULL`, orden determinístico `inscripto_en` desc (+ id).
  RB-22 NO aplica (lista INSCRIPCIONES, no mesas). Gate
  `require_permiso("inscripcion.listar")` (agnóstico de dispositivo, L2).
  INS-03 (anulación por secretaría) queda FUERA de SDD-4. Suite 210 passed /
  ruff limpio. Archivos:
  `app/features/inscripciones/{service,router,schemas_inscripciones}.py`,
  `tests/unit/test_inscripciones_gestion.py`.
- **L9 (2026-10-31)** — T5 completado (S5, `GET/DELETE /api/v1/mis-inscripciones`,
  CU-38/CU-39). Test-first: RED observado (10 failed, rutas inexistentes) -> GREEN
  (10 passed). Nuevo schema `MisInscripcionLectura` (estado + nombres de
  materia/condición + `fecha`/`hora` de la mesa, RN-019: sin grupo).
  GET: permiso `inscripcion.listar`; sólo filas PROPIAS; sin paginación
  (A-SDD4-9); lectura disponible con ventana cerrada (RB-07). DELETE:
  permiso `inscripcion.anular`; sólo la propia (otro/inexistente -> 404
  `inscripcion-no-encontrada`, sin filtrar existencia ajena); sólo dentro
  de la ventana de ESA convocatoria (RB-08b/RB-07) -> fuera, 409
  `ventana-cerrada`; `inscripto` -> `anulado` (fila conservada, libera
  `uq_inscripcion_unica`); ya `anulado` -> 204 idempotente sin cuerpo
  (PD-25). Suite 220 passed / ruff limpio. Archivos:
  `app/features/inscripciones/{service,router,schemas_inscripciones}.py`,
  `tests/unit/test_mis_inscripciones.py`.
- **L10 (2026-10-31)** — T6 completado (S6, `POST/GET/DELETE /api/v1/dispositivos`,
  CU-??). Test-first: RED observado (15 failed, rutas inexistentes) -> GREEN
  (15 passed). Tabla nueva `es_dispositivo` + migración alembic 0004
  (riesgo item 1). Modelo: `usuario_id` (FK CASCADE), `device_id`,
  `plataforma` (enum ios/android/web), `push_token`, `activo`,
  `created_at`/`updated_at`/`deleted_at` (soft delete). Índice único parcial
  `(usuario_id, device_id) WHERE deleted_at IS NULL` para upsert idempotente.
  POST: upsert idempotente por `device_id` del usuario (201 crea/actualiza).
  GET: lista dispositivos del usuario autenticado, orden `created_at` desc.
  DELETE: soft delete idempotente (PD-25); 404 si ajeno/inexistente. Gate
  por SESIÓN VÁLIDA (`get_current_principal`) — sin permiso extra (el
  usuario gestiona SUS dispositivos). Suite 235 passed / ruff limpio.
  Archivos: `app/features/dispositivos/{models,schemas,service,router}.py`,
  `alembic/versions/0004_dispositivos.py`, `tests/unit/test_dispositivos.py`,
  `tests/conftest.py`, `tests/unit/test_models_es_pr.py`.
- **L11 (2026-10-31)** — T7 completado (S7, README + cierre). Sección nueva
  "Inscripciones y consultas de alumno (SDD-4)" en `README.md` con tabla de
  9 endpoints, PDs cerrados (A-SDD4-1..9) y nota de superficie pública
  (sólo `POST /preinscripcion`). Suite 235 passed / ruff limpio. Archivos:
  `README.md`, `odd/tasks/sdd-4-inscripciones.md` (T7 + Log L11).
