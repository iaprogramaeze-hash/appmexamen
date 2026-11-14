# 01 · Glosario y alcance — Backend EPET36

Este documento fija los dos cimientos de la serie de análisis: **qué es** el
producto de este proyecto y **qué significa cada palabra** que se usa para
describirlo. Se lee solo, pero sirve también como referencia durante todos los
documentos siguientes: cualquier término que aparezca en `02` a `11` está
definido aquí.

Toda afirmación de regla de negocio cita su fuente: `RB-xx` y `PD-xx` remiten a
`analisis.txt` (secciones 4 y 7 respectivamente); `§n.m` remite a la sección de
ese archivo; `plan §n` remite a `00-plan-de-analisis.md`. Lo que ninguna fuente
resuelve se marca como **PENDIENTE**, nunca se completa por suposición.

## Rápido recorrido

1. Leer **1.1** para entender qué entra y qué no en este proyecto.
2. Usar **1.2** como diccionario durante toda la serie.
3. Antes de usar una palabra coloquial, verificarla en **1.3**.
4. Consultar **1.4** (actantes) y **1.5** (preguntas abiertas) alrededor de
   dudas sobre quién hace qué o sobre lo que falta.

---

## 1.1 Alcance: dentro y fuera

**Respuesta corta:** el producto de este proyecto es **únicamente el backend**
(API, modelo de datos, reglas, seguridad y requisitos no funcionales). Las tres
interfaces son consumidores del API, no producto a diseñar.

| Área | ¿En alcance? | Detalle | Fuente |
|---|---|---|---|
| API REST del backend | **Sí** | Endpoints, contratos, códigos de respuesta | plan §2 |
| Modelo de datos (`pe_*`, `us_*`, `es_*`, `pr_*`) | **Sí** | DDL, índices, FK, triggers | `analisis.txt` §1, §3 |
| Reglas de negocio RB-01…RB-32 | **Sí** | Invariantes que el backend hace cumplir | `analisis.txt` §4 |
| Seguridad: JWT, RBAC, Argon2id, rate limit | **Sí** | `analisis.txt` §2 | `analisis.txt` §2 |
| Requisitos no funcionales del backend | **Sí** | Rendimiento, disponibilidad, Ley 25.326 (art. 9, 14, 16) | plan §3 (09) |
| Contratos que el backend ofrece a los clientes | **Sí** | Idempotencia, reintentos, paginación, respuestas offline-friendly | plan §3 (06.6) |
| Interfaces: Landing, SIGME web, SIGME-M móvil | **No** | Proyectos futuros separados; aparecen sólo como consumidores del API | plan §2; `odd/tasks` |
| Requisitos de pantalla de esas interfaces (WCAG 2.2, WCAG2Mobile, UX de carga offline) | **No — heredados a los clientes** | Se listan en `09` como requisito de los proyectos futuros, no como obligación de este proyecto | plan §3 (09.6) |
| Código fuente del backend | **No** | La tarea actual es de análisis: OUT escribir código | `odd/tasks` |
| Consentimiento de datos personales (Ley 25.326, art. 5) | **No** | Proceso físico externo posterior; no hay columna de consentimiento | O-1; `analisis.txt` §3.20 |
| Aviso previo al titular (Ley 25.326, art. 6) | **No** | Requisito heredado a la landing | O-1 |
| Recordatorio de 48 h antes de la mesa | **No en v1** | Deferido a v2; exige un job programado que en v1 no existe | PD-11; RB-24 |
| Preinscripción de la landing (`pr_*`) | **Sí, como contrato** | El backend expone `POST /landing/preinscripcion`; la interfaz que lo llama es externa | `analisis.txt` §2.9, §6 |

**Cómo aparecen las tres aplicaciones.** Sólo como **clientes del API** que
imponen requisitos sobre el backend. Ejemplo del plan: *"SIGME-M reintenta en
red móvil inestable"* es un requisito del backend (debe aceptar reintentos sin
duplicar); *"el botón se ve así"* o *"WCAG en la app"* no lo son (plan,
"Cómo aparecen las 3 aplicaciones en este análisis").

---

## 1.2 Glosario — español → término técnico

### 1.2.1 Dominio de mesas de exámenes

| Término (ES) | Definición operativa | Técnico / entidad | Fuente |
|---|---|---|---|
| **Mesa** (mesa de exámenes) | Instancia en la que se rinde una materia: combinación de materia + condición dentro de una convocatoria, con la **fecha y la hora que copia de su grupo**. No tiene cupo. La crea el secretario **en bloque** con su grupo (RB-28); el alumno nunca la crea. | `es_mesa_examen` | RB-01, RB-05, RB-27, RB-28 |
| **Grupo de mesas** | Agrupación de mesas de una misma convocatoria definida por **una fecha y una hora** que todas comparten. Unidad de planificación: una convocatoria puede abarcar varios días, un grupo por fecha y franja horaria. Explícitamente **ni aula ni profesor** (fuera de alcance, confirmado 2026-10-01). | `es_grupo_horario` | RB-27, RB-29; `analisis.txt` §3.22 |
| **Convocatoria** | Campaña de exámenes con **una** ventana de inscripción, que puede abarcar **varios días** de rendición (un grupo de mesas por fecha y hora). Agrupa N mesas y grupos, y **delimita todo**: cerrada la campaña se abre otra después. | `es_convocatoria` | RB-16, RB-09, RB-27 |
| **Ventana** (de inscripción) | Rango `[fecha_inicio_inscripcion, fecha_fin_inscripcion]` de una convocatoria, dentro del cual se puede inscribir y anular. Siempre calificar: *ventana de inscripción* vs *ventana de preinscripción*. | `es_convocatoria.fecha_*` | RB-06, RB-07, RB-23 |
| **Inscripción** | Registro de un alumno en una mesa. Sólo tiene dos estados: `inscripto` y `anulado`. | `es_mesa_inscripcion` | RB-06, RB-21 |
| **Anulación** | Revocación de la propia inscripción por error de elección. La fila se conserva como `anulado`; no se borra y no ocupa en el índice único. | `estado = 'anulado'` | RB-08b |
| **Unicidad de inscripción** | Un alumno no se inscribe dos veces a la **misma materia** dentro de la **misma convocatoria**. No es unicidad por mesa. | `uq_inscripcion_unica (convocatoria_id, usuario_id, materia_id)` | RB-08 |
| **Condición** | Categoría académica con la que se rinde una mesa: Regular, Previa o Libre. Puede llevar un límite de materias. | `es_condicion` | RB-03 |
| **Previa** | Condición con límite de materias: Previa hasta 3, Regular hasta 8 y Libre sin límite (NULL) — valores por defecto sembrados y editables desde SIGME. | `es_condicion.limite_materias` | RB-03, PD-02 (cerrado 2026-10-06) |
| **Límite de materias por condición** | Tope de materias que un alumno puede llevar en una mesa según su condición. Unidad de conteo **por convocatoria**: el tope se reinicia en cada campaña. Se controla **sólo al inscribirse** (o al anular y reinscribir); nunca el día de la mesa. | `es_condicion.limite_materias` | RB-03, RB-08c, RB-17, PD-02 |
| **Materia** | Unidad curricular de un curso. Puede ser un taller. | `es_materia` | RB-04 |
| **Taller** | Materia normal con la marca `es_taller = true`. El sistema **no distingue** su comportamiento del resto. | `es_materia.es_taller` | RB-04 |
| **Orientación** | Tecnicatura de la escuela (por ejemplo, Gestión y Administración de las Organizaciones, Tecnología de los Alimentos). | `es_orientacion` | `analisis.txt` §3.13 |
| **Curso** | **Año** dentro de la orientación (1.º, 2.º, 3.º). No incluye letra de división ni turno. | `es_curso.anio` | RB-15 |
| **Permiso de examen** | Reporte **individual por alumno** que detalla qué materias rinde ese día (corrección: solo lista mesas en las que el alumno se encuentra inscripto indistinto del grupo o fecha), con la **fecha y la hora** de cada mesa (de su grupo). Sale de SIGME, en papel, y se entrega en mano al alumno (corrección: puede darse este caso de darle en mano, como que el alumno tenga la posibilidad de bajárselo desde la aplicación móvil, también es posible que el secretario decida imprimir en masa todos los permisos, cosa que sería poco usado pero la posibilidad existe). | `GET /reportes/permiso-examen/{usuario_id}` (crear path para impresión masiva, y aclarar que luego voy a pasar un template de cómo es el diseño de los reportes impresos, en pos de ahorrar hoja tipo A4 se deberían imprimir al menos 3 por carilla, en lo posible dependiendo de lo largo de la lista de materias que aparecen en cada permiso de examen) | RB-19, RB-27 |
| **Acta volante** | Reporte **por mesa de una materia** con todos los alumnos inscriptos en esa mesa. Sale de SIGME, en papel, y se entrega a los profesores evaluadores. | `GET /reportes/acta-volante/{mesa_id}` | RB-19 | (así como los permisos se pueden imprimir en masa, luego voy a pasar un template de cómo es el diseño de los reportes impresos, en pos de ahorrar hoja tipo A4 se deberían imprimir al menos 3 por carilla, en lo posible dependiendo de lo largo de la lista de alumnos que aparecen en cada acta volante)
| **Planilla de grupos** | Tercer reporte impreso, **por convocatoria**: cada grupo (fecha, hora) con las mesas que se rinden en él (materia, condición). Da la **vista de horario**, no el detalle de alumnos por mesa. Aplica RB-22. **[CONFIRMADO — 2026-10-04]: su inclusión en la primera entrega está confirmada.** | `GET /reportes/planilla-grupos/{convocatoria_id}` | RB-32, RB-19, RB-22 |
| **Reporte** | Toda impresión de cierre desde SIGME. Son **tres**: permiso de examen y acta volante (RB-19) y planilla de grupos (RB-32, confirmada 2026-10-04). Todo reporte entrega únicamente mesas con al menos una inscripción activa. | `/reportes/*` | RB-19, RB-22, RB-32 |
| **Lista definitiva** | Conjunto de inscriptos tal como queda al cerrar la ventana; no se revalida ni se modifica después. | inscripciones con `estado = 'inscripto'` | RB-17, RB-18 |
| **Nota / resultado de la mesa** | **No existe en el sistema.** No hay columna de nota, ni aprobado/desaprobado, ni rectificación: el resultado vive en el acta en papel. | — (concepto inexistente) | RB-21 |
| **Inasistencia** | **No se registra.** Quien no se presenta queda fuera del sistema. | — (concepto inexistente) | RB-18 |
| **Profesor evaluador** | Destinatario del acta volante en papel. No aparece como rol del sistema (ver 1.5.2). | — | RB-19 |

### 1.2.2 Dominio de la preinscripción (landing)

| Término (ES) | Definición operativa | Técnico / entidad | Fuente |
|---|---|---|---|
| **Preinscripción** | Solicitud de ingreso a la escuela para el **próximo año lectivo**. Ajena a las mesas de exámenes; comparte base de datos sólo por practicidad y para agilizar una migración futura, **sin foreign keys** hacia `pe_*` ni `es_*`. | `pr_preinscripcion` | `analisis.txt` §3.20; plan §3 (11.1, 11.2) |
| **Ventana de preinscripción** | Rango `[fecha_desde, fecha_hasta]` durante el cual el formulario de la landing acepta envíos. Sólo puede haber **una vigente** a la vez. | `pr_ventana`, `vw_ventana_vigente` | RB-14, O-3 |
| **Año lectivo** | Año al que se preinscribe. Lo toma el backend de la ventana vigente; **el cliente no lo envía**. | `pr_ventana.anio_lectivo` | O-3, `analisis.txt` §3.21 |
| **Upsert de preinscripción** | Repetir el formulario **no es error**: si la identidad `(anio_lectivo, documento)` no existe se inserta (201), si existe se actualizan los campos mutables (200). Nunca 409 por duplicado. | `uq_preinscripcion_unica` | RB-13, O-4 |
| **Landing** | Página promocional anónima: cualquiera completa el formulario, sin roles, sin JWT. **Sólo escribe**; no hay endpoint de lectura público. | `POST /landing/preinscripcion` | RB-10; `analisis.txt` §2.9 |
| **Consentimiento (Ley 25.326)** | Se recoge después, en formulario físico. Es un proceso externo: no hay columna de consentimiento ni fecha de otorgamiento en la tabla. | — (fuera del sistema) | O-1 |
| **Estado de la preinscripción** | Ciclo de vida del registro: `pendiente`, `convertido`, `descartado`. | `pr_preinscripcion.estado` | `analisis.txt` §3.20 |

### 1.2.3 Seguridad, actores y aplicación

| Término (ES) | Definición operativa | Técnico / entidad | Fuente |
|---|---|---|---|
| **Usuario** | Cuenta con la que una persona se autentica en el backend. Se distingue de la persona física que lo representa. | `us_usuario` ↔ `pe_persona` | `analisis.txt` §3.5 |
| **Rol** | Conjunto de permisos asignable a un usuarios (Alumno, Secretario/a, Director, Administrador, Superadmin). | `us_rol`, `us_usuario_rol` | P-08; `analisis.txt` §3.6 |
| **Permiso** | Acción concreta que un rol puede realizar, con código estable (`mesa.crear`), nunca descripción libre. | `us_permiso`, `us_rol_permiso` | `analisis.txt` §2.7 |
| **Módulo** | Aplicación en la que un usuario puede operar: `landing`, `sigme_web`, `sigme_mobile`. El módulo dice **a qué app puede entrar**; el permiso dice **qué puede hacer adentro**. | `us_modulo`, `us_usuario_modulo` | `analisis.txt` §2.8 |
| **Sesión** | Registro de un login: familia de refresh tokens, estado (`activo`/`revocado`), expiración, IP y user agent. Habilita rotación, reuse detection y "cerrar sesión en todos lados". | `us_sesion` | `analisis.txt` §2.3, §3.12 |
| **Access token** | Token JWT de vida corta (15 min, máx. 30) que transporta roles, permisos y módulos. Sólo firmado, no cifrado. | claim `exp` | `analisis.txt` §2.1 |
| **Refresh token** | Token opaco de 7 días que rota en cada uso; si se reutiliza, se revoca toda la familia. En base de datos sólo se guarda su hash SHA-256. | `us_sesion.refresh_token_hash` | `analisis.txt` §2.2 |
| **Invalidación global (`token_version`)** | Entero que sube al cambiar clave, cambiar un rol o bloquear la cuenta; los access tokens emitidos con la versión vieja dejan de servir. | `us_usuario.token_version`, claim `ver` | `analisis.txt` §2.6 |
| **Rate limit** | Toque de intentos: máximo 5 fallos de login por usuario/IP cada 15 minutos y después bloqueo temporal; en la landing, límite estricto anti-bots. | `us_usuario.bloqueado_hasta` | `analisis.txt` §2.4, §2.9 |
| **Consumidor / cliente** | Aplicación que llama al API (SIGME, SIGME-M, Landing). No es producto de este análisis. | — | plan §2 |
| **Backend** | El producto de este proyecto: API, modelo de datos, reglas, seguridad y requisitos no funcionales. | — | plan §2; `odd/tasks` |

### 1.2.4 Términos técnicos transversales

| Término (ES) | Definición operativa | Fuente |
|---|---|---|
| **Snapshot** | Copia inmutable de nombres (orientación, curso, materia, condición) guardada en la mesa al crearla o al editar su asignación; nunca cambia por un renombre de la tabla origen. | RB-11, RB-12 |
| **Soft delete** | Borrado lógico con `deleted_at`; los índices únicos son parciales (`WHERE deleted_at IS NULL`) para poder reinsertar después. | `analisis.txt` §1.5, §1.7 |
| **Job programado (scheduler)** | Tarea que corre sola a una hora fija. **No existe en v1**: todos los envíos nacen de una acción de usuario. | RB-24, PD-11 |
| **Cola de email** | Infraestructura de envío con reintento y registro de estado; **obligatoria desde v1** porque sin ella no funciona el password reset. | RB-25 |
| **Campanita in-app** | Notificación dentro de SIGME, dirigida a los roles administrativos. | RB-24 |
| **Push** | Notificación a SIGME-M (alumno) sobre apertura y cierre de inscripciones; requiere tokens por dispositivo. | RB-24 |
| **Idempotencia** | Propiedad de que reintentar la misma operación no produce un efecto duplicado. El plan la exige para las operaciones que el cliente reintenta. | plan §3 (06.6, 09.4) |
| **Reloj autoritativo / zona horaria** | El backend evalúa fechas en `America/Argentina/Buenos_Aires` comparando fecha de calendario; no usa el reloj del cliente ni timestamps crudos de UTC. | RB-23 |
| **Ley 25.326 (Habeas Data)** | Norma de protección de datos: aviso (art. 6, heredado a la landing), consentimiento (art. 5, externo), seguridad (art. 9), acceso en 10 días y rectificación/supresión en 5 días hábiles (art. 14 y 16, a cargo del backend). | `analisis.txt` §3.20; plan §3 (09.3) |

---

## 1.3 Vocabulario prohibido

Palabras del habla cotidiana de la escuela que **no son sinónimas** de los
términos del sistema. Usarlas en requisitos, tickets o specs introduce
ambigüedad; se reemplazan por el término de la columna "Término correcto".
La tabla incluye también **vocabulario retirado por decisiones del análisis**:
términos que alguna vez fueron válidos y que hoy ya no existen en el modelo
(RB-20 revocada; PD-14 resuelto). Se listan acá para que nadie los
reintroduzca.

| Palabra coloquial | Por qué NO equivale | Término correcto | Fuente |
|---|---|---|---|
| **"llamado"** | Es la manera informal de referirse a la campaña de exámenes. El sistema no usa la palabra en ninguna tabla, columna ni regla. | **convocatoria** | `analisis.txt` §3.17, §4 |
| **"mesa" = "convocatoria"** | La convocatoria es la **campaña** con su ventana de fechas; la mesa es **una instancia de rendir** dentro de esa campaña. Una convocatoria agrupa N mesas. | distinguir **convocatoria** vs **mesa** | `analisis.txt` §3.17; RB-16 |
| **"inscribirse" (a la escuela)** | En este sistema "inscribirse" es anotarse a **una mesa de exámenes**. El ingreso a la escuela del próximo año es otro proceso. | **preinscripción** | RB-13, RB-14 |
| **"matricularse" / "matrícula"** | La palabra **no aparece en `analisis.txt`**: no hay entidad, columna ni regla de matrícula. El análisis no la usa ni la define. | **preinscripción** (ingreso) o **inscripción** (mesa), según el caso. Uso de "matrícula": **PENDIENTE** de confirmación con el cliente (ver 1.5.2) | `analisis.txt` (ausencia); plan §3 (01.2) |
| **"cupo"** | No hay cupo por mesa; una mesa puede tener cualquier cantidad de alumnos. Hablar de "cupo" o "cupo agotado" introduce un requisito inexistente. | no aplica — **RB-01** | RB-01 |
| **"división" (1.º A, 1.º D) y "turno"** | No existen en el modelo: todas las divisiones y turnos comparten las mismas materias. | **curso** = año dentro de la orientación | RB-15 |
| **"aprobar / desaprobar" a un alumno en el sistema** | El sistema no guarda resultados; sólo sabe que el alumno está inscripto. | **inscripto** / **anulado** | RB-21 |
| **"nota", "calificación", "rectificación de nota"** | No hay columnas ni estados de resultado; tampoco existe el trámite de rectificación dentro del sistema. | el resultado vive en el **acta en papel** | RB-21 |
| **"asistencia", "ausente", "presente", "inasistencia"** | No se registra quién se presentó. | no aplica — **RB-18** | RB-18 |
| **"aprobar la inscripción" / "cola de aprobación"** | No hay etapa de aprobación: anotarse es directo. | **inscripción** efectiva al instante | RB-02 |
| **"taller" como entidad aparte** | El taller es una materia con una marca informativa; el sistema no distingue su comportamiento. | **materia** con `es_taller = true` | RB-04 |
| **"la mesa la crea el primer alumno" / "el sistema crea la mesa al anotarse"** | Era cierto bajo RB-20, hoy **REVOCADA**: las mesas las crea el secretario **en bloque**, con la fecha y la hora de su grupo. El alumno sólo se inscribe a mesas que ya existen. | **alta masiva de mesas por el secretario** | RB-20 (revocada), RB-28 |
| **"grupo con aula" / "grupo con profesor"** | El grupo es únicamente `fecha` + `hora`; aula y profesor están **fuera de alcance** (confirmado 2026-10-01). | **grupo de mesas** = fecha + hora | RB-27 |
| **"fecha común de mesas"** | **Ya no existe.** La convocatoria no declara ninguna fecha de exámenes: la columna `es_convocatoria.fecha_mesa` fue **eliminada** (PD-14 resuelto). Cada mesa toma su fecha de su grupo. | **grupo de mesas** (fecha + hora) | RB-27, RB-29; PD-14 (resuelto) |
| **"mesa especial"** | **Retirada por el modelo de grupos.** Una fecha inusual no es una excepción de una fecha común (ya no hay fecha común): es simplemente **otro grupo**. | **grupo de mesas** | RB-27; PD-14 (resuelto) |
| **"ventana" sin calificar** | Hay dos ventanas distintas y no se confunden: la de inscripción a mesas y la de preinscripción de la landing. | **ventana de inscripción** / **ventana de preinscripción** | RB-07, RB-14 |
| **"acta" digital editable** | El acta es papel. Los reportes de SIGME (permiso de examen, acta volante y planilla de grupos) son impresiones, no documentos editables en el sistema. | **permiso de examen** / **acta volante** | RB-19, RB-21, RB-32 |
| **"estudiantes / registradores / operadores"** | Nombres genéricos de roles que no corresponden a ningún rol real. | **Alumno, Secretario/a, Director, Administrador, Superadmin** | P-08 |

---

## 1.4 Actantes y sistemas externos

| Actante | Tipo | Qué hace | Requisito que impone al backend | Fuente |
|---|---|---|---|---|
| **Alumno** | Actor primario (vía SIGME-M) | Consulta, se inscribe, anula | Lectura con caché y escritura online; unicidad por materia × convocatoria; límite de ventana | RB-26, RB-08, RB-07 |
| **Secretario/a** | Actor primario (vía SIGME) | **Crea grupos de mesas y sus mesas en bloque**; consulta personas, inscripciones y mesas; anula inscripciones; emite reportes | RBAC por permiso (`mesa.crear` para crear grupos); reportes que aplican RB-22 | RB-19, RB-22, RB-27, RB-28, `analisis.txt` §3.19 |
| **Director** | Actor primario (vía SIGME) | Consulta estado y reportes | Permisos de lectura y de reporte — reparto según la matriz rol × permiso (doc 02 §2.4), decidida en PD-03 (2026-10-06) | P-08, PD-03 |
| **Administrador** | Actor primario (vía SIGME) | Gestiona catálogo, usuarios y ventanas | Módulo `sigme_web` + permisos de gestión | `analisis.txt` §2.8, §3.21 |
| **Superadmin** | Actor primario (vía SIGME) | Igual que Administrador, más estructura de seguridad | Gestión de roles, permisos y módulos | P-08, `analisis.txt` §2.7 |
| **Persona anónima en la landing** | Actor primario sin identidad | Completa y reenvía el formulario de preinscripción | Endpoint público sin JWT, con rate limit, CORS restringido y validación estricta | RB-10, `analisis.txt` §2.9 |
| **Reloj del sistema** | Sistema externo | Define qué día es hoy en `America/Argentina/Buenos_Aires` | Toda ventana se evalúa por fecha de calendario en esa zona; sin dependencia del reloj del cliente | RB-23 |
| **Servicio de correo (cola de email)** | Sistema externo | Envía acuses, confirmaciones y password reset | Cola con reintento y estado de envío **obligatoria desde v1** | RB-24, RB-25 |
| **Servicio push** | Sistema externo | Entrega notificaciones a SIGME-M | Tokens por dispositivo con refresco y purga de caducos | RB-24; `analisis.txt` §4 (infra `us_dispositivo`) |
| **Base de datos PostgreSQL (Neon)** | Sistema externo | Persistencia | Driver HTTP serverless de Neon (sin pool TCP: no hay proceso persistente en Vercel); migraciones Alembic desde CI/local sobre la conexión directa | `analisis.txt` §0 |
| **Landing (como cliente)** | Cliente del API | Envía `POST /landing/preinscripcion` | Único consumidor sobre `pr_preinscripcion`; sólo escritura | RB-10; plan §2 |
| **SIGME web / SIGME-M (como clientes)** | Clientes del API | Gestión e inscripción | Contratos de idempotencia, reintentos y expiración de sesión | plan §2, §3 (06.6) |
| **Proveedor de despliegue (Vercel)** | Sistema externo | Alojamiento del backend (FastAPI, soporte zero-config) | Variables de entorno definidas en el panel de Vercel por entorno, nunca en el repo; CORS obligatorio hacia los clientes | PD-06 (cerrado 2026-10-06) |

---

## 1.5 Preguntas abiertas hacia el cliente

**Respuesta corta:** no quedan preguntas de análisis bloqueantes (P-01…P-09 y
O-1…O-4 están resueltas, plan §6). Lo que sigue abierto son **pendientes de
diseño PD-xx** (`analisis.txt` §7).

### 1.5.1 Pendientes de diseño abiertos

| ID | Pregunta que sigue abierta | Qué bloquea | Estado |
|---|---|---|---|
| **PD-02** | Valores de `es_condicion.limite_materias` (Previa 3 / Regular 8) y si el límite se cuenta por convocatoria o por ciclo lectivo. Ya está decidido que se valida **sólo** al inscribirse. | Validación al inscribir (docs 05, 06, 08) | **CERRADO** — 2026-10-06: Previa hasta 3, Regular hasta 8, Libre sin límite (NULL); unidad de conteo **por convocatoria** (se reinicia en cada campaña, multi-día y multi-grupo incluidos); valores sembrados como default y editables desde SIGME (`PATCH /condiciones`, §6); arrastra PD-21 |
| **PD-03** | Semilla inicial de roles, permisos y usuarios administradores (script seed), incluido el reparto exacto rol × permiso. | Matriz de 2.4, autorización en detalle | **CERRADO** — 2026-10-06: roles y permisos viajan en la migración inicial de Alembic (reproducible en dev, staging y prod); el primer superadmin entra por variable de entorno (la credencial nunca toca el repo); el reparto y el mapeo endpoint → permiso salen de la matriz rol × permiso del doc 02 |
| **PD-05** | ¿Se necesita bitácora de auditoría (quién modificó qué mesa)? Si sí: tabla `aud_evento` con snapshot JSONB. | Auditoría, doc 09 | **CERRADO** — 2026-10-06: SÍ desde v1, `aud_evento` append-only con snapshot JSONB; alcance: escrituras exitosas, intentos denegados (401/403) y descargas/impresiones de reportes; se excluyen las lecturas corrientes; el snapshot no contiene `password_hash`, refresh tokens ni hashes de sesión |
| **PD-06** | Estrategia de despliegue (Railway/Render/VPS) y variables de entorno por entorno. | Operación, doc 09 | **CERRADO** — 2026-10-06: Vercel con FastAPI (zero-config); backend independiente de los tres clientes, por lo que el CORS es obligatorio; sin proceso persistente se retira el pool TCP y Neon se usa por driver HTTP serverless; Alembic desde CI/local; variables en el panel de Vercel por entorno |
| **PD-09** | Detalle de qué materias corresponde a cada curso y orientación (6 cursos × 8-10 materias por orientación). | Semilla de catálogo, datos iniciales | **[RESUELTO — 2026-10-04]** — catálogo entregado en `analisis/orientaciones-cursos-materias.md` |
| **PD-10** | Conjunto exacto de notificaciones in-app por rol (secretario, director, admin, superadmin). RB-24 sólo fija el canal. | Notificaciones, doc 06/09 | **ABIERTO** — definición iterativa con el usuario |
| **PD-11** | Recordatorio 48 h antes de la mesa: exige job programado, seguimiento de entrega y reintentos. No arrastra cambios de esquema. | **Nada en v1** | **DEFERIDO A V2** |
| **PD-12** | ¿Se pueden **crear o mover** grupos con la ventana de inscripción **abierta**? | Docs 04, 05, 06 | **ABIERTO** — nace del cambio de alcance 2026-10-01 |
| **PD-13** | ¿`uq_mesa_unica` debe incluir `hora`? Hoy no: prohíbe dos mesas de la misma materia y condición el mismo día aunque cambie el horario. | Esquema, doc 04 | **CERRADO** — 2026-10-06: `UNIQUE (convocatoria_id, materia_id, condicion_id, fecha) WHERE deleted_at IS NULL` — se agrega `convocatoria_id` (hueco contra RN-007) y `hora` queda fuera (dos franjas serían turnos, RB-15); migración del índice |
| **PD-14** | Destino de la columna de fecha común de `es_convocatoria` → **RESUELTO: se ELIMINA.** No queda fecha de exámenes que declarar en la convocatoria: cada grupo declara su `fecha` y su `hora` (RB-27) y la mesa copia ese par (RB-29). El nombre retirado de la columna queda en 1.3 (vocabulario retirado). | — (ya no bloquea) | **RESUELTO** — 2026-10-01: eliminada |
| **PD-15** | RB-31 (cobertura de mesas): falta especificar de dónde sale el conjunto esperado de pares (materia × condición) de una convocatoria; la convocatoria no tiene FK directa a orientaciones/cursos y hay que derivarlo del catálogo. Fuente: `analisis.txt` (RB-31) y endpoint `GET /cobertura-mesas`. | Docs 04, 05 (cobertura) | **ABIERTO** — severidad de origen CRITICAL (inferential) |
| **PD-16** | `es_grupo_horario` (§3.22) no tiene restricción única sobre `(convocatoria_id, fecha, hora)`: permite grupos duplicados idénticos en la misma convocatoria. Definir si se agrega `UNIQUE`. | Esquema | **CERRADO** — 2026-10-06: SÍ, `UNIQUE (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` (índice parcial, misma convención que `idx_grupo_activa`); colisión → 409 |
| **PD-17** | `grupo.hora` es `time` sin zona horaria; RB-23 evalúa por fecha de calendario en `America/Argentina/Buenos_Aires`. Definir cómo se interpreta `hora` (BA vs UTC) al combinarse con `fecha`. | Docs 04, 05 | **ABIERTO** — severidad de origen WARNING (inferential) |
| **PD-18** | Borrado lógico de un grupo (`deleted_at`) con mesas vivas que lo referencian (`ON DELETE RESTRICT`): ¿se permite? ¿las mesas quedan apuntando a un grupo borrado? ¿RB-22 / `vw_mesa_con_alumnos` considera `deleted_at` del grupo? | Esquema, doc 04 | **CERRADO** — 2026-10-06: cascada lógica transaccional — borrar el grupo borra lógicamente todas sus mesas en la misma transacción; si alguna tiene inscripciones activas, falla entera y no se borra nada; el `ON DELETE RESTRICT` de la FK sigue cubriendo sólo el borrado físico |
| **PD-19** | Rechazo de `POST /inscripciones` cuando la combinación no tiene mesa (RB-31): la respuesta dice "Rechazo" sin código HTTP (¿404, 409, 422?). Definirlo junto con los códigos existentes de §6. | Doc 05, contrato | **ABIERTO** — severidad de origen WARNING (inferential) |
| **PD-20** | El catálogo `analisis/orientaciones-cursos-materias.md` (PD-09, resuelto) es texto sin estructura machine-readable: sin IDs de materias, sin mapping a condiciones ni flags `es_taller`; la semilla y la cobertura RB-31 no pueden validarlo programáticamente. | Semilla de catálogo, cobertura RB-31 | **ABIERTO** — severidad de origen SUGGESTION (inferential) |
| **PD-21** | Renombrado/alta de catálogo sin endpoint declarado: doc 03 §3.1 (E-08, S-09) materializa el renombre como `PATCH /orientaciones` (y `/cursos`, `/materias`, `/condiciones`), mientras que `analisis.txt` §6 declara sólo `GET\|POST` para esas colecciones. El contrato debe agregar el `PATCH` o declarar el renombre fuera de contrato. Fuente: `analisis.txt` §6; docs 03 y 05. | Contrato (§6), docs 03 y 05 | **ABIERTO** — severidad de origen WARNING (deterministic) |
| **PD-22** | Efecto del `PATCH /preinscripciones` sin definir: `analisis.txt` §6 declara `GET\|PATCH /preinscripciones (sólo consulta)`, pero ninguna regla de §4 o §6 define qué cambia el `PATCH`. El contrato debe definir el efecto o eliminar el `PATCH`. Fuente: `analisis.txt` §6; docs 02, 03 y 11. | Contrato (§6), docs 02, 03 y 11 | **ABIERTO** — severidad de origen WARNING (deterministic) |
| **PD-23** | Alcance de RB-22 sobre `GET /mesas-disponibles`: aplicado literalmente, RB-22 excluiría de la lista una mesa recién creada que todavía no tiene inscripciones (RB-28, RB-31); hay que decidir qué filtra esa consulta. Fuente: `analisis.txt` §7; docs 06 §6.8, 07 EX-16 y 08 RN-021. | RN-021 y CU-35 (doc 06) | **ABIERTO** — severidad de origen WARNING (inferential) |
| **PD-24** | Contrato de cuerpo de las respuestas de error fuera de `/landing/preinscripcion`: los documentos fijan los códigos HTTP de cada estado pero ninguno declaraba el `shape` del body de error (¿único o variable por endpoint?). Fuente: `analisis.txt` §7; doc 07 §7.7.2. | Cuerpo de error de todos los endpoints de §6 (doc 07) | **CERRADO** — 2026-10-05: forma única `{ code, detail, errors[] }` en `application/json`, `errors[]` sólo en 422; §6 |
| **PD-25** | Código HTTP de la respuesta repetida de `DELETE /mis-inscripciones/{id}` cuando la inscripción ya estaba anulada: §6 no la declaraba; el efecto nulo ya lo fija RN-012. Fuente: `analisis.txt` §7; docs 06 §6.8, 07 §7.8 y 08. | EX-10, RN-012, NFR-030 | **CERRADO** — 2026-10-05: `204 No Content` en la primera llamada y también en la repetida (idempotente, sin cuerpo); §6 |
| **PD-26** | Endpoint de alta y baja del token de push (`us_dispositivo`): los documentos modelan el refresco y la purga de caducos. Fuente: `analisis.txt` §7; docs 06 §6.8, 07 EX-22 y 08 RN-052. | RN-052 y CU-42 (doc 06) | **CERRADO** — 2026-10-05: `POST /dispositivos` (alta → `201 { id }`) y `DELETE /dispositivos/{id}` bajo `/api/v1/sigme-mobile`, sólo el dispositivo propio del alumno autenticado (sin permiso nuevo); §6 |
| **PD-27** | Duración exacta del bloqueo de login tras intentos fallidos y el código de respuesta que lo informa: los documentos nombraban el bloqueo sin fijar la ventana ni el estado HTTP. Fuente: `analisis.txt` §7; doc 04 US-03; doc 07 EX-13. | EX-13, RN-044, NFR-010 | **CERRADO** — 2026-10-05: `429` + `Retry-After` y bloqueo de 15 minutos (`bloqueado_hasta = now + 15 min`); `intentos_fallidos` a 0 al levantarse el bloqueo; §6 |
| **PD-28** | Paginación de `GET /mis-inscripciones`: sin un contrato de página, la lectura degradada de SIGME-M depende de cuánto crezca la tabla; definir `offset`/`cursor` y tope de página. Fuente: `analisis.txt` §7; plan §3.06; doc 06 §6.6. | Contrato de lectura de SIGME-M (doc 06 §6.6) | **ABIERTO** — severidad de origen SUGGESTION (inferential) |
| **PD-29** | Alcance de `POST /mesas` fuera de la alta masiva del grupo: §6 declara la ruta pero el doc 04 §4.6.4 modela sólo el alta en bloque, así que la creación de una mesa suelta queda sin reglas de estado; decidir si entra en la primera entrega. Fuente: `analisis.txt` §7; doc 04 §4.6.4. | ME-01 y CU-19 (doc 05) | **ABIERTO** — severidad de origen WARNING (inferential) |

**Nota sobre PD-14:** la fila se conserva en la tabla —pese a estar
resuelta— para no perder el ID ni su trazabilidad hacia `analisis.txt` §7.

**Nota sobre PD-23…PD-29:** los siete IDs nuevos los creó el mantenedor en
`analisis.txt` §7 el 2026-10-05 para dar identidad a los casos que los docs
05–10 dejaban sin identificar en la fuente; PD-24…PD-27 se cerraron el
2026-10-05, el resto sigue **[PENDIENTE]** en §7 y aquí como **ABIERTOS**.

**Notas de estado sobre PD fuera del listado anterior:**

- **PD-04 (reset de contraseña por email)** está **[CERRADO — 2026-10-06]**:
  SÍ desde v1, con la tabla adicional `us_password_reset`; confirma la cola
  de email como obligatoria (RB-25) y sostiene RN-050 y RN-051. El contrato
  de reintento de la cola no queda resuelto en PD-04.
- **PD-01** (payload de `pr_preinscripcion`), **PD-07** (push) y **PD-08**
  (schemas vs prefijos) están **cerrados**: RB-24, RB-13 y la decisión de
  mantener prefijos respectivamente.

### 1.5.2 Derivadas de este documento

Estas preguntas no estaban en la fuente; aparecen al escribir el glosario y la
matriz de permisos. Se marcan PENDIENTE en lugar de resolverlas por supuesto.

| # | Pregunta | Por qué apareció | Dónde queda |
|---|---|---|---|
| G-01 | ¿Qué significa **"matrícula"** para el cliente? La palabra no existe en `analisis.txt`. | El plan la pide en el glosario (plan §3, 01.2) y no hay entidad que la responda. | 1.3, marco PENDIENTE |
| G-02 | ¿Qué rol usa el permiso **`preinscripcion.crear`**? La landing es anónima y no pasa por RBAC, así que ese permiso no puede aplicarse allí. | El catálogo de permisos lo incluye (§2.7) pero ningún endpoint autenticado lo usa. | 2.4 (dueño propuesto + PENDIENTE; PD-03 cerrado 2026-10-06 no lo resuelve) |
| G-03 | ¿Existe el rol **"docente"**? Aparece como comentario de ejemplo en `us_rol` (§3.6), pero la lista cerrada de roles (P-08) no lo incluye. | Discrepancia entre DDL y decisión de rol. | 2.2 y 2.6 (marcado) |
| G-04 | ¿Cómo obtiene SIGME-M las opciones de orientación → curso → materia → condición? El esquema de endpoints sólo las describe como comentario junto a `GET /mesas-disponibles`. | Contrato incompleto en `analisis.txt` §6. | 2.1 y doc 06 (PENDIENTE) |
| G-05 | ¿Quién y cómo cambia el **estado de la convocatoria y de la mesa** (`activa`, `planificada` → `cerrada` → `realizada`)? | RB-16 y el CHECK de `es_mesa_examen` (§3.18) no declaran quién dispara. | **RESUELTA** — 2026-10-06: el disparador es el calendario, no un usuario. Las mesas cuya fecha/hora pasó dejan de listarse; la constatación se calcula **al leer** en `America/Argentina/Buenos_Aires`, no se graba en `estado` y no hay job (coherente con RN-005). Resuelve también EX-05, EX-20 y ME-03…ME-05 (doc 04) |

---

## Checklist de cierre (1 · Glosario y alcance)

- [x] 1.1 declara explícitamente que el producto es **sólo el backend** y que
      las tres interfaces son consumidores.
- [x] 1.1 separa los requisitos de pantalla (WCAG, UX) como **heredados a los
      clientes**, no como obligación de este proyecto.
- [x] 1.2 define todos los términos del plan: mesa, llamado, convocatoria,
      condición, previa, acta volante, permiso de examen, matrícula, taller,
      preinscripción y ventana; añade el **grupo de mesas** (RB-27), que el
      cambio de alcance 2026-10-01 introduce como término del dominio, y la
      **planilla de grupos** (RB-32), **[CONFIRMADO — 2026-10-04]** para la
      primera entrega.
- [x] 1.2 define además cada término técnico que los documentos 02 y 03 usan
      (snapshot, soft delete, módulo, sesión, token, job programado, idempotencia).
- [x] 1.3 lista el vocabulario coloquial prohibido **y el vocabulario retirado**
      por decisiones del análisis (los dos términos que RB-27 y PD-14
      retiraron) con su término correcto.
- [x] 1.4 identifica actantes humanos y sistemas externos con el requisito que
      impone.
- [x] 1.5 lista PD-10, PD-12, PD-15, PD-17, PD-19…PD-23, PD-28 y PD-29
      como abiertos; **PD-02, PD-03, PD-05, PD-06, PD-13, PD-16 y PD-18 como
      CERRADOS el 2026-10-06** (con su decisión redactada), **PD-09 y PD-14
      como RESUELTOS** (catálogo de materias en
      `analisis/orientaciones-cursos-materias.md`; columna de fecha eliminada
      — el grupo define las fechas), **PD-24…PD-27 como CERRADOS el
      2026-10-05** y deja explícito que **PD-11 está deferido a v2**.
- [x] Toda cita RB-xx/PD-xx corresponde a un identificador existente en
      `analisis.txt`.
- [ ] **Criterio del plan:** ninguna palabra del dominio aparece sin definir.
      Autoverificación: cada término de 1.2.1–1.2.4 tiene definición; los
      términos rechazados en 1.3 quedan marcados como vocabulario prohibido.
      **No se cierra:** G-01 sigue abierta — la palabra «matrícula» del
      cliente no tiene definición (1.3, marco PENDIENTE hasta que el cliente
      la confirme).

## Siguiente paso

`02-actores-y-consumidores.md`: quién consume el API, con qué permisos y desde
qué módulo — usando este glosario como referencia única de vocabulario.
