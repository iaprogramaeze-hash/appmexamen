# 10 · Matriz de trazabilidad — Backend EPET36

Este documento cierra la serie de análisis (plan §10): cruza cada invariante
`RN-001`…`RN-059` con su caso de uso, su entidad, su estado y su criterio de
aceptación; detecta huérfanos en ambos sentidos; consolida los ítems de
cada serie (abiertos y resueltos con su estado) y deja el inventario de entregables listo para SDD.
El criterio de cierre del plan es **cero filas sin correspondencia**: se
verifica en 10.1 y se declara el veredicto en 10.2.

Vocabulario e identificadores: los mismos de `01-glosario-y-alcance.md` y de
las convenciones de lectura de los docs 07, 08 y 09. `§n.m` remite a
`analisis.txt`; `doc NN §n.n` remite a la sección de ese documento; `plan §n`
remite a `00-plan-de-analisis.md`. Este documento **no cierra** ningún
`PD-xx` ni ningún `G-xx`: todo lo no resuelto queda visible en 10.3, con el
identificador que le asignó el mantenedor en `analisis.txt` §7 (PD-23…PD-29)
y sin crear IDs nuevos por cuenta propia.

| Campo | Contenido |
|---|---|
| Documento | 10 de la serie de análisis; depende de todos los anteriores (plan §4) |
| Alcance | `RN-001`…`RN-059` (doc 08), `CU-01`…`CU-42` (docs 05 y 06), entidades de `analisis.txt` §3, transiciones del doc 04, `EX-01`…`EX-23` (doc 07), criterios de aceptación (doc 07 §7.2 y plan §5) |
| Fuente única | los documentos 00–09 y 11 de `analisis/`, más `analisis.txt`; nada se redeclara ni se reenumera acá |
| Nombre en `odd/tasks/analisis-sigme.md` | `10-matriz-trazabilidad.md` (sin la segunda palabra separada); se conserva el nombre del plan (doc 09, Siguiente paso) |
| Criterio de cierre | plan §10: cero filas sin correspondencia |

## 10.1 RN ↔ CU ↔ entidad ↔ estado ↔ criterio de aceptación

Una fila por invariante, en el orden de doc 08 §8.1 y §8.2: **59 filas**
(`RN-001`…`RN-059`, sin huecos ni duplicados). La columna *CU / contrato*
sale de 8.2 (trazabilidad de casos de uso); las de *entidad* y *estado*,
de 8.1; la de *fuente*, de la columna Fuente de 8.1; y la de *criterio* es
la observación comprobable que se verifica en cada caso —el escenario
ejecutable Given/When/Then vive en doc 07 §7.2, según plan §5.

**Cómo leer la columna Estado.** `C-xx`, `ME-xx`, `INS-xx`, `US-xx`,
`SES-xx` y `GR-xx` son transiciones del doc 04; `EX-xx` es un estado crítico
del doc 07; `T-xx` y `S-xx` son gatillos del doc 03. Cuando la regla no
tiene dimensión de estado —es una regla de esquema, de seguridad o de
contrato— la celda dice `no aplica` con su motivo: **no es una fila sin
correspondencia, es una regla cuya correspondencia es la entidad y el
criterio**.

| RN | Afirmación | CU / contrato | Entidad | Estado | Criterio de aceptación | Fuente |
|---|---|---|---|---|---|---|
| RN-001 | Escritura de inscripción o anulación sólo dentro de la ventana de la convocatoria (`current_date` en AR). | CU-37, CU-39, CU-40 | `es_convocatoria`, `es_mesa_inscripcion` | INS-01, INS-02, INS-04; EX-01, EX-04, EX-09 | `POST /inscripciones` y `DELETE` rechazan con `hoy` fuera de rango y ninguna fila nace fuera de ventana (EX-01 → doc 07 §7.2). | RB-07, RB-08b, RB-09, RB-23; §3.17, §6 |
| RN-002 | Límite inclusivo hasta las 23:59:59; comparación por fecha de calendario, nunca por timestamp de UTC. | CU-37, CU-39, CU-26 | `es_convocatoria`, `pr_ventana`, `vw_ventana_vigente` | T-02, T-03, T-04; EX-01, EX-02 | A las 00:00:00 del día siguiente la ventana responde cerrada; dentro del día hábil hasta las 23:59:59 responde abierta (doc 07 §7.3). | RB-23, RB-07, RB-14; §3.17, §3.21 |
| RN-003 | Ninguna inscripción se crea si la convocatoria tiene `activa = false`, aunque su ventana esté vigente. | CU-37, CU-34 | `es_convocatoria` | C-05, INS-01; EX-04 | No se crea fila sobre convocatoria desactivada y `GET /convocatoria-vigente` no la ofrece como vigente (código PENDIENTE, EX-04). | RB-09; §3.17; S-07 |
| RN-004 | La ventana la decide el reloj del backend; ningún reloj ni parámetro de fecha del cliente participa. | CU-37, CU-39, CU-41 | `es_convocatoria`, `pr_ventana` | no aplica — regla transversal de reloj, sin transición propia | Ningún resultado de escritura depende de la hora o la fecha reportada por el dispositivo. | RB-23; doc 02 §2.1.2; doc 06 §6.6 |
| RN-005 | En v1 no existe ningún job programado: toda ventana y todo aviso se constatan en una acción o un request. | CU-34, CU-13, CU-42 | `es_convocatoria`, `pr_ventana`, `ntf_*` | no aplica — se afirma por ausencia de scheduler | Ningún cierre de ventana ni entrega depende de un cron; el recordatorio de 48 h queda en PD-11 (v2). | RB-23, RB-24; PD-11; doc 04 Convenciones |
| RN-006 | No existen dos filas de `es_mesa_inscripcion` activas con el mismo `(convocatoria_id, usuario_id, materia_id)`; unicidad por materia × convocatoria. | CU-37, CU-40 | `es_mesa_inscripcion` | INS-01, INS-04; EX-06 | `uq_inscripcion_unica` presente y la segunda inscripción activa a la misma materia responde `409` (EX-06 → doc 07 §7.2). | RB-08; §3.19; `uq_inscripcion_unica` |
| RN-007 | Las convocatorias son independientes: ninguna fila se restringe ni se modifica desde otra. | CU-37, CU-34, CU-11 | `es_convocatoria`, `es_mesa_inscripcion` | ME-06 | La unicidad nunca rechaza una inscripción válida de la convocatoria B por existir una de la convocatoria A. | RB-08, RB-16; §3.19, §3.17 |
| RN-008 | Dentro de la ventana, cada solicitud de inscripción que cumple las reglas se acepta: una o varias activas por alumno. | CU-37, CU-40 | `es_mesa_inscripcion` | INS-01 | El backend no rechaza una segunda inscripción válida de distinta materia alegando un límite de cantidad. | RB-06; §6 |
| RN-009 | No hay cupo: ninguna columna, índice ni validación limita la cantidad de inscriptos por mesa. | CU-37, CU-19 | `es_mesa_examen`, `es_mesa_inscripcion` | no aplica — ausencia declarada de capacidad | No existe columna de cupo y ninguna inscripción se rechaza por cupo agotado (doc 04 §4.6.6). | RB-01; §3.18, §3.19 |
| RN-010 | Sin etapa de aprobación: la inscripción queda en `estado = 'inscripto'` en la misma transacción de la request. | CU-37, CU-23 | `es_mesa_inscripcion` | INS-01 | `CHECK estado IN ('inscripto','anulado')` y ninguna fila en un estado intermedio. | RB-02; §3.19 |
| RN-011 | La anulación sólo opera durante la ventana y sobre la propia fila en `inscripto`; pasa a `anulado` y se conserva, nunca se elimina. | CU-39 | `es_mesa_inscripcion` | INS-02; EX-09 | `DELETE` fuera de ventana rechazado y ninguna fila borrada físicamente (EX-09 → doc 07 §7.2). | RB-08b, RB-07, RB-23; §3.19 |
| RN-012 | Una fila `anulado` no ocupa la unicidad ni se reutiliza: la reinscripción crea una fila nueva. | CU-39, CU-40 | `es_mesa_inscripcion` | INS-02, INS-04; EX-10 | Tras anular, la materia queda libre en el mismo instante y no existe `UPDATE` que reactive la fila. | RB-08b, RB-08c; §3.19 |
| RN-013 | `limite_materias` se evalúa sólo al crear la inscripción y nunca sobre filas existentes; valores y unidad de conteo **[CERRADOS — 2026-10-06]** (PD-02). | CU-37, CU-40 | `es_condicion`, `es_mesa_inscripcion` | INS-01, INS-04; EX-08 | Ningún proceso posterior invalida inscripciones ya creadas; Previa hasta 3, Regular hasta 8, Libre sin límite, unidad por convocatoria y edición desde SIGME. | RB-03, RB-08c; §3.16; S-05; PD-02 |
| RN-014 | Lista fija: a partir del cierre, el conjunto de inscripciones activas de la convocatoria no crece ni se recorta. | CU-37, CU-39, CU-38 | `es_mesa_inscripcion` | INS-01, INS-02; C-04; EX-01 | Ningún `inscripto_en` posterior al cierre ni inscripción que sale del listado definitivo después del cierre. | RB-17, RB-07, RB-23; §3.19 |
| RN-015 | Ninguna regla se reevalúa sobre inscripciones ya creadas después del cierre. | CU-38, CU-27, CU-30 | `es_mesa_inscripcion` | no aplica — sólo lectura posterior al cierre | Cero `INSERT`, `UPDATE` o `DELETE` sobre `es_mesa_inscripcion` con `hoy` posterior a `fecha_fin_inscripcion`. | RB-17, RB-18; §4 |
| RN-016 | Sin registro de asistencia: el modelo no contiene columna ni estado de presentación o falta. | CU-28, CU-38 | `es_mesa_inscripcion` | no aplica — ausencia de columna y de operación | No aparece ningún valor `presente`/`ausente` ni operación que marque faltas (doc 04 §4.6.6). | RB-18; §3.19; doc 04 §4.6.6 |
| RN-017 | Sin notas ni resultados: `estado` sólo admite `inscripto` y `anulado` y ninguna tabla guarda resultado. | CU-28, CU-29, CU-38 | `es_mesa_inscripcion`, `es_mesa_examen` | no aplica — ausencia de columna y de endpoint de resultado | `CHECK` vigente y ningún endpoint escribe el resultado de una mesa. | RB-21; §3.19, §3.18; doc 04 §4.6.6 |
| RN-018 | Si no hay mesa para la combinación materia × condición, `POST /inscripciones` no crea mesa ni inscripción (código: PD-19). | CU-37, CU-40 | `es_mesa_examen`, `es_mesa_inscripcion` | INS-01; EX-07 | El rechazo no inserta nada ni crea reserva de ningún tipo; el código HTTP queda por PD-19. | RB-31, RB-28; §6; PD-19 |
| RN-019 | El alumno nunca ve ni elige el grupo: ninguna respuesta bajo `/api/v1/sigme-mobile` expone `grupo_id`. | CU-35, CU-38 | `es_grupo_horario` (oculta), `es_mesa_examen` | no aplica — regla de contrato de respuesta | Ningún payload móvil incluye `grupo_id` ni campos del grupo, y ninguna validación depende de una elección de grupo. | RB-30; §3.22, §6 |
| RN-020 | Todo listado y toda impresión devuelven únicamente mesas con al menos una inscripción `inscripto`; la mesa vacía se ignora, no se borra. | CU-19, CU-21, CU-23, CU-27, CU-28, CU-30, CU-34, CU-35, CU-36 | `es_mesa_examen`, `es_mesa_inscripcion` | EX-16 | `vw_mesa_con_alumnos` aplicada en todo listado e impresión; ninguna mesa sin alumnos incluida ni eliminada por quedar vacía. | RB-22; §3.18 |
| RN-021 | **Condicional — PD-23:** no está decidido el alcance de RB-22 sobre `GET /mesas-disponibles`. | CU-35 | `es_mesa_examen`, `vw_mesa_con_alumnos` | no aplica — alcance sin decidir (EX-16, S-03) | No se fija qué filtra esa consulta hasta resolver el hueco heredado de doc 06 §6.8 y de EX-16. | RB-22, RB-28, RB-31; §3.18; S-03; PD-23 |
| RN-022 | `es_curso` identifica el año dentro de la orientación: no hay columna de división ni de turno. | CU-05, CU-06, CU-36 | `es_curso`, `es_materia` | no aplica — regla de modelo de datos | No aparece columna de división o turno ni validación que filtre por letra de división. | RB-15; §3.14 |
| RN-023 | Los talleres son `es_materia` con `es_taller = true`: no existe entidad de taller ni comportamiento diferenciado. | CU-05, CU-06, CU-21 | `es_materia` | no aplica — regla de modelo de datos | Ninguna tabla ni rama de negocio trata distinto al taller. | RB-04; §3.15 |
| RN-024 | Los cuatro snapshot se recalculan sólo al editar la asignación de la mesa, nunca al renombrar una fila de catálogo. | CU-06, CU-20, CU-29 | `es_mesa_examen` | S-08, S-09; E-07, E-08 | El renombre de catálogo no modifica mesas ya creadas y `PATCH /mesas/{id}` recalcula los cuatro en la misma transacción. | RB-11; §3.18; S-08, S-09 |
| RN-025 | No existe `v_mesa_examen`: los reportes leen columnas snapshot y las foreign keys sólo filtran y navegan. | CU-27, CU-28, CU-29, CU-30 | `es_mesa_examen` | no aplica — ausencia de vista | La vista no está creada y ningún reporte resuelve los nombres desde el catálogo en vivo. | RB-12; §3.18 |
| RN-026 | Convocatoria delimita todo: cada campaña nace con grupos, mesas e inscripciones nuevos; ninguna fila se reutiliza. | CU-11, CU-13, CU-34 | `es_convocatoria`, `es_grupo_horario`, `es_mesa_examen`, `es_mesa_inscripcion` | ME-06, GR-01 | Ninguna fila compartida entre convocatorias y el alta del ciclo siguiente crea filas `planificada` nuevas sin tocar las viejas. | RB-16; §3.17, §3.19 |
| RN-027 | Toda mesa tiene grupo: `grupo_id` es `NOT NULL` con foreign key `RESTRICT` y el grupo es de la misma convocatoria. | CU-15, CU-19, CU-30 | `es_mesa_examen`, `es_grupo_horario` | GR-01, ME-01 | Ninguna mesa con `grupo_id` nulo, con grupo inexistente o con grupo de otra convocatoria. | RB-27, RB-29; §3.18, §3.22 |
| RN-028 | El grupo declara sólo `fecha` y `hora` (más el `nombre` informativo): sin aula, profesor ni división. | CU-15, CU-16, CU-17 | `es_grupo_horario` | no aplica — regla de modelo de datos | No aparece columna de aula o profesor ni regla que dependa de ellas. | RB-27; §3.22 |
| RN-029 | `fecha` y `hora` de la mesa son copia sincronizada del grupo, escrita en la misma transacción de la edición. | CU-16, CU-35, CU-38 | `es_mesa_examen`, `es_grupo_horario` | GR-01, ME-01; S-21; EX-17 | Tras `PATCH /grupos/{id}` ninguna mesa difiere del horario de su grupo y el cambio mueve todas sus mesas a la vez. | RB-29; §3.18, §3.22; S-21 |
| RN-030 | El alumno no crea mesas: `POST /grupos` y `POST /mesas` exigen `mesa.crear` desde `sigme_web`. | CU-15, CU-37 | `es_mesa_examen`, `es_grupo_horario` | GR-01, ME-01 | Ninguna alta de mesa aceptada con el token de un alumno ni sin el permiso `mesa.crear`. | RB-28, RB-27; §2.7, §6 |
| RN-031 | Unicidad de mesas por `(convocatoria_id, materia_id, condicion_id, fecha)` — clave **[CERRADA — 2026-10-06]** (PD-13), sin `hora`. | CU-15, CU-30 | `es_mesa_examen` | ME-01; EX-18 | No existe fila duplicada según la clave cerrada; `hora` queda fuera (RB-15) y el índice se migra. | §3.18 (`uq_mesa_unica`); RB-27; PD-13 |
| RN-032 | **[CERRADO — 2026-10-06]** (PD-16): "no hay dos grupos idénticos en la misma convocatoria" está garantizado por la base con `uq_grupo_unico (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL`. | CU-15, CU-17 | `es_grupo_horario` | GR-01; EX-18 | No se inserta un segundo grupo idéntico (la colisión responde `409`) ni se da por existente una clave distinta de la cerrada. | §3.22; PD-16; RB-27 |
| RN-033 | **[CERRADO — 2026-10-06]** (PD-18): el borrado físico está impedido por `ON DELETE RESTRICT`; el lógico arrastra las mesas del grupo en la misma transacción y falla entera si alguna tiene inscripciones activas. | CU-17, CU-18, CU-30 | `es_grupo_horario`, `es_mesa_examen` | GR-02; EX-19 | Ningún `DELETE` físico arrastra mesas y ningún grupo borrado queda con mesas vivas apuntándolo. | §1.8, §3.22; PD-18; GR-02 |
| RN-034 | `POST /landing/preinscripcion` es un **UPSERT** sobre `(anio_lectivo, documento)`: `201`/`200`, jamás `409` por documento repetido. | doc 11 §11.4 — la serie `CU-xx` no cubre la landing | `pr_preinscripcion` | EX-02, EX-03 | Ninguna respuesta `409`/`422` motivada por un reenvío y ninguna fila duplicada para la misma identidad y año (EX-03 → doc 07 §7.2). | RB-13; §3.20, §6; O-4; EX-03 |
| RN-035 | Existe una sola ventana de preinscripción vigente por año lectivo; fuera de ella el POST responde `409 { code: "ventana-cerrada" }`. | CU-14; doc 11 §11.5 | `pr_ventana`, `vw_ventana_vigente` | T-04, T-05; EX-02 | Nunca dos ventanas vigentes a la vez y el `409` sólo significa ventana cerrada (EX-02 → doc 07 §7.2). | RB-14; §3.21; T-04, T-05 |
| RN-036 | La landing sólo escribe `pr_preinscripcion`: no existe endpoint público de lectura de preinscripciones. | doc 11 §11.6 | `pr_preinscripcion` | EX-02 | Ningún `GET` sin autenticación devuelve preinscripciones. | RB-10; §2.9 |
| RN-037 | Aislamiento topológico: ninguna foreign key entre `pr_preinscripcion` y `pe_*`, `us_*` ni `es_*`, en ninguna dirección. | doc 11 §11.2 | `pr_preinscripcion`, `pe_*`, `us_*`, `es_*` | no aplica — decisión arquitectónica del esquema | Cero foreign keys entre el dominio `pr_*` y el resto del esquema. | §3.20, §1.1; plan §3 (11.2) |
| RN-038 | Los seis campos del payload son `NOT NULL`; `anio_lectivo` lo toma el servidor de la ventana vigente, nunca del body. | doc 11 §11.3 | `pr_preinscripcion` | EX-03 | Ningún `INSERT` con alguno de los seis campos nulo y ningún `anio_lectivo` decidido por el cliente. | §3.20; O-2; RB-13 |
| RN-039 | Sólo se persiste el hash SHA-256 del refresh token; el access token no se almacena. | CU-01, CU-02, CU-31, CU-32 | `us_sesion` | EX-12 | Ninguna columna con el refresh en texto claro ni con tokens de acceso persistidos. | §2.2, §3.12 |
| RN-040 | Toda request autenticada exige `ver == us_usuario.token_version` vigente; subir la versión invalida los tokens anteriores. | CU-04, CU-09, CU-10 | `us_usuario` | US-02, US-04; EX-14 | Un token con `ver` antiguo no autoriza ninguna escritura después del cambio (EX-14 → doc 07 §7.2). | §2.6; S-15 |
| RN-041 | Todo endpoint protegido declara su permiso con `require_permiso()` antes de ejecutar el service; el reparto rol × permiso es la matriz de doc 02 §2.4 **[CERRADA — 2026-10-06]** (PD-03), sembrada en la migración inicial. | CU-05, CU-15, CU-37 | no aplica — catálogo de permisos §2.7 | EX-15 | Sin permiso no hay escritura y cada par (rol, endpoint) de la matriz está verificado; los celdas `PENDIENTE` de la matriz y `convocatoria.*` siguen en §2.7. | §2.7; doc 02 §2.4; PD-03 |
| RN-042 | Contraseñas con Argon2id (m=19456, t=2, p=1) y longitud mínima de 12 caracteres; nunca SHA-256 o MD5 puros ni texto plano. | CU-01, CU-04, CU-31 | `us_usuario` | no aplica — regla de almacenamiento de credenciales | Ningún hash reconocible como SHA-256 o MD5, ninguna clave en claro y bcrypt sólo como fallback con coste mínimo 10. | §2.5 |
| RN-043 | Módulo y permiso son acumulativos: el módulo nunca sustituye al permiso ni uno reemplaza al otro. | CU-01, CU-05, CU-31 | `us_usuario_modulo`, `us_sesion` | no aplica — regla de autorización compuesta | Ningún request aceptado sólo por tener el módulo sin el permiso, ni operación en un módulo no asignado. | §2.8; doc 02 §2.5 |
| RN-044 | Rate limit de login: cinco fallos en 15 minutos incrementan `intentos_fallidos`, setean `bloqueado_hasta` y suben `token_version`. | CU-01, CU-31 | `us_usuario` | US-02, US-03; EX-13 | Ningún intento aceptado tras el quinto fallo en la ventana y todo bloqueo lleva `bloqueado_hasta`; duración exacta PENDIENTE. | §2.4; E-14, S-16, T-09 |
| RN-045 | Todo índice único sobre tabla con soft delete es parcial (`WHERE deleted_at IS NULL`), de modo que borrar libera el valor. | CU-07, CU-09, CU-37 | `pe_persona`, `us_usuario`, `es_mesa_examen`, `es_mesa_inscripcion`, `pr_preinscripcion` | no aplica — regla de DDL | Ningún índice único total impide crear un registro nuevo después de borrar el anterior. | §1.7; §3.2, §3.5, §3.18, §3.19, §3.20 |
| RN-046 | Toda foreign key declara `ON DELETE` explícito; las referencias que no se pueden perder son `RESTRICT`. | CU-06, CU-08, CU-20 | tablas `pe_*`, `es_*`, `us_*` | S-17 | Ninguna foreign key sin `ON DELETE` y ningún borrado en cascada de filas que debían conservarse. | §1.8; S-17 |
| RN-047 | `updated_at` lo escribe un trigger `BEFORE UPDATE` en cada tabla, nunca un `DEFAULT now()`. | CU-08, CU-16, CU-20 | todas las tablas con `updated_at` | no aplica — regla de DDL | Ninguna tabla queda con `updated_at` congelada desde la creación. | §1.6 |
| RN-048 | Todas las columnas temporales son `timestamptz` y toda tabla con soft delete tiene su índice parcial `idx_{tabla}_activa`. | CU-01, CU-34 | todas las tablas | no aplica — regla de DDL | Cero columnas `timestamp` sin zona y cero tablas con `deleted_at` sin su índice parcial. | §1.4, §1.5 |
| RN-049 | Todo envío nace de una acción de usuario: en v1 ningún job programado; el recordatorio de 48 h está deferido a v2 (PD-11). | CU-34, CU-42 | `ntf_notificacion`, `ntf_envio`, `us_dispositivo` | EX-21 | Ningún envío disparado por un cron y ninguna notificación de v1 depende de un scheduler. | RB-24, RB-25; PD-11; S-20 |
| RN-050 | Lista cerrada de notificaciones por canal en v1; el conjunto in-app por rol sigue en PD-10; el restablecimiento de clave se encola desde v1 (PD-04, cerrado 2026-10-06). | CU-34, CU-37, CU-42 | `ntf_notificacion`, `ntf_envio` | EX-21 | Ningún canal ni evento fuera de la lista de RB-24 y RB-25, y ningún envío por tiempo dentro de v1. | RB-24, RB-25; PD-10, PD-04; §4 |
| RN-051 | La cola de email es obligatoria desde v1, con reintento y estado de envío registrado en `ntf_envio`; el password reset usa esa cola con su tabla `us_password_reset` (PD-04, cerrado 2026-10-06). | CU-37, CU-42 | `ntf_envio` | EX-21 | El fallo de entrega ocurre después de la respuesta y no modifica la respuesta HTTP ni ninguna fila de negocio. | RB-25; S-20; PD-04 |
| RN-052 | Los tokens push viven en `us_dispositivo` con refresco y purga; el alta y la baja no tienen endpoint declarado (PENDIENTE). | CU-42 | `us_dispositivo` | EX-22 | No se inventa una ruta de registro de tokens ni se da por entregado el alta con el endpoint inexistente. | RB-24; §4, §6; EX-22 |
| RN-053 | Las tres lecturas de SIGME-M se sirven desde la caché local sin red y sin token, con su marca de última actualización. | CU-34, CU-35, CU-38, CU-41 | contrato de lectura de SIGME-M | EX-23 | Ninguna lectura exige red o token para mostrarse y la respuesta trae datos suficientes para marcarse desactualizada. | RB-26; doc 06 §6.6; doc 02 §2.1.2 |
| RN-054 | Escritura siempre online: inscribir y anular exigen conexión y sesión válida, exigidas en toda escritura. | CU-37, CU-39, CU-40 | `es_mesa_inscripcion`, `us_sesion` | EX-11, EX-23 | Ninguna escritura aceptada sin token válido y ningún contrato que prometa completarla sin red. | RB-26; doc 06 §6.6 |
| RN-055 | Ninguna cola de acciones offline; la caché nunca decide ventana, unicidad ni límite de condición. | CU-41 | contrato de SIGME-M | EX-23 | No existe endpoint de sincronización diferida y toda validación de negocio corre en línea en el backend. | RB-26; doc 06 §6.6; doc 07 §7.6 |
| RN-056 | Los tres reportes de cierre se emiten sólo desde SIGME con `reporte.exportar`, aplican RB-22 y no exponen notas ni asistencia. | CU-27, CU-28, CU-29, CU-30 | `es_mesa_examen`, `es_mesa_inscripcion` | E-09 | Ningún reporte emitido sin permiso, con mesas sin inscriptos o con columnas de resultado o asistencia. | RB-19, RB-32, RB-21, RB-18, RB-22; §3.18 |
| RN-057 | **Condicional — PD-15, PD-20:** `GET /cobertura-mesas` devuelve los pares materia × condición sin mesa, antes de abrir la ventana. | CU-21, CU-37 | `es_convocatoria`, `es_mesa_examen`, catálogo | E-17 | El endpoint existe y responde pares reales; no se da por resuelto el origen del conjunto sin cerrar PD-15. | RB-31; §6; E-17; PD-15, PD-20 |
| RN-058 | Ley 25.326 art. 5: no existe columna de consentimiento en `pr_preinscripcion` porque el proceso es físico y externo. | doc 11 §11.3 — la serie `CU-xx` no cubre la landing | `pr_preinscripcion` | no aplica — cumplimiento por ausencia | Ninguna columna de consentimiento ni endpoint que lo recoja en el esquema. | §3.20 (O-1); doc 11 §11.3 |
| RN-059 | Ley 25.326 art. 6: el aviso previo de uso de datos es un requisito heredado a la landing, no una obligación del backend. | doc 11 §11.3 — la serie `CU-xx` no cubre la landing | `pr_preinscripcion` | no aplica — requisito heredado | El backend no expone ni guarda ese aviso; el requisito queda trazado al doc 11. | §3.20; plan §3 (11.3) |

**Total: 59 filas** (`RN-001`…`RN-059`, sin huecos ni duplicados). **53** invocan
al menos un `CU-xx`; las **6** restantes — `RN-034`, `RN-036`, `RN-037`,
`RN-038`, `RN-058` y `RN-059` — no pueden citarlo porque la serie `CU-xx` no
cubre la preinscripción de la landing ni los requisitos normativos, y se
trazan al doc 11 y a la Ley 25.326 (el ítem sigue **PENDIENTE** en el
checklist de doc 08 línea 392 y se lista en 10.3).

## 10.2 Cobertura: huérfanos en ambos sentidos

Conteos medidos sobre los documentos de la serie, no estimados. Cada fila
compara lo que la matriz espera con lo que la fuente declara.

| Relación | Esperado | Hallado | Huérfanos |
|---|---|---|---|
| RN → CU o contrato | 59 | 59 (10.1) | **0** |
| CU → RN | 42 | 36 citados en doc 08 §8.2 | **6** |
| RB → RN | 32 | 32 (doc 08 §8.4) | **0** — `RB-05` y `RB-20` con nota *no es un invariante* |
| Evento o gatillo → destino (doc 03 §3.4) | 48 (`E-01`…`E-17`, `S-01`…`S-21`, `T-01`…`T-10`) | 43 con `CU-xx` | **5** |
| EX → RN | 23 | 21 citados en doc 08 §8.1/§8.2 | **2** |
| Transición → cobertura (docs 05–08) | 35 (`C-01`…`C-08`, `ME-01`, `ME-03`…`ME-07`, `INS-01`…`INS-04`, `US-01`…`US-09`, `SES-01`…`SES-05`, `GR-01`…`GR-03`) | 33 | **2** |
| NFR → vía de verificación | 54 | 54 (doc 09 declara método en cada fila) | **0** — 6 `[POR DEFINIR]` siguen sin número (bajaron de 9 con los cierres de PD-05 y PD-06 el 2026-10-06); los 7 que eran `Propuesta` fueron aprobados el 2026-10-05 |
| PD y G → documento dueño | 29 (24 `PD-xx` + 5 `G-xx`) | 29 (docs 08 §8.5 y 09 los listan todos) | **0** |

**Hallazgos.** Ninguno se cierra en este documento: cada uno queda trazado a
la sección de 10.3 que lo lleva.

| # | Hallazgo | Detalle medido | Destino |
|---|---|---|---|
| 1 | `CU-03` y `CU-33` sin RN | Cerrar sesión (`POST /auth/logout`, `POST /auth/logout-all`) no es citado por ninguna RN en doc 08 §8.2, aunque `RN-039` y `RN-040` sostienen justamente la sesión y el `token_version` | checklist doc 08 línea 392 |
| 2 | `CU-12` sin RN | Consultar convocatorias y constatar la ventana no tiene invariante propia: el filtrado por `activa` y ventana vive en `RN-003` y `RN-020` con otros CU | checklist doc 08 línea 392 |
| 3 | `CU-22`, `CU-24` y `CU-25` sin RN **y** sin contrato | Cambio de estado de mesa (**G-05**, resuelta 2026-10-06), anulación desde SIGME (sin endpoint) e inscripción en nombre de un alumno (**PD-03**, cerrado 2026-10-06 sin cubrirlo) | 10.3 — filas `CU-22`, `CU-24`, `CU-25` |
| 4 | 5 eventos sin `CU-xx` | `E-04`, `S-12` y `S-13` apuntan a la landing, ya cubierta por el contrato del doc 11 (`RN-034`, `RN-038`); `S-10` (cierre del acta — G-05 resuelta 2026-10-06) y `T-10` (recordatorio 48 h — PD-11, sigue deferido a v2) no invocan ningún CU | 10.3 — filas `G-05` (S-10) y `PD-11` (T-10) |
| 5 | 2 EX sin RN | `EX-05` (cierre de campaña por calendario) y `EX-20` (estados de la mesa sin disparador) no son sostenidos por ninguna RN: el disparador que los gobierna es **G-05** | 10.3 — fila `G-05` (ambos) y fila `EX-20` (además sin contrato de respuesta) |
| 6 | 2 transiciones sin cobertura | `C-03` (`borrador` → `abierta`, **PENDIENTE** por el hueco `convocatoria.*` de §2.7 — PD-03 se cerró el 2026-10-06 sin crearlo) y `ME-07` (sólo si se adopta la opción (ii) sobre `acta_cerrada`) no aparecen en los docs 05–08 | 10.3 — filas `C-03` y `ME-07` |
| 7 | 7 casos hasta ahora sin identificador → **PD-23…PD-29** | El mantenedor les asignó ID en `analisis.txt` §7 (2026-10-05): alcance de RB-22 sobre `GET /mesas-disponibles` (PD-23), contrato de cuerpo de las respuestas de error (PD-24), código de la respuesta repetida del `DELETE /mis-inscripciones/{id}` (PD-25), alta y baja del token de push (PD-26), duración del bloqueo de login (PD-27), paginación de `GET /mis-inscripciones` (PD-28) y la alta individual de una mesa fuera de la alta masiva (PD-29, saldo del doc 04) | 10.3 — filas `PD-23`…`PD-29` |

**Nota sobre `EX-05` y `EX-20`:** ninguno de los dos se formula como
invariante porque el disparador que los gobierna es **G-05** —
**[RESUELTA — 2026-10-06]**: nadie dispara la transición, la constatación es
del calendario al leer. `EX-20` sí figura
entre los **13** `EX` sin contrato de respuesta (doc 07 §7.7.2) y
`EX-05` no, porque su cierre es una constatación de calendario sin request
(doc 07 §7.1).

**Veredicto.** El criterio de cierre del plan §10 —cero filas sin
correspondencia— **se cumple para las 59 filas de 10.1** (59/59 RN con CU o
contrato declarado). En la dirección inversa el resultado **no es cero**: los
**6** `CU-xx` sin RN, los **2** `EX` sin RN, las **2** transiciones sin
cobertura, los **5** eventos sin `CU-xx` y los **7** casos que no estaban
anclados a un ID (hoy **PD-23…PD-29**) quedan listados arriba y trazados a su
fila de 10.3 cuando el hueco tiene una propia. Este documento los hace
visibles para SDD; no los resuelve.

## 10.3 `[ABIERTA]` y `[POR DEFINIR]` consolidada

Un solo consolidado — agrupado por familia de ítem — con **todos** los ítems
de cada serie (los resueltos, con su estado), tomados de su fuente sin reabrirlos
ni reenumerarlos; recuento medido el 2026-10-07. El estado usa el vocabulario del doc 09: `[ABIERTA]` (pregunta
sin decidir), `[POR DEFINIR]` (el requisito existe pero ningún número lo
cierra), **Propuesta** (número sugerido por el doc 09, todavía sin aprobar) y el estado de los cerrados: **[CERRADA]** o **[RESUELTA]** con fecha.
Los 7 NFR que estaban en **Propuesta** fueron aprobados por el mantenedor el
2026-10-05, pasaron a **Medible** en el doc 09 y ya no se listan acá. Todo
ítem figura con el `PD-xx` que le asignó el mantenedor en `analisis.txt`
§7; este documento no crea ni reenumera IDs.

**23 `PD-xx` + 5 `G-xx` (28 filas):**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| PD-02 | Valores de `es_condicion.limite_materias` y criterio de conteo | `analisis.txt` §7; doc 08 §8.5 | RN-013, CU-37, CU-40 (resueltos: Previa 3, Regular 8, Libre sin límite; unidad por convocatoria) | [CERRADA — 2026-10-06] |
| PD-03 | Semilla de roles, permisos y usuarios; reparto rol × permiso y mapeo endpoint → permiso | `analisis.txt` §7; doc 08 §8.5 | RN-041, NFR-021 (reparto y mapeo resueltos con la matriz doc 02 §2.4); CU-25 y C-03 siguen por huecos de la matriz y de §2.7 | [CERRADA — 2026-10-06] |
| PD-04 | Diseño de la tabla de restablecimiento de clave (`us_password_reset`) | `analisis.txt` §7; doc 08 §8.5 | RN-050, RN-051 (resueltos: `us_password_reset` desde v1, email por la cola; el contrato de reintento sigue abierto) | [CERRADA — 2026-10-06] |
| PD-05 | ¿Se necesita bitácora de auditoría (`aud_evento` con snapshot JSONB)? | `analisis.txt` §7; doc 08 §8.5 | NFR-044 (resuelto: `aud_evento` append-only con snapshot JSONB y alcance definido) | [CERRADA — 2026-10-06] |
| PD-06 | Estrategia de despliegue y variables de entorno por entorno | `analisis.txt` §7; doc 08 §8.5 | NFR-011, NFR-042 y la condición de NFR-006 (resueltos: Vercel + FastAPI zero-config); NFR-023 conserva el valor del origen | [CERRADA — 2026-10-06] |
| PD-10 | Conjunto exacto de notificaciones in-app por rol | `analisis.txt` §7; doc 08 §8.5 | RN-050, CU-42 | [ABIERTA] |
| PD-11 | Recordatorio de 48 h antes de la mesa — **deferido a v2** | `analisis.txt` §7; doc 08 §8.5 | RN-049, T-10, CU-42 | [ABIERTA] |
| PD-12 | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? | `analisis.txt` §7; doc 08 §8.5 | RN-027, RN-029, RN-031, GR-01 | [ABIERTA] |
| PD-13 | ¿Debe `uq_mesa_unica` incluir `hora`? | `analisis.txt` §7; doc 08 §8.5 | RN-031, EX-18 (resueltos: clave con `convocatoria_id`, sin `hora`; el código del choque de mesas sigue en EX-18) | [CERRADA — 2026-10-06] |
| PD-15 | De dónde sale el conjunto esperado de pares materia × condición de la cobertura | `analisis.txt` §7; doc 08 §8.5 | RN-057, CU-21 | [ABIERTA] |
| PD-16 | ¿Se agrega `UNIQUE (convocatoria_id, fecha, hora)` a `es_grupo_horario`? | `analisis.txt` §7; doc 08 §8.5 | RN-032, EX-18 (resueltos: `uq_grupo_unico` con `WHERE deleted_at IS NULL`, colisión → `409`) | [CERRADA — 2026-10-06] |
| PD-17 | Interpretación de `grupo.hora` (`time` sin zona) frente a RB-23 | `analisis.txt` §7; doc 08 §8.5 | RN-002, RN-029, GR-01 | [ABIERTA] |
| PD-18 | Borrado lógico de un grupo con mesas vivas y su efecto en `vw_mesa_con_alumnos` | `analisis.txt` §7; doc 08 §8.5 | RN-033, GR-02 (resueltos: cascada lógica transaccional que falla si alguna mesa tiene inscripciones activas; el endpoint y su permiso siguen sin declarar) | [CERRADA — 2026-10-06] |
| PD-19 | Código HTTP del rechazo de `POST /inscripciones` sin mesa | `analisis.txt` §7; doc 08 §8.5 | RN-018, EX-07 | [ABIERTA] |
| PD-20 | Formato canónico del catálogo de materias para validarlo programáticamente | `analisis.txt` §7; doc 08 §8.5 | RN-057 | [ABIERTA] |
| PD-21 | Renombrado o alta de catálogo sin endpoint declarado | `analisis.txt` §7; doc 08 §8.5 | RN-024, CU-06 | [ABIERTA] |
| PD-22 | Efecto del `PATCH /preinscripciones` | `analisis.txt` §7; doc 08 §8.5 | CU-26 | [ABIERTA] |
| PD-23 | Alcance de RB-22 sobre `GET /mesas-disponibles` | `analisis.txt` §7; doc 06 §6.8; doc 07 EX-16; doc 08 §8.5 | RN-021, CU-35 | [ABIERTA] |
| PD-24 | Contrato de cuerpo de las respuestas de error | `analisis.txt` §7; §6 (cerrado 2026-10-05); doc 07 §7.7.2 | cuerpo de error de todos los endpoints fuera de `/landing/preinscripcion` (resuelto) | [CERRADA — 2026-10-05] |
| PD-25 | Código de la respuesta repetida de `DELETE /mis-inscripciones/{id}` | `analisis.txt` §7; §6 (cerrado 2026-10-05); doc 06 §6.8; doc 07 §7.8; doc 08 §8.5 | NFR-030, EX-10 (resueltos: `204` en ambas) | [CERRADA — 2026-10-05] |
| PD-26 | Endpoint de alta y baja del token de push (`us_dispositivo`) | `analisis.txt` §7; §6 (cerrado 2026-10-05); doc 06 §6.8; doc 07 EX-22; doc 08 §8.5 | RN-052, CU-42 (resueltos: `POST /dispositivos` y `DELETE /dispositivos/{id}`) | [CERRADA — 2026-10-05] |
| PD-27 | Duración exacta del bloqueo de login y su código de respuesta | `analisis.txt` §7; §6 (cerrado 2026-10-05); doc 04 US-03; doc 07 EX-13 | RN-044, NFR-010 (resueltos: `429` + `Retry-After`, 15 min) | [CERRADA — 2026-10-05] |
| PD-28 | Paginación de `GET /mis-inscripciones` | `analisis.txt` §7; plan §3.06; doc 06 §6.6 | lectura degradada de SIGME-M | [ABIERTA] |
| G-01 | Qué significa "matrícula" para el cliente: la palabra no existe en `analisis.txt` | doc 01 §1.5.2 | vocabulario de docs 05 y 06; checklist doc 01 línea 277 | [ABIERTA] |
| G-02 | Qué rol usa el permiso `preinscripcion.crear`, si la landing es anónima | doc 01 §1.5.2 | RN-041, CU-14, CU-26, NFR-021 | [ABIERTA] |
| G-03 | Si existe el rol "docente", comentado en el DDL de `us_rol` | doc 01 §1.5.2 | doc 04 §4.6.3 (rol no opera ninguna transición) | [ABIERTA] |
| G-04 | Cómo obtiene SIGME-M la cascada orientación → curso → materia → condición | doc 01 §1.5.2 | CU-36 | [ABIERTA] |
| G-05 | Quién y cómo cambia el estado de la convocatoria y de la mesa | doc 01 §1.5.2; regla temporal 2026-10-06 | CU-13, CU-22, CU-34, EX-05, EX-20, ME-03…ME-05 (resuelta: nadie lo cambia — la constatación es del calendario al leer) | [RESUELTA — 2026-10-06] |

**11 NFR (6 `[POR DEFINIR]` y 5 resueltos — NFR-010 y NFR-030 con PD-27 y PD-25 el 2026-10-05; NFR-011 y NFR-042 con PD-06 y NFR-044 con PD-05 el 2026-10-06 —; los 7 `Propuesta` fueron aprobados por el mantenedor el 2026-10-05):**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| NFR-007 | Tamaño máximo de body del `POST /landing/preinscripcion` y su código de respuesta | doc 09 §9.2; doc 11 PENDIENTE 2 | doc 11 §11.4.4 | [POR DEFINIR] |
| NFR-008 | Umbral numérico del rate limit estricto de la landing | doc 09 §9.2; doc 11 PENDIENTE 1 | doc 11 §11.4 y §11.6 | [POR DEFINIR] |
| NFR-010 | Bloqueo de login: 15 minutos de duración y `429` con `Retry-After` ante intento bloqueado | doc 09 §9.2 | EX-13; RN-044 (resuelto con PD-27) | [RESUELTA — 2026-10-05] |
| NFR-011 | Estrategia de despliegue y variables de entorno por entorno | doc 09 §9.2 | PD-06 (resuelto 2026-10-06: Vercel + FastAPI zero-config) | [RESUELTA — 2026-10-06] |
| NFR-021 | Reparto rol × permiso, mapeo endpoint → permiso y dueño de `preinscripcion.crear` | doc 09 §9.3 | G-02, EX-15 (PD-03 cerrado 2026-10-06: reparto y mapeo con la matriz doc 02 §2.4) | [POR DEFINIR] |
| NFR-023 | Valor exacto del origen CORS de la landing | doc 09 §9.3; doc 11 PENDIENTE 3 | doc 11 §11.6 (PD-06 cerró 2026-10-06 la estrategia, no el valor) | [POR DEFINIR] |
| NFR-030 | `204 No Content` idempotente en la segunda respuesta de `DELETE /mis-inscripciones/{id}` | doc 09 §9.4 | EX-10; RN-012 (resuelto con PD-25) | [RESUELTA — 2026-10-05] |
| NFR-042 | Obtención de la `ip` detrás de proxy (`X-Forwarded-For` u otro header confiable) | doc 09 §9.5; doc 11 PENDIENTE 5 | doc 11 §11.6 — PD-06 resuelto 2026-10-06 (Vercel, con el proxy siempre delante del API) | [RESUELTA — 2026-10-06] |
| NFR-043 | Mecanismo de captura de los UTM (no puede ir en el body de 6 campos) | doc 09 §9.5; doc 11 PENDIENTE 4 | doc 11 §11.6 | [POR DEFINIR] |
| NFR-044 | Bitácora de auditoría `aud_evento` con snapshot JSONB | doc 09 §9.5 | PD-05 (resuelto 2026-10-06: `aud_evento` append-only con snapshot JSONB y alcance definido) | [RESUELTA — 2026-10-06] |
| NFR-047 | Observabilidad: métricas del API, punto de salud y registro de errores | doc 09 §9.5 | ninguna fuente declara métricas ni health check | [POR DEFINIR] |

**13 `EX` sin contrato de respuesta (doc 07 §7.7.2):**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| EX-04 | Convocatoria inactiva o fuera de su ventana: ningún código declarado | doc 07 §7.1, §7.7.2 | respuesta de `POST /inscripciones` ante RB-09 | [ABIERTA] |
| EX-07 | Combinación materia × condición sin mesa | doc 07 §7.1, §7.7.2 | PD-19; RN-018 | [ABIERTA] |
| EX-08 | Límite de materias por condición alcanzado | doc 07 §7.1, §7.7.2 | código del rechazo (PD-02 cerró 2026-10-06 sólo los valores); RN-013 | [ABIERTA] |
| EX-09 | Anulación fuera de la ventana de inscripción | doc 07 §7.1, §7.7.2 | código del `DELETE` rechazado | [ABIERTA] |
| EX-10 | Anulación repetida (reintento del `DELETE`): efecto nulo, código sin declarar | doc 07 §7.1, §7.7.2 | NFR-030; RN-012 | [ABIERTA] |
| EX-14 | Invalidación global por `token_version` | doc 07 §7.1, §7.7.2 | respuesta ante token con `ver` antiguo; RN-040 | [ABIERTA] |
| EX-15 | Usuario sin el permiso del endpoint | doc 07 §7.1, §7.7.2 | código de la respuesta (matriz definitiva desde PD-03, cerrado 2026-10-06); RN-041 | [ABIERTA] |
| EX-17 | Edición de un grupo con la ventana de inscripción abierta | doc 07 §7.1, §7.7.2 | PD-12; RN-029 | [ABIERTA] |
| EX-18 | Choque de unicidad al crear grupos o mesas | doc 07 §7.1, §7.7.2 | código del choque de mesas (PD-13 y PD-16 cerrados 2026-10-06: claves y `409` de grupos); RN-031, RN-032 | [ABIERTA] |
| EX-19 | Grupo borrado con mesas vivas que lo referencian | doc 07 §7.1, §7.7.2 | código del `409` (PD-18 cerró 2026-10-06 la cascada); RN-033 | [ABIERTA] |
| EX-20 | Estados de la mesa sin disparador declarado | doc 07 §7.1, §7.7.2 | G-05 resuelta 2026-10-06 — sin operación ni código: la constatación es al leer; queda la frontera `cerrada`/`realizada` (ME-05, opciones (i)/(ii)) | [ABIERTA] |
| EX-21 | Cola de email con fallo de envío | doc 07 §7.1, §7.7.2 | contrato de reintento de la cola (PD-04 cerró 2026-10-06 el password reset, no el reintento); RN-051 | [ABIERTA] |
| EX-22 | Registro del token de push sin endpoint | doc 07 §7.1, §7.7.2 | RN-052; CU-42 | [ABIERTA] |
**5 `CU-xx` sin contrato declarado:**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| CU-18 | Baja de un grupo: `mesa.eliminar` existe en §2.7 pero §6 no expone la operación | doc 05 §5.11 | GR-02 (endpoint y permiso siguen sin declarar); PD-18 cerró 2026-10-06 la cascada | [ABIERTA] |
| CU-22 | Cambio de estado de la mesa: el `CHECK` admite tres valores y ninguno los escribe | doc 05 §5.11 | G-05 resuelta 2026-10-06 — sin escritura: la constatación es al leer | [CERRADA — 2026-10-06] |
| CU-24 | Anulación de inscripción desde SIGME: permiso real sin endpoint en `/api/v1/sigme` | doc 05 §5.11 | contrato de `inscripcion.anular`; INS-03 | [ABIERTA] |
| CU-25 | Inscripción en nombre de un alumno desde SIGME: `inscripcion.crear` sin dueño ni endpoint | doc 05 §5.11 | dueño y endpoint (hueco de la matriz; PD-03 cerró 2026-10-06 sin cubrirlo), PD-19 | [ABIERTA] |
| CU-36 | Cascada orientación → curso → materia → condición: descrita sólo como comentario en §6 | doc 06 §6.8 | G-04 | [ABIERTA] |

**5 ítems de checklist sin marcar en los documentos de la serie:**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| checklist doc 01 (línea 277) | Ninguna palabra del dominio aparece sin definir | doc 01 checklist de cierre | G-01 | [ABIERTA] |
| checklist doc 05 (línea 599) | Cada excepción mapea a un código HTTP | doc 05 checklist de cierre | códigos de doc 07 §7.7.2 | [ABIERTA] |
| checklist doc 06 (línea 361) | Las excepciones sin código HTTP concreto no se cierran acá | doc 06 checklist de cierre | códigos de doc 07 §7.7.2 | [ABIERTA] |
| checklist doc 08 (línea 392) | Cada RN aparece en al menos un `CU-xx`: **53 de 59** | doc 08 checklist de cierre | trazado de RN-034, RN-036, RN-037, RN-038, RN-058, RN-059 | [ABIERTA] |
| checklist doc 11 (línea 416) | Verificación conjunta con el usuario de los puntos (b), (c) y (d) | doc 11 checklist de cierre | estado `[PROVISIONAL]` → `[VERIFICADO]` del doc 11 | [ABIERTA] |

**15 PENDIENTE del doc 11 — 14 abiertos, con el punto 5 resuelto el 2026-10-06** (el punto 16 quedó resuelto el
2026-10-04):

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| doc 11 · PENDIENTE 1 | Umbral numérico del rate limit de la landing | doc 11 PENDIENTE consolidados | NFR-008; §11.4 y §11.6 | [ABIERTA] |
| doc 11 · PENDIENTE 2 | Tamaño máximo de body y su código de respuesta | doc 11 PENDIENTE consolidados | NFR-007; §11.4.4 | [ABIERTA] |
| doc 11 · PENDIENTE 3 | Valor exacto del origen CORS de la landing | doc 11 PENDIENTE consolidados | NFR-023; §11.6 | [ABIERTA] |
| doc 11 · PENDIENTE 4 | Mecanismo de captura de UTM | doc 11 PENDIENTE consolidados | NFR-043; §11.6 | [ABIERTA] |
| doc 11 · PENDIENTE 5 | Obtención de la `ip` detrás de proxy | doc 11 PENDIENTE consolidados | NFR-042 (resuelto 2026-10-06: header de proxy confiable, despliegue Vercel); §11.6 | [RESUELTA — 2026-10-06] |
| doc 11 · PENDIENTE 6 | Formato de `documento` (¿sólo dígitos?) | doc 11 PENDIENTE consolidados | §11.3 | [ABIERTA] |
| doc 11 · PENDIENTE 7 | Rango de `fecha_nacimiento` (¿no futura?) | doc 11 PENDIENTE consolidados | §11.3 | [ABIERTA] |
| doc 11 · PENDIENTE 8 | ¿`orientacion` debe coincidir con `es_orientacion.descripcion`? | doc 11 PENDIENTE consolidados | §11.3, §11.7 | [ABIERTA] |
| doc 11 · PENDIENTE 9 | Tratamiento de campos extra del body (ignorar vs `422`) | doc 11 PENDIENTE consolidados | §11.3 | [ABIERTA] |
| doc 11 · PENDIENTE 10 | Forma del item en `errors[]` y cuerpo del `429` | doc 11 PENDIENTE consolidados | §11.4.3 — **(D), PROVISIONAL** | [ABIERTA] |
| doc 11 · PENDIENTE 11 | Orden de evaluación `422` vs `409` | doc 11 PENDIENTE consolidados | §11.4.4 — **(D), PROVISIONAL** | [ABIERTA] |
| doc 11 · PENDIENTE 12 | Instante del acuse de preinscripción por email | doc 11 PENDIENTE consolidados | §11.4.5 | [ABIERTA] |
| doc 11 · PENDIENTE 13 | Validación de no-solape entre ventanas de años distintos | doc 11 PENDIENTE consolidados | §11.5 | [ABIERTA] |
| doc 11 · PENDIENTE 14 | Migración futura a `pe_persona` (disparador, `nombre_tutor`, destino de `anio_lectivo`/`estado`) | doc 11 PENDIENTE consolidados | §11.7 | [ABIERTA] |
| doc 11 · PENDIENTE 15 | Dueño del permiso `preinscripcion.crear` | doc 11 PENDIENTE consolidados | G-02; §11.6 (PD-03 cerró 2026-10-06 sin fijar este dueño) | [ABIERTA] |

**1 saldo del doc 04 — PD-29:**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| PD-29 | Alta individual de una mesa: alcance de `POST /mesas` fuera de la alta masiva del grupo | `analisis.txt` §7; doc 04 §4.6.4 | ME-01, RB-28, RB-27 | [ABIERTA] |

**2 transiciones del doc 04 sin cobertura en los docs 05–08:**

| ID | Qué es | Documento/sección que lo levantó | Qué bloquea | Estado |
|---|---|---|---|---|
| C-03 | `borrador` → `abierta` por activación manual con la ventana ya iniciada: **PENDIENTE**, mismo hueco que C-01 | doc 04 §4.6.1, §4.6.4 | código `convocatoria.*` (hueco de §2.7; PD-03 cerró 2026-10-06 sin crearlo); RN-003 | [ABIERTA] |
| ME-07 | `acta cerrada` → `planificada` (fila nueva del ciclo siguiente): existe **sólo si se adopta la opción (ii)** sobre `acta_cerrada` | doc 04 §4.2 | opción (i) vs (ii) de los estados de la mesa (G-05 resuelta 2026-10-06 no la cubre) | [ABIERTA] |

**Recuento medido el 2026-10-07: 80 ítems = 54 `[ABIERTA]` (entre ellas PD-11,
deferido a v2) + 6 `[POR DEFINIR]` + 20 resueltos (13 `[CERRADA]` y 7
`[RESUELTA]`).** De los 20, 6 cerraron el 2026-10-05 (PD-24…PD-27, NFR-010 y
NFR-030) y 14 el 2026-10-06 (PD-02, PD-03, PD-04, PD-05, PD-06, PD-13, PD-16,
PD-18, CU-22, G-05, NFR-011, NFR-042, NFR-044 y el punto 5 del doc 11).
Ninguno se resuelve en este documento; los que un día se cierren deben
cerrarlos en su documento de origen y actualizarse acá.

## 10.4 Inventario de entregables listos para SDD

Conteos de líneas medidos con `(Get-Content <archivo>).Count` sobre el estado
del repositorio el 2026-10-07: son el dato objetivo que permite detectar
cambios posteriores a este cierre.

| Documento | Líneas | Qué aporta a SDD | Estado |
|---|---|---|---|
| `analisis.txt` | 1351 | Fuente única: DDL de §3, endpoints de §6, reglas `RB-01`…`RB-32` de §4, pendientes `PD-01`…`PD-29` de §7 | fuente |
| `00-plan-de-analisis.md` | 297 | Serie, criterios de cierre por documento y puente hacia SDD (§5) | lista |
| `01-glosario-y-alcance.md` | 287 | Glosario, vocabulario prohibido, actantes, `G-01`…`G-05` | lista (1 ítem de checklist abierto) |
| `02-actores-y-consumidores.md` | 350 | Consumidores, usuarios finales, matriz rol × permiso, módulos | lista |
| `03-eventos-y-gatillos.md` | 255 | `E-01`…`E-17`, `S-01`…`S-21`, `T-01`…`T-10` y la maestra de §3.4 | lista |
| `04-maquinas-de-estados.md` | 609 | 35 transiciones con actor, permiso y precondiciones; exclusiones anti-regresión | lista |
| `05-casos-de-uso-sigme.md` | 613 | `CU-01`…`CU-30` con permisos y fuentes; consolidado §5.11 | lista (1 ítem de checklist abierto) |
| `06-casos-de-uso-sigme-m.md` | 376 | `CU-31`…`CU-42`, semántica de idempotencia y operación degradada; §6.8 | lista (1 ítem de checklist abierto) |
| `07-estados-criticos-y-excepciones.md` | 644 | `EX-01`…`EX-23` con escenario Given/When/Then ejecutable por cada uno (§7.2) | lista |
| `08-reglas-de-negocio.md` | 414 | `RN-001`…`RN-059`, cobertura `RB-xx` → RN (§8.4) y pendientes (§8.5) | lista (1 ítem de checklist abierto) |
| `09-requisitos-no-funcionales.md` | 325 | 54 NFR, cada uno con su método de verificación | lista |
| `10-matriz-de-trazabilidad.md` | 356 | Esta matriz: 10.1–10.4 y el inventario de huecos | lista |
| `11-landing-preinscripcion.md` | 426 | Contrato completo del `POST /landing/preinscripcion` con sus 5 respuestas | `[PROVISIONAL]` (1 ítem de checklist abierto) |

Fuera de la serie numerada: `analisis/orientaciones-cursos-materias.md`
(196 líneas) es material de catálogo, no un documento con criterio de cierre.

### Checklist de cierre (10 · Matriz de trazabilidad)

- [x] **10.1 con 59 filas**: `RN-001`…`RN-059`, sin huecos ni duplicados,
      cada una con CU o contrato, entidad, estado, criterio de aceptación y
      fuente.
- [x] **Los 42 `CU-xx` están presentes en el documento**: 36 citados en
      10.1 y los 6 restantes (`CU-03`, `CU-12`, `CU-22`, `CU-24`, `CU-25`,
      `CU-33`) en los hallazgos de 10.2.
- [x] **10.2 cubre ambas direcciones** con conteos medidos: RN → CU 59/59,
      CU → RN 36/42, RB → RN 32/32, eventos 43/48, EX 21/23, transiciones
      33/35, NFR 54/54, PD y G 29/29.
- [x] **10.3 consolida 80 ítems** en tablas por familia: 54 `[ABIERTA]` y
      6 `[POR DEFINIR]` más los 20 resueltos — 13 `[CERRADA]` y 7
      `[RESUELTA]`, 6 de ellos el 2026-10-05 (PD-24…PD-27, NFR-010 y
      NFR-030) y 14 el 2026-10-06 —, sin crear ningún ID nuevo (los 7 que
      eran `Propuesta` fueron aprobados por el mantenedor el 2026-10-05).
- [x] **10.4 con conteos de líneas medidos** para los 13 entregables.
- [x] **Criterio del plan §10 para las filas de la matriz**: las 59 filas de
      10.1 tienen correspondencia — **cero filas sin correspondencia**.
- [ ] **Criterio inverso (10.2)**: quedan **6** `CU-xx` sin RN, **2** `EX`
      sin RN, **2** transiciones sin cobertura y **5** eventos sin destino.
      Todos están listados y trazados a 10.3; **este documento no los
      cierra**. Los 7 casos que no tenían ID ya están anclados a
      **PD-23…PD-29**.

## Siguiente paso

La serie queda cerrada para SDD (plan §5): cada spec toma de **10.1** su
criterio de aceptación ya desplazado desde el doc 07, de **10.4** su
entregable de origen y de **10.3** la lista de huecos que no puede dar por
resueltos. El orden sugerido por el plan §4 y el estado de 10.3 indican
empezar por los bloques que no dependen de ningún `PD-xx` abierto — catálogo,
seguridad y sesión, listados y reportes — dejando inscripción y grupos, que
son los que más PD concentran, para cuando se decidan.
