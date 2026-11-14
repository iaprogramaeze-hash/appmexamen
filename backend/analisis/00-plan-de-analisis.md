# Plan de análisis — Backend EPET36

**Objetivo.** Descomponer el análisis del **backend** en piezas pequeñas,
verificables y con orden claro, de modo que la fase posterior de Spec-Driven
Development reciba requisitos ya sin ambigüedad.

**Alcance — esto es lo que se analiza.**

| | |
|---|---|
| **Producto de este proyecto** | El **backend**: su API, su modelo de datos, sus reglas, su seguridad, sus requisitos no funcionales. |
| **En alcance** | Todo lo anterior, más los contratos que el backend debe ofrecer. |
| **Fuera de alcance** | Las **interfaces** (Landing, SIGME web, SIGME-M móvil). Son proyectos futuros separados. |

**Cómo aparecen las 3 aplicaciones en este análisis.** Sólo como **clientes
del API**: consumidores que imponen requisitos sobre el backend, nunca como
producto a diseñar. Ejemplo: *"SIGME-M reintentar en red móvil inestable"* es
un requisito del backend (debe aceptar reintentos sin duplicar), pero
*"el botón se ve así"* o *"WCAG en la app"* no lo son.

**Quick path**

1. Completar Fase 1 (marco): `01`, `02`, `03`.
2. Completar Fase 2 (comportamiento): `04` → `07`.
3. Completar Fase 3 (reglas y calidad): `08` → `10`.
4. Cerrar con `10-matriz-de-trazabilidad.md`: todo hueco queda visible ahí.

---

## 1. Mapa de dependencias

```
00 plan ──┬─> 01 glosario ──> 02 actores ──┐
          │                                ├─> 03 eventos ──> 04 estados ──┬─> 05 CU SIGME
          └─> (analisis.txt: datos) ───────┘                              │
                                                                          ├─> 06 CU SIGME-M
                                                                          │
                              04 estados ──> 07 estados críticos <────────┘
                                                                  │
                    05,06,07 ──> 08 reglas ──> 09 NFR ──> 10 trazabilidad
```

**Regla:** un documento no se abre hasta que sus entradas estén cerradas. Si
una entrada queda parcial, se marca `[ABIERTA]` y no se arrastra silencio.

---

## 2. Inventario de piezas

| # | Documento | Responde | Entradas | Estado |
|---|---|---|---|---|
| 00 | `00-plan-de-analisis.md` | ¿Qué vamos a analizar y en qué orden? | analisis.txt, investigación | ✅ |
| 01 | `01-glosario-y-alcance.md` | ¿Qué significa cada término y qué entra? | analisis.txt | ⬜ |
| 02 | `02-actores-y-consumidores.md` | ¿Quién consume el API y con qué permisos? | 01 | ⬜ |
| 03 | `03-eventos-y-gatillos.md` | ¿Qué sucesos obligan al backend a responder? | 01, 02 | ⬜ |
| 04 | `04-maquinas-de-estados.md` | ¿Qué estados existen y quién transiciona? | 03 | ⬜ |
| 05 | `05-casos-de-uso-sigme.md` | ¿Qué operaciones necesita el cliente SIGME? | 02, 04 | ⬜ |
| 06 | `06-casos-de-uso-sigme-m.md` | ¿Qué operaciones necesita el cliente SIGME-M? | 02, 04 | ⬜ |
| 07 | `07-estados-criticos-y-excepciones.md` | ¿Qué puede salir mal y qué responde el backend? | 04, 05, 06 | ⬜ |
| 08 | `08-reglas-de-negocio.md` | ¿Qué invariantes no se violan jamás? | 05, 06, 07 | ⬜ |
| 09 | `09-requisitos-no-funcionales.md` | ¿Qué tan bien debe funcionar la API? | 01, 08 | ⬜ |
| 10 | `10-matriz-de-trazabilidad.md` | ¿Está todo cubierto y trazado? | todos | ⬜ |
| 11 | `11-landing-preinscripcion.md` | ¿Qué recibe el backend en `POST /landing/preinscripcion`? | 01 | ⚠️ **urgente** |

> **Los 3 clientes no son producto de este análisis.** Se listan en `02` sólo
> como consumidores del API que imponen requisitos sobre él.
>
> **`11` es de entrega inmediata**: la landing ya se está construyendo y necesita
> el contrato del endpoint antes que nada. Se resuelve junto con Fase 1.

---

## 3. Desglose fino de cada pieza

Cada documento se abre en secciones. Éste es el nivel que después consume SDD.

### 01 · Glosario y alcance
- 1.1 Alcance en / fuera de alcance (tabla)
- 1.2 Glosario ES → término técnico (mesa, llamado, convocatoria, condición,
      previa, acta volante, permiso de examen, matrícula, taller, preinscripción)
- 1.3 Vocabulario prohibido: palabras que se usan coloquialmente y NO son el
      mismo concepto (ej. "mesa" vs "llamado" vs "convocatoria")
- 1.4 Actantes y sistema externos (reloj, correo, push)
- 1.5 Preguntas abiertas hacia el cliente
- **Criterio de cierre:** ninguna palabra del dominio aparece sin definir.

### 02 · Actores y consumidores
- 2.1 **Consumidores del API** (clientes): SIGME web, SIGME-M móvil, Landing
      *(sólo como fuente de tráfico sobre `pr_preinscripcion`)*. Para cada uno:
      qué operaciones necesita y qué lesiones de red/expiración impone.
- 2.2 **Usuarios finales** que el backend debe distinguir — **CERRADO (P-08)**:

  | Rol | Cliente | Módulo |
  |---|---|---|
  | Alumno | SIGME-M | `sigme_mobile` |
  | Secretario/a | SIGME | `sigme_web` |
  | Director | SIGME | `sigme_web` |
  | Administrador | SIGME | `sigme_web` |
  | Superadmin | SIGME | `sigme_web` |
  | *(anónimo)* | Landing | `landing` — sin roles, cualquiera envía |
- 2.3 Objetivo de nivel de cada actor (Cockburn, "un párrafo")
- 2.4 Rol × permiso — matriz explícita
- 2.5 Alcance por módulo (`us_modulo`: quién opera en qué app)
- 2.6 Separación de duties (¿un docente edita su propio acta?)
- **Criterio de cierre:** cada permiso de `analisis.txt` tiene dueño; cada
  actor tiene al menos un permiso; cada consumidor está asociado a las
  operaciones que el backend deberá exponerle.

### 03 · Eventos y gatillos
- 3.1 Eventos externos (alumno toca "inscribirse", admin cierra ventana)
- 3.2 **Eventos temporales** (abre/cierra ventana, vence plazo de acta,
      "48 h antes de la mesa")
- 3.3 Eventos de estado (mesa pasa a "realizada", inscripción queda huérfana)
- 3.4 Tabla: evento → respuesta del sistema → caso de uso → regla
- **Criterio de cierre:** todo caso de uso de `05`/`06` nace de un evento de
  esta tabla. Ningún evento sin respuesta.

### 04 · Máquinas de estados
- 4.1 `es_convocatoria`: borrador → abierta → cerrada → archivada
- 4.2 `es_mesa_examen`: planificada → (cerrada) → realizada → acta cerrada
- 4.3 `es_mesa_inscripcion`: inscripto ↔ anulado. **Sin notas ni asistencia**
      (RB-21) — el sistema no guarda el resultado de la mesa.
- 4.4 `us_usuario`: activo ↔ bloqueado, baja lógica
- 4.5 Para cada transición: **quién la dispara, con qué permiso, precondición**
- **Criterio de cierre:** no existe estado sin transición de salida ni
  transición sin dueño.

### 05 · Casos de uso del backend — cliente SIGME
- 5.1 Consumidor: qué operaciones expone el backend para la web de gestión
- 5.2 CU por dominio: catálogo (orientaciones/cursos/materias/condiciones),
      convocatorias, mesas, inscripciones, reportes (permiso de examen,
      acta volante), usuarios
- 5.3 Formato por CU: **quién consume** (rol + cliente), objetivo,
      precondiciones, operación del API, flujo principal, flujos
      alternativos, flujos de excepción (con su código HTTP), postcondiciones
- **Criterio de cierre:** cada CU de nivel 2 o 3, con al menos un flujo
  alternativo documentado o una nota explícita de "sin alternativos". Cada
  excepción mapea a un código HTTP concreto.

### 06 · Casos de uso del backend — cliente SIGME-M
- 6.1 Sesión y expiración de token desde el cliente móvil
- 6.2 Consultar convocatoria vigente / mesas disponibles
- 6.3 Inscribirse (incluye reintentos, ventana cerrada, duplicado)
- 6.4 Ver mis inscripciones y fechas
- 6.5 Anular inscripción *(si aplica — ver P-02)*
- 6.6 Contratos que el backend debe ofrecer para operar degradado:
      idempotencia, reintentos, paginación, respuestas offline-friendly
- **Criterio de cierre:** cubierto el ciclo completo del alumno, y cada
  operación que el cliente reintentará declara su semántica de idempotencia.

### 07 · Estados críticos y excepciones
- 7.1 Catálogo E1..EEn (estados críticos identificados en investigación)
- 7.2 Para cada uno: disparador → qué se pierde → mitigación → quién la
  verifica → escenario de aceptación (Given/When/Then)
- 7.3 Ventana temporal: semántica de cierre, reloj autoritativo, skew
- 7.4 Concurrencia: unicidad, bloqueos, idempotencia
- 7.5 Integridad de datos históricos (snapshot vs. renombre)
- 7.6 Degradación y recuperación
- **Criterio de cierre:** cada estado crítico tiene **al menos un escenario
  de aceptación ejecutable** en lenguaje Given/When/Then.

### 08 · Reglas de negocio
- 8.1 Invariantes `RN-001…` con identificador estable
- 8.2 Para cada RN: formulación, fuente (cliente / norma / análisis),
      entidades afectadas, cómo se viola, cómo se previene
- 8.3 Reglas derivadas de normativa (Ley 25.326)
- **Criterio de cierre:** ninguna RN es contradictoria con otra; cada RN
  aparece en al menos un CU.

### 09 · Requisitos no funcionales (del backend)
- 9.1 Taxonomía ISO/IEC 25010:2023 (9 características), aplicada al API
- 9.2 Rendimiento y disponibilidad con **números**, no adjetivos
      (latencia p95, límite de concurrencia, presupuesto de errores)
- 9.3 Seguridad y privacidad (Ley 25.326: plazos 10 días / 5 días hábiles,
      consentimiento, log de accesos ≥ 3 años)
- 9.4 Resiliencia: idempotencia, backoff con jitter, reintentos,
      degradación controlada
- 9.5 Auditoría y trazabilidad
- 9.6 **Requisitos heredados a los clientes**: todo lo que corresponde a la
      interfaz (WCAG 2.2, WCAG2Mobile, UX de carga offline) queda listado
      aquí como *requisito para los proyectos futuros*, NO como obligación
      de este proyecto — para que no se pierda.
- **Criterio de cierre:** todo NFR de este backend es medible o está marcado
  `[POR DEFINIR]`; los heredados están separados en su propia tabla.

### 10 · Matriz de trazabilidad
- 10.1 RN ↔ CU ↔ entidad ↔ estado ↔ criterio de aceptación
- 10.2 Cobertura: detectar huérfanos en ambos sentidos
- 10.3 Lista de `[ABIERTA]` y `[POR DEFINIR]` consolidada
- 10.4 Inventario de entregables listos para SDD
- **Criterio de cierre:** cero filas sin correspondencia.

### 11 · Landing — contrato de preinscripción *(entrega inmediata)*
- 11.1 Qué es la preinscripción: inscripción a la escuela para el **próximo
      año lectivo**. Ajena a mesas de exámenes; misma base de datos por
      practicidad y para agilizar una migración futura.
- 11.2 **Aislamiento**: sin foreign keys hacia `pe_*` ni `es_*`. Confirmado.
- 11.3 Payload del `POST /api/v1/landing/preinscripcion` — **CONFIRMADO**:
      `nombre_alumno`, `documento`, `fecha_nacimiento`, `orientacion`,
      `nombre_tutor`, `email`.
      Consentimiento (Ley 25.326) **fuera del sistema**: se recoge en un
      formulario físico posterior. El aviso del art. 6 queda como requisito
      heredado a la landing.
- 11.4 Reglas: **los 6 campos son obligatorios** (`NOT NULL`). Respuestas:
      `201` creada, `200` actualizada (UPSERT), `409 ventana-cerrada`,
      `422` validación, `429` rate limit. **Nunca `409` por duplicado.**
- 11.5 `pr_ventana` (desde/hasta, una sola vigente) + `vw_ventana_vigente`.
- 11.6 Endpoint **anónimo**: sin JWT, sin roles. Sólo rate limit + CORS
      restringido. Gestión de la ventana desde SIGME.
- 11.6 Trazabilidad: IP, user agent, UTM.
- 11.7 Estrategia de migración futura a `pe_persona` (alineación de nombres).
- **Criterio de cierre:** el payload está confirmado por el usuario y la
  landing puede implementar el POST contra el contrato sin preguntar nada.
- **Estado actual:** el **payload real** que envía la landing quedó
  **aprobado el 2026-10-04** (punto (a) del alcance provisional, resuelto).
  `11` sigue `[PROVISIONAL]` por los puntos **(b), (c) y (d)** — formas
  derivadas, números de rate limit y de tamaño de body, y captura de UTM —
  que se cierran en la verificación conjunta con el usuario.

---

## 4. Secuencia recomendada y coste estimado

| Orden | Documento | Esfuerzo | Bloqueante |
|---|---|---|---|
| 1 | 01 glosario y alcance | Medio | Preguntas al cliente |
| 2 | 02 actores y roles | Bajo | 01 |
| 3 | 03 eventos y gatillos | **Alto** | 02 |
| 4 | 04 máquinas de estados | **Alto** | 03 |
| 5 | 05 CU SIGME | **Alto** | 04 |
| 6 | 06 CU SIGME-M | Medio | 04 |
| 7 | 07 estados críticos | **Alto** | 05, 06 |
| 8 | 08 reglas de negocio | Medio | 07 |
| 9 | 09 NFR | Medio | 01, 08 |
| 10 | 10 trazabilidad | Bajo | todos |

**Dónde está la dificultad real:** `03`, `04`, `05` y `07`. Ahí es donde un
análisis flojo se nota después en producción, porque son los lugares donde se
esconden los estados que nadie escribió.

---

## 5. Cómo esto alimenta SDD

| Artefacto de análisis | Se convierte en |
|---|---|
| Caso de uso (nivel 2/3) | Historia de usuario + criterios de aceptación |
| Escenario Given/When/Then de `07` | Escenario ejecutable en la spec |
| `RN-nnn` | Requisito trazable con ID estable |
| Transición de `04` | Regla de validación + test de transición |
| `10` matriz | Definición de "terminado" para cada spec |

La ventaja de hacer esto **antes** de SDD: los criterios de aceptación no se
inventan en la etapa de specs, se **desplazan** desde `07`. Eso es lo que
evita idas y vueltas.

---

## 6. Gaps y preguntas abiertas heredadas de la investigación

Bloqueantes para avanzar en Fase 2:

| ID | Pregunta | Bloquea |
|---|---|---|
| ~~P-01~~ | ~~¿La unicidad es por **mesa** o por **materia × turno**?~~ → **RESUELTA**: por **materia × convocatoria**. No hay turnos ni divisiones (RB-08, RB-15) | 04, 06 |
| ~~P-02~~ | ~~¿Se puede **anular** la propia inscripción, y hasta cuándo?~~ → **RESUELTA**: SÍ, para corregir error de elección; sólo durante la ventana de la convocatoria (RB-08b, RB-07) | 04, 06 |
| ~~P-03~~ | ~~¿La condición se valida al inscribirse, el día de la mesa, o ambas?~~ → **RESUELTA**: SÓLO al inscribirse. Cerrada `fecha_fin_inscripcion` la lista es fija y no se revalida ni se registra inasistencia (RB-03, RB-17, RB-18) | 05, 07 |
| ~~P-04~~ | ~~¿Quién y hasta cuándo puede **rectificar** una nota ya cerrada?~~ → **NO APLICA**: el sistema no guarda notas (RB-21). El resultado vive en el acta en papel | 04, 05 |
| ~~P-05~~ | ~~Instante de cierre: `23:59:59` o `24:00` (exclusivo)~~ → **RESUELTA**: inclusivo hasta las **23:59:59** de `fecha_fin_inscripcion`; a las 00:00:00 del día siguiente se cierra (RB-23) | 03, 04, 07 |
| P-06 | ~~Canales y consentimiento de notificaciones (push/email)~~ → **RESUELTA**: 3 canales (push / campanita in-app / email), sólo por eventos de usuario. Cualquier rol puede recibir; conjunto por rol pendiente (PD-10). Recordatorio 48 h → **v2** (RB-24, RB-25, PD-11) | 06, 09 |
| P-07 | ~~¿SIGME-M debe funcionar **sin conexión**, o sólo mostrar datos en caché?~~ → **RESUELTA**: lectura con caché (sin red ni token), escritura siempre online, ninguna cola offline (RB-26) | 06, 07, 09 |
| P-08 | ~~Lista definitiva de roles~~ | 02 | **✅ RESUELTA** — Alumno, Secretario/a, Director, Administrador, Superadmin; landing anónima |
| P-09 | ~~Payload del `POST /landing/preinscripcion`~~ — **6 campos exactos recibidos**: `nombre_alumno`, `documento`, `fecha_nacimiento`, `orientacion`, `nombre_tutor`, `email` | 11 | **✅ RESUELTA** |

| ~~O-1~~ | ~~El payload NO trae `consentimiento`~~ → **RESUELTO**: proceso físico externo, fuera del sistema. Aviso art. 6 heredado a la landing | 11 |
| ~~O-2~~ | ~~¿`nombre_tutor` obligatorio si es menor?~~ → **RESUELTO**: los 6 campos son obligatorios, así se impusieron | 11 |
| ~~O-3~~ | ~~`anio_lectivo` no se envía; ¿una sola preinscripción abierta a la vez?~~ → **RESUELTO**: `pr_ventana` con desde/hasta, una sola vigente | 11 |
| ~~O-4~~ | ~~¿2º envío devuelve 409 o sobrescribe?~~ → **RESUELTO**: UPSERT (RB-13), repetir no es error | 11 |

**✅ TODAS LAS PREGUNTAS DE ANÁLISIS RESUELTAS:** P-01…P-09 y O-1…O-4.
No queda ningún bloqueo para la Fase 1.

---

## Checklist de este documento

- [x] Alcance definido (SIGME + SIGME-M; landing excluida)
- [x] Piezas desglosadas con entradas, salidas y criterio de cierre
- [x] Dependencias explícitas
- [x] Orden de ejecución y esfuerzo estimado
- [x] Puente hacia SDD explicitado
- [x] Preguntas bloqueantes inventariadas

## Siguiente paso

Cerrar **Fase 1**: `01-glosario-y-alcance.md`, partiendo de las preguntas
P-01…P-08 de la sección 6.
