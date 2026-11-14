# 03 · Eventos y gatillos — Backend EPET36

**Respuesta corta:** este documento cataloga **todo lo que obliga al backend a
responder**: acciones de un usuario, cambios de fecha, y transiciones de estado
de los propios datos. La tabla de la sección 3.4 es el contrato de salida: de
sus filas nacen los casos de uso de los documentos 05 y 06, y ningún evento se
queda sin respuesta.

Vocabulario: se usan los términos definidos en
`01-glosario-y-alcance.md` (1.2, 1.3) y los actores de
`02-actores-y-consumidores.md` (2.2).

## Rápido recorrido

1. **3.1** — eventos externos: alguien del mundo real hace algo.
2. **3.2** — eventos temporales: el calendario hace algo (RB-23).
3. **3.3** — eventos de estado: los datos hacen algo entre sí.
4. **3.4** — la tabla maestra evento → respuesta → caso de uso → RB.

---

## 3.1 Eventos externos

Suceden fuera del sistema y llegan al backend como una operación HTTP.

| # | Evento | Actante | Operación que lo materializa | Fuente |
|---|---|---|---|---|
| E-01 | El alumno toca "inscribirse" con la cascada completa elegida, sobre una mesa que **ya existe** | Alumno (SIGME-M) | `POST /inscripciones` | RB-28, RB-08; §6 |
| E-02 | El alumno toca "anular" su propia inscripción | Alumno (SIGME-M) | `DELETE /mis-inscripciones/{id}` | RB-08b; §6 |
| E-03 | El alumno consulta sus inscripciones, las mesas disponibles o la convocatoria vigente | Alumno (SIGME-M) | `GET /mis-inscripciones`, `GET /mesas-disponibles`, `GET /convocatoria-vigente` | §6; RB-26 |
| E-04 | Una persona envía el formulario de preinscripción de la landing | Anónimo (Landing) | `POST /landing/preinscripcion` | RB-13; §6 |
| E-05 | El secretario o administrador abre o cierra una ventana de preinscripción | Administrador/Superadmin (SIGME) | `POST /ventanas-preinscripcion` | §3.21; RB-14 |
| E-06 | Se crea o edita una convocatoria (o su `activa`) | Secretario/a o administración (SIGME) | `POST /convocatorias` | §6; RB-09 |
| E-07 | Se edita la **asignación** de una mesa (materia o condición) | Rol con `mesa.modificar` (SIGME) | `PATCH /mesas/{id}` | RB-11 |
| E-08 | Se renombra una fila de catálogo (orientación, curso, materia, condición) | Rol de catálogo (SIGME) | §6 declara sólo `GET\|POST` en `/orientaciones`, `/cursos`, `/materias` y `/condiciones`: no hay `PATCH` de renombre en el contrato — cuestión abierta **PD-21** | RB-11; §6; PD-21 |
| E-09 | Se solicita un reporte impreso de cierre (permiso de examen, acta volante o planilla de grupos) | Rol con `reporte.exportar` (SIGME) | `GET /reportes/*` | RB-19, RB-22, RB-32 |
| E-10 | Login, refresh, logout, logout-all o cambio de clave | Cualquier usuario autenticado | `POST /auth/*` | §2.4 |
| E-11 | Se gestiona usuarios, roles, permisos o módulos | Rol con `usuario.gestionar` (SIGME) | `GET\|POST /usuarios`, `/roles`, `/permisos`, `/modulos` | §2.7 |
| E-12 | Se consulta una preinscripción desde SIGME | Rol con `preinscripcion.listar` (SIGME) | `GET\|PATCH /preinscripciones` — ninguna regla define qué cambia el `PATCH`, cuestión abierta **PD-22** | §6; PD-22 |
| E-13 | Un cliente reintenta una escritura tras un timeout de red | SIGME / SIGME-M / Landing | Misma operación de nuevo | RB-08, RB-13, RB-26 |
| E-14 | Se supera el límite de intentos de login o de envíos | Cualquier cliente | — (respuesta 429 o bloqueo) | §2.4, §2.9 |
| E-15 | El secretario crea un grupo con sus mesas **en bloque** (materias[] × condiciones[] × fecha × hora) | Secretario/a (SIGME) | `POST /grupos` | RB-27, RB-28; §6 |
| E-16 | El secretario cambia la fecha u hora de un grupo: se mueven todas sus mesas | Rol con `mesa.modificar` (SIGME) | `PATCH /grupos/{id}` | RB-29; PD-12 (PENDIENTE) |
| E-17 | Se pide la **cobertura de mesas** de una convocatoria (materias × condiciones sin mesa) | Rol con `mesa.listar` (SIGME) | `GET /cobertura-mesas` | RB-31; §6 |

---

## 3.2 Eventos temporales

**Regla rectora (RB-23):** toda ventana se evalúa **por fecha de calendario**
en la zona horaria del backend, `America/Argentina/Buenos_Aires`, con límite
**inclusivo hasta las 23:59:59** de la fecha declarada. A las 00:00:00 del día
siguiente la fecha ya cambió y la operación está cerrada. Implementación
mandatoria: comparar `current_date` contra la columna `date`; **no** usar un
timestamp crudo de UTC ni sumar horas. Vale igual para
`fecha_inicio_inscripcion`, `fecha_fin_inscripcion` y para `pr_ventana`.

**No hay job programado en v1.** RB-24 declara que todos los envíos de
notificación nacen de una acción de usuario, y PD-11 deja el recordatorio de
48 h **deferido a v2**. En consecuencia, en v1 **no existe ningún scheduler**:
los cierres de ventana no se "disparan" a una hora fija, se **constatan** en
cada request comparando la fecha (RB-23).

| # | Evento temporal | Cuándo ocurre | Respuesta del backend | Fuente |
|---|---|---|---|---|
| T-01 | Se cumple `fecha_inicio_inscripcion` | Al pasar a esa fecha (00:00:00, ya incluyendo el día completo hasta 23:59:59) | Queda habilitada la inscripción y la anulación mientras la convocatoria siga `activa` | RB-23, RB-09, RB-06 |
| T-02 | Se cumple `fecha_fin_inscripcion` (23:59:59 inclusive) | Último minuto del día declarado | La inscripción y la anulación siguen permitidas hasta ese instante | RB-23, RB-07, RB-08b |
| T-03 | Cambia la fecha de calendario a 00:00:00 del día siguiente | Medianoche del backend | La ventana está cerrada: no se inscribe ni se anula; SIGME-M sólo permite **consultar** la fecha de rendir | RB-23, RB-07, RB-17 |
| T-04 | Se cumple `fecha_hasta` de `pr_ventana` | Fin de la ventana de preinscripción | `POST /landing/preinscripcion` responde 409 `ventana-cerrada` | RB-14, RB-23 |
| T-05 | Se cumple `fecha_desde` de `pr_ventana` | Inicio de la ventana de preinscripción | `vw_ventana_vigente` devuelve la ventana y el POST se vuelve válido | RB-14; §3.21 |
| T-06 | Pasa el último día de rendir de la convocatoria | Día siguiente a la **última fecha de sus grupos** (RB-27) | La convocatoria se cierra; en la fecha que corresponda se abre **otra** convocatoria y todo arranca de nuevo | RB-16, RB-27 |
| T-07 | Expira el access token | 15 minutos (máx. 30) después de emitido | 401 en la acción protegida; el cliente rota con `/auth/refresh` | §2.1 |
| T-08 | Expira el refresh token / la sesión | 7 días (`us_sesion.expires_at`) | La sesión ya no rota: se exige un login nuevo | §2.2, §3.12 |
| T-09 | Vence `bloqueado_hasta` | Tras los 5 intentos fallidos de login en 15 minutos | El bloqueo temporal se levanta y vuelve a aceptar intentos | §2.4 |
| T-10 | Recordatorio de 48 h antes de la mesa | — | **Sin respuesta en v1: DEFERIDO A V2 (PD-11).** Requeriría un job programado, seguimiento de entrega y reintentos; RB-24 confirma que en v1 no hay ningún job programado | PD-11, RB-24 |

**Pendiente relacionado (G-05) — [RESUELTA — 2026-10-06]:** RB-16 dice
"cerrado el día de rendir, la convocatoria se cierra", y **nadie dispara ese
cierre**: es una constatación del calendario, igual que la ventana (T-03).
Mismo criterio para los estados `planificada → cerrada → realizada` de
`es_mesa_examen` (§3.18): se derivan **al leer** en
`America/Argentina/Buenos_Aires`, sin escritura y sin job. Detalle en el doc
04 §4.6.2 y en el doc 01 §1.5.2. Queda sin declarar, por falta de fuente, la
frontera entre `cerrada` y `realizada`.

---

## 3.3 Eventos de estado

Suceden cuando los propios datos cambian y arrastran consecuencias.

| # | Evento de estado | Condición que lo dispara | Respuesta del sistema | Fuente |
|---|---|---|---|---|
| S-01 | **Se crea un grupo y el backend crea N mesas de una** (alta masiva) | `POST /grupos` con materias[] × condiciones[] × fecha × hora dentro de una convocatoria | Se crea el grupo y sus N mesas en `planificada`, todas con `grupo_id` NOT NULL; los 4 snapshot se rellenan de cada materia y condición | RB-27, RB-28, RB-29 |
| S-02 | Ya existe la mesa para esa combinación | `POST /inscripciones` con la combinación ya creada | Sólo se agrega la inscripción; no se duplica la mesa (las mesas ya vienen creadas del grupo, RB-28) | RB-08, RB-28 |
| S-03 | **La mesa queda con 0 alumnos** (todos anularon) | Última inscripción activa pasa a `anulado` | La mesa **no se borra**: desaparece de todo listado e impresión vía `vw_mesa_con_alumnos` | RB-22; §3.18 |
| S-04 | **Anulación de una inscripción** | Alumno o secretario anulan dentro de la ventana | La fila pasa a `anulado`, se conserva para auditoría y queda **fuera del índice único**: no ocupa y libera la materia para reinscribirse | RB-08b; §3.19 |
| S-05 | Tras anular, se inscribe a la mesa correcta | `POST /inscripciones` nuevo después de un `anulado` | Se permite **sólo si no se viola** el límite de materias de la condición | RB-08c, RB-03 |
| S-06 | Segundo intento de inscripción a la misma materia en la misma convocatoria | Choque contra `uq_inscripcion_unica` | Respuesta **409**; no se crea fila | RB-08; §6 |
| S-07 | La convocatoria está inactiva o fuera de su ventana | `POST /inscripciones` con convocatoria `activa = false` o fecha fuera de rango | Rechazo: no se inscribe | RB-09 |
| S-08 | Cambia la **asignación** de la mesa (materia/condición) | `PATCH /mesas/{id}` con otra materia u otra condición | El servicio **recalcula los 4 snapshot** en la misma transacción | RB-11 |
| S-09 | Se renombra una fila de catálogo | §6 sólo declara `GET\|POST` en `/materias` (u `/orientaciones`, `/cursos`, `/condiciones`) y no fija el endpoint del renombre — cuestión abierta **PD-21** | Los snapshot de las mesas existentes **no cambian**: las mesas históricas conservan su nombre | RB-11, RB-12; §6; PD-21 |
| S-10 | Se rinde la mesa / se cierra el acta | Paso de la jornada de rendición | La mesa avanza `planificada → cerrada → realizada`; **quién dispara** la transición: nadie — es constatación de calendario al leer (G-05 **[RESUELTA — 2026-10-06]**, doc 04 §4.6.2) | §3.18 |
| S-11 | La última inscripción activa de una mesa desaparece | Ver S-03 | La mesa sale de la impresión masiva de permisos de examen ("a toda ley") | RB-22, RB-19 |
| S-12 | Llega una preinscripción con identidad nueva | `POST` con `(anio_lectivo, documento)` inexistente | INSERT con estado `pendiente`, responde **201** | RB-13; §3.20 |
| S-13 | Llega una preinscripción con identidad existente | `POST` repetido dentro de la ventana | UPDATE de los campos mutables, responde **200**; `created_at` se conserva | RB-13 |
| S-14 | Se reutiliza un refresh token ya usado | Reintento o robo con respuesta perdida | Se revoca **toda la familia** de la sesión y se exige login nuevo | §2.2 |
| S-15 | Cambio de clave, cambio de rol o bloqueo de cuenta | Acción de gestión o del propio usuario | `token_version` sube: los access tokens ya emitidos dejan de servir | §2.6 |
| S-16 | Login fallido consecutivo (5 en 15 minutos) | Intentos de autenticación | `intentos_fallidos` + bloqueo temporal (`bloqueado_hasta`) | §2.4 |
| S-17 | Soft delete de una persona o materia referenciada | `DELETE` sobre fila con FK `RESTRICT` | La base lo impide (error 23503 evitado por diseño): no se pierden referencias | §1.8 |
| S-18 | Cambio de estado de la sesión | `POST /auth/logout` o `/logout-all` | `estado = 'revocado'`; la sesión deja de rotar | §2.3, §3.12 |
| S-19 | Se cierra o abre una ventana de preinscripción | E-05 | Cambia quién recibe 409 en el POST de la landing (ver T-04/T-05) | RB-14 |
| S-20 | Se produce un evento de usuario (apertura/cierre de ventana, confirmación de inscripción, acuse de preinscripción, password reset) | Acción de usuario, nunca un cron | Se **encola** la notificación por el canal que corresponda: push (SIGME-M), campanita in-app (SIGME) o email — la cola de email es obligatoria desde v1 | RB-24, RB-25 |
| S-21 | **Se edita la fecha u hora de un grupo** (E-16) | `PATCH /grupos/{id}` con otra fecha u hora | Todas las mesas del grupo actualizan `fecha`/`hora` en la **misma transacción** (RB-29). El efecto sobre alumnos ya inscriptos queda **PENDIENTE** — lo decide PD-12, no se resuelve acá | RB-29; PD-12 |

---

## 3.4 Tabla maestra: evento → respuesta → caso de uso → regla

**Uso de esta tabla.** Es la semilla de los casos de uso: toda fila declara un
evento, la respuesta del backend, el caso de uso (con su documento de destino)
y la regla que la gobierna. Los identificadores `CU-nnn` se asignan **en los
docs 05 y 06**; aquí se usan nombres descriptivos para no anticipar
numeración.

**Cómo verificar el criterio de cierre:** todo caso de uso de `05` y `06` debe
rastrearse a al menos una fila de abajo, y ninguna fila de abajo puede quedar
sin respuesta.

### Inscripciones (destino: doc 06)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-01 · alumno envía `POST /inscripciones` con combinación sin mesa | Rechazo: no hay mesa que crear — la creación es del secretario y en bloque (RB-28); la cobertura se revisa con E-17 **antes** de abrir | Inscribirse — excepción | RB-28, RB-31 |
| E-01 · combinación ya existente | Sólo anexa la inscripción | Inscribirse a una mesa | RB-08, RB-28 |
| S-06 · materia ya inscripta en la convocatoria | 409, sin fila nueva | Inscribirse — flujo alternativo | RB-08 |
| S-07 · convocatoria inactiva o fuera de ventana | Rechazo de la inscripción | Inscribirse — excepción | RB-09, RB-07 |
| S-05 · límite de la condición alcanzado | Rechazo de la inscripción (o de la reinscripción tras anular) | Inscribirse — excepción | RB-03, RB-08c |
| E-01 · alumno se anota a varias materias en la ventana | Se aceptan todas las que cumplan las reglas | Inscribirse a varias mesas | RB-06 |
| E-02 · alumno toca "anular" dentro de la ventana | Fila → `anulado`, conservada, sin ocupar en el índice único | Anular inscripción | RB-08b |
| E-02 · alumno toca "anular" fuera de la ventana | Rechazo; sólo consulta | Anular inscripción — excepción | RB-07, RB-08b |
| E-02 → S-05 · anular y anotarse a la correcta | Permitido si respeta el límite de la condición | Anular y reinscribir | RB-08c, RB-03 |
| E-13 · reintento de escritura tras timeout | Misma respuesta aplicable, sin duplicar | Inscribirse (reintento) | RB-08, RB-26 |
| E-13 · reintento del formulario de la landing | Upsert: 201 primera vez, 200 en reenvíos | Preinscribirse (reintento) | RB-13 |

### Consultas en SIGME-M (destino: doc 06)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-03 · consulta de convocatoria, mesas o inscripciones **con red** | Devuelve los datos vigentes, con la **fecha y la hora** de cada mesa (RB-30); sólo mesas con inscriptos activos cuando aplica | Consultar convocatoria y mesas | RB-26, RB-30, RB-22 |
| E-03 · consulta **sin red o con sesión vencida** | El cliente sirve su caché con "última actualización"; el backend no es llamado | Consultar sin conexión (caché) | RB-26 |
| T-03 · ventana cerrada | Sólo lectura: se consulta la fecha de rendir, no se inscribe ni se anula | Consultar después del cierre | RB-07, RB-17 |
| S-03 · mesa quedó con 0 alumnos | No aparece en las consultas ni en la impresión | Consultar mesas disponibles | RB-22 |

### Ventanas y convocatorias (destino: doc 05)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| T-01 · llega `fecha_inicio_inscripcion` | Habilita inscripción y anulación | Gestionar convocatoria | RB-23, RB-09 |
| T-02/T-03 · se cumple `fecha_fin_inscripcion` hasta 23:59:59 y luego cambia la fecha | La ventana queda cerrada por fecha de calendario en `America/Argentina/Buenos_Aires` | Gestionar convocatoria | RB-23, RB-17 |
| T-06 · pasó el día de rendir | La convocatoria se cierra; se abre otra después (disparador: el calendario — G-05 **[RESUELTA — 2026-10-06]**) | Cerrar convocatoria | RB-16 |
| E-06 · convocatoria inactiva | Cualquier inscripción es rechazada | Gestionar convocatoria | RB-09 |
| E-05 · se abre o cierra `pr_ventana` | Cambia la vigencia del formulario de la landing | Gestionar ventana de preinscripción | RB-14 |
| T-04 · fuera de `pr_ventana` | 409 `ventana-cerrada` | Preinscribirse — excepción | RB-14, RB-23 |

### Grupos de mesas (destino: doc 05)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-15 · secretario crea un grupo con materias[] × condiciones[] × fecha × hora | Se crea el grupo y N mesas `planificada`, todas con `grupo_id` NOT NULL | Crear grupo de mesas | RB-27, RB-28, RB-29 |
| E-16 · secretario cambia la fecha/hora de un grupo | Todas sus mesas cambian en la misma transacción; el efecto sobre alumnos **ya inscriptos** queda **PENDIENTE (PD-12)** — aquí no se decide | Editar grupo — decisión abierta | RB-29, PD-12 |
| E-17 · se pide la cobertura de la convocatoria | Devuelve las materias × condiciones **sin mesa**, utilizable antes de abrir la ventana de inscripción | Revisar cobertura de mesas | RB-31 |
| S-03 · mesas de un grupo que quedaron con 0 alumnos | Siguen invisibles para listados e impresión: crear ~180 mesas de una **no ensucia nada** gracias a RB-22 | Gestionar grupo | RB-22 |

### Preinscripción de la landing (destino: doc 11)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-04 · identidad nueva, dentro de la ventana | INSERT `pendiente`, 201 `creada` | Preinscribirse | RB-13 |
| E-04 · identidad repetida, dentro de la ventana | UPDATE de campos mutables, 200 `actualizada` | Preinscribirse (reenvío) | RB-13 |
| E-04 · payload inválido | 422 con detalle de errores | Preinscribirse — excepción | §6 (contrato), O-2 |
| E-14 · ráfaga de envíos | 429 rate limit | Preinscribirse — excepción | §2.9, §6 |
| E-04 · origen no permitido | CORS rechaza la petición | Preinscribirse — excepción | §2.9 |

### Reportes de cierre (destino: doc 05)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-09 · permiso de examen individual o masivo | Se emiten sólo con mesas que tienen al menos una inscripción activa | Emitir permiso de examen | RB-19, RB-22 |
| E-09 · acta volante por mesa | Se emite con los inscriptos activos de esa mesa | Emitir acta volante | RB-19, RB-22 |
| E-09 · planilla de grupos por convocatoria | Lista cada grupo (fecha, hora) con sus mesas (materia, condición), sólo mesas con inscripción activa. **[CONFIRMADO — 2026-10-04] (RB-32): la planilla de grupos entra en la primera entrega** | Emitir planilla de grupos | RB-32, RB-22 |
| S-03 · mesa sin alumnos | No se imprime, no se borra | Emitir reportes | RB-22 |
| S-08/S-09 · mesa con asignación editada o catálogo renombrado | El reporte lee el snapshot vigente de la mesa, no el nombre actual de la tabla origen | Emitir reportes | RB-11, RB-12 |

### Seguridad y sesión (destino: doc 05)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| E-10 · login correcto | Emite access + refresh y crea `us_sesion` | Autenticarse | §2.1, §2.3 |
| E-14 · 5 logins fallidos en 15 min | Bloqueo temporal (`bloqueado_hasta`) | Autenticarse — excepción | §2.4 |
| T-07/T-08 · expira access o refresh token | 401 y rotación, o login nuevo si venció la sesión | Renovar sesión | §2.1, §2.2 |
| S-14 · refresh reutilizado | Se revoca la familia entera | Renovar sesión — excepción | §2.2 |
| E-10 · logout / logout-all | Sesión `revocado`; en `/logout-all`, todas | Cerrar sesión | §2.3, §2.4 |
| S-15 · cambio de clave, rol o bloqueo | `token_version` sube y los tokens viejos mueren | Cambiar clave / gestionar usuario | §2.6 |
| E-11 · gestión de usuarios, roles y módulos | Se aplican los permisos correspondientes a la operación | Gestionar seguridad | §2.7, §2.8 |

### Notificaciones (destino: docs 06 y 09)

| Evento | Respuesta del sistema | Caso de uso | RB |
|---|---|---|---|
| S-20 · evento de usuario (apertura/cierre de ventana, confirmación de inscripción, acuse de preinscripción, password reset) | Se encola por push, campanita in-app o email; sin ningún job programado | Notificar por evento | RB-24, RB-25 |
| T-10 · recordatorio 48 h antes de la mesa | **Sin respuesta en v1 — deferido a v2 (PD-11)** | — (fuera de alcance de v1) | PD-11, RB-24 |

**Nota sobre respuestas sin regla RB propia:** las filas que citan sólo
secciones de `analisis.txt` (§2.x, §6) corresponden a requisitos de seguridad
o al contrato de endpoints, que no son RB-xx en la fuente; se citan tal como
aparecen para no inventar identificadores.

---

## Checklist de cierre (3 · Eventos y gatillos)

- [x] **3.1** cubre los eventos externos: acciones del alumno, del personal de
      SIGME, de la landing anónima, de sesión y de reintento.
- [x] **3.2** aplica RB-23: apertura y cierre **inclusive hasta las 23:59:59**,
      comparado por fecha de calendario en `America/Argentina/Buenos_Aires`.
- [x] **3.2** deja explícito que el recordatorio de 48 h está **deferido a v2
      (PD-11)** y que, en consecuencia, **no hay job programado en v1**.
- [x] **3.3** cubre los tres eventos de estado pedidos: creación de un grupo
      con sus N mesas en bloque (RB-27, RB-28, S-01), mesa con 0 alumnos
      (RB-22) y anulación (RB-08b); S-21 deja la edición de grupo marcada
      con **PD-12 PENDIENTE** en lugar de resolverla.
- [x] **3.4** es una tabla evento → respuesta → caso de uso → regla RB, y cada
      fila tiene respuesta.
- [x] **3.4 · reportes** cubre los tres reportes impresos: permiso de examen y
      acta volante (RB-19) más la **planilla de grupos** (RB-32), fila nueva
      bajo E-09 (sin ID nuevo), **[CONFIRMADO — 2026-10-04]** para la primera
      entrega.
- [x] **Ningún evento sin respuesta:** los casos sin respuesta operativa en v1
      están declarados como tales (T-10 / PD-11 y
      el efecto de editar un grupo con la ventana abierta — PD-12), no
      omitidos; el endpoint del renombre de catálogo (E-08 / S-09 — **PD-21**)
      y el efecto del `PATCH /preinscripciones` (E-12 — **PD-22**) quedan como
      preguntas abiertas en lugar de afirmarse como contrato. El caso G-05 ya
      **[RESUELTA — 2026-10-06]** y por eso figura resuelto en 3.2.
- [x] Toda cita RB-xx/PD-xx corresponde a un identificador existente en
      `analisis.txt`; lo no determinado está marcado PENDIENTE.

## Siguiente paso

`04-maquinas-de-estados.md`: para cada entidad (`es_convocatoria`,
`es_mesa_examen`, `es_mesa_inscripcion`, `us_usuario`), definir estados y
transiciones — los disparadores de la convocatoria y de la mesa ya están
resueltos acá por la regla temporal (**G-05 [RESUELTA — 2026-10-06]**), y
siguen marcados los que ninguna fuente declara.
