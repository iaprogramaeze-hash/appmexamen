# 08 · Reglas de negocio — Backend EPET36

**Respuesta corta:** este documento fija **59 invariantes** con identificador
estable (`RN-001`…`RN-059`). Cada regla que los documentos 05, 06 y 07 usaron
para aceptar o rechazar una operación queda aquí redactada como **afirmación
comprobable** — con su fuente, los estados y las tablas que restringe, la forma
concreta en que se violaría y el mecanismo que la previene—: 57 invariantes en
doce dominios (8.1) y dos más, `RN-058` y `RN-059`, que le asigna la Ley
25.326 (8.3). Cubre las 32 reglas `RB-01`…`RB-32` de `analisis.txt` §4 —con
nota explícita de **"no es un invariante"** para las dos que ya no tienen
vigencia—, los índices y las restricciones del DDL de §3, y los contratos de
ventana, unicidad, listados, landing, notificaciones y degradación. **No se
cierra ningún `PD-xx` ni ningún `G-xx`:** donde una invariante depende de una
decisión abierta se enuncia **condicionada** y se nombra el hueco —con su
`PD-xx`— que la decide (8.5).

Vocabulario: se usan los términos de `01-glosario-y-alcance.md` (1.2 y 1.3,
incluido el vocabulario prohibido y retirado), los actores y la matriz
rol × permiso de `02-actores-y-consumidores.md` (2.2 y 2.4), los eventos de
`03-eventos-y-gatillos.md` (3.1–3.4) y las transiciones de
`04-maquinas-de-estados.md` (4.6). Los casos de uso citados salen de
`05-casos-de-uso-sigme.md` (`CU-01`…`CU-30`) y de
`06-casos-de-uso-sigme-m.md` (`CU-31`…`CU-42`); los estados críticos, de
`07-estados-criticos-y-excepciones.md` (`EX-01`…`EX-23`); el contrato de la
landing, de `11-landing-preinscripcion.md`. Toda cita `RB-xx` y `PD-xx`
remite a `analisis.txt` (§4 y §7); `§n.m` remite a la sección de ese archivo;
`E-xx`, `S-xx` y `T-xx` remiten a doc 03; `G-xx` a doc 01 §1.5.2; `C-xx`,
`ME-xx`, `INS-xx`, `US-xx`, `SES-xx` y `GR-xx` a doc 04.

## Rápido recorrido

1. **8.1** — las 57 invariantes `RN-001`…`RN-057` en doce dominios, **una por
   fila**: afirmación comprobable, fuente, estados y tablas, y forma de
   violación.
2. **8.2** — cómo se previene cada RN y su trazabilidad a casos de uso y
   transiciones.
3. **8.3** — reglas derivadas de la Ley 25.326: las dos que sí son
   invariantes (`RN-058`, `RN-059`) y las tres que se resuelven en el doc 09.
4. **8.4** — cobertura `RB-xx` → `RN-001…`: ninguna regla de `analisis.txt`
   queda sin invariante ni sin nota de "no es un invariante".
5. **8.5** — pendientes heredados: **PD-24…PD-27 cerrados**; los demás, con el
   hueco que lo mantiene abierto.
6. **Checklist** — incluye la verificación del criterio de cierre del plan
   (plan §3.08): ninguna RN contradice a otra y cada RN queda trazada a un
   `CU-xx` o al contrato que la contiene.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Alcance** | Los tres consumidores del backend (SIGME web, SIGME-M y landing) y todas las reglas de `analisis.txt` §4 y §3. Los estados críticos, los códigos HTTP y los casos de uso se definen en los docs 05, 06 y 07; aquí se referencian, no se redefinen. | plan §3 (08); doc 07 §Convenciones; doc 05 §Convenciones |
| **Identificadores** | `RN-001…` es una **serie local** de este documento, de tres dígitos, **sin huecos y sin duplicados**, con **una invariante por fila**; empieza en `RN-001` y no se reutiliza ninguna serie ajena. `RB-xx`/`PD-xx` → `analisis.txt` (§4, §7); `E-xx`/`S-xx`/`T-xx` → doc 03; `G-xx` → doc 01 §1.5.2; `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` → doc 04; `CU-01`…`CU-42` → docs 05 y 06; `EX-xx` → doc 07; `O-x` → `analisis.txt` §3.20. | plan §3 (08.1); doc 07 Convenciones |
| **Relación `RB-xx` ↔ `RN-001…`** | Son dos series de naturaleza distinta y **no se confunden**: `RB-xx` es la **regla tal como está declarada en la fuente** (`analisis.txt` §4), en voz del análisis; `RN-001…` es la **misma regla normalizada como afirmación comprobable**, en voz de este documento. Una `RB-xx` puede originar varias RN y una RN puede reunir varias `RB-xx`; **RN no sustituye a RB, no la reescribe y no la renumera**. El mapa completo está en 8.4. | `analisis.txt` §4; plan §3 (08.1), §5 |
| **Invariante** | Afirmación que se sostiene **en todo momento** y que se puede comprobar con una consulta SQL, una restricción de la base (índice, `CHECK`, FK, vista) o una prueba de integración. No es un deseo ni una recomendación: o se cumple, o la fila de "Viola cuando" describe el estado roto. | plan §3 (08.1, 08.2) |
| **Fuente** | Cada RN cita de dónde sale: `RB-xx` y `§n.m` de `analisis.txt`, `PD-xx` cuando la regla depende de una decisión abierta, `EX-xx` del doc 07, `CU-xx` de los docs 05/06, y `E-xx`/`S-xx`/`T-xx` o `C-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx` cuando el evento o la transición son parte de la regla. | docs 03, 04, 05, 06, 07; `analisis.txt` |
| **PENDIENTE** | Este documento **no cierra** ningún `PD-xx` ni `G-xx`. Una RN que depende de una decisión abierta se escribe **condicionada** y nombra en su propia fila el hueco que la decide; los casos que no tenían ID hoy están anclados a `PD-23`…`PD-29` en `analisis.txt` §7. | doc 05 §5.11; doc 06 §6.8; doc 07 §7.8; `analisis.txt` §7 |
| **Ventana y reloj** | Toda ventana se **constata** en cada request por fecha de calendario en `America/Argentina/Buenos_Aires`, inclusive hasta las 23:59:59; el reloj autoritativo es el del backend, nunca el del dispositivo; no hay ningún job programado en v1. | RB-23, RB-24; doc 03 §3.2; doc 07 §7.3 |
| **Vocabulario** | Se respetan los términos de doc 01 §1.2 y el vocabulario prohibido y retirado de §1.3: convocatoria ≠ mesa, preinscripción ≠ inscripción, grupo de mesas = fecha + hora, el alumno elige sólo materia + condición. | doc 01 §1.2, §1.3; RB-27, RB-30 |
| **Verificación** | Cada RN declara en 8.2 el mecanismo que la sostiene (índice, `CHECK`, FK, validación del service, permiso, transacción única o contrato) y el caso de uso donde se observa. Donde la verificación depende de una decisión abierta, la propia fila dice **condicional** y nombra el PD. | plan §3 (08.2) |

---

## 8.1 Invariantes `RN-001…RN-057`

Doce dominios, **una invariante por fila**, numeración continua de `RN-001` a
`RN-057`. Las filas marcadas **condicional** siguen abiertas: se enuncian para
que el hueco sea visible, no para resolverlo. `RN-058` y `RN-059` —las dos
que le asigna la Ley 25.326— se formulan en 8.3.

### 8.1.1 Ventanas, calendario y reloj

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-001 | Toda escritura de inscripción o anulación se acepta **sólo** si `current_date` (zona `America/Argentina/Buenos_Aires`) cae dentro de `[fecha_inicio_inscripcion, fecha_fin_inscripcion]` de la convocatoria. | RB-07, RB-08b, RB-09, RB-23; §3.17, §6; `ck_convocatoria_ventana` | `es_convocatoria`, `es_mesa_inscripcion`; INS-01, INS-02, INS-04; EX-01, EX-04, EX-09 | Existe una fila de `es_mesa_inscripcion` creada fuera de la ventana, o `POST /inscripciones` o `DELETE /mis-inscripciones/{id}` responden éxito con `hoy` fuera del rango. |
| RN-002 | El límite es **inclusivo hasta las 23:59:59** del día declarado: a las 00:00:00 del día siguiente la ventana ya está cerrada. Vale igual para `fecha_inicio_inscripcion`, para `fecha_fin_inscripcion` y para `pr_ventana`. La comparación es por fecha de calendario, nunca por timestamp crudo de UTC ni sumando horas. | RB-23, RB-07, RB-14; §3.17, §3.21 | `es_convocatoria`, `pr_ventana`, `vw_ventana_vigente`; T-02, T-03, T-04; EX-01, EX-02 | Una escritura se acepta después de las 00:00:00 del día siguiente, o se rechaza dentro del día hábil hasta las 23:59:59. |
| RN-003 | Ninguna inscripción se crea si la convocatoria tiene `activa = false`, **aunque** su ventana de fechas esté vigente. | RB-09; §3.17; S-07 | `es_convocatoria.activa`; INS-01; EX-04 | `POST /inscripciones` crea una fila sobre una convocatoria desactivada, o `GET /convocatoria-vigente` la presenta como vigente. |
| RN-004 | La ventana la decide el reloj del **backend**; ningún reloj de dispositivo participa en la evaluación y ningún parámetro de fecha enviado por el cliente la altera. | RB-23; doc 02 §2.1.2; doc 06 §6.6 | Todas las ventanas; CU-37, CU-39, CU-41 | El resultado de una escritura depende de la hora o de la fecha reportada por el dispositivo. |
| RN-005 | En v1 **no existe ningún job programado**: ninguna regla temporal se dispara por un cron; toda ventana y todo aviso se constatan en una acción de usuario o en un request. | RB-23, RB-24; PD-11; doc 04 Convenciones | `es_convocatoria`, `pr_ventana`, `ntf_*` | Un scheduler cuyo fallo impida cerrar una ventana o entregar una notificación prevista en v1. |

### 8.1.2 Inscripción

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-006 | No existen dos filas de `es_mesa_inscripcion` con el mismo `(convocatoria_id, usuario_id, materia_id)` teniendo `deleted_at IS NULL` y `estado <> 'anulado'`. La unicidad es por **materia × convocatoria**, no por mesa. | RB-08; §3.19; `uq_inscripcion_unica` | `es_mesa_inscripcion`; INS-01, INS-04; EX-06 | Una segunda inscripción activa a la misma materia en la misma convocatoria —incluso en otra mesa—, o la ausencia del índice único. |
| RN-007 | Las convocatorias son independientes: las filas de una convocatoria nunca restringen ni se modifican desde otra, y cada campaña arranca con inscripciones nuevas. | RB-08, RB-16; §3.19, §3.17 | `es_convocatoria`, `es_mesa_inscripcion`; ME-06 | Rechazar por unicidad una inscripción válida de la convocatoria B por existir una de la convocatoria A, o alterar filas de una campaña desde otra. |
| RN-008 | Dentro de la ventana, cada solicitud de inscripción que cumple las reglas se acepta: un alumno puede sostener **una o varias** inscripciones activas en la misma convocatoria. | RB-06; §6 | `es_mesa_inscripcion`; INS-01 | El backend rechaza una segunda inscripción válida de distinta materia alegando un límite de cantidad de inscripciones por alumno. |
| RN-009 | **No hay cupo.** Ninguna columna, índice, tabla ni validación limita la cantidad de inscriptos por mesa; toda mesa admite cualquier número de alumnos. | RB-01; §3.18, §3.19 | `es_mesa_examen`, `es_mesa_inscripcion`; CU-37, CU-19 | Existe una columna de cupo, o una inscripción se rechaza por un motivo de cupo agotado. |
| RN-010 | **No hay etapa de aprobación:** una inscripción que pasa la validación queda en `estado = 'inscripto'` en la misma transacción de la request; no existe ningún estado intermedio. | RB-02; §3.19 (`CHECK estado IN ('inscripto','anulado')`) | `es_mesa_inscripcion.estado`; INS-01 | Una fila en un estado fuera del `CHECK`, o una inscripción que requiere una aprobación posterior para existir. |
| RN-011 | La anulación sólo se aplica **durante** la ventana de la convocatoria y sólo sobre la propia fila en `inscripto`; la fila **pasa a `anulado` y se conserva**, nunca se elimina. | RB-08b, RB-07, RB-23; §3.19 | `es_mesa_inscripcion`; INS-02; EX-09 | Un `DELETE` exitoso con `hoy` fuera de la ventana, o una fila de inscripción borrada físicamente. |
| RN-012 | Una fila `anulado` **no ocupa la unicidad y no se reutiliza**: la reinscripción crea una fila nueva, y la materia queda libre en el mismo instante de la anulación. | RB-08b, RB-08c; §3.19; `uq_inscripcion_unica` | `es_mesa_inscripcion`; INS-02, INS-04; EX-10 | Reactivar una fila anulada con un `UPDATE` de estado, o que el índice único incluya las filas anuladas y bloquee la reinscripción. |
| RN-013 | El límite de `es_condicion.limite_materias` se evalúa **sólo** al crear una inscripción (o al reinscribir tras anular) y **nunca** sobre filas ya existentes. **[CERRADO — 2026-10-06]** (PD-02): valores sembrados como `DEFAULT` — Previa hasta 3, Regular hasta 8, Libre sin límite —, unidad de conteo **por convocatoria**, editables desde SIGME (`PATCH /condiciones`). | RB-03, RB-08c; §3.16; S-05; PD-02 | `es_condicion`, `es_mesa_inscripcion`; INS-01, INS-04; EX-08 | Una inscripción que supera el límite activo, o cualquier proceso que invalide inscripciones ya creadas porque el límite se superó después. |
| RN-014 | **Lista fija:** a partir de las 00:00:00 posteriores a `fecha_fin_inscripcion` el conjunto de inscripciones activas de la convocatoria no crece ni se recorta — no se crea ninguna fila (`inscripto_en` ≤ cierre) y ninguna desaparece. | RB-17, RB-07, RB-23; §3.19 | `es_mesa_inscripcion`; INS-01, INS-02; EX-01 | Una fila con `inscripto_en` posterior al cierre, o una inscripción que sale del listado definitivo después del cierre. |
| RN-015 | Ninguna regla (ventana, unicidad, límite de condición, cobertura) se **reevalúa** sobre inscripciones ya creadas después del cierre: no hay ninguna escritura sobre `es_mesa_inscripcion` con `current_date > fecha_fin_inscripcion`. | RB-17, RB-18; §4 | `es_mesa_inscripcion`; CU-38, CU-27 | Cualquier `INSERT`, `UPDATE` o `DELETE` sobre `es_mesa_inscripcion` ejecutado con `hoy` posterior al cierre. |
| RN-016 | **Sin registro de asistencia:** el modelo no contiene ninguna columna ni estado de presentación o falta, y ninguna operación los escribe. | RB-18; §3.19; doc 04 §4.6.6 | `es_mesa_inscripcion` | Aparece una columna de asistencia, un valor `presente`/`ausente`, o una operación que marque faltas. |
| RN-017 | **Sin notas ni resultados:** `es_mesa_inscripcion.estado` sólo admite `inscripto` y `anulado`, y ninguna tabla del esquema guarda nota, aprobado o desaprobado, ni trámite de rectificación. | RB-21; §3.19, §3.18; doc 04 §4.6.6 | `es_mesa_inscripcion`, `es_mesa_examen` | Una columna o un estado de resultado, un valor fuera del `CHECK`, o un endpoint que escriba el resultado de una mesa. |

### 8.1.3 Cobertura y visibilidad para el alumno

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-018 | Si en la convocatoria no existe mesa para la combinación materia × condición elegida, `POST /inscripciones` **no crea ninguna mesa ni ninguna inscripción**, y no existe creación de reserva de ningún tipo. El código del rechazo sigue **PENDIENTE (PD-19)**. | RB-31, RB-28; §6; INS-01; EX-07 | `es_mesa_examen`, `es_mesa_inscripcion`; CU-37, CU-40 | Aparece una mesa creada por el propio alumno, una inscripción sin mesa detrás, o un código de respuesta fijado por supuesto. |
| RN-019 | **El alumno nunca ve ni elige el grupo:** ninguna respuesta bajo `/api/v1/sigme-mobile` expone `grupo_id` ni la noción de grupo; el alumno elige sólo materia y condición, y la agrupación es de presentación. | RB-30; §3.22, §6 | `es_grupo_horario` (oculta), `es_mesa_examen`; CU-35, CU-38 | Una respuesta con `grupo_id` o con campos del grupo, o una validación que dependa de una elección de grupo hecha por el alumno. |
| RN-020 | Todo listado y toda impresión devuelven **únicamente** mesas con al menos una inscripción en `estado = 'inscripto'` (vista `vw_mesa_con_alumnos`); la mesa que queda sin alumnos se ignora y **no se borra**. | RB-22; §3.18 | `es_mesa_examen`, `es_mesa_inscripcion`; CU-19, CU-21, CU-23, CU-27, CU-28, CU-30, CU-34, CU-35, CU-36; EX-16 | Un listado o una impresión que incluye una mesa sin inscripciones activas, o una mesa eliminada por quedar vacía. |
| RN-021 | **Condicional — PENDIENTE (PD-23):** no está decidido el alcance de RB-22 sobre `GET /mesas-disponibles`. Aplicado literalmente, el filtro excluiría una mesa **recién creada** y ninguna inscripción podría iniciarse en ella (RB-28, RB-31); mientras el hueco siga abierto **no se fija** qué filtra esa consulta. | RB-22, RB-28, RB-31; §3.18; S-03; PD-23 | `es_mesa_examen`, `vw_mesa_con_alumnos`; CU-35 | Dar por resuelto el comportamiento del endpoint —en cualquiera de los dos sentidos— antes de resolver el alcance. |

### 8.1.4 Modelo de datos y catálogo

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-022 | `es_curso` identifica el **año** dentro de la orientación: el esquema no contiene ninguna columna de división ni de turno, y ninguna regla las referencia. | RB-15; §3.14 | `es_curso`, `es_materia`; CU-05, CU-06, CU-36 | Aparece una columna de división o de turno, o una validación que filtre por letra de división. |
| RN-023 | Los talleres son `es_materia` con `es_taller = true`: no existe entidad de taller y no hay comportamiento diferenciado para ellos. | RB-04; §3.15 | `es_materia`; CU-05, CU-06, CU-21 | Una tabla o un estado de taller propio, o una rama de negocio que trate distinto al taller. |
| RN-024 | Los cuatro snapshot (`orientacion_nombre`, `curso_nombre`, `materia_nombre`, `condicion_nombre`) se recalculan **sólo** al editar la asignación de la mesa, en la misma transacción, y **nunca** cuando se renombra una fila de catálogo. | RB-11; §3.18; S-08 | `es_mesa_examen`; CU-06, CU-20, CU-29; E-07, E-08, S-09 | Un renombre de `es_orientacion`, `es_curso`, `es_materia` o `es_condicion` que modifica el `*_nombre` de mesas ya creadas. |
| RN-025 | No existe `v_mesa_examen`: los reportes leen directamente las columnas snapshot y usan las foreign keys sólo para filtrar y navegar. | RB-12; §3.18 | `es_mesa_examen`; CU-27, CU-28, CU-29, CU-30 | La creación de esa vista, o un reporte que resuelva los nombres desde el catálogo en vivo. |
| RN-026 | **Convocatoria delimita todo:** cada campaña nueva nace con sus grupos, sus mesas y sus inscripciones **nuevas**; ninguna fila de una campaña se reutiliza ni se modifica desde otra. | RB-16; §3.17, §3.19; ME-06 | `es_convocatoria`, `es_grupo_horario`, `es_mesa_examen`, `es_mesa_inscripcion`; CU-11, CU-13, CU-34 | Mesas o inscripciones compartidas entre convocatorias, o inscripciones de una campaña alteradas al abrir la siguiente. |

### 8.1.5 Grupos y mesas

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-027 | **Toda mesa tiene grupo:** `es_mesa_examen.grupo_id` es `NOT NULL` con foreign key a `es_grupo_horario` (`ON DELETE RESTRICT`), y el grupo pertenece a la misma convocatoria que la mesa. | RB-27, RB-29; §3.18, §3.22 | `es_mesa_examen`, `es_grupo_horario`; GR-01, ME-01; CU-15, CU-19, CU-30 | Una mesa con `grupo_id` nulo, con grupo inexistente, o con grupo de otra convocatoria. |
| RN-028 | Un grupo declara **sólo** `fecha` y `hora` (más el `nombre` informativo): no hay aula, ni profesor, ni ningún otro atributo de planificación en `es_grupo_horario`. | RB-27; §3.22 | `es_grupo_horario`; CU-15, CU-16, CU-17 | Aparece una columna de aula, de profesor o de división en el grupo, o una regla que dependa de ellas. |
| RN-029 | `fecha` y `hora` de la mesa son **copia sincronizada** del grupo: se actualizan en la misma transacción que la edición del grupo, de modo que al cambiar el horario se mueven **todas** sus mesas a la vez. | RB-29; §3.18, §3.22; S-21 | `es_mesa_examen`, `es_grupo_horario`; GR-01, ME-01; CU-16, CU-35, CU-38; EX-17 | Una mesa cuya `fecha` o `hora` difiere de la de su grupo después de un `PATCH /grupos/{id}`, o un grupo editado que deja mesas con el horario anterior. |
| RN-030 | **El alumno no crea mesas:** toda alta de mesas (`POST /grupos`, `POST /mesas`) exige el permiso `mesa.crear` desde el módulo `sigme_web`, y no hay ninguna escritura de `es_mesa_examen` declarada para `sigme_mobile`. | RB-28, RB-27; §2.7, §6; GR-01, ME-01 | `es_mesa_examen`, `es_grupo_horario`; CU-15, CU-37 | Una alta de mesa aceptada con el token de un alumno, o sin el permiso `mesa.crear`. |
| RN-031 | **Unicidad de mesas:** no existen dos filas de `es_mesa_examen` con `(convocatoria_id, materia_id, condicion_id, fecha)` idénticos y `deleted_at IS NULL`. **[CERRADO — 2026-10-06]** (PD-13): la clave gana `convocatoria_id` (hueco contra RN-007) y sigue **sin** `hora` (RB-15); migración del índice. | §3.18 (`uq_mesa_unica`); RB-27; PD-13 | `es_mesa_examen`; CU-15, CU-30; EX-18 | Una segunda fila duplicada según la clave cerrada, o dar por buena una variante con `hora`. |
| RN-032 | **[CERRADO — 2026-10-06]** (PD-16): "no hay dos grupos idénticos en la misma convocatoria" queda **garantizada por la base** con `uq_grupo_unico (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` en `es_grupo_horario`; la colisión responde `409`. | §3.22; PD-16; RB-27 | `es_grupo_horario`; CU-15, CU-17; EX-18 | Insertar dos grupos con misma convocatoria, fecha y hora (la transacción aborta en el índice), o dar por buena una clave distinta de la cerrada. |
| RN-033 | El borrado **físico** de un grupo con mesas vivas está impedido por `ON DELETE RESTRICT`; el borrado **lógico** (`deleted_at`) arrastra lógicamente todas las mesas del grupo en la misma transacción — **[CERRADO — 2026-10-06]** (PD-18): si alguna mesa tiene inscripciones activas, la operación entera falla y no se borra nada. | §1.8, §3.22; PD-18; GR-02; EX-19 | `es_grupo_horario`, `es_mesa_examen`; CU-17, CU-18, CU-30 | Un `DELETE` físico que arrastre mesas, un borrado lógico que deje mesas vivas apuntando al grupo borrado, o la cascada aplicada sin verificar inscripciones activas. |

### 8.1.6 Preinscripción de la landing

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-034 | `POST /landing/preinscripcion` es un **UPSERT** sobre `(anio_lectivo, documento)`: `201` cuando la identidad no existía, `200` cuando existía —actualiza sólo los campos mutables y conserva `created_at`—, y **jamás devuelve `409` por documento repetido**. | RB-13; §3.20, §6; O-4; EX-03 | `pr_preinscripcion`; `uq_preinscripcion_unica`; EX-02, EX-03 | Dos filas para la misma identidad y año lectivo, o una respuesta `409` o `422` motivada por un reenvío del mismo documento. |
| RN-035 | Existe **una sola** ventana de preinscripción vigente por año lectivo (`uq_ventana_anio`) y la vigencia se lee en `vw_ventana_vigente` —`activa`, sin `deleted_at`, con el rango que contiene `current_date`—; fuera de ella el POST responde `409 { code: "ventana-cerrada" }`. | RB-14; §3.21; T-04, T-05 | `pr_ventana`, `vw_ventana_vigente`; CU-14; EX-02 | Dos ventanas vigentes a la vez, un POST aceptado sin fila vigente, o un `409` motivado por algo distinto de la ventana. |
| RN-036 | La landing **sólo escribe** `pr_preinscripcion`: no existe endpoint público de lectura de preinscripciones. | RB-10; §2.9 | `pr_preinscripcion`; doc 11 §11.6; EX-02 | Un `GET` sin autenticación que devuelva preinscripciones. |
| RN-037 | **Aislamiento topológico:** `pr_preinscripcion` no tiene ninguna foreign key hacia `pe_*`, `us_*` ni `es_*`, y ninguna tabla de esos prefijos referencia `pr_*`. | §3.20, §1.1; plan §3 (11.2) | `pr_preinscripcion`, `pe_*`, `us_*`, `es_*` | Una foreign key en cualquier dirección entre el dominio `pr_*` y el resto del esquema. |
| RN-038 | Los seis campos del payload (`nombre_alumno`, `documento`, `fecha_nacimiento`, `orientacion`, `nombre_tutor`, `email`) son `NOT NULL`; `anio_lectivo` lo toma el servidor de la ventana vigente —nunca del body—, y servidor completan `ip`, `user_agent`, `utm_*` y `estado`. | §3.20; O-2; RB-13 | `pr_preinscripcion`; doc 11 §11.3; EX-03 | Un `INSERT` con alguno de los seis campos nulo, o un valor de `anio_lectivo` decidido por el cliente. |

### 8.1.7 Seguridad, sesiones y permisos

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-039 | En base de datos sólo se persiste el **hash SHA-256** del refresh token (`us_sesion.refresh_token_hash`), nunca el token en texto claro; el access token no se almacena. | §2.2, §3.12 | `us_sesion`; CU-01, CU-02, CU-31, CU-32; EX-12 | Una columna con el refresh crudo, o con tokens de acceso persistidos. |
| RN-040 | Toda request autenticada exige `ver == us_usuario.token_version` vigente: subir la versión —cambio de clave, cambio de rol, bloqueo— invalida de inmediato los tokens emitidos antes. | §2.6; S-15 | `us_usuario.token_version`; CU-04, CU-09, CU-10; EX-14 | Un token con `ver` antiguo que sigue autorizando escrituras después del cambio. |
| RN-041 | Todo endpoint protegido declara su permiso con `require_permiso()` y el rechazo ocurre **antes** de ejecutar el service: sin permiso no hay escritura. **[CERRADO — 2026-10-06]** (PD-03): el reparto rol × permiso y el mapeo endpoint → permiso salen de la matriz de doc 02 §2.4, ya definitiva. | §2.7; doc 02 §2.4; PD-03 | Todos los CU de docs 05 y 06; EX-15 | Un endpoint sin dependencia de permiso, o una operación ejecutada con un rol que no tiene el código requerido. |
| RN-042 | Las contraseñas se guardan con **Argon2id** (m=19456, t=2, p=1) y longitud mínima de 12 caracteres; nunca SHA-256 o MD5 puros, nunca texto plano, y bcrypt sólo como fallback legacy con coste mínimo 10. | §2.5 | `us_usuario.password_hash`; CU-01, CU-04, CU-31 | Un hash reconocible como SHA-256 o MD5, una clave almacenada en claro, o un coste por debajo del mínimo. |
| RN-043 | **Módulo y permiso son acumulativos:** un usuario sólo opera en los módulos de `us_usuario_modulo`, y el módulo nunca sustituye al permiso —uno no reemplaza al otro—. | §2.8; doc 02 §2.5 | `us_usuario_modulo`, `us_sesion.modulo_id`; CU-01, CU-05, CU-31 | Un request aceptado sólo por tener el módulo y no el permiso, o un usuario operando en un módulo no asignado. |
| RN-044 | **Rate limit de login:** cinco intentos fallidos por usuario o IP en 15 minutos incrementan `intentos_fallidos`, setean `bloqueado_hasta` y suben `token_version` (US-02); el vencimiento del bloqueo los reinicia (US-03). El intento dentro del bloqueo responde **`429`** con `Retry-After` y el bloqueo dura **15 minutos** (PD-27, cerrado en `analisis.txt` §6). | §2.4; E-14, S-16, T-09; PD-27 | `us_usuario`; CU-01, CU-31; US-02, US-03; EX-13 | Un intento aceptado dentro de la ventana de 15 minutos después del quinto fallo, o un bloqueo sin `bloqueado_hasta`. |

### 8.1.8 Integridad referencial y auditoría

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-045 | Todo índice único sobre una tabla con soft delete es **parcial** (`WHERE deleted_at IS NULL`, más `email IS NOT NULL` donde aplica), de modo que borrar libera el valor para poder reinsertar. | §1.7; §3.2, §3.5, §3.18, §3.19, §3.20 | `pe_persona`, `us_usuario`, `es_mesa_examen`, `es_mesa_inscripcion`, `pr_preinscripcion` | Un índice único total que impida crear un registro nuevo después de borrar el anterior. |
| RN-046 | Toda foreign key declara `ON DELETE` explícito; las referencias que no se pueden perder —`pe_persona`, `es_materia`, `es_condicion`, `es_convocatoria`, `es_mesa_examen`, `es_grupo_horario`— son `RESTRICT`, de modo que el borrado se rechaza antes de producir un error 23503. | §1.8; S-17 | Tablas `pe_*`, `es_*`, `us_*`; CU-06, CU-08, CU-20 | Una foreign key sin `ON DELETE`, o un borrado que elimine en cascada filas que debían conservarse. |
| RN-047 | `updated_at` lo escribe un trigger `BEFORE UPDATE` en cada tabla: nunca depende de un `DEFAULT now()`, que sólo se evalúa en el `INSERT`. | §1.6 | Todas las tablas con `updated_at`; CU-08, CU-16, CU-20 | Una tabla cuya `updated_at` queda congelada desde la creación. |
| RN-048 | Todas las columnas temporales son `timestamptz` —nunca `timestamp` sin zona— y toda tabla con soft delete tiene su índice parcial `idx_{tabla}_activa`. | §1.4, §1.5 | Todas las tablas; CU-01, CU-34 | Una columna `timestamp` sin zona, o una tabla con `deleted_at` sin índice parcial. |

### 8.1.9 Notificaciones

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-049 | **Todo envío nace de una acción de usuario:** en v1 no hay ningún job programado y ninguna notificación depende de un scheduler. El recordatorio de 48 horas está **deferido a v2 (PD-11)**. | RB-24, RB-25; PD-11; S-20 | `ntf_notificacion`, `ntf_envio`, `us_dispositivo`; CU-34, CU-42; EX-21 | Un envío disparado por un cron, o el recordatorio de 48 horas implementado dentro de v1. |
| RN-050 | **Lista cerrada de notificaciones por canal en v1:** push → apertura y cierre de las inscripciones; campanita in-app → conjunto por rol **PENDIENTE (PD-10)**; email → acuse de preinscripción, confirmación de inscripción con fecha y hora, resumen al cerrar la ventana con aviso de retiro de permisos de examen, y restablecimiento de clave (existente desde v1 — **PD-04 cerrado 2026-10-06**, `us_password_reset`, email por la cola). Ningún otro envío. | RB-24, RB-25; PD-10, PD-04; §4 | `ntf_notificacion`, `ntf_envio`; CU-34, CU-37, CU-42; EX-21 | Un canal o un evento fuera de esa lista, o un envío programado por tiempo dentro de v1. |
| RN-051 | **La cola de email es obligatoria desde v1**, con reintento y con el estado de envío registrado en `ntf_envio`; el fallo de entrega ocurre **después** de la respuesta y no modifica la respuesta HTTP ni ninguna fila de negocio. El password reset usa esa misma cola desde v1 (**PD-04 cerrado 2026-10-06**); el contrato de reintento de la cola no queda resuelto en ese cierre. | RB-25; S-20; PD-04 | `ntf_envio`; CU-37, CU-42; EX-21 | Un envío sin registro de estado o sin reintento, o un fallo del proveedor que revierta la operación de negocio. |
| RN-052 | Los tokens push viven en `us_dispositivo` con refresco y purga de caducos; el alta y la baja se declaran en §6 (`POST /dispositivos` y `DELETE /dispositivos/{id}`, sólo el dispositivo propio, sin permiso nuevo — PD-26 cerrado). | RB-24; §4, §6; EX-22; PD-26 | `us_dispositivo`; CU-42 | Registrar un token por fuera de los endpoints declarados, o dar de baja un dispositivo que no sea el propio. |

### 8.1.10 Degradación (RB-26)

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-053 | **Lectura con caché:** las tres lecturas de SIGME-M —`GET /convocatoria-vigente`, `GET /mesas-disponibles`, `GET /mis-inscripciones`— se sirven desde la caché local **sin red y sin token**, con su marca de "última actualización". | RB-26; doc 06 §6.6; doc 02 §2.1.2 | Contrato de lectura de SIGME-M; CU-34, CU-35, CU-38, CU-41; EX-23 | Una lectura que exija red o token para mostrarse, o una respuesta sin datos suficientes para marcarse desactualizada. |
| RN-054 | **Escritura siempre online:** inscribir y anular exigen conexión y sesión válida, y el backend exige autenticación y sesión activa en toda escritura. | RB-26; doc 06 §6.6 | `es_mesa_inscripcion`, `us_sesion`; CU-37, CU-39, CU-40; EX-23 | Una escritura aceptada sin token válido, o un contrato que prometa completarla sin red. |
| RN-055 | **Ninguna cola de acciones offline:** no existe endpoint ni mecanismo para encolar acciones y sincronizarlas después, y la caché **nunca** decide ventana, unicidad ni límite de condición. | RB-26; doc 06 §6.6; doc 07 §7.6 | Contrato de SIGME-M; CU-41; EX-23 | Un endpoint de sincronización diferida, o una validación de ventana, unicidad o límite ejecutada con datos de la caché. |

### 8.1.11 Reportes de cierre

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-056 | Los tres reportes de cierre —permiso de examen individual y masivo, acta volante y planilla de grupos— se emiten sólo desde SIGME con el permiso `reporte.exportar`, aplican el filtro de RB-22 y **no exponen notas ni asistencia**: sólo inscripciones activas y columnas snapshot. | RB-19, RB-32, RB-21, RB-18, RB-22; §3.18 | `es_mesa_examen`, `es_mesa_inscripcion`; CU-27, CU-28, CU-29, CU-30; E-09 | Un reporte emitido sin permiso, que incluya mesas sin inscriptos, o que muestre columnas de resultado o de asistencia. |

### 8.1.12 Cobertura de mesas

| RN | Invariante (afirmación comprobable) | Fuente | Estados y tablas | Viola cuando |
|---|---|---|---|---|
| RN-057 | `GET /cobertura-mesas?convocatoria_id=` devuelve los pares materia × condición **sin mesa** de la convocatoria y es utilizable **antes** de abrir la ventana. **Condicional — PENDIENTE (PD-15, PD-20):** el origen del conjunto esperado y su validación programática siguen abiertos. | RB-31; §6; E-17; PD-15, PD-20 | `es_convocatoria`, `es_mesa_examen`, catálogo; CU-21, CU-37 | Un endpoint inexistente, una respuesta con pares inventados, o dar por resuelto el origen del conjunto sin cerrar PD-15. |

---

## 8.2 Prevención y trazabilidad a casos de uso

Mecanismo que sostiene cada invariante y dónde se observa. Reproduce el orden
de 8.1 y de 8.3: `RN-001`…`RN-059`, una fila por invariante.

| RN | Cómo se previene (mecanismo) | Casos de uso y transiciones |
|---|---|---|
| RN-001 | Validación de ventana en el service, en el mismo request, contra `current_date` del backend; precondición de INS-01, INS-02 e INS-04 | CU-37, CU-39, CU-40; INS-01, INS-02, INS-04 |
| RN-002 | Comparación por fecha de calendario en `America/Argentina/Buenos_Aires`, sin timestamps de UTC; la misma lógica gobierna `pr_ventana` vía `vw_ventana_vigente` | CU-37, CU-39, CU-26; T-02, T-03, T-04 |
| RN-003 | Chequeo de `es_convocatoria.activa` junto con la ventana, en la misma evaluación; el cliente consulta antes de ofrecer la acción | CU-37, CU-34; C-05, INS-01 |
| RN-004 | Ningún parámetro de fecha del body ni del dispositivo entra en la evaluación; el reloj del backend es el único | CU-37, CU-39, CU-41 |
| RN-005 | No se declara ningún scheduler en v1: la constatación vive en el código de cada endpoint | CU-34, CU-13, CU-42 |
| RN-006 | Índice único `uq_inscripcion_unica (convocatoria_id, usuario_id, materia_id) WHERE deleted_at IS NULL AND estado <> 'anulado'` más la validación previa del service | CU-37, CU-40; INS-01, INS-04 |
| RN-007 | `convocatoria_id` forma parte de la clave de unicidad y cada campaña crea sus propias filas; convención de ciclo | CU-37, CU-34, CU-11; ME-06 |
| RN-008 | No existe ninguna restricción de cantidad por alumno; sólo aplican ventana, unicidad, límite de condición y mesa existente | CU-37, CU-40; INS-01 |
| RN-009 | No hay columna de cupo ni validación de cupo en el DDL ni en el service; la mesa no conoce una capacidad | CU-37, CU-19 |
| RN-010 | `CHECK (estado IN ('inscripto','anulado'))` y escritura del estado en la misma transacción de la request; no existe fila de aprobación | CU-37, CU-23; INS-01 |
| RN-011 | Precondición de ventana en INS-02 y escritura de `estado = 'anulado'` sin `DELETE` físico; la fila queda para auditoría | CU-39; INS-02 |
| RN-012 | Cláusula `estado <> 'anulado'` del índice único; INS-04 crea una fila nueva en lugar de reactivar la vieja | CU-39, CU-40; INS-02, INS-04 |
| RN-013 | Chequeo de `limite_materias` sólo en el alta de la inscripción; ningún proceso posterior la evalúa. Valores y criterio de conteo: **[CERRADO — 2026-10-06]** (PD-02) — Previa hasta 3, Regular hasta 8, Libre sin límite; unidad por convocatoria; editables desde SIGME | CU-37, CU-40; INS-01, INS-04 |
| RN-014 | Cierre evaluado en cada request; ninguna escritura de inscripción supera el cierre; `inscripto_en` registra el instante | CU-37, CU-39, CU-38; C-04 |
| RN-015 | No hay ninguna ruta declarada que modifique inscripciones después del cierre; el único filtro posterior es de lectura | CU-38, CU-27, CU-30 |
| RN-016 | El `CHECK` de estado no admite valores de asistencia y el esquema no contiene columnas de asistencia | CU-28, CU-38 |
| RN-017 | `CHECK` de estado, ausencia total de columnas de resultado y exclusión explícita del doc 04 §4.6.6 | CU-28, CU-29, CU-38 |
| RN-018 | La creación de mesas es exclusiva del secretario en bloque; el backend sólo busca la mesa existente y, si no hay, no inserta nada | CU-37, CU-40; INS-01, GR-01, ME-01 |
| RN-019 | Contrato de respuesta de SIGME-M que expone materia, condición, fecha y hora, sin `grupo_id`; el grupo es sólo de planificación | CU-35, CU-38 |
| RN-020 | Vista `vw_mesa_con_alumnos` con `EXISTS` de inscripción activa, aplicada a todo listado e impresión; la fila no se borra | CU-19, CU-21, CU-23, CU-27, CU-28, CU-30, CU-34, CU-35, CU-36 |
| RN-021 | **Condicionada:** ninguna decisión tomada sobre el endpoint mientras el alcance siga abierto | CU-35 |
| RN-022 | No existen esas columnas en `es_curso` ni en `es_materia`; el catálogo se consulta tal cual | CU-05, CU-06, CU-36 |
| RN-023 | Una sola tabla de materias con la marca `es_taller`; ninguna rama de negocio la lee | CU-05, CU-06, CU-21 |
| RN-024 | Recálculo del snapshot sólo en la edición de asignación de la mesa, dentro de la misma transacción; el renombre de catálogo no toca mesas | CU-06, CU-20, CU-29; E-07, E-08, S-08 |
| RN-025 | La vista no existe y los reportes se escriben contra las columnas snapshot; las FK sólo filtran y navegan | CU-27, CU-28, CU-29, CU-30 |
| RN-026 | `convocatoria_id` en grupo, mesa e inscripción, con `ON DELETE RESTRICT`; el alta del ciclo siguiente crea filas nuevas | CU-11, CU-13, CU-34; ME-06, GR-01 |
| RN-027 | Columna `grupo_id NOT NULL` con foreign key `RESTRICT` y validación de pertenencia a la convocatoria en el alta | CU-15, CU-19, CU-30; GR-01, ME-01 |
| RN-028 | El DDL de `es_grupo_horario` sólo declara `convocatoria_id`, `fecha`, `hora` y `nombre`; aula y profesor están fuera de alcance | CU-15, CU-16, CU-17 |
| RN-029 | Transacción única en `PATCH /grupos/{id}`: grupo y todas sus mesas se escriben juntos; la mesa no edita su horario por su cuenta | CU-16, CU-35, CU-38; GR-01, ME-01, S-21 |
| RN-030 | `require_permiso('mesa.crear')` en `POST /grupos` y `POST /mesas`, con módulo `sigme_web`; ninguna ruta de alta bajo `/api/v1/sigme-mobile` | CU-15, CU-37; GR-01, ME-01 |
| RN-031 | Índice `uq_mesa_unica (convocatoria_id, materia_id, condicion_id, fecha) WHERE deleted_at IS NULL` — clave **[CERRADA — 2026-10-06]** (PD-13: gana `convocatoria_id`, sigue sin `hora`; migración del índice), más la validación del alta masiva | CU-15, CU-30; ME-01 |
| RN-032 | `uq_grupo_unico (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` en `es_grupo_horario` — **[CERRADO — 2026-10-06]** (PD-16), con migración del índice; colisión → `409` | CU-15, CU-17; GR-01 |
| RN-033 | `ON DELETE RESTRICT` en `es_mesa_examen.grupo_id` para el borrado físico; borrado lógico con cascada lógica transaccional — **[CERRADO — 2026-10-06]** (PD-18) | CU-17, CU-18, CU-30; GR-02 |
| RN-034 | `uq_preinscripcion_unica (anio_lectivo, documento) WHERE deleted_at IS NULL` y lógica de upsert en el service: INSERT o UPDATE según existencia | doc 11 §11.4; EX-03 |
| RN-035 | `uq_ventana_anio (anio_lectivo)`, vista `vw_ventana_vigente` y chequeo previo al upsert; el `409` sólo significa ventana cerrada | CU-14; doc 11 §11.5; EX-02 |
| RN-036 | El único endpoint declarado bajo `/api/v1/landing` es `POST /preinscripcion`; §2.9 prohíbe la lectura pública | doc 11 §11.6; EX-02 |
| RN-037 | `pr_preinscripcion` se declara sin foreign keys en el DDL y el aislamiento es una decisión explícita del análisis | doc 11 §11.2 |
| RN-038 | Las seis columnas con `NOT NULL`, validación estricta de payload y `anio_lectivo` tomado de `pr_ventana` | doc 11 §11.3; EX-03 |
| RN-039 | Columna `refresh_token_hash varchar(64) NOT NULL UNIQUE` y ningún almacén de access tokens | CU-01, CU-02, CU-31, CU-32 |
| RN-040 | Comparación de `ver` con `token_version` en cada request autenticado; subida de la versión en los tres disparadores de S-15 | CU-04, CU-09, CU-10; US-02, US-04 |
| RN-041 | Dependencia `require_permiso()` en cada endpoint protegido, antes de delegar al service; reparto concreto en la matriz de doc 02 §2.4 (**[CERRADO — 2026-10-06]**, PD-03) | CU-05, CU-15, CU-37; EX-15 |
| RN-042 | Argon2id con los parámetros de OWASP en el service de autenticación; ninguna otra función de hash aceptada | CU-01, CU-04, CU-31 |
| RN-043 | Dos controles independientes: `require_modulo()` para entrar a la app y `require_permiso()` para operar dentro | CU-01, CU-05, CU-31 |
| RN-044 | Conteo de `intentos_fallidos` con ventana de 15 minutos, `bloqueado_hasta` y subida de `token_version`; desbloqueo al vencer | CU-01, CU-31; US-02, US-03 |
| RN-045 | Índices únicos parciales declarados en el DDL de cada tabla con soft delete; checklist de calidad antes de codificar | CU-07, CU-09, CU-37 |
| RN-046 | `ON DELETE` explícito en toda foreign key, con `RESTRICT` en las referencias que no se pueden perder | CU-06, CU-08, CU-20; S-17 |
| RN-047 | Función `trg_set_updated_at()` y su trigger `BEFORE UPDATE` creados en todas las tablas | CU-08, CU-16, CU-20 |
| RN-048 | Uso obligatorio de `timestamptz` y del índice parcial `idx_{tabla}_activa` en toda tabla con soft delete | CU-01, CU-34 |
| RN-049 | Ningún scheduler declarado en v1; todos los envíos cuelgan de un evento de usuario (S-20) | CU-34, CU-42; EX-21 |
| RN-050 | Catálogo cerrado de eventos y canales en RB-24 y RB-25; el conjunto por rol sigue en **PD-10**; el restablecimiento de clave se encola desde v1 (**PD-04**, 2026-10-06) | CU-34, CU-37, CU-42 |
| RN-051 | Tabla `ntf_envio` con estado y reintentos, obligatoria desde v1; la notificación se encola después de responder; el password reset usa su propia tabla `us_password_reset` desde v1 (PD-04, 2026-10-06) | CU-37, CU-42; EX-21 |
| RN-052 | Infraestructura `us_dispositivo` declarada en §4; alta y baja con endpoints `POST /dispositivos` y `DELETE /dispositivos/{id}` en §6 (sin permiso nuevo) | CU-42; EX-22 |
| RN-053 | El cliente conserva la última respuesta y la muestra con su fecha; la respuesta del backend es autosuficiente para eso | CU-34, CU-35, CU-38, CU-41 |
| RN-054 | Autenticación y sesión activa exigidas en toda escritura; la respuesta `401` corta la operación antes del service | CU-37, CU-39, CU-40; EX-11, EX-23 |
| RN-055 | No existe endpoint de sincronización diferida; las validaciones de negocio se ejecutan sólo en el backend, en línea | CU-41; EX-23 |
| RN-056 | `require_permiso('reporte.exportar')`, filtro de la vista `vw_mesa_con_alumnos` y lectura de columnas snapshot | CU-27, CU-28, CU-29, CU-30; E-09 |
| RN-057 | Endpoint declarado en §6 y consulta pensada para usarse antes de abrir la ventana; el origen del conjunto queda en **PD-15** | CU-21, CU-37; E-17 |
| RN-058 | No existen columnas de consentimiento en `pr_preinscripcion` ni endpoint que las recoja: el proceso es físico y externo | doc 11 §11.3 (la serie `CU-xx` no cubre la landing) |
| RN-059 | No existe endpoint ni campo de aviso previo en el contrato: el requisito está heredado a la landing | doc 11 §11.3 (la serie `CU-xx` no cubre la landing) |

---

## 8.3 Reglas derivadas de la Ley 25.326

Reparto de las cinco disposiciones que el análisis citó (§3.20). **Dos son
invariantes de este documento** porque el backend las cumple por ausencia —no
existe la columna, no existe el endpoint—; **las otras tres son requisitos con
plazo**, y por eso se trazan hacia el doc 09 (plan §3 (09.3)) en lugar de
formularse aquí como reglas de negocio.

| Disposición | Qué obliga | Tratamiento en este documento | Fuente |
|---|---|---|---|
| Art. 5 — consentimiento | Se recoge en un formulario físico posterior, fuera del sistema: por eso `pr_preinscripcion` no tiene columna de consentimiento ni de fecha de otorgamiento | **RN-058**: no existe esa columna en el esquema | §3.20 (O-1); doc 11 §11.3 |
| Art. 6 — aviso previo | El aviso de para qué se usan los datos y de derechos es un requisito **heredado a la landing**, no una obligación del backend | **RN-059**: el backend no expone ese aviso ni lo guarda | §3.20; plan §3 (11.3) |
| Art. 9 — medidas de seguridad | Seguridad técnica y organizativa sobre los datos personales que el backend almacena | **No es una RN:** es un requisito no funcional con verificación propia → doc 09 (plan §3 (09.3)) | §3.20; plan §3 (09.3) |
| Art. 14 — acceso | Acceso a los datos en 10 días corridos | **No es una RN:** plazo medible → doc 09 | §3.20; plan §3 (09.3) |
| Art. 16 — rectificación y supresión | Rectificación o supresión en 5 días hábiles | **No es una RN:** plazo medible → doc 09 | §3.20; plan §3 (09.3) |

---

## 8.4 Cobertura: `RB-xx` → `RN-001…`

**Cómo leer esta tabla.** `RB-xx` es el identificador de **regla** de la fuente
(`analisis.txt` §4); `RN-001…` es el identificador de **invariante** de este
documento. Una regla puede traducirse en varias invariantes (cada una mira un
comprobable distinto) y una invariante puede reunir varias reglas (cuando la
misma restricción las sostiene a todas). **Ninguna `RB-xx` queda sin fila
acá**: o lleva sus RN, o lleva la nota explícita de que **no es un
invariante**. Las variantes `RB-08b` y `RB-08c` se resuelven en la fila de
`RB-08`.

| RB | Regla en la fuente (resumen) | RN o tratamiento |
|---|---|---|
| RB-01 | No hay cupo por mesa de exámenes | RN-009 |
| RB-02 | No hay etapa de aprobación de inscripciones | RN-010 |
| RB-03 | Límite de materias por condición, sólo al inscribirse | RN-013 (condicional, **PD-02**) |
| RB-04 | Los talleres se modelan como materias normales | RN-023 |
| RB-05 | Premisa de una fecha única de rendición por convocatoria | **No es un invariante:** premisa **sin vigencia** por RB-27 y PD-14 —con grupos, la convocatoria abarca varios días de rendición—; su conclusión vigente (una sola ventana de inscripción por convocatoria) ya está en RN-001 y RN-035 |
| RB-06 | Una o varias inscripciones dentro de la ventana | RN-008 |
| RB-07 | Cerrada la ventana, sólo consulta | RN-001, RN-002, RN-011, RN-014 |
| RB-08 | Unicidad por materia × convocatoria (no por mesa) | RN-006, RN-007 — **RB-08b** → RN-011, RN-012; **RB-08c** → RN-013 |
| RB-09 | No se inscribe con la convocatoria inactiva o fuera de ventana | RN-003 |
| RB-10 | La landing sólo escribe, sin lectura pública | RN-036 |
| RB-11 | Snapshot recalculado sólo al editar la asignación | RN-024 |
| RB-12 | No existe `v_mesa_examen` | RN-025 |
| RB-13 | Preinscripción como upsert, repetir no es error | RN-034, RN-038 |
| RB-14 | Una sola ventana de preinscripción vigente | RN-035 |
| RB-15 | Sin división ni turno: `es_curso` es el año | RN-022 |
| RB-16 | La convocatoria delimita todo, campaña por campaña | RN-026 |
| RB-17 | Lista fija al cerrar la ventana | RN-014, RN-015 |
| RB-18 | Sin revalidación ni registro de inasistencia | RN-015, RN-016 |
| RB-19 | Tres reportes de cierre en papel | RN-056 |
| RB-20 | Creación de la mesa desde la inscripción del alumno | **No es un invariante:** regla **revocada** por RB-28; el ID se conserva sin renumerar y la creación de mesas queda en RN-030 |
| RB-21 | El sistema no guarda notas | RN-017 |
| RB-22 | Sólo se entregan mesas con inscripciones activas | RN-020; el alcance sobre `GET /mesas-disponibles` queda **PENDIENTE** en RN-021 |
| RB-23 | Límite inclusivo 23:59:59 y comparación por fecha de calendario | RN-002, RN-004, RN-005 |
| RB-24 | Notificaciones: 3 canales, sólo por eventos de usuario | RN-049, RN-050, RN-052 |
| RB-25 | Cola de email obligatoria desde v1 | RN-051 |
| RB-26 | Lectura con caché, escritura online, ninguna cola offline | RN-053, RN-054, RN-055 |
| RB-27 | Grupo de mesas: fecha y hora compartidas | RN-027, RN-028 |
| RB-28 | El secretario crea grupos y mesas en bloque | RN-030, RN-018 |
| RB-29 | Toda mesa tiene grupo con copia sincronizada | RN-029, RN-027 |
| RB-30 | El alumno nunca ve el grupo | RN-019 |
| RB-31 | Cobertura: sin mesa, no hay inscripción | RN-018, RN-057 |
| RB-32 | Planilla de grupos, tercer reporte de cierre | RN-056 |

---

## 8.5 Pendientes heredados

Ninguno de estos identificadores se cierra en este documento. Se listan con la
invariante que los hace visibles, para que los documentos 09 y 10 los hereden
trazados; los que ya tienen decisión en `analisis.txt` §7 se conservan
marcados **[CERRADO — 2026-10-06]** (o **[RESUELTA]** para G-05) sin
renumerar.

| ID | Pregunta abierta | Qué toca en este documento | Fuente |
|---|---|---|---|
| **PD-02** | **[CERRADO — 2026-10-06]** — Valores de `es_condicion.limite_materias` (Previa 3, Regular 8, Libre sin límite) y unidad de conteo por convocatoria, editables desde SIGME | RN-013 deja de estar condicionada: la regla se sostiene entera | `analisis.txt` §7; RB-03 |
| **PD-03** | **[CERRADO — 2026-10-06]** — Semilla de roles, permisos y usuarios en la migración inicial de Alembic; reparto y mapeo de la matriz doc 02 §2.4 | RN-041 deja de estar condicionada; el catálogo §2.7 sigue sin `convocatoria.*` (hueco no cubierto) | `analisis.txt` §7; doc 02 §2.4 |
| **PD-04** | **[CERRADO — 2026-10-06]** — Reseteo de contraseña por email desde v1: tabla `us_password_reset`, email por la cola obligatoria | Toca RN-050 y RN-051: el envío existe desde v1; el contrato de reintento de la cola sigue sin resolverse | `analisis.txt` §7; RB-24, RB-25 |
| **PD-05** | **[CERRADO — 2026-10-06]** — Bitácora de auditoría: `aud_evento` append-only con snapshot JSONB (escrituras, denegaciones 401/403 y descargas de reportes; sin `password_hash` ni tokens) | **No es una RN:** es requisito → doc 09 NFR-044 | `analisis.txt` §7 |
| **PD-06** | **[CERRADO — 2026-10-06]** — Despliegue en Vercel + FastAPI zero-config; CORS obligatorio, Neon por driver HTTP serverless, Alembic desde CI/local | **No es una RN:** es operación → doc 09 NFR-006, NFR-011, NFR-042 | `analisis.txt` §7 |
| **PD-10** | Conjunto exacto de notificaciones in-app por rol | RN-050 declara el canal y deja el conjunto **PENDIENTE** | `analisis.txt` §7; RB-24 |
| **PD-11** | Recordatorio de 48 horas antes de la mesa | RN-049 lo deja **deferido a v2**; en v1 no hay job | `analisis.txt` §7; RB-24 |
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? | Tocaría la precondición de RN-027, RN-029 y RN-031; aquí no se decide | `analisis.txt` §7; RB-29 |
| **PD-13** | **[CERRADO — 2026-10-06]** — `uq_mesa_unica` pasa a `(convocatoria_id, materia_id, condicion_id, fecha)` y sigue sin `hora` | RN-031 deja de estar condicionada: la clave ya no incluye `hora` | `analisis.txt` §7; §3.18 |
| **PD-15** | De dónde sale el conjunto esperado de pares materia × condición de la cobertura | RN-057 queda **condicionada** | `analisis.txt` §7; RB-31 |
| **PD-16** | **[CERRADO — 2026-10-06]** — Sí: `UNIQUE (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` (`uq_grupo_unico`); colisión → `409` | RN-032 deja de estar condicionada: la restricción ya existe en el diseño | `analisis.txt` §7; §3.22 |
| **PD-17** | Interpretación de `grupo.hora` (`time` sin zona) frente a RB-23 | Toca RN-002 y RN-029: la ventana se evalúa por fecha y el horario no tiene zona declarada | `analisis.txt` §7; RB-23 |
| **PD-18** | **[CERRADO — 2026-10-06]** — Borrado lógico de grupo con cascada lógica transaccional; falla si alguna mesa tiene inscripciones activas | RN-033 deja de estar condicionada: el criterio del borrado lógico ya está escrito | `analisis.txt` §7; doc 04 GR-02 |
| **PD-19** | Código HTTP del rechazo de `POST /inscripciones` sin mesa | RN-018 sostiene el efecto (no se inserta nada) y deja el código **PENDIENTE** | `analisis.txt` §7; RB-31 |
| **PD-20** | Formato canónico del catálogo de materias para validarlo programáticamente | Toca RN-057 y la verificación de la cobertura | `analisis.txt` §7; RB-31 |
| **PD-21** | Renombrado o alta de catálogo sin endpoint declarado | Toca RN-024: el recálculo del snapshot supone que el renombre ocurre por alguna ruta | `analisis.txt` §7; doc 03 S-09 |
| **PD-22** | Efecto del `PATCH /preinscripciones` | **No es una RN:** ninguna regla declara ese efecto, así que no hay nada que afirmar | `analisis.txt` §7; doc 05 CU-26 |
| **PD-23** | Alcance de RB-22 sobre `GET /mesas-disponibles` | RN-021 queda **condicionada (PD-23)** y no fija el comportamiento del endpoint | `analisis.txt` §7; doc 06 §6.8; doc 07 EX-16 |
| **PD-24** | **[CERRADO — 2026-10-05]** Contrato de cuerpo de las respuestas de error fuera de `/landing/preinscripcion` | Cerrado en `analisis.txt` §6: sobre único `{ code, detail, errors[] }` en `application/json`, `errors[]` sólo en 422 — no es una RN | `analisis.txt` §7; doc 07 §7.7.2 |
| **PD-25** | **[CERRADO — 2026-10-05]** Código HTTP de la respuesta repetida de `DELETE /mis-inscripciones/{id}` | Cerrado en `analisis.txt` §6: `204 No Content` idempotente, igual que la primera; RN-012 ya fijaba el efecto nulo | `analisis.txt` §7; doc 06 §6.8; doc 07 §7.8 |
| **PD-26** | **[CERRADO — 2026-10-05]** Endpoint de alta y baja del token de push (`us_dispositivo`) | Cerrado en `analisis.txt` §6: RN-052 ya declara `POST /dispositivos` y `DELETE /dispositivos/{id}`, sólo el dispositivo propio | `analisis.txt` §7; doc 06 §6.8; doc 07 EX-22 |
| **PD-27** | **[CERRADO — 2026-10-05]** Duración exacta del bloqueo de login y el código de su respuesta | Cerrado en `analisis.txt` §6: RN-044 fija `429` + `Retry-After` y bloqueo de 15 minutos | `analisis.txt` §7; doc 04 US-03; doc 07 EX-13 |
| **PD-28** | Paginación de `GET /mis-inscripciones` | **No es una RN:** es un contrato de lectura que §6 no declara | `analisis.txt` §7; plan §3.06; doc 06 §6.6 |
| **PD-29** | Alcance de `POST /mesas` fuera de la alta masiva del grupo | **No es una RN:** ninguna regla declara el alta individual → doc 04 §4.6.4 | `analisis.txt` §7; doc 04 §4.6.4 |
| **G-01** | Qué significa "matrícula" para el cliente: la palabra no existe en `analisis.txt` | **No es una RN:** es vocabulario; el uso sigue **PENDIENTE** en doc 01 §1.3 | doc 01 §1.5.2 |
| **G-02** | Qué rol usa el permiso `preinscripcion.crear`, si la landing es anónima | Toca RN-041: el catálogo §2.7 incluye un permiso sin endpoint autenticado | doc 01 §1.5.2; doc 02 §2.4 |
| **G-03** | Si existe el rol "docente", comentado en el DDL de `us_rol` | **No es una RN:** P-08 cerró la lista de roles y el rol no opera ninguna transición | doc 01 §1.5.2; doc 04 §4.6.3 |
| **G-04** | Cómo obtiene SIGME-M las opciones de orientación → curso → materia → condición | **No es una RN:** es un contrato sin endpoint; CU-36 sigue **PENDIENTE** | doc 01 §1.5.2; doc 06 §6.8 |
| **G-05** | **[RESUELTA — 2026-10-06]** — Nadie cambia el estado: la convocatoria y la mesa se constatan al leer por calendario | **No es una RN:** no se formula un invariante sobre escritura de estados que no ocurren (ME-03, ME-04, ME-05 son lecturas derivadas) | doc 01 §1.5.2; doc 04 §4.6.2 |

---

## Checklist de cierre (8 · Reglas de negocio)

**Criterio de cierre del plan (plan §3.08): *ninguna RN es contradictoria con
otra; cada RN aparece en al menos un CU* — verificación:**

- [x] **59 invariantes con ID estable** (`RN-001`…`RN-059`), una por fila: 57
      en los doce dominios de 8.1 —ventana, inscripción, cobertura, modelo,
      grupos y mesas, landing, seguridad, integridad, notificaciones,
      degradación, reportes y cobertura de mesas— y 2 en 8.3, por la Ley
      25.326.
- [x] **Cada RN declara** lo pedido por el plan §3.08 (8.2): afirmación
      comprobable, fuente (`RB-xx`, `PD-xx`, `§n.m`, `E-xx`/`S-xx`/`T-xx`,
      `C-xx`/`ME-xx`/`INS-xx`/`US-xx`/`SES-xx`/`GR-xx`, `EX-xx`), estados y
      tablas que restringe, forma de violación, y en 8.2 el mecanismo de
      prevención con su caso de uso.
- [x] **Cobertura de `RB-xx` completa:** las **32** reglas `RB-01`…`RB-32`
      figuran en 8.4, cada una con la RN que la sostiene o con la nota *no es
      un invariante* (`RB-05` y `RB-20`); `RB-08` aparece desdoblada en sus
      tres variantes de ventana.
- [x] **Ninguna RN contradice a otra:** donde dos reglas podrían chocar —el
      reloj del backend frente al del dispositivo (RN-004), la unicidad por
      convocatoria frente al reintento de E-13 (RN-006 y RN-012), la lista
      fija de materias frente a la cobertura de mesas (RN-023 y RN-057)—
      8.1 nombra la que gobierna y la que queda subordinada.
- [ ] **Cada RN aparece en al menos un `CU-xx`:** **53 de 59** invocan al
      menos un caso de uso en 8.2. Las **6** restantes (`RN-034`, `RN-036`,
      `RN-037`, `RN-038`, `RN-058` y `RN-059`) no pueden citarlo: la serie
      `CU-xx` no cubre la preinscripción de la landing ni los requisitos
      normativos. Se trazan al **doc 11** y a la Ley 25.326 y quedan
      **PENDIENTES** de que el plan acepte ese trazado alternativo.
- [x] **Los pendientes se heredan, no se cierran:** 8.5 lista los **24**
      `PD-xx` (de `PD-02` a `PD-29`, con `PD-07`, `PD-08`, `PD-09` y `PD-14`
      fuera: cerrados o resueltos) y los **5** `G-xx`, cada uno con la
      invariante que lo hace visible o con la nota *no es una RN*; ninguno se
      resuelve por suposición. **8** `PD-xx` (PD-02, PD-03, PD-04, PD-05,
      PD-06, PD-13, PD-16 y PD-18) llevan **[CERRADO — 2026-10-06]** y G-05
      **[RESUELTA — 2026-10-06]**: se conservan en la tabla, sin renumerar,
      por trazabilidad.

## Siguiente paso

`09-requisitos-no-funcionales.md`: de aquí salen los requisitos que la API
debe cumplir — tiempos de respuesta, límites de tasa, tamaño de payloads,
disponibilidad y observabilidad—, tomados de cada invariante de 8.1 que el
backend tiene que sostener en producción y de doc 01 (§1.5.1 y §1.5.2) los
huecos que todavía no permiten fijarlos. Lo que hoy está condicionado a un
`PD-xx` llega allí como requisito condicionado, sin cerrarlo.
