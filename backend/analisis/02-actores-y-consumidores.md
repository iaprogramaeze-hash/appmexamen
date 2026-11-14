# 02 · Actores y consumidores — Backend EPET36

**Respuesta corta:** el backend tiene **tres consumidores** (SIGME web,
SIGME-M móvil, Landing), **seis actores finales** (Alumno, Secretario/a,
Director, Administrador, Superadmin y el anónimo de la landing) y **trece
permisos** con dueño propuesto. Los consumidores sólo interesan aquí como
fuente de tráfico y como imposición de requisitos sobre el API; las interfaces
mismas siguen fuera de alcance (1.1).

Vocabulario: este documento usa los términos definidos en
`01-glosario-y-alcance.md` (secciones 1.2 y 1.3).

## Rápido recorrido

1. **2.1** — qué necesita cada cliente y qué fallas/expiraciones impone.
2. **2.2** — quiénes son los usuarios finales (pregunta P-08, cerrada).
3. **2.3** — el objetivo de cada actor, en un párrafo.
4. **2.4** — la matriz rol × permiso (definitiva: es la fuente de la semilla,
   PD-03 cerrado 2026-10-06).
5. **2.5** y **2.6** — módulos y separación de duties.

---

## 2.1 Consumidores del API

**"Lesión"** designa toda condición de fallo, expiración o restricción de red
que un cliente puede sufrir y que el backend debe tolerar sin corromper datos
ni dejar al usuario sin salida.

### 2.1.1 SIGME web (módulo `sigme_web`)

Aplicación de gestión de escritorio/navegador. Necesita el catálogo completo de
operaciones de `/api/v1/sigme` ( `analisis.txt` §6):

| Dominio | Operaciones que necesita | Fuente |
|---|---|---|
| Auth | `POST /auth/login`, `/refresh`, `/logout`, `/logout-all`, `/cambiar-clave`, `GET /auth/yo` | `analisis.txt` §2.4, §6 |
| Personas y usuarios | `GET\|POST /personas`, `GET\|PATCH /personas/{id}`, `GET\|POST /usuarios` | `analisis.txt` §6 |
| Seguridad | `GET\|POST /roles`, `/permisos`, `/modulos` | `analisis.txt` §6 |
| Catálogo | `GET\|POST /orientaciones`, `/cursos`, `/materias`, `/condiciones` | `analisis.txt` §6 |
| Convocatorias y ventanas | `GET\|POST /convocatorias`, `GET\|POST /ventanas-preinscripcion` | `analisis.txt` §6; RB-14 |
| Preinscripciones | `GET\|PATCH /preinscripciones` (sólo consulta) — **PD-22 abierto**: ninguna regla define el efecto del `PATCH` | `analisis.txt` §6 |
| Mesas, grupos e inscripciones | `GET\|POST /mesas`, `GET\|PATCH /mesas/{id}`, `GET /mesas/por-fecha`, `POST /grupos`, `PATCH /grupos/{id}`, `GET /grupos?convocatoria_id=`, `GET /cobertura-mesas`, `GET /inscripciones` | `analisis.txt` §6; RB-27, RB-28, RB-31 |
| Reportes | `GET /reportes/permiso-examen/{usuario_id}`, `GET /reportes/permisos-examen`, `GET /reportes/acta-volante/{mesa_id}`, `GET /reportes/mesa/{id}`, `GET /reportes/planilla-grupos/{convocatoria_id}` *(RB-32, [CONFIRMADO — 2026-10-04], primera entrega)* | RB-19, RB-22, RB-32 |

| Lesión que impone | Respuesta que el backend debe dar | Fuente |
|---|---|---|
| Sesión que expira: access token de 15 min y refresh de 7 días | Rotación de tokens en `/auth/refresh`; revoke de la sesión en `/logout` | `analisis.txt` §2.1, §2.2 |
| Refresh token reutilizado (reintento con respuesta perdida) | Revoke de **toda la familia** y exigir login nuevo | `analisis.txt` §2.2 |
| Reintento de una escritura tras timeout de red | No duplicar: unicidad por materia × convocatoria responde 409 | RB-08; `analisis.txt` §6 |
| 5 intentos de login fallidos | Bloqueo temporal (`bloqueado_hasta`) | `analisis.txt` §2.4 |
| Usuario sin el permiso del endpoint | Respuesta de prohibición vía dependencia `require_permiso()` | `analisis.txt` §2.7 |
| Impresión masiva de reportes | Todos los listados filtran mesas sin inscriptos activos | RB-22 |
| Edición concurrente de la misma mesa | Recálculo del snapshot en la misma transacción al editar la asignación | RB-11 |

Sin requisitos offline declarados para la web: la fuente no impone modo
degradado a este consumidor — **no determinado por el análisis**.

### 2.1.2 SIGME-M móvil (módulo `sigme_mobile`)

Aplicación del alumno. Operaciones (`analisis.txt` §6):

| Operación | Propósito | Fuente |
|---|---|---|
| `GET /convocatoria-vigente` | Saber si hay ventana abierta | `analisis.txt` §6 |
| `GET /mesas-disponibles` | Alimentar la cascada orientación → curso → materia → condición; devuelve la **fecha y la hora** de cada mesa (el alumno nunca elige grupo) | `analisis.txt` §6; RB-30 |
| `POST /inscripciones` | Anotarse a una mesa **que ya existe** — la crea el secretario en bloque (RB-28), nunca el alumno | RB-28, RB-08 |
| `GET /mis-inscripciones` | Ver inscripciones y fechas | `analisis.txt` §6 |
| `DELETE /mis-inscripciones/{id}` | Anular por error de elección, sólo dentro de la ventana | RB-08b |
| Auth (`/auth/login`, `/refresh`) | Sesión válida para toda acción | RB-26 |

**RB-26 gobierna este consumidor:**

| Modo | Qué exige el cliente | Qué exige al backend | Fuente |
|---|---|---|---|
| **Lectura con caché** | La última respuesta (mesas disponibles, mis inscripciones, convocatoria vigente) se guarda localmente y se muestra con su "última actualización". **No requiere red ni token**: sirve con el teléfono sin datos y con la sesión vencida. | Ninguna llamada de red en este modo; las respuestas deben ser autosuficientes para mostrarse desactualizadas. | RB-26 |
| **Escritura online** | Toda acción (inscribir, anular, refrescar datos) exige conexión y sesión válida. | Exigir autenticación y sesión activa en toda escritura. | RB-26 |
| **Sin cola offline** | No existe ninguna cola de acciones offline. | Si el cliente reintenta por timeout, el backend no debe duplicar (unicidad → 409). | RB-26, RB-08, RB-08c, RB-17, RB-23, RB-22 |
| **Login y refresh** | Siempre necesitan red. | Rate limit y bloqueo temporal aplican igual que en la web. | RB-26; `analisis.txt` §2.4 |

Otras lesiones móviles:

| Lesión | Respuesta del backend | Fuente |
|---|---|---|
| Access token expirado mientras el alumno navega | 401 en la acción; la lectura en caché del cliente sigue funcionando sin llamar al backend | RB-26; `analisis.txt` §2.1 |
| Reloj del dispositivo desfasado (hora incorrecta del celular) | La ventana se evalúa con el reloj del **backend**, por fecha de calendario en `America/Argentina/Buenos_Aires`; nunca con un timestamp del cliente | RB-23 |
| Reintento de `POST /inscripciones` | Respuesta 409 si la materia ya estaba inscripta en la convocatoria; si la combinación no tiene mesa, no se crea nada (no hay mesa que crear: RB-31) | RB-08, RB-31; `analisis.txt` §6 |
| Push con token de dispositivo caducado | Infraestructura de refresco y purga de caducos en `us_dispositivo` | RB-24; `analisis.txt` §4 |

**PENDIENTE (G-04):** la forma en que SIGME-M obtiene las opciones de
orientación, curso, materia y condición no está definida en el esquema de
endpoints: `analisis.txt` §6 la describe sólo como comentario junto a
`GET /mesas-disponibles`. Se resuelve en el doc 06.

### 2.1.3 Landing (módulo `landing`)

Cliente anónimo cuya única operación es `POST /api/v1/landing/preinscripcion`
(`analisis.txt` §6). **Sólo escribe**: no hay endpoint de lectura público
(RB-10).

| Lesión que impone | Respuesta del backend | Fuente |
|---|---|---|
| Visitante sin sesión ni identidad | Endpoint público: **sin JWT, sin roles**; sólo rate limit y CORS restringido al origen de la landing | `analisis.txt` §2.9 |
| Envíos repetidos del mismo formulario | Upsert sobre `(anio_lectivo, documento)`: 201 si se crea, 200 si se actualiza. **Nunca 409 por duplicado** | RB-13, O-4 |
| Envíos fuera de la ventana de preinscripción | 409 `ventana-cerrada` | RB-14; `analisis.txt` §6 |
| Payload incompleto o inválido | 422 con detalle de errores; los 6 campos son obligatorios | O-2; `analisis.txt` §6 |
| Ráfaga de envíos (bots) | Rate limit estricto (429) y límite de tamaño del body | `analisis.txt` §2.9, §6 |
| Origen distinto de la landing | CORS restringido exclusivamente al origen declarado; nunca `*` | `analisis.txt` §2.9 |
| Reloj o zona horaria del visitante | Sin efecto: la ventana se decide con la fecha del backend | RB-23, RB-14 |

### 2.1.4 Resumen de consumidores

| Consumidor | Módulo | Autenticación | Escrituras que realiza | Lesión dominante |
|---|---|---|---|---|
| SIGME web | `sigme_web` | JWT (access + refresh) | Personas, usuarios, catálogo, convocatorias, ventanas, mesas, grupos de mesas, anulaciones, reportes | Sesión que expira y edición concurrente |
| SIGME-M | `sigme_mobile` | JWT (access + refresh) | Inscribir, anular | Red móvil inestable y reloj del dispositivo (RB-26, RB-23) |
| Landing | `landing` | **Ninguna** (pública) | Preinscripción | Ráfagas de envíos y reintentos repetidos |

---

## 2.2 Usuarios finales — RESUELTO (P-08)

La pregunta P-08 (lista definitiva de roles) está **cerrada**: la lista es la
siguiente y no se agregan roles fuera de ella.

| Rol | Cliente | Módulo (`us_modulo`) | Identidad |
|---|---|---|---|
| Alumno | SIGME-M | `sigme_mobile` | Persona con usuario, se autentica con JWT |
| Secretario/a | SIGME | `sigme_web` | Persona con usuario |
| Director | SIGME | `sigme_web` | Persona con usuario |
| Administrador | SIGME | `sigme_web` | Persona con usuario |
| Superadmin | SIGME | `sigme_web` | Persona con usuario |
| *(anónimo)* | Landing | `landing` — sin roles, cualquiera envía | **No tiene usuario ni sesión** (sin JWT, §2.9) |

**Discrepancia detectada (G-03):** el DDL de `us_rol` (§3.6) incluye como
comentario de ejemplo `-- admin, docente, alumno`, pero la lista cerrada de
P-08 **no contiene "docente"**, y el profesor evaluador sólo recibe el acta
volante en papel (RB-19). Hasta que el cliente confirme lo contrario (G-03),
este análisis trata al docente como **fuera del sistema**. — PENDIENTE.

**Módulo `landing`:** el catálogo `us_modulo` contempla el código `landing`
(§2.8), pero el cliente anónimo no tiene `us_usuario` ni `us_sesion`, por lo
que no hay asignación efectiva usuario-módulo para él. La semilla de PD-03
(2026-10-06) fija en la migración inicial los roles y los permisos; si el
catálogo de módulos entra en esa semilla sigue **PENDIENTE**.

---

## 2.3 Objetivo de nivel de cada actor (Cockburn)

Los niveles propuestos a continuación son **análisis de este documento**: las
fuentes (P-08 y `analisis.txt`) no asignan niveles de objetivo. Se escriben en
un párrafo cada uno, con un objetivo principal y sus subobjetivos.

**Alumno — resumen de nivel 2.**
El alumno quiere saber, con el teléfono en la mano y sin importar la calidad de
la señal, qué mesas puede rendir y anotarse correctamente en la que le
corresponde; después quiere confirmar que su inscripción quedó registrada y
consultar las fechas. Sus subobjetivos son: consultar la convocatoria vigente
y las mesas disponibles; inscribirse dentro de la ventana; anular si se equivocó
de materia o condición; y volver a consultar "mis inscripciones". Opera sólo
desde SIGME-M y sólo dentro de la ventana de la convocatoria (RB-07, RB-09),
con una inscripción por materia × convocatoria (RB-08), sin cupo que agotar
(RB-01) y sin etapa de aprobación que esperar (RB-02).

**Secretario/a — resumen de nivel 2.**
El secretario o la secretaria quiere que el proceso de mesas funcione día a
día: localizar personas, planificar la rendición creando los grupos con sus
mesas, ver quién está inscripto en cada mesa, corregir los errores de elección
anulando inscripciones y emitir los reportes de cierre en papel para la
jornada de rendición. Sus subobjetivos son: crear grupos de mesas en bloque —
fecha + hora con materias × condiciones, N mesas de una (RB-28); consultar
personas, mesas e inscripciones; anular inscripciones por error (§3.19); y
exportar el permiso de examen, el acta volante y la planilla de grupos
(RB-19, RB-32 — esta última **[CONFIRMADO — 2026-10-04]** para la primera
entrega), siempre sobre mesas
con al menos un inscripto activo (RB-22). Opera en SIGME con módulo
`sigme_web`.

**Director — resumen de nivel 2.**
El director quiere verificar el estado del proceso de exámenes y contar con
los documentos de cierre para la escuela, sin necesidad de modificar datos. Sus
subobjetivos son: consultar convocatorias, mesas e inscripciones, y obtener los
reportes de cierre (RB-19). El reparto de permisos de este rol sale de la
matriz de 2.4 — adoptada como fuente de la semilla en PD-03 (2026-10-06)—:
permisos de consulta y de reporte, sin escrituras.

**Administrador — resumen de nivel 2.**
El administrador quiere tener el sistema listo antes de cada convocatoria:
catálogo de orientaciones, cursos, materias y condiciones en orden; usuarios
altas y roles asignados; y las ventanas de inscripción y de preinscripción
abiertas en las fechas correctas. Sus subobjetivos son: mantener el catálogo,
gestionar usuarios y módulos, y administrar `pr_ventana` desde SIGME (§3.21).
Las mesas ya **no** las crea el primer alumno en anotarse (RB-20 revocada):
el alta es administrativa y **en bloque**, a cargo del secretario o de un rol
con `mesa.crear` (RB-28).

**Superadmin — resumen de nivel 2.**
El superadmin quiere que la estructura de seguridad del sistema sea correcta y
gobernada: roles, permisos y módulos dados de alta, y su asignación a
usuarios, además de todo lo que hace el administrador. Sus subobjetivos son:
gestionar `/roles`, `/permisos` y `/modulos`, y administrar usuarios y
ventanas. El detalle de qué hace el Superadmin que el Administrador no hace
no está fijado por las fuentes: el reparto sale de la matriz de 2.4 (fuente
de la semilla, PD-03 2026-10-06) y la diferencia efectiva de funciones con
Administrador sigue sin declararse — **PENDIENTE**.

**Persona anónima en la landing — resumen de nivel 2.**
La persona que llega de la página promocional quiere dejar su preinscripción
para el próximo año lectivo y recibir una confirmación inmediata, aunque
reenvíe el formulario varias veces por un error propio. Sus subobjetivos son:
completar los 6 campos obligatorios, enviar dentro de la ventana de
preinscripción y, si se equivoca, corregir reenviando — repetir **no es error**
(RB-13) y fuera de la ventana recibe 409 (RB-14). No inicia sesión: no tiene
identidad en el sistema (RB-10).

---

## 2.4 Matriz rol × permiso

**Estado: DEFINITIVA — fuente de la semilla (PD-03, [CERRADO — 2026-10-06]).**
PD-03 decidió el mecanismo de la semilla: los roles y los permisos viajan en
la migración inicial de Alembic (datos estáticos, reproducibles en dev,
staging y prod), el primer superadmin entra por variable de entorno (la
credencial nunca toca el repo) y el reparto rol × permiso y el mapeo
endpoint → permiso salen de esta matriz junto con el catálogo de §2.7.
La matriz garantiza que **cada permiso del catálogo tenga dueño** y que
**cada actor tenga al menos un permiso**; las celdas marcadas `PENDIENTE`
son huecos de esta matriz que el cierre de PD-03 no cubrió — quedan visibles
para el cliente, no se resuelven por silencio ni por suposición.

Leyenda: `S` = sí · `—` = no · `PENDIENTE` = decisión no tomada.

| Permiso (§2.7) | Alumno | Secretario/a | Director | Administrador | Superadmin | Anónimo (landing) | Justificación |
|---|---|---|---|---|---|---|---|
| `mesa.listar` | S | S | S | S | S | — | Consulta de mesas disponibles (§6) y listados de gestión; filtra RB-22 |
| `mesa.crear` | — | S | — | S | S | — | **RB-28: el secretario crea grupos y sus mesas en bloque** (materias[] × condiciones[] × fecha × hora); el alumno ya NO crea mesas (RB-20 revocada). **No hace falta ningún permiso nuevo** (§2.7): crear un grupo es `mesa.crear`; mover la fecha/hora de un grupo es `mesa.modificar`. Director queda en — porque su objetivo es consultar sin modificar datos (2.3). Reparto según la matriz, definitiva desde PD-03 (2026-10-06) |
| `mesa.modificar` | — | S | — | S | S | — | Corrección de asignación, que dispara el recálculo del snapshot (RB-11); **mover la fecha/hora de un grupo** arrastra todas sus mesas en la misma transacción (RB-29) — crear grupo es `mesa.crear`, mover grupo es `mesa.modificar` (§2.7), sin códigos nuevos |
| `mesa.eliminar` | — | PENDIENTE | — | S | S | — | La fuente no indica quién elimina mesas ni grupos completos; el soft delete existe (§1.7) — **PENDIENTE** (hueco de la matriz) |
| `inscripcion.listar` | S | S | S | S | S | — | `GET /mis-inscripciones` (§6) para el alumno; `GET /inscripciones` para gestión |
| `inscripcion.crear` | S | PENDIENTE | — | PENDIENTE | PENDIENTE | — | El alumno se inscribe a mesas que **ya existen** (§6, RB-28). Si el secretario puede anotar en nombre de un alumno, **no está determinado por el análisis** — PENDIENTE (hueco de la matriz; ver CU-25 del doc 05) |
| `inscripcion.anular` | S | S | — | S | S | — | RB-08b (propia) y §3.19 ("el propio alumno o el secretario revoca") |
| `persona.listar` | — | S | S | S | S | — | Búsqueda de personas para inscripciones y reportes |
| `persona.modificar` | — | S | — | S | S | — | Corrección de datos de contacto; detalle de autor-edición **PENDIENTE** (hueco de la matriz) |
| `usuario.gestionar` | — | — | — | S | S | — | Altas, roles y módulos (§2.7, §2.8); semilla inicial decidida en PD-03 (migración de Alembic + superadmin por variable de entorno) |
| `reporte.exportar` | — | S | S | S | S | — | RB-19: los **tres** reportes salen de SIGME (permiso de examen, acta volante y planilla de grupos RB-32); reparto entre rol exacto **PENDIENTE** (hueco de la matriz) |
| `preinscripcion.crear` | — | — | — | — | — | **S (sin RBAC)** | La landing escribe sin JWT (§2.9): el permiso **no puede aplicarse allí**. Dueño dentro de SIGME **no determinado** — PENDIENTE (G-02) |
| `preinscripcion.listar` | — | S | S | S | S | — | `GET\|PATCH /preinscripciones` es sólo consulta (§6) — **PD-22 abierto**: ninguna regla declara qué cambia el `PATCH` |

Gestión de la ventana de preinscripción (`POST /ventanas-preinscripcion`):

| Acción | Dueño | Fuente |
|---|---|---|
| Abrir/cerrar `pr_ventana` | Administrador o Superadmin, **desde SIGME** — nunca desde la landing | §3.21 |
| Código de permiso para esa acción | No existe en el catálogo de §2.7 — **PENDIENTE** si se agrega uno nuevo (hueco de la matriz) | §2.7, §3.21 |

---

## 2.5 Alcance por módulo (`us_modulo`)

`us_modulo` contiene tres códigos (§2.8). Regla: **el módulo dice a qué app
puede entrar; el permiso dice qué puede hacer adentro** — uno no reemplaza al
otro (§2.8).

| Módulo | Aplicación | Quién opera | Autenticación | Alcance efectivo |
|---|---|---|---|---|
| `sigme_web` | SIGME web | Secretario/a, Director, Administrador, Superadmin | JWT con sesión | Catálogo, convocatorias, ventanas, personas, usuarios, mesas, inscripciones, reportes, preinscripciones (§6) |
| `sigme_mobile` | SIGME-M | Alumno | JWT con sesión | Consulta de convocatoria y mesas, inscripción y anulación (§6, RB-26) |
| `landing` | Landing promocional | Persona anónima | **Sin autenticación** | Sólo `POST /landing/preinscripcion` (RB-10, §2.9) |

Restricciones transversales de módulo:

- Un usuario **sólo puede operar en los módulos que tiene asignados**
  (`us_usuario_modulo`, §2.8).
- `us_sesion.modulo_id` es `NOT NULL` (§3.12): toda sesión pertenece a un
  módulo autenticado. Consistente con que la landing no tenga sesión.
- Asignación efectiva de módulos por rol: **PENDIENTE** — la semilla de
  PD-03 (2026-10-06) fija roles y permisos en la migración inicial, pero no
  declara la asignación de módulos por rol.

---

## 2.6 Separación de duties

**Pregunta del plan: ¿un docente edita su propio acta?**

**Respuesta: no aplica, y la razón es estructural.**

1. **No existe acta digital.** El sistema **no guarda notas** (RB-21): no hay
   `nota`, ni aprobado/desaprobado, ni rectificación. El resultado de la mesa
   vive en el acta en papel.
2. Los tres documentos de cierre —permiso de examen, acta volante y planilla
   de grupos (esta última **[CONFIRMADO — 2026-10-04]** en la primera
   entrega)— son **impresiones** que salen de SIGME (RB-19, RB-32); no son
   registros editables.
3. El rol "docente" **no existe** en la lista cerrada de roles (P-08); el
   profesor evaluador sólo es destinatario del acta volante en papel (RB-19).
   Su ausencia como actor del sistema queda marcada como G-03 / PD-03.

En consecuencia, la separación de duties clásica (quién firma vs. quién
modifica) se traslada a las operaciones que **sí** existen:

| Decisión de diseño | Respuesta | Fuente |
|---|---|---|
| ¿Quién **crea** una mesa? | El secretario (o un rol con `mesa.crear`), **en bloque y dentro de un grupo**: N mesas de una, con la fecha y la hora del grupo (RB-28). El alumno nunca crea mesas — RB-20 revocada. | RB-28, RB-27 |
| ¿Quién **mueve** la fecha u hora de un grupo? | Un rol con `mesa.modificar`; el cambio arrastra todas las mesas del grupo en la misma transacción (RB-29). Si se permite con la ventana de inscripción **abierta**: **PENDIENTE** (PD-12). | RB-29, PD-12 |
| ¿Quién **edita** la asignación de una mesa (materia/condición)? | Un rol con `mesa.modificar` desde SIGME; el backend recalcula el snapshot en la misma transacción. | RB-11; 2.4 |
| ¿Quién **anula** una inscripción? | El propio alumno, dentro de la ventana (RB-08b); o el secretario, según el comentario del modelo (§3.19). | RB-08b, §3.19 |
| ¿Quién **gestiona** las ventanas? | Administrador o Superadmin, sólo desde SIGME. La landing no toca `pr_ventana`. | §3.21 |
| ¿Quién **gestiona** usuarios, roles y permisos? | Roles con `usuario.gestionar` (Administrador/Superadmin, según la matriz de 2.4 — fuente de la semilla desde PD-03, 2026-10-06). | §2.7, 2.4, PD-03 |
| ¿Puede alguien aprobar su propia inscripción? | **No hay aprobación**: anotarse es directo. | RB-02 |
| ¿Puede alguien alterar el resultado de una mesa? | **No**: no hay resultados almacenados que alterar. | RB-21 |
| ¿Quién modifica la bitácora de auditoría? | **Nadie**: `aud_evento` es append-only desde v1 (PD-05, cerrado 2026-10-06) — escrituras exitosas, intentos denegados (401/403) y descargas/impresiones de reportes, con snapshot JSONB que excluye `password_hash`, refresh tokens y hashes de sesión. | PD-05 |

**Límites de esta sección:** el análisis **no determina** si un usuario puede
modificarse a sí mismo (persona propia, contraseña, módulos), ni si hay
cuarentena entre quien carga el catálogo y quien lo aprueba. Quedan como
huecos abiertos de la matriz 2.4; no se rellenan con supuestos.

---

## Checklist de cierre (2 · Actores y consumidores)

- [x] **Cada permiso de `analisis.txt` (§2.7) tiene dueño:** los 13 códigos
      (`mesa.listar`, `mesa.crear`, `mesa.modificar`, `mesa.eliminar`,
      `inscripcion.listar`, `inscripcion.crear`, `inscripcion.anular`,
      `persona.listar`, `persona.modificar`, `usuario.gestionar`,
      `reporte.exportar`, `preinscripcion.crear`, `preinscripcion.listar`)
      aparecen en 2.4 con dueño; los no resueltos están marcados PENDIENTE.
- [x] **Cada actor tiene al menos un permiso:** Alumno (4), Secretario/a (9),
      Director (5), Administrador (11 + 1 pendiente), Superadmin (11 + 1
      pendiente), Anónimo (`preinscripcion.crear`, fuera de RBAC).
- [x] **2.4 refleja el cambio de alcance 2026-10-01:** `mesa.crear` está en
      Secretario/a, Administrador y Superadmin, y **fuera** del Alumno, con
      justificación RB-28 (RB-20 revocada); crear un grupo es `mesa.crear` y
      mover un grupo es `mesa.modificar` — sin códigos de permiso nuevos
      (§2.7).
- [x] **Cada consumidor está asociado a operaciones concretas:** 2.1.1 (SIGME
      web), 2.1.2 (SIGME-M con RB-26), 2.1.3 (Landing con RB-10/RB-13/RB-14).
- [x] P-08 está presentado como resuelta en 2.2.
- [x] 2.6 responde "¿un docente edita su propio acta?" con base en RB-21 y
      RB-19, no con una suposición.
- [x] Toda cita RB-xx/PD-xx corresponde a un identificador existente en
      `analisis.txt`; las decisiones sin fuente están marcadas PENDIENTE.

## Siguiente paso

`03-eventos-y-gatillos.md`: qué sucesos obligan al backend a responder, con la
tabla evento → respuesta → caso de uso → regla que servirá de semilla para los
docs 05 y 06.
