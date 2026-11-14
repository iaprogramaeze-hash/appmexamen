# ODD — Análisis profesional del BACKEND EPET36

## Objetivo
Producir un análisis de sistemas completo, de calidad profesional, del
**backend**, de modo que la posterior fase de Spec-Driven Development sea
inequívoca en cada etapa.

## Alcance  [ACLARADO POR EL USUARIO]
- **Producto de este proyecto:** SOLO el backend (API, modelo de datos,
  reglas, seguridad, requisitos no funcionales).
- **Fuera de alcance:** las 3 interfaces (Landing, SIGME web, SIGME-M móvil).
  Son proyectos futuros separados.
- Las 3 aplicaciones aparecen en el análisis **únicamente como consumidores
  del API** que imponen requisitos sobre él (p. ej. idempotencia para
  reintentos en red móvil), nunca como producto a diseñar.
- **OUT**: escribir código. Sólo documentos de análisis.

## Fuente base
`analisis.txt` (v2, 740 líneas) — esquema de datos y stack ya corregidos.

## Restricciones confirmadas por el usuario
- Sin cupo por mesa de exámenes.
- Sin etapa de aprobación de inscripciones.
- Límite de materias por condición: sólo previsto
  (`es_condicion.limite_materias`, inactivo; Previa 3 / Regular 8).
- Talleres = materias normales (`es_materia.es_taller`).
- Snapshot en `es_mesa_examen` con política RB-11 (recalcular sólo al editar
  la asignación de la mesa, nunca por renombre de la tabla origen).
- **Roles (P-08 RESUELTO)**: Alumno (SIGME-M), Secretario/a, Director,
  Administrador, Superadmin (SIGME). Landing **anónima**, sin roles.
- **`pr_preinscripcion` es AJENA al cuerpo principal**: preinscripción al
  próximo año lectivo, misma base de datos sólo por practicidad y para
  agilizar migración futura. SIN foreign keys hacia `pe_*` ni `es_*`.
- El **payload** del `POST /landing/preinscripcion` **está CONFIRMADO** (6 campos
  exactos): `nombre_alumno`, `documento`, `fecha_nacimiento`, `orientacion`,
  `nombre_tutor`, `email`. PD-01 y P-09 cerrados.
  ⚠️ El consentimiento de Ley 25.326 es un proceso FÍSICO externo posterior;
  no lo contempla el sistema. El aviso del art. 6 queda heredado a la landing.

## Cambio de alcance (2026-10-01) — mesas creadas EN GRUPOS  [CONFIRMADO]

**Qué cambia.** Las mesas ya **no** las crea el primer alumno en anotarse:
**las crea el secretario, en grupos, por fecha y hora.** Ejemplo del usuario:
grupo "Lengua, Lengua Extranjera, Matemática — día X 08:00"; otro grupo
"Taller de esto y de aquello — mismo día, otra hora".

**Por qué.** 6 cursos × 8-10 materias por orientación y **no alcanza un solo
día**; y para no hacer venir a un profesor que rinde a la tarde a la mañana
esperando su turno de aula.

**Confirmado:**
- **Grupo = `fecha` + `hora`, y nada más.** **Aula FUERA DE ALCANCE** (dicho
  explícitamente por el usuario). **Profesor FUERA**: P-08 cerró los roles sin
  rol docente; el G-03 ya lo dejaba fuera del sistema.
- El alumno **no gestiona el grupo**: se anota a la mesa que ya existe y sólo
  se le informa **día y hora**. El grupo es agrupación/presentación para
  SIGME-M, no una elección del alumno.
- SIGME: el secretario crea **todas** las mesas y las asigna a grupos
  (alta masiva: `materias[] × condiciones[] × fecha × hora`).

**Revoca / obliga a reinterpretar:**

| ID | Efecto del cambio |
|---|---|
| **RB-20** | **REVOCADA.** "El alta de mesas NO es tarea de administración" deja de ser cierto: vuelve a serlo, en bloque. |
| RB-05 | "Todas las mesas se rinden el mismo día" deja de ser cierto: la convocatoria abarca **N días** (un grupo por horario). La conclusión de **ventana única** se mantiene, cerrada antes de la primera fecha de grupo. |
| RB-16 | "Cerrado el día de rendir" → **la última fecha de grupo**. |
| RB-22 | **Se mantiene y gana peso**: es lo que permite crear ~180 mesas de una sin ensuciar listados ni impresiones. |

**Documentos afectados:** `analisis.txt` (RB-05, RB-16, RB-20, DDL §3.17/§3.18,
§7) · `01` (§1.2 "Mesa", §1.3 fila *"el secretario habilita las mesas"*
**se da vuelta**, §1.4 actantes) · `02` (`mesa.crear` deja de ser PENDIENTE) ·
`03` (evento "primera inscripción crea mesa") · `04`…`08`, `10`.
**`11` (landing/preinscripción) NO se afecta.**

**Abierto por este cambio:**

| ID | Pregunta | Bloquea |
|---|---|---|
| **PD-12** | ¿Se pueden **crear o mover** grupos con la ventana de inscripción **abierta**? | 04, 05, 06 |
| **PD-13** | ¿`uq_mesa_unica` debe incluir `hora`? Hoy no: impide dos mesas de la misma materia+condición el mismo día aunque cambie el horario. | esquema, 04 |
| ~~**PD-14**~~ | Destino de `es_convocatoria.fecha_mesa` → **RESUELTO (2026-10-01): SE ELIMINA.** El grupo define las fechas que se rinden (RB-27/RB-29); no queda fecha común que referenciar | — **RESUELTO** |

**Derivado de PD-14 — conceptos que se retiran:** **"fecha común de mesas"** y
**"mesa especial"**. Con grupos, una fecha inusual es simplemente un grupo
distinto; no hay fecha de la que desviarse. RB-05 conserva su **conclusión**
(una sola ventana de inscripción por convocatoria, cerrada antes de la primera
fecha de grupo) pero su **premisa** ("todas las mesas el mismo día salvo mesa
especial") queda **SIN VIGENCIA**.

**Nuevo requisito (2026-10-01): planilla de grupos.** El usuario quiere poder
imprimir, en el futuro, **todos los grupos detallando las mesas que se rinden**.
→ Nueva regla **RB-32** (tercer reporte, junto a los dos de RB-19; RB-19 deja
de decir "DOS reportes") y endpoint `GET /reportes/planilla-grupos/{convocatoria_id}`.
Aplica **RB-22** como toda impresión. **[CONFIRMADO — 2026-10-04]**: la
inclusión en la primera entrega está confirmada.

## Convenios
- Documentos en `analisis/`, numerados, en español profesional neutro.
- Cada documento cierra con checklist verificable y "siguiente paso".
- Reglas de negocio numeradas de forma estable (`RN-001`...).
- Casos de uso numerados (`CU-001`...) con flujo principal y alternativos.

## Checklist

### Fase 0 — Base
- [x] `analisis.txt` v2 corregido y validado (20 tablas, FKs resueltas)
- [x] Investigación de metodología y estados críticos (delegada, 43 fuentes)
- [x] Plan maestro de desglose (`analisis/00-plan-de-analisis.md`)

### Fase 1 — Marco
- [x] `01-glosario-y-alcance.md`
- [x] `02-actores-y-consumidores.md` (consumidores del API + matriz rol × permiso)
- [x] `03-eventos-y-gatillos.md` (tabla eventos → respuesta → casos de uso)
  (los tres cerrados con su checklist interno; commiteados en `53fceb4`)

### Fase 1R — Reapertura por cambio de alcance (mesas en grupos)
- [x] `analisis.txt`: **RB-20 REVOCADA**, nuevas RB-27…RB-31 (grupo, alta
      masiva, copia sincronizada, alumno no ve grupo, cobertura), DDL
      `es_grupo_horario` (§3.22) y `es_mesa_examen.grupo_id` (§3.18),
      PD-12…PD-14 en §7, endpoints de grupo y cobertura en §6
- [x] `01-glosario-y-alcance.md` — término **Grupo de mesas**; §1.3 fila
      *"el secretario habilita las mesas"* **invertida**; §1.4 actantes
- [x] `02-actores-y-consumidores.md` — `mesa.crear`: Alumno S→**—**,
      Secretario —→**S**; cero permisos nuevos (`mesa.crear`/`mesa.modificar`)
- [x] `03-eventos-y-gatillos.md` — E-01 reescrito, E-15/E-16/E-17 y S-21 nuevos
- **Regla**: **Fase 2 (`04`…`07`) no arranca** hasta cerrar esta reapertura —
  `04` se escribiría dos veces si no.

### Fase 1R.2 — PD-14 resuelto + planilla de grupos
- [x] `analisis.txt`: **`es_convocatoria.fecha_mesa` ELIMINADA** (DDL §3.17 +
      comentario `[CORREGIDO]`); RB-05 premisa SIN VIGENCIA (conclusión
      intacta); RB-19 → **TRES reportes**; PD-14 → RESUELTO; **RB-32**
      (planilla de grupos, `[PLANTEADO]`); endpoint
      `GET /reportes/planilla-grupos/{convocatoria_id}` en §6
- [x] `01`: filas **Mesa especial** y **Fecha común de mesas** retiradas y
      llevadas a §1.3 como vocabulario retirado; PD-14 → RESUELTO
- [x] `03`: T-06 sin `fecha_mesa`; E-09 extendido con la planilla
- [x] `02` (ripple de RB-19): endpoints de reporte, subobjetivo del
      Secretario, matriz `reporte.exportar` y §2.8 → "tres documentos"
- [x] **Contradicción detectada y corregida**: RB-32 decía "complementa a los
      **dos** reportes de RB-19" mientras RB-19 ya decía **TRES** → RB-32
      ahora dice "los dos reportes **originales**"

### Fase 1R.3 — Reconciliar `04-maquinas-de-estados.md`  [COMPLETADA 2026-10-05]
- [x] **Reescrito entero** (decisión del writer: la reconciliación quirúrgica
  costaba más — el cambio tocaba ME-01, ME-02, ME-06, ME-07, L66, el índice
  y el checklist de cierre). 438 → **591 líneas**.
  - ME-01 → **alta masiva del secretario** en `materias[] × condiciones[] ×
    fecha × hora` (RB-27/RB-28); el alumno ya no crea mesas (RB-30/RB-31).
  - **Máquina nueva del grupo** (`es_grupo_horario`) con sus PD abiertos
    (PD-12, PD-16, PD-18) modelados como preguntas, no como resoluciones.
  - `fecha_mesa`, "mesa especial" y "fecha común de mesas": **fuera**.
  - RB-32 incorporada a las lecturas de reporte (tres reportes, RB-19).
  - Checklist interno re-verificado contra el texto final; saldo de
    pendientes declarado (G-05, PD-12…PD-19, etc.).
- [x] Verificación (readback estructural, ejecutada):
  - `fecha_mesa|mesa especial|primero en anotarse|primer alumno` → **0 hits**
  - `RB-27|RB-28|RB-32|es_grupo_horario` → **41 hits**
  - 72 IDs citados (RB/PD/E/S/T/G/P): **todos existen** en `analisis.txt` +
    docs `01`/`02`/`03` — 0 ausentes.
  - UTF-8 válido, `Máquinas` sin mojibake; termina con checklist + "Siguiente
    paso".

### Fase 2 — Comportamiento
- [x] `04-maquinas-de-estados.md` (convocatoria, mesa, inscripción, usuario,
      grupo) — **reescrito en Fase 1R.3**; verificado y commiteado 2026-10-05
- [x] `05-casos-de-uso-sigme.md` — **escrito 2026-10-05**; verificado y
      commiteado (`326aee9`); RDD **aprobado** (ver Evidencia)
- [x] `06-casos-de-uso-sigme-m.md` — **escrito 2026-10-05**; verificado y
      commiteado (`04f1a85`); RDD `passive` (ver Evidencia)
- [x] `07-estados-criticos-y-excepciones.md` — **escrito 2026-10-05**; verificado
      y commiteado (`27ef091`); RDD `passive` (ver Evidencia). **Fase 2
      COMPLETA**

### Fase 3 — Reglas y no funcionales
- [x] `08-reglas-de-negocio.md` — **escrito 2026-10-05**; verificado y commiteado
      (`369ba92`); RDD `passive` (ver Evidencia). **RN-001…RN-059** sin huecos,
      mapeo RB-01…RB-32 completo
- [x] `09-requisitos-no-funcionales.md` — **escrito 2026-10-05**; verificado y
      commiteado (`c4180e2`); RDD `passive` (ver Evidencia). **NFR-001…NFR-054**
      (45 Medible / 9 `[POR DEFINIR]` tras cerrar PD-25 y PD-27)
- [x] `10-matriz-de-trazabilidad.md` (regla ↔ caso de uso ↔ entidad ↔ criterio)
      — **escrito 2026-10-05**; verificado y commiteado (`af214e0` + corrección
      `441af8f`); RDD `passive` (ver Evidencia). **Serie 00–11 COMPLETA**
- [x] `11-landing-preinscripcion.md` — **URGENTE**: contrato del
      `POST /api/v1/landing/preinscripcion`; la landing ya se está construyendo
      → **escrito, `[PROVISIONAL]`**. Checklist interno: **12/13 cerrados**
      (payload real aprobado 2026-10-04); el punto abierto depende de la
      verificación conjunta con el usuario — puntos (b), (c) y (d) del
      "Alcance de lo PROVISIONAL".

## Preguntas bloqueantes (heredadas de la investigación)
| ID | Pregunta | Bloquea |
|---|---|---|
| ~~P-01~~ | ~~Unicidad de inscripción: por mesa o por materia × turno~~ → **RESUELTO**: por **materia × convocatoria**. No hay turnos ni divisiones (RB-08, RB-15) | — **RESUELTO** |
| ~~P-02~~ | ~~¿Se puede anular la propia inscripción y hasta cuándo?~~ → **RESUELTO**: SÍ, para corregir error de elección; sólo dentro de la ventana de la convocatoria (RB-08b) | — **RESUELTO** |
| ~~P-03~~ | ~~Validación de condición: al inscribirse, el día, o ambas~~ → **RESUELTO**: SÓLO al inscribirse; cerrada la ventana la lista es fija (RB-17, RB-18) | — **RESUELTO** |
| ~~P-04~~ | ~~Quién rectifica notas cerradas y hasta cuándo~~ → **NO APLICA**: el sistema no guarda notas (RB-21) | — **RESUELTO** |
| ~~P-05~~ | ~~Instante de cierre: 23:59:59 vs 24:00 exclusivo~~ → **RESUELTO**: inclusivo hasta 23:59:59 de `fecha_fin_inscripcion`, comparando por fecha de calendario en la timezone del backend (RB-23) | — **RESUELTO** |
| ~~P-06~~ | ~~Canales y consentimiento de notificaciones~~ → **RESUELTO**: push / campanita in-app / email, sólo por eventos de usuario. Recordatorio 48 h → **v2** (RB-24, RB-25) | — **RESUELTO** |
| ~~P-07~~ | ~~SIGME-M offline real vs caché~~ → **RESUELTO**: lectura con caché (sin red ni token), escritura siempre online, ninguna cola offline (RB-26) | — **RESUELTO** |
| ~~P-08~~ | ~~Lista definitiva de roles~~ | — **RESUELTO** |
| ~~P-09~~ | ~~Payload exacto del `POST /landing/preinscripcion`~~ | — **RESUELTO** |

## Pendientes de diseño (numeración propia de `analisis.txt`, no confundir con P-xx)
~~PD-01~~ RESUELTO (payload de `pr_preinscripcion`) ·
PD-02 límites de `es_condicion.limite_materias` ·
PD-03 seed de roles/permisos · PD-04 reseteo de contraseña ·
PD-05 bitácora de auditoría · PD-06 estrategia de despliegue ·
PD-07 ~~notificaciones push~~ (CERRADO: RB-24) · PD-08 schemas de Postgres vs
prefijos (decidido: prefijos) · ~~PD-09~~ **RESUELTO** (catálogo de materias
por curso y orientación en `analisis/orientaciones-cursos-materias.md`) ·
PD-10 conjunto exacto de notificaciones in-app por rol ·
PD-11 recordatorio 48 h antes de la mesa (**deferido a v2**) ·
**PD-12 grupos con ventana abierta · PD-13 `hora` en `uq_mesa_unica`** (abiertos
por el cambio de alcance) · ~~PD-14 destino de `fecha_mesa`~~ **RESUELTO:
se elimina** · **PD-15 cobertura de mesas: origen del conjunto de pares
materia × condición · PD-16 unicidad de `es_grupo_horario` · PD-17 zona
horaria de `grupo.hora` · PD-18 grupos borrados con mesas vivas · PD-19
código HTTP del rechazo en `POST /inscripciones` · PD-20 catálogo de
materias sin estructura machine-readable (semilla y RB-31) ·
PD-21 nombre de la operación del catálogo de especialidades (`PATCH` vs
`GET|POST`, E-08/S-09 vs §6) · PD-22 efecto de escritura de
`PATCH /preinscripciones` (§6 lo declara "sólo consulta")** (abiertos:
revisión R3 del 2026-10-04; PD-20, de la revisión R3 del 2026-10-05;
PD-21 y PD-22, decisión del 2026-10-05)

**Infraestructura nueva prevista (RB-24/RB-25):** `us_dispositivo` (tokens
push), `ntf_notificacion` (campanita), `ntf_envio` (cola de email con
reintento — **obligatoria desde v1** por el password reset).

## Nuevas observaciones derivadas del payload de la landing
| # | Observación | Bloquea |
|---|---|---|
| ~~O-1~~ | ~~El payload NO trae `consentimiento`~~ → **RESUELTO**: proceso físico externo, fuera del sistema. Aviso art. 6 heredado a la landing | 11 |
| ~~O-2~~ | ~~`nombre_tutor` obligatorio si es menor?~~ → **RESUELTO**: TODOS los campos son obligatorios, así se impusieron | 11 |
| ~~O-3~~ | ~~`anio_lectivo` no se envía~~ → **RESUELTO**: `pr_ventana` (desde/hasta), una sola vigente; el backend toma el año de ahí | 11 |
| ~~O-4~~ | ~~¿2º envío = 409 o sobrescribe?~~ → **RESUELTO**: UPSERT (RB-13). Repetir el formulario NO es error; la validación previa la hace la landing | 11 |

**Nuevas reglas confirmadas:** RB-08 (unicidad por materia × convocatoria),
RB-08b (anulación), RB-08c (límite de condición al reinscribir),
RB-13 (upsert de preinscripción), RB-14 (ventana única vigente),
RB-15 (SIN división ni turno), RB-16 (la convocatoria delimita todo),
RB-17 (lista fija al cerrar la ventana), RB-18 (sin revalidación ni registro
de inasistencia), RB-19 (permiso de examen + acta volante),
RB-20 (**el primero en anotarse crea la mesa**; 6 cursos × 8-10 materias por
orientación, imposible habilitarlas a mano), RB-21 (el sistema no guarda
notas), RB-22 (sólo se entregan mesas con ≥1 inscripción activa),
RB-23 (límite inclusivo hasta 23:59:59, por fecha de calendario en la
timezone del backend), RB-24 (notificaciones: push / campanita / email, sólo
por eventos de usuario), RB-25 (cola de email obligatoria desde v1),
RB-26 (SIGME-M: lectura con caché, escritura siempre online).

**PD-09 resuelto (2026-10-04):** el detalle de materias por curso y
orientación llegó como anexo de datos en
`analisis/orientaciones-cursos-materias.md`; cubre las 2 orientaciones que
define el sistema (`analisis.txt` §3.13).

**Diseño nuevo:** columna `materia_id` en `es_mesa_inscripcion` (copia de
seguimiento) para imponer la unicidad por materia a nivel de BD; estado
`'anulado'` que no ocupa en el índice único.
**Eliminado:** `nota`, `nota_estado` y los estados `presente`/`ausente`/
`rendido` — el sistema no guarda resultados de la mesa (RB-21).
**Nueva tabla:** `pr_ventana` (patrón de `es_convocatoria`).

## Estado
- **Fase**: **ANÁLISIS COMPLETO** — `00`…`11` escritos y verificados (Fases 0,
  1, 1R, 1R.2, 1R.3, 2 y 3 todas cerradas).
- **Siguiente acción** (en este orden, sin saltos):
  1. **Fase 2: COMPLETA** (`04` OK · `05` OK · `06` OK · `07` OK).
  2. **Fase 3: COMPLETA** (`08` OK · `09` OK · `10` OK). **Serie `00`–`11`
     completa → el análisis está listo para SDD.**
  3. **Siguiente decisión del usuario** (no bloquea el cierre, pero sí el
     arranque de SDD): (a) **[RESUELTO — 2026-10-05]** los **7 casos sin id
     `PD-xx`** de la doc 10 §10.3 recibieron `PD-23`…`PD-29` en
     `analisis.txt` §7 y ya están anclados en los docs 01 y 05–10;
     (b) **[RESUELTO — 2026-10-05]** las **7 NFR
     `Propuesta`** (p95, disponibilidad, concurrencias, backoff) fueron
     aprobadas por el mantenedor tal como estaban escritas y hoy figuran
     como `Medible` en el doc 09; (c) los **6 `CU-xx` sin `RN`** que dejan
     el checklist del doc 08 sin cerrar.
- **Preguntas bloqueantes**: NINGUNA. **Pendientes de diseño abiertos**:
  PD-02, PD-03, PD-04, PD-05, PD-06, PD-10, **PD-12, PD-13**, PD-15…PD-29
  (salvo **PD-24…PD-27, cerrados** el 2026-10-05; PD-14 y PD-09 **RESUELTOS**:
  `fecha_mesa` se elimina y el catálogo de
  materias quedó en `analisis/orientaciones-cursos-materias.md`; PD-11
  deferido a v2) · las derivadas G-01…G-05 · más **`PD-23`, `PD-28` y
  `PD-29`** (de los 7 ex-casos sin id; PD-24…PD-27 ya cerrados) y **9 NFR
  sin número aprobado**, consolidados en `analisis/10-matriz-de-trazabilidad.md`
  §10.3 (80 ítems = 65 `[ABIERTA]` + 9 `[POR DEFINIR]` + 6 resueltos).
- **[CONFIRMADO — 2026-10-04]**: la **planilla de grupos (RB-32)** entra en la
  **primera entrega** (decisión del 2026-10-04; hasta entonces su alcance no
  estaba comprometido).
- **[RESUELTO — 2026-10-04]**: PD-09 — detalle de materias por curso y
  orientación, entregado como anexo de datos en
  `analisis/orientaciones-cursos-materias.md` (antes: entrada pendiente).
- **Alcance**: sólo el backend. Las 3 interfaces son proyectos futuros; entran
  únicamente como consumidores del API. **Aula y profesor: FUERA DE ALCANCE**
  — el grupo es únicamente `fecha` + `hora`.
- **Ruta**: delegada directa (documentación de análisis). Sin SDD todavía.
  **Trigger de delegación**: la reapertura toca 4 archivos no triviales
  (`analisis.txt` + `01` + `02` + `03`) → un único writer delegado.
- **Última sincronización**: **ANÁLISIS COMPLETO — serie `00`–`11`** (2026-10-05).
  `04` reescrito y corregido; `05`, `06`, `07`, `08`, `09`, `10` escritos,
  verificados y commiteados; PD-21/PD-22 abiertos; **PD-23…PD-29 creados por
  decisión del mantenedor y propagados a los docs 01 y 05–10**. Frontera
  revisada: **`e99f93b`** (`326aee9` → RDD `approved` + acknowledgment
  quemado; todo lo demás → `passive`, sin ceremonia).
  **7 casos sin id `PD-xx` → `PD-23`…`PD-29`** (decisión del mantenedor,
  2026-10-05): alcance de RB-22 sobre `GET /mesas-disponibles`, contrato de
  cuerpo de las
  respuestas de error, código del reintento `DELETE`, token de push, duración
  del bloqueo de login, paginación de `GET /mis-inscripciones` y alta
  individual de mesa (saldo del doc 04) — creados en `analisis.txt` §7 y
  trazados en doc 10 §10.3 y en los docs 01 y 05–09.

## Evidencia por tarea

| Tarea | Commit | Verificación | RDD assess | Resultado |
|---|---|---|---|---|
| `11-landing-preinscripcion.md` + sync checklist | `0f411e9` (rama `docs/analisis-landing-contract`) | Readback estructural: 425 líneas, secciones 11.1–11.7, 6 campos y 5 códigos presentes, 0 FK `pe_*`/`es_*`, `409` sólo por ventana cerrada, los 9 IDs citados (`RB-10/13/14/23/24/25`, `PD-01/03/06`) existen en `analisis.txt` | `passive` (`non_executable_only`), `review_due: false` | **Cerrada** (borde revisado: `0f411e9`) |
| `04-maquinas-de-estados.md` (reescritura total, Fase 1R.3) | *(ver `git log` — docs(analisis): reconcile state machines to group model)* | Readback estructural: 591 líneas; `fecha_mesa\|mesa especial\|primero en anotarse\|primer alumno` → **0 hits**; `RB-27\|RB-28\|RB-32\|es_grupo_horario` → **41 hits**; 72 IDs citados, **0 ausentes** en spec + docs 01/02/03; UTF-8 válido; cierra con checklist + "Siguiente paso" | `medium` (`slice_budget_reached`, 1409 líneas), lineage `review-12a176070d759144` | **Cerrada** — revisión terminal `escalated` / `native_stop_required` (informativa; la entrega la decide la política ordinaria del repo). Lens `review-reliability` → 4 CRITICAL: **R3-003 refutado**; **R3-004 = G-05** (quién dispara `planificada → cerrada → realizada`), **R3-001 = PD-18** (grupo borrado con mesas vivas), **R3-002 = PD-13** (`uq_mesa_unica` sin `hora`). Los dos últimos degradados en admisión por `unverified_location` → causalidad desconocida, que dispara la escalada. **Los tres ya estaban trackeados** (G-05, PD-18, PD-13): gap nuevo = ninguno |
| Corrección de datos en `04` (2 fechas, §3.12) + `05` + PD-21/PD-22 | `dfb594f`, `2dbd3ae`, `326aee9` | Readback estructural: `analisis.txt` +15/−0 (sólo §7), §6 sin tocar; `04` con 2 "fechas" en `§3.17` y `§3.12` para `us_sesion.modulo_id`; docs 01/03/05/02/11 sincronizados | assess inicial `medium` (`slice_budget_reached`, 10 paths / 2054 líneas desde `0f411e9`) → START falló `lens_context_budget_exceeded` (sin autoridad creada, `retry_safe`); re-evaluado con `--base-ref fee7ad3` → 7 paths / 649 líneas | **Cerrada** — START `review-dbce247f3410f9ec` (lens `review-reliability`), estado **`approved`**, acknowledgment ejecutado → `authority: burned`. **6 hallazgos advisory, todos `informational`** (4 WARNING, 2 SUGGESTION; R3-001…R3-006, sobre `analisis.txt` y `05`, no bloquean, sin corrección ofrecida). Frontera revisada: `326aee9` |
| `05-casos-de-uso-sigme.md` | `326aee9` | Readback estructural: **608 líneas**, 30 use cases (`CU-01`…`CU-30`), 11 secciones, **82 IDs externos únicos con 0 ausentes** en spec + docs 00/01/02/03/04/11, `fecha_mesa\|mesa especial\|primero en anotarse\|primer alumno` → **0 hits**, sin mojibake, cierra con checklist + "Siguiente paso" (→ `06`) | misma transacción que la fila anterior | **Cerrada** (borde revisado: `326aee9`, RDD `approved`) |
| `06-casos-de-uso-sigme-m.md` | `04f1a85` | Readback estructural **re-ejecutado por el orquestador**: 380 líneas, 12 `##` de sección, 11 ítems de checklist, `## Siguiente paso` presente, `CU-31`…`CU-42` (12 únicos, sin fugas de `CU-01`…`CU-30`), términos vetados → **0 hits**, mojibake → **0** (`Ã\|Â` con `-Encoding UTF8`; el patrón con `\|` final tiene alternativa vacía y cuenta todas las líneas — cuidado), **71 IDs externos únicos con 0 ausentes**, commit con mensaje de una línea y sin atribución | `passive` (`non_executable_only`, 380 líneas desde `32123c3`) → `review_due: false` | **Cerrada** (sin ceremonia de revisión; frontera avanza a `04f1a85`) |
| `07-estados-criticos-y-excepciones.md` | `27ef091` | Readback estructural **re-ejecutado por el orquestador**: 652 líneas, 12 `##`, **23 estados `EX-01`…`EX-23`**, 8 ítems de checklist, `## Siguiente paso` presente, sin BOM (`35,32,48`), términos vetados → **0 hits**, mojibake → **0** (`Ã\|Â` con `-Encoding UTF8`), **150 IDs (serie local `EX-xx` excluida) con 0 ausentes**, commit de una línea sin atribución, árbol limpio | `passive` (`non_executable_only`, 652 líneas desde `4ad9106`) → `review_due: false` | **Cerrada** — regla dura respetada: **ningún código HTTP sin fuente que lo declare**; los 13 estados sin contrato quedan `PENDIENTE` con su gap dueño; ningún `PD-xx`/`G-xx` cerrado. **13/23 estados sin respuesta declarada** (mayores: EX-04 convocatoria inactiva, EX-08 límite de condición, EX-09 anulación fuera de ventana, EX-15 `require_permiso()`); EX-16 marca el conflicto potencial de aplicar RB-22 a `GET /mesas-disponibles` (escondería mesas nuevas y bloquearía RB-31) |
| `08-reglas-de-negocio.md` | `369ba92` | Readback estructural **re-ejecutado por el orquestador**: 414 líneas, 9 `##`, **`RN-001`…`RN-059` (59 únicos, 0 huecos)**, **`RB-01`…`RB-32` completos (32 únicos)**, 116 IDs externos con **0 ausentes**, 6 ítems de checklist (1 sin cerrar, honesto: 6 RN no pueden citesarse en un `CU-xx` porque no hay CU de landing ni de la ley 25.326), `## Siguiente paso` presente, sin BOM, términos vetados → **0**, mojibake → **0**, commit de una línea sin atribución, árbol limpio | `passive` (`non_executable_only`, 414 líneas desde `fc2c21f`) → `review_due: false` | **Cerrada** — serie `RN` estable sin huecos, mapeo RB→RN completo (2 RB declarados "no es un invariante": RB-05 y RB-20, ambos revocados). Ningún gap abierto cerrado |
| `09-requisitos-no-funcionales.md` | `c4180e2` | Readback estructural **re-ejecutado por el orquestador**: 323 líneas, 12 `##`, **`NFR-001`…`NFR-054` (54 únicos, 0 huecos)**, sección `9.6` propia presente, `WCAG 2.2`/`WCAG2Mobile` citados, 93 IDs externos con **0 ausentes**, `## Siguiente paso` presente, sin BOM, términos vetados → **0**, mojibake → **0**, commit de una línea sin atribución, árbol limpio | `passive` (`non_executable_only`, 346 líneas / 2 paths desde `369ba92`) → `review_due: false` | **Cerrada** — criterio de cierre del plan cumplido: **0 filas sin estado** (36 `Medible` / 11 `[POR DEFINIR]` / 7 `Propuesta`); los 6 requisitos heredados a los clientes viven en tabla propia y **fuera de la serie NFR**. **Atención**: las 7 `Propuesta` (p95 300/500/2000 ms, presupuesto de errores 0,5 %, disponibilidad 99,5 %, 20 concurrencias, backoff 500 ms ×2 / 5 con ±20 % jitter) **no tienen respaldo en `analisis.txt` → requieren aprobación explícita**; `NFR-011` depende de PD-06; PD-05 sigue abierta |
| `10-matriz-de-trazabilidad.md` | `af214e0` + corrección `441af8f` | Readback estructural **re-ejecutado por el orquestador** (tras corregir una inconsistencia interna que encontré): 349 líneas, 5 `##`, **59 filas `RN-001`…`RN-059`**, **42 `CU-xx` cubiertos**, **7 filas `(sin ID)`**, **249 IDs externos con 0 ausentes** (los IDs fantasma `PD-23`/`PD-24` que había dejado el writer **eliminados**), 10.2 y 10.3 ahora coinciden (7 = 7), `## Siguiente paso` presente, sin BOM, términos vetados → **0**, mojibake → **0**, árbol limpio | `passive` (`non_executable_only`, 349 líneas desde `df8a19b`) → `review_due: false` | **Cerrada** — criterio de cierre cumplido con excepciones documentadas: **59/59 filas de 10.1 con correspondencia**; en la dirección inversa el resultado NO es cero y así se declara (6 `CU` sin `RN`, 2 `EX` sin `RN`, 2 transiciones sin cobertura, 5 eventos sin `CU`, 7 casos sin id). §10.3 consolida **87 ítems abiertos** = 69 `[ABIERTA]` + 11 `[POR DEFINIR]` + 7 `Propuesta`. §10.4 inventaría los 13 entregables con líneas medidas |
| `PD-23`…`PD-29` creados y propagados a los docs 01 y 05–10 | `e99f93b` (9 archivos: `analisis.txt` §7 + 8 docs) | `analisis.txt` §7 con 7 entradas `PD-23`…`PD-29` + nota de origen (decisión del mantenedor 2026-10-05); **readback re-ejecutado por el orquestador**: 0 claims obsoletos (`(sin ID)`, `sin identificador propio`, `pendiente sin PD propio`, `requiere decisión del mantenedor`), 29 `PD-xx` citados con **0 sin resolver**, docs 05–10 con **0 términos vetados**, mojibake **0**, doc 10 sin filas `(sin ID)` (7 filas con id), primera tabla 10.3 = 28 filas, §10.4 con las 13 líneas medidas coincidiendo con la realidad, 1 `## Siguiente paso` por doc, árbol limpio | assess base `c697155`: **`medium`** (`executable_change` sobre `analisis.txt`), 9 paths / 370 líneas → `review_due: false` por **`under_budget`** | **Cerrada** — pero el rango medium **queda pendiente en el slice**: si este alcance crece hasta ~400 líneas autorizadas, toca START con consentimiento del mantenedor (no se salta con `passive`) |
| Aprobación de las 7 NFR `Propuesta` → `Medible` (docs 09, 10 y este archivo) | *(ver `git log` — docs(analisis): approve the seven proposed NFR values)* | Readback estructural: doc 09 → **43 filas `Medible`** / **11 `[POR DEFINIR]`** / **0 `Propuesta`** (NFR-001…NFR-006 y NFR-032 ahora `Medible — aprobada por el mantenedor 2026-10-05`, con la dependencia de PD-06 en NFR-006); doc 10 → **0** celdas de estado `Propuesta`, bloque NFR de §10.3 = **11 filas**, **Recuento: 80 ítems = 69 `[ABIERTA]` + 11 `[POR DEFINIR]`**; §10.4 re-medido: **13/13** líneas coinciden (09 = 319, 10 = 348); mojibake **0**; términos vetados en docs 09/10 = **0**; tablas contiguas | N/A — sólo markdown, sin ejecutable | **Cerrada** — cambio limitado a `09`, `10` y este archivo; números, métodos de verificación, fuentes e IDs intactos; rollback = revertir este commit |

## Notas
- Engram quedó operativo otra vez (v3.0.0, doctor 10/10 tras reparar el
  sync-target); este archivo sigue siendo el espejo local de recuperación.
