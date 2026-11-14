# 04 · Máquinas de estados — Backend EPET36

**Respuesta corta:** este documento define las seis máquinas de estados del
backend — `es_convocatoria`, `es_mesa_examen`, `es_mesa_inscripcion`,
`us_usuario`, `us_sesion` y `es_grupo_horario` (4.5) — con **18 estados** y
**35 transiciones**, y para cada transición declara **quién la dispara, con qué
permiso y bajo qué precondiciones**. Resuelve lo que los documentos previos
dijeron diferido hacia acá: la parte de **G-05** que las fuentes sí sostienen
(la ventana de la convocatoria no se "abre" ni se "cierra" a mano: se constata
por fecha, RB-23) y — desde la **regla temporal del 2026-10-06** — también la
mitad de la mesa: el disparador de `planificada` → `cerrada` → `realizada` es
**el calendario, no un usuario**, constatado al leer sin escritura y sin job.
Deja **PENDIENTE**, con propuesta explícita y con lo que bloquea, lo que
ninguna fuente declara (el estado `acta cerrada` que el modelo no contiene).

**Modelo vigente (cambio de alcance 2026-10-01, RB-27…RB-32).** Las mesas las
crea **el secretario, en bloque**, dentro de un **grupo de mesas** definido por
una fecha y una hora (RB-27, RB-28); la mesa copia ese par de su grupo en la
misma transacción (RB-29) y el alumno **nunca** crea mesas: sólo se inscribe a
mesas que ya existen, y si la combinación no tiene mesa simplemente no hay
inscripción (RB-31). Este documento modela la máquina del grupo: **PD-16** y
**PD-18** se cerraron en `analisis.txt` §7 el 2026-10-06 y aquí se reflejan
como decisión; **PD-12** y **PD-17** siguen como preguntas abiertas.

Vocabulario: se usan los términos de `01-glosario-y-alcance.md` (1.2 y 1.3,
incluido el vocabulario retirado), los actores y la matriz rol × permiso de
`02-actores-y-consumidores.md` (2.2, 2.4) y los eventos de
`03-eventos-y-gatillos.md` (3.1–3.4). Toda cita `RB-xx` y `PD-xx` remite a
`analisis.txt` (§4 y §7); `§n.m` remite a la sección de ese archivo; `plan §n`
remite a `00-plan-de-analisis.md`.

## Rápido recorrido

1. Leer **Convenciones de lectura** (abajo): explica estados derivados vs.
   almacenados, la convención de ciclo y la regla del grupo (fecha + hora).
2. **4.1 → 4.5**: una máquina por entidad, con tabla de estados y tabla de
   transiciones (desde → evento → quién → permiso → precondiciones → hacia →
   fuente). **4.5** (`es_grupo_horario`) es una sección añadida tras el cambio
   de alcance: el plan §3.04 no la lista porque su lista de secciones se
   escribió antes de RB-27.
3. **4.6**: índice consolidado de las 35 transiciones, el caso **G-05**
   (resuelto el 2026-10-06), el caso **G-03**, los huecos de la matriz de
   permisos (PD-03 cerrado), los **PD de diseño** que este documento modela
   (PD-13, PD-16 y PD-18 cerrados el 2026-10-06, con su decisión) y las
   exclusiones explícitas.
4. **Checklist**: incluye la verificación mecánica del criterio de cierre del
   plan (plan §3.04): *ningún estado sin transición de salida, ninguna
   transición sin dueño*.

---

## Convenciones de lectura

| Convención | Detalle | Fuente |
|---|---|---|
| **Estado derivado vs. almacenado** | Un estado es **almacenado** si vive en una columna (`estado`, `activo`, `bloqueado`); es **derivado** si se calcula al leer, sin escritura. Las ventanas nunca "se disparan": **se constatan en cada request** comparando fechas. | `analisis.txt` §3.12, §3.17, §3.18, §3.22; doc 03 §3.2 (RB-23) |
| **`hoy`** | Fecha de calendario `current_date` en `America/Argentina/Buenos_Aires`; límite inclusivo 23:59:59. Nunca un timestamp crudo de UTC ni el reloj del cliente. | RB-23 |
| **Grupo = fecha + hora** | Un grupo de mesas es **sólo** `fecha` + `hora` (RB-27): sin aula, sin profesor (fuera de alcance, confirmado 2026-10-01). La `fecha` y la `hora` de cada mesa son **copia sincronizada** del grupo (RB-29). El alumno **nunca ve el grupo** (RB-30): elige sólo materia + condición. | RB-27, RB-29, RB-30; §3.22 |
| **Sin scheduler en v1** | No existe ningún job programado: todos los envíos y todas las constataciones nacen de una acción de usuario o de un request. | RB-24, PD-11; doc 03 §3.2 |
| **Salida de estados terminales (convención de ciclo)** | Cuando una fila llega a un estado terminal, su transición de salida se expresa **a nivel de proceso**: crea filas nuevas en el siguiente ciclo (una convocatoria nueva, un grupo con sus mesas nuevas, una sesión nueva). La fila vieja queda intacta para auditoría. | RB-16, RB-28, RB-08b; §3.19 |
| **Soft delete como superposición** | `deleted_at` (§1.4, §1.7) es una superposición de persistencia, no un estado de negocio, **excepto** donde este documento lo levanta a estado con justificación escrita: `archivada` en 4.1 y *baja lógica* en 4.4 (ambas las pide el plan, plan §3.04), y `borrada` del grupo en 4.5, porque PD-18 obliga a preguntar qué pasa con las mesas vivas de un grupo borrado. Se declara esa asimetría para no esconderla. | `analisis.txt` §1.4, §1.7; plan §3.04; PD-18 |
| **Permisos** | Cada transición nombra un permiso **real** del catálogo §2.7 con el dueño propuesto en doc 02 §2.4, o marca **PENDIENTE**. No se inventan códigos: el catálogo §2.7 no contiene ningún `convocatoria.*`. | `analisis.txt` §2.7; doc 02 §2.4 |
| **IDs de transición** | `C-xx`, `ME-xx`, `GR-xx`, `INS-xx`, `US-xx`, `SES-xx` son IDs **creados por este documento** (el plan los demanda en su 4.5). Los identificadores ajenos (`RB-xx`, `PD-xx`, `E-xx`, `T-xx`, `S-xx`, `G-xx`, `P-08`) siempre citan su documento de origen. Los IDs retirados **no se renumeran**: se conservan marcados como retirados. | plan §3.04 |
| **Fuera de esta máquina** | `pr_preinscripcion` (`pendiente` → `convertido`/`descartado`) y `pr_ventana` se analizan en `11-landing-preinscripcion.md`, no acá. | plan §3.04 (11); `analisis.txt` §3.20, §3.21 |

---

## 4.1 `es_convocatoria` — borrador → abierta → cerrada → archivada

**Estado del almacenamiento:** la tabla **no tiene columna de estado**
(§3.17): sólo `activa`, las dos fechas, `deleted_at` y
`ck_convocatoria_ventana`. Por eso los cuatro estados del plan (plan §3.04)
son **derivados**, siguiendo el patrón que este análisis ya aplica a las
ventanas: *no se disparan a una hora fija, se constatan en cada request*
(doc 03 §3.2, RB-23).

**Función de estado — PROPUESTA (04), PENDIENTE de confirmación**
(`analisis.txt` no declara cómo se representan estos estados):

| Estado | Condición (con `deleted_at IS NULL`) | Significado operativo | Fuente de la condición |
|---|---|---|---|
| `borrador` | `activa = false` **o** `hoy < fecha_inicio_inscripcion` | Creada y aún no habilitada: nadie se inscribe | RB-09, E-06, §3.17 |
| `abierta` | `activa = true` **y** `fecha_inicio_inscripcion ≤ hoy ≤ fecha_fin_inscripcion` | Ventana vigente: se inscribe y se anula | RB-06, RB-07, RB-08b, RB-23, T-01 |
| `cerrada` | `activa = true` **y** `hoy > fecha_fin_inscripcion` | Lista fija (RB-17); incluye la sub-fase posterior a la última fecha de rendir, que es la **última fecha de los grupos** de la convocatoria | RB-17, RB-07, RB-16, RB-27, T-03, T-06 |
| `archivada` | `deleted_at IS NOT NULL` | Campaña fuera de servicio, conservada para auditoría | §1.4, §1.7 (soft delete) |

**Notas de diseño:**

- `cerrada` cubre **dos momentos de una sola vez**: ventana cumplida (sólo
  consulta en SIGME-M, RB-07) y rendición cumplida (RB-16, actualizado por
  RB-27: la convocatoria se cierra al pasar la **última fecha de sus grupos**;
  ya no hay una única fecha de rendición para toda la convocatoria). El plan no
  los separa y una sola columna `activa` tampoco; distinguirlos es trabajo de
  lectura, no de máquina.
- **RB-05 — premisa sin vigencia, conclusión mantenida:** hay **una sola**
  ventana de inscripción por convocatoria, y ésta **cierra antes de la primera
  fecha de grupo**. Ninguna columna lo impone (`ck_convocatoria_ventana` sólo
  compara `fecha_inicio ≤ fecha_fin`): es una **invariante de negocio** que
  ninguna fuente expresa como validación de esquema. Se deja marcada como
  observación — propuesta (04), sin cerrar.
- **Estado atrapado previsto:** una convocatoria con `activa = false` cuya
  ventana ya venció queda en `borrador` sin posibilidad de abrirse (C-02 y
  C-03 exigen `hoy ≤ fecha_fin_inscripcion`). Por eso existe la transición
  C-06.
- **Alternativa descartada pero documentada:** tomar `archivada` como
  `activa = false` después de usarla. Se descarta porque `activa` ya tiene
  significado explícito en RB-09 (habilitar/deshabilitar inscripción) y
  sobrecargarlo introduciría un tercer significado no escrito en ninguna
  fuente.
- **PENDIENTE:** confirmar la representación (estado derivado vs. columna
  `estado` almacenada). Bloquea: el CU "gestionar convocatoria" del doc 05,
  los estados críticos del doc 07 y una eventual migración de esquema.

```
(nacimiento) ─C-01→ borrador ─C-02/C-03→ abierta ─C-04→ cerrada ─C-07→ archivada
                  │  ▲                     │                              │
                  │  └──────── C-05 ───────┘                              │
                  └──C-06──→ archivada                                    │
                                                     cerrada ◀──── C-08 ───┘
```

### Transiciones

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7 / doc 02 §2.4) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| C-01 | — (nacimiento) | E-06 · se crea una convocatoria | Secretario/a o administración, desde SIGME | **PENDIENTE** — el catálogo §2.7 no tiene código `convocatoria.*` (propuesta: `convocatoria.gestionar`; el cierre de PD-03 el 2026-10-06 confirmó el reparto desde la matriz 2.4, no creó este código) | Nombre y las dos fechas `NOT NULL`; `fecha_inicio_inscripcion ≤ fecha_fin_inscripcion` (`ck_convocatoria_ventana`); `activa` nace `true` | `borrador` | E-06; §3.17; §6 |
| C-02 | `borrador` | T-01 · el calendario llega a `fecha_inicio_inscripcion` | **Reloj del sistema** — constatación en el request, no una acción de usuario | **No aplica** (no es autorización de usuario) | `activa = true` y `deleted_at IS NULL`; `hoy ≥ fecha_inicio_inscripcion` | `abierta` | T-01; RB-23, RB-06; doc 03 §3.2 |
| C-03 | `borrador` | E-06 · activación manual (`activa` pasa a `true`) con la ventana ya iniciada | Administración desde SIGME | **PENDIENTE** (mismo hueco que C-01) | `hoy` dentro de la ventana; sin la activación manual, RB-09 bloquea igual | `abierta` | E-06; RB-09 |
| C-04 | `abierta` | T-03 · cambia la fecha a 00:00:00 posterior a `fecha_fin_inscripcion` | **Reloj del sistema** | **No aplica** | — (a las 23:59:59 de `fecha_fin` aún estaba abierta) | `cerrada` | T-03; RB-23, RB-17, RB-07, RB-16 |
| C-05 | `abierta` | E-06 · desactivación manual (`activa` pasa a `false`) | Administración desde SIGME | **PENDIENTE** (mismo hueco que C-01) | Efecto inmediato: cualquier inscripción queda rechazada | `borrador` | E-06; RB-09 |
| C-06 | `borrador` | Archivar una campaña que nunca abrió o que quedó desactivada ya vencida | Administración desde SIGME (Administrador/Superadmin propuesto) | **PENDIENTE** — §6 no expone `DELETE`/`PATCH /convocatorias` | Soft delete (`deleted_at`); la fila se conserva para auditoría | `archivada` | plan §3.04 (4.1); §1.4, §1.7 |
| C-07 | `cerrada` | Archivar la campaña después de usarla | Administración desde SIGME (Administrador/Superadmin propuesto) | **PENDIENTE** (igual que C-06) | Propuesta: `hoy > fecha_fin_inscripcion` | `archivada` | plan §3.04 (4.1); RB-16 |
| C-08 | `archivada` | Restauración (`deleted_at` → `NULL`) | Administración desde SIGME | **PENDIENTE** — ninguna fuente declara endpoint ni permiso de restauración | — | `cerrada` (la ventana ya venció) | §1.7 (los índices parciales permiten reinsertar); propuesta (04) |

---

## 4.2 `es_mesa_examen` — planificada → (cerrada) → realizada → acta cerrada

**Estado del almacenamiento:** **almacenado**, con
`estado varchar(20) NOT NULL DEFAULT 'planificada' CHECK (estado IN
('planificada','cerrada','realizada'))` (§3.18). La columna nace
`planificada`; desde la **regla temporal del 2026-10-06** (§7), la progresión
`planificada` → `cerrada` → `realizada` **no se graba**: se constata al leer
(ME-03, ME-04). En v1 esa columna conserva su `DEFAULT 'planificada'` sin
más escrituras ni backfill: la fuente de verdad de los estados es la
constatación derivada, no la columna.

| Estado | Significado | Existe en el `CHECK` (§3.18) | Fuente |
|---|---|---|---|
| `planificada` | Mesa creada en bloque por el secretario, dentro de un grupo. Estado inicial. | Sí (DEFAULT) | RB-27, RB-28, §3.18 |
| `cerrada` | Paso intermedio de la jornada, encadenado por S-10; con la regla temporal es una constatación de calendario: la mesa cuya `fecha`/`hora` pasó deja de listarse. | Sí | §3.18, S-10; §7 (2026-10-06) |
| `realizada` | Mesa rendida; también decidida por la constatación, sin escritura. | Sí | §3.18, S-10; §7 (2026-10-06) |
| `acta cerrada` | Cuarta etapa pedida por el plan (plan §3.04). | **NO** — el `CHECK` no la admite | plan §3.04 vs. §3.18 |

**Advertencia sobre `acta cerrada` — PENDIENTE.** El modelo no la contiene y
las fuentes van en contra de meterla: el acta es **papel** (RB-19) y el sistema
**no guarda resultados** (RB-21). Opciones, sin resolver aquí:

- **(i) recomendada:** `realizada` queda como estado terminal y "acta cerrada"
  es un suceso del proceso en papel, **fuera del sistema**.
- **(ii):** agregar el valor `acta_cerrada` al `CHECK` (migración Alembic) y
  definir quién lo dispara.

Bloquea: la máquina de mesas en los docs 05, 07 y 08, y el cuerpo del
`PATCH /mesas/{id}`.

**Nacimiento de la mesa (ME-01).** Toda mesa nace dentro de un grupo de su
convocatoria (RB-27, `grupo_id NOT NULL` en §3.18) y de la alta masiva del
secretario: `POST /grupos` crea el grupo y `materias[]` × `condiciones[]` mesas
de una, con la `fecha` y la `hora` del grupo (RB-28, RB-29). **ME-02** —que era
el alta manual excepcional— queda **RETIRADA**: el modelo de grupos la absorbió
(doc 01 §1.3, vocabulario retirado). Su ID se conserva **sin renumerar**, igual
que hace `analisis.txt` §4 con las reglas revocadas. §6 conserva el endpoint
`POST /mesas`, pero ninguna regla declara hoy un alta individual fuera de la
masiva del grupo: su alcance queda **PENDIENTE (04)** (ver 4.6.4).

```
(grupo: GR-01) ─ME-01→ planificada ─ME-03→ cerrada ─ME-04→ realizada ─ME-05?→ acta cerrada
                          ▲                                             │
                          └────────── ME-06 / ME-07 (fila nueva) ────────┘
```

### Transiciones

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7 / doc 02 §2.4) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| ME-01 | — (nacimiento) | S-01 con E-15 · el secretario crea un grupo y sus mesas **en bloque** (`materias[]` × `condiciones[]` × `fecha` × `hora`) | **Secretario/a** (SIGME); también Administrador y Superadmin con el mismo permiso (doc 02 §2.4). El Alumno **no** interviene | `mesa.crear` — Secretario: **S**, Administrador: **S**, Superadmin: **S**, Alumno: **—** (doc 02 §2.4) | Convocatoria existente y **grupo de esa misma convocatoria** (RB-27; FK `RESTRICT`, §3.18 y §3.22); la mesa toma `fecha` y `hora` de su grupo como copia sincronizada (RB-29); N = `materias[]` × `condiciones[]` (RB-28); combinación única `uq_mesa_unica` (convocatoria × materia × condición × fecha, §3.18) — **PD-13 cerrado 2026-10-06**: el índice gana `convocatoria_id` y sigue sin `hora`; los 4 snapshot se rellenan de materia y condición (RB-11); **PD-12 abierto**: ¿se puede crear con la ventana de inscripción abierta? | `planificada` | RB-27, RB-28, RB-29, RB-11; E-15, S-01; §3.18, §3.22, §6; doc 02 §2.4 |
| ME-03 | `planificada` | S-10 · se cierra la mesa durante la jornada | **El calendario** — regla temporal (§7, 2026-10-06): la constatación ocurre al leer, no hay acción de usuario ni job | **No aplica** (constatación de calendario, sin escritura) | `fecha`/`hora` vencidas en `America/Argentina/Buenos_Aires` (RB-23); el valor no se graba en `estado`. **Sigue sin definir** qué distingue `cerrada` de `realizada` (S-10 sólo los encadena, ninguna fuente los separa) y si `cerrada` es saltable (plan §3.04 la escribe entre paréntesis) | `cerrada` (derivado) | §3.18, S-10; §7 (regla temporal, 2026-10-06); G-05 (doc 01 §1.5.2, doc 03 §3.2) |
| ME-04 | `cerrada` | S-10 · se rinde la mesa | **El calendario** — misma constatación que ME-03 (regla temporal, 2026-10-06) | **No aplica** (constatación de calendario, sin escritura) | Mismo disparador que ME-03: `fecha`/`hora` vencidas. La frontera exacta entre `cerrada` y `realizada` no la declara ninguna fuente (misma observación que ME-03) | `realizada` (derivado) | §3.18, S-10; §7 (2026-10-06); G-05 |
| ME-05 | `realizada` | Cierre del acta | **El calendario** — misma constatación, **sólo si** se adopta la opción (ii): el valor `acta_cerrada` **no existe** en el `CHECK` de §3.18 | **No aplica** (constatación; la transición existe únicamente con la opción (ii)) | Ver opciones (i)/(ii) arriba; RB-19 y RB-21 empujan a la opción (i) | `acta cerrada` | plan §3.04 (4.2); §3.18; RB-19, RB-21; §7 (2026-10-06) |
| ME-06 | `realizada` | Ciclo: en la convocatoria siguiente el secretario vuelve a crear las mesas en bloque y la combinación vuelve a existir como fila nueva | **Secretario/a** (SIGME) — alta masiva del nuevo ciclo; el Alumno no crea filas | `mesa.crear` — Secretario: **S** (doc 02 §2.4) | Nueva convocatoria (RB-16); grupo nuevo con su fecha y su hora (RB-27, RB-28); la fila nueva nace `planificada` (ME-01); la fila vieja queda intacta (convención de ciclo) | `planificada` (fila nueva) | RB-16, RB-27, RB-28; convención de ciclo |
| ME-07 | `acta cerrada` | Ciclo (igual que ME-06) — **sólo si se adopta la opción (ii)** | **Secretario/a** (SIGME) | `mesa.crear` — Secretario: **S** | Igual que ME-06; con la opción (i) este estado no existe y la transición cae junto con ME-05 | `planificada` (fila nueva) | RB-16, RB-27, RB-28 |

**No son transiciones de estado** (se listan para que nadie las confunda):

| Suceso | Por qué no cambia `estado` | Fuente |
|---|---|---|
| Se edita la asignación de la mesa (materia/condición) | Cambia el *contenido* y recalcula los 4 snapshot en la misma transacción; el estado sigue igual | RB-11; S-08 |
| Se renombra una fila de catálogo | Los snapshot **no** cambian (SCD Type 1) | RB-11, RB-12; S-09 |
| Se mueve la fecha u hora de la mesa (por edición de su grupo) | Cambian `fecha`/`hora` — de esa mesa y de todas las del grupo, en la misma transacción (RB-29, S-21) — pero `estado` no cambia: la edición se analiza en 4.5. Su efecto con la ventana de inscripción **abierta** queda **PD-12 abierto** | RB-29, S-21, E-16; PD-12 |
| Se consulta la cobertura de mesas (E-17) | Es una **lectura** (materias × condiciones sin mesa, utilizable antes de abrir la ventana), no un cambio de estado. De dónde sale el conjunto esperado de pares: **PD-15 abierto** | RB-31, E-17; §6; PD-15 |
| La mesa queda con 0 alumnos activos | No se borra ni cambia de estado: sólo desaparece de listados e impresión (`vw_mesa_con_alumnos`) | RB-22; S-03; §3.18 |
| Se emiten permiso de examen, acta volante o planilla de grupos | Son **impresiones en papel** —tres reportes (RB-19 y RB-32)—, no estados; todos aplican RB-22 | RB-19, RB-21, RB-32 |
| Soft delete de la mesa (`mesa.eliminar`) | Superposición de persistencia (§1.4, §1.7); **no** es estado de esta máquina. El permiso `mesa.eliminar` tiene al Secretario marcado **PENDIENTE** en doc 02 §2.4 (hueco de la matriz; PD-03 cerrado 2026-10-06 sin cubrirlo) | §1.4, §1.7; doc 02 §2.4 |

## 4.3 `es_mesa_inscripcion` — inscripto ↔ anulado

**Estado del almacenamiento:** **almacenado**,
`estado varchar(20) NOT NULL DEFAULT 'inscripto' CHECK (estado IN
('inscripto','anulado'))` (§3.19).

**Sin notas, sin asistencia, sin aprobación.** El sistema **no guarda el
resultado de la mesa** (RB-21): no hay `nota`, ni aprobado/desaprobado, ni
rectificación. Tampoco se registra quién se presentó ni quién faltó (RB-18), y
no hay etapa de aprobación de inscripciones (RB-02). Por eso el `CHECK` sólo
admite dos valores — y **ningún estado de este documento agrega uno más**
(verificado en el checklist).

```
(nacimiento) ─INS-01→ inscripto ─INS-02/INS-03→ anulado
                         ▲   │
                         │   └── INS-04 (fila NUEVA) ──┘
```

| Estado | Significado | Fuente |
|---|---|---|
| `inscripto` | El alumno tiene permiso de examen para esa mesa. Lista definitiva al cerrar la ventana (RB-17). | §3.19, RB-17 |
| `anulado` | Revocación por error de elección. La fila se conserva, no se borra y **no ocupa** en `uq_inscripcion_unica`. | RB-08b, §3.19 |

### Transiciones

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7 / doc 02 §2.4) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| INS-01 | — (nacimiento) | E-01 · `POST /inscripciones` sobre una mesa que **ya existe** | **Alumno** (SIGME-M). *Inscribir en nombre de un alumno desde SIGME: PENDIENTE (hueco de la matriz, doc 02 §2.4; PD-03 cerrado 2026-10-06 sin cubrirlo)* | `inscripcion.crear` — Alumno: **S**; Secretario/Administrador/Superadmin: **PENDIENTE** (doc 02 §2.4) | Sesión válida y módulo asignado (RB-26, §2.8); convocatoria `activa` (RB-09); `hoy` dentro de la ventana, 23:59:59 inclusive (RB-07, RB-23); unicidad por **materia × convocatoria** — si choca: 409 (RB-08, S-06); límite de la condición validado **sólo aquí** (RB-03, RB-08c); sin cupo (RB-01); sin aprobación (RB-02); la mesa **ya existe** porque la creó el secretario en bloque dentro de un grupo (RB-27, RB-28) — el alumno no la crea; si la combinación materia × condición no tiene mesa, la inscripción se **rechaza** y nada falla de forma ruidosa (RB-31), con código HTTP **PD-19 abierto**; el alumno elige sólo materia + condición, nunca grupo (RB-30); después de `fecha_fin` ya no entra (RB-17) | `inscripto` | RB-28, RB-31, RB-30, RB-08, RB-09, RB-07, RB-03, RB-01, RB-02, RB-17, RB-23, RB-26; E-01, S-06, S-07; §3.19, §6 |
| INS-02 | `inscripto` | E-02 · `DELETE /mis-inscripciones/{id}` | **Alumno**, sobre su **propia** inscripción | `inscripcion.anular` — Alumno: **S** (doc 02 §2.4) | Sólo dentro de la ventana de la convocatoria (RB-08b, RB-07, RB-23); la fila pasa a `anulado` y queda para auditoría; libera la materia porque el índice único la excluye (§3.19) | `anulado` | RB-08b, RB-07, RB-23; E-02, S-04; §3.19, §6 |
| INS-03 | `inscripto` | S-04 · el secretario revoca una inscripción por error | **Secretario/a** (SIGME) | `inscripcion.anular` — Secretario: **S** (doc 02 §2.4) | **PENDIENTE:** ¿la ventana limita también al secretario? RB-08b y RB-07 se formulan desde SIGME-M (el alumno); §3.19 habilita al secretario sin poner ese límite. No se decide acá | `anulado` | §3.19 (comentario del modelo); doc 02 §2.6; S-04 |
| INS-04 | `anulado` | S-05 · se anota a la mesa correcta después de anular | **Alumno** (SIGME-M) | `inscripcion.crear` — Alumno: **S** | **Crea una fila nueva** (la anulada no se reutiliza); sólo dentro de la ventana (RB-08b); respeta el límite de la condición (RB-08c, RB-03); la unicidad no choca porque la fila `anulado` queda fuera de `uq_inscripcion_unica` (§3.19, RB-08); la mesa destino debe existir (RB-31) | `inscripto` (fila nueva) | RB-08b, RB-08c, RB-03, RB-08, RB-31; S-05; §3.19 |

**Lo que este sistema nunca transiciona** — verificado en el checklist:
`inscripto → ausente/presente` (RB-18), `→ aprobado/desaprobado/nota`
(RB-21), `→ pendiente de aprobación` (RB-02). Si una mesa queda sin
inscriptos activos, **la mesa** sale de los listados (RB-22, S-03); las filas
`anulado` no cambian más.

---

## 4.4 `us_usuario` (y `us_sesion`) — activo ↔ bloqueado, baja lógica

### 4.4.1 `us_usuario`

**Almacenamiento:** no hay una única columna de estado (§3.5): `activo
boolean DEFAULT true`, `bloqueado boolean DEFAULT false` + `bloqueado_hasta`,
y `deleted_at`.

| Estado | Condición | Fuente |
|---|---|---|
| `activo` | `activo = true AND bloqueado = false AND deleted_at IS NULL` | §3.5 |
| `bloqueado` | `bloqueado = true` (temporal o por gestión) | §2.4, §3.5 |
| `inactivo` | `activo = false AND bloqueado = false AND deleted_at IS NULL` | §3.5 (la columna existe); **uso no declarado** |
| `baja lógica` | `deleted_at IS NOT NULL` — el plan la pide como "baja lógica" (plan §3.04) | §1.4, §1.7 |

```
(nacimiento) ─US-01→ activo ⇄ bloqueado        (US-02/US-04 → bloqueado)
                  │      ⇅ US-06 / US-07 (PENDIENTE)
                  │   inactivo                     (US-03/US-05 → activo)
                  └─US-08→ baja lógica ─US-09→ activo
```

**Nota sobre bloqueo y tokens:** al bloquear la cuenta sube `token_version`,
así los access tokens ya emitidos mueren (§2.6, S-15).

### Transiciones — `us_usuario`

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7 / doc 02 §2.4) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| US-01 | — (nacimiento) | E-11 · `POST /usuarios` | Administrador / Superadmin (SIGME) | `usuario.gestionar` — Admin: **S**, Superadmin: **S** | Persona existente (FK `RESTRICT`, §3.5); `username` único entre no borrados (`uq_usuario_username`); `password_hash` Argon2id (§2.5); `activo = true` por defecto; los módulos se asignan aparte (§2.8) | `activo` | E-11; §3.5, §2.5, §2.8; §6 |
| US-02 | `activo` | E-14 y S-16 · 5 logins fallidos en 15 minutos | **Backend** — reacción a una autenticación fallida, no una acción de usuario autorizada | **No aplica** (nadie lo "pide": es una consecuencia) | `intentos_fallidos` alcanza 5 en la ventana (§2.4); se setea `bloqueado_hasta` y sube `token_version` (§2.6, S-15) | `bloqueado` | §2.4, §2.6; E-14, S-16 |
| US-03 | `bloqueado` | T-09 · vence `bloqueado_hasta` | **Reloj del sistema** | **No aplica** | `hoy ≥ bloqueado_hasta`. **PENDIENTE:** la duración exacta del bloqueo y el reinicio de `intentos_fallidos` no los declara §2.4 | `activo` | §2.4; T-09 |
| US-04 | `activo` | S-15 · bloqueo de cuenta por gestión | Administrador / Superadmin (SIGME) | `usuario.gestionar` — Admin: **S**, Superadmin: **S** | **PENDIENTE:** S-15 declara que el bloqueo puede venir de "una acción de gestión", pero no el detalle (¿motivo?, ¿desde qué endpoint? §6 sólo expone `GET`/`POST /usuarios`) | `bloqueado` | S-15, §2.6; doc 02 §2.4 |
| US-05 | `bloqueado` | Desbloqueo manual | Administrador / Superadmin (SIGME) | `usuario.gestionar` (propuesto) — **PENDIENTE** | **PENDIENTE:** las fuentes declaran el bloqueo (§2.4, S-15) pero no el desbloqueo manual | `activo` | §2.4, S-15 (por simetría; propuesta (04)) |
| US-06 | `activo` | Desactivación de la cuenta (`activo = false`) | Administrador / Superadmin (SIGME) | `usuario.gestionar` (propuesto) — **PENDIENTE** | **PENDIENTE:** la columna `activo` existe (§3.5) pero ninguna regla ni endpoint declara quién la apaga ni cómo se distingue de `bloqueado` | `inactivo` | §3.5; propuesta (04) |
| US-07 | `inactivo` | Reactivación (`activo = true`) | Administrador / Superadmin (SIGME) | `usuario.gestionar` (propuesto) — **PENDIENTE** | **PENDIENTE** (misma causa que US-06) | `activo` | §3.5; propuesta (04) |
| US-08 | `activo` / `bloqueado` / `inactivo` | Baja lógica de la cuenta | Administrador / Superadmin (SIGME) | `usuario.gestionar` (propuesto) — **PENDIENTE** (no hay `DELETE /usuarios` en §6) | Soft delete con `deleted_at` (§1.4, §1.7); no dispara FK porque no borra filas; `uq_usuario_username` es parcial, así que el username queda libre | `baja lógica` | §1.4, §1.7, §3.5; plan §3.04 (4.4) |
| US-09 | `baja lógica` | Restauración (`deleted_at` → `NULL`) | Administrador / Superadmin (SIGME) | **PENDIENTE** — ninguna fuente lo declara | — | `activo` | §1.7 (permite reinsertar); propuesta (04) |

### 4.4.2 `us_sesion` — estados declarados en §3.12

§3.12 **sí declara estados**: `estado varchar(12) NOT NULL DEFAULT 'activo'
CHECK (estado IN ('activo','revocado'))`. Una sesión **no se "borra"**: cambia
de estado (§3.12).

| Estado | Significado | Fuente |
|---|---|---|
| `activo` | Login vigente; rota refresh tokens hasta `expires_at` | §3.12, §2.2 |
| `revocado` | Sesión dada de baja; ya no rota y se exige login nuevo | §3.12, §2.4 |

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| SES-01 | — (nacimiento) | E-10 · `POST /auth/login` | Cualquier usuario con credenciales válidas | **No aplica** — autenticación, no autorización (el permiso gobierna los endpoints protegidos, §2.7) | Credenciales válidas (Argon2id, §2.5); rate limit OK (§2.4); cuenta no bloqueada (US-02/US-04); módulo asignado (`us_sesion.modulo_id NOT NULL`, §3.12, §2.8); se emiten access + refresh y se guarda sólo el hash (§2.1, §2.2) | `activo` | E-10; §2.1–§2.4, §3.12; §6 |
| SES-02 | `activo` | E-10 · `POST /auth/logout` | El **dueño** de la sesión | **No aplica** (autenticación) | Sesión propia vigente | `revocado` | §2.3, §2.4; E-10, S-18 |
| SES-03 | `activo` | E-10 · `POST /auth/logout-all` | El **dueño** del usuario, sobre todas sus sesiones | **No aplica** (autenticación) | Todas las sesiones del usuario pasan a `revocado` | `revocado` | §2.4; E-10, S-18 |
| SES-04 | `activo` | S-14 · se reutiliza un refresh token ya usado | **Backend** — reuse detection | **No aplica** | Un refresh ya consumido llega de nuevo → se revoca **toda la familia** (`familia_id`) y se exige login nuevo | `revocado` | §2.2; S-14 |
| SES-05 | `revocado` | E-10 · login nuevo | Cualquier usuario con credenciales válidas | **No aplica** (autenticación) | Crea una **fila nueva** en `activo`; la revocada queda como registro (convención de ciclo) | `activo` (fila nueva) | §2.4, §3.12 |

**La expiración no es estado.** El `CHECK` de §3.12 no tiene `'expirado'`:
cuando vence `expires_at` (T-08) la fila sigue en `activo` y simplemente ya no
rota. Se trata como las ventanas: **condición derivada constatada en cada
request**, no una transición (doc 03 §3.2).

---

## 4.5 `es_grupo_horario` — vigente ⇄ borrada

**Sección añadida** tras el cambio de alcance 2026-10-01 (RB-27…RB-32): el
plan §3.04 no la lista porque su lista de secciones se escribió antes de que
existiera el concepto de grupo. El índice consolidado, que el plan figura como
4.5, queda en **4.6**.

**Estado del almacenamiento:** **derivado** — §3.22 no declara columna de
estado: el grupo tiene `convocatoria_id`, `fecha`, `hora`, `nombre`
(informativo), auditoría y `deleted_at`. Los dos estados se calculan al leer.

| Estado | Condición | Significado operativo | Fuente |
|---|---|---|---|
| `vigente` | `deleted_at IS NULL` | Grupo en uso: sus mesas copian `fecha` y `hora` (RB-29) | §3.22, RB-27, RB-29 |
| `borrada` | `deleted_at IS NOT NULL` | Grupo dado de baja. **PD-18 cerrado 2026-10-06:** cascada lógica transaccional — al borrar el grupo se borran lógicamente sus mesas en la misma transacción; si alguna tiene inscripciones activas, falla entera y no se borra nada (§3.22) | §1.4, §1.7, §3.18, §3.22; PD-18 (§7) |

**Notas de diseño:**

- **El grupo es sólo `fecha` + `hora`** (RB-27): ni aula ni profesor, que
  están **fuera de alcance** (confirmado 2026-10-01). No existe rol docente
  (P-08 cerrado; G-03, ver 4.6.3).
- **El alumno nunca ve el grupo** (RB-30): SIGME-M muestra la fecha y la hora
  de la mesa; pertenecer a un grupo no es una elección del alumno ni afecta
  ninguna validación.
- **Copia sincronizada** (RB-29): editar la fecha u hora de un grupo mueve
  todas sus mesas en la misma transacción. No es transición de estado (ver
  abajo); su efecto con la ventana abierta queda **PD-12 abierto**.
- **PD-16 cerrado 2026-10-06:** `es_grupo_horario` pasa a tener
  `uq_grupo_unico` sobre `(convocatoria_id, fecha, hora)` con `WHERE
  deleted_at IS NULL` (§3.22); la colisión de un duplicado idéntico responde
  **409** (§6).
- **PD-17 abierto:** `grupo.hora` es `time` sin zona horaria y RB-23 evalúa
  por fecha de calendario en `America/Argentina/Buenos_Aires`; la interpretación
  de `hora` junto a `fecha` no está definida.
- **PD-12** sigue abierto: se modela como pregunta abierta (ver
  4.6.5). Los cerrados (PD-16, PD-18) se listan con su decisión, tomada de
  `analisis.txt` §7.

```
(nacimiento) ─GR-01→ vigente ─GR-02→ borrada ─GR-03→ vigente
                  │
                  └── (mover fecha/hora: NO es transición de estado — S-21, PD-12)
```

### Transiciones

| ID | Desde | Evento (doc 03) | Quién dispara | Permiso (§2.7 / doc 02 §2.4) | Precondiciones | Hacia | Fuente |
|---|---|---|---|---|---|---|---|
| GR-01 | — (nacimiento) | E-15 con S-01 · `POST /grupos` — el secretario crea el grupo y N mesas de una (`materias[]` × `condiciones[]` × `fecha` × `hora`) | **Secretario/a** (SIGME); también Administrador y Superadmin con el mismo permiso (doc 02 §2.4) | `mesa.crear` — Secretario: **S**, Administrador: **S**, Superadmin: **S**, Alumno: **—**; crear un grupo es `mesa.crear` (§2.7, sin códigos nuevos) | Convocatoria existente (FK `RESTRICT`, §3.22); `fecha` y `hora` `NOT NULL`; el grupo no declara aula ni profesor (RB-27); **PD-12 abierto:** ¿se puede crear con la ventana de inscripción abierta?; unicidad de `(convocatoria_id, fecha, hora)` **PD-16 cerrado 2026-10-06** (`uq_grupo_unico`, §3.22); **PD-17 abierto:** interpretación de `hora`; sus mesas nacen `planificada` con `grupo_id` (ME-01, RB-29) | `vigente` | RB-27, RB-28, RB-29; E-15, S-01; §3.22, §6; doc 02 §2.4 |
| GR-02 | `vigente` | Borrado lógico del grupo (`deleted_at`) | **PENDIENTE (hueco de la matriz).** Ninguna fuente declara quién da de baja un grupo: §6 sólo declara `POST`, `PATCH` y `GET /grupos`, y en doc 02 §2.4 `mesa.eliminar` tiene al Secretario **PENDIENTE** (PD-03 cerrado 2026-10-06 eligió la matriz 2.4 como reparto definitivo, sin cubrir esa celda) y a Administrador/Superadmin en **S** | `mesa.eliminar` — Secretario: **PENDIENTE** (hueco de la matriz), Administrador: **S**, Superadmin: **S** | **PD-18 cerrado 2026-10-06:** cascada lógica transaccional — al borrar el grupo se borran lógicamente sus mesas en la misma transacción; si alguna tiene inscripciones activas, la operación entera falla y no se borra nada (§3.22). El borrado **físico** sigue impedido por `ON DELETE RESTRICT` mientras haya mesas (§3.18, §3.22). Queda por confirmar que RB-22 / `vw_mesa_con_alumnos` considera el `deleted_at` del grupo | `borrada` | §3.22, §1.4, §1.7; PD-18 (§7); doc 02 §2.4; §6 |
| GR-03 | `borrada` | Restauración (`deleted_at` → `NULL`) | Administración desde SIGME (Administrador/Superadmin propuesto) | **PENDIENTE** — ninguna fuente declara endpoint ni permiso de restauración de grupos | — | `vigente` | §1.7 (los índices parciales permiten reinsertar); propuesta (04) |

**No son transiciones de estado:**

| Suceso | Por qué no cambia `estado` | Fuente |
|---|---|---|
| Se cambia la fecha u hora del grupo (E-16, `PATCH /grupos/{id}`) | Es una **edición de contenido**: todas sus mesas actualizan `fecha`/`hora` en la misma transacción (RB-29, S-21) y el `estado` del grupo no cambia. El efecto —con la ventana de inscripción abierta y sobre alumnos ya inscriptos— queda **PD-12 abierto**: no se resuelve acá | RB-29, E-16, S-21; PD-12 |
| Se cambia el `nombre` del grupo | Informativo (§3.22); no afecta a las mesas | §3.22 |
| Se crea otro grupo con otra fecha u hora | No es una excepción: la convocatoria abarca varios días de rendición, un grupo por fecha y franja horaria (RB-27). El duplicado idéntico ya no pasa: **PD-16 cerrado 2026-10-06** con `uq_grupo_unico` y respuesta 409 (§3.22, §6) | RB-27; PD-16 (§7) |
| El alumno consulta sus mesas en SIGME-M | Ve la fecha y la hora de la mesa; el grupo no se expone (RB-30) | RB-30 |

---

## 4.6 Transiciones consolidadas: quién, con qué permiso, precondiciones

Índice único de las **35 transiciones** de este documento. Es la verificación
mecánica de que **toda transición tiene dueño y todo permiso es real o está
marcado PENDIENTE** (plan §3.04, 4.5).

### 4.6.1 Índice

| ID | Transición | Quién dispara | Permiso (§2.7) | Precondición clave | Estado del permiso |
|---|---|---|---|---|---|
| C-01 | — → `borrador` (crear convocatoria) | Secretario/a o administración (SIGME) | `convocatoria.*` **no existe** | `ck_convocatoria_ventana` | **PENDIENTE** (hueco §2.7) |
| C-02 | `borrador` → `abierta` (calendario) | Reloj del sistema | No aplica | `activa = true`, `hoy ≥ fecha_inicio` | Sin permiso (derivada) |
| C-03 | `borrador` → `abierta` (activación manual) | Administración (SIGME) | `convocatoria.*` **no existe** | Ventana ya iniciada | **PENDIENTE** (hueco §2.7) |
| C-04 | `abierta` → `cerrada` (calendario) | Reloj del sistema | No aplica | `hoy > fecha_fin` | Sin permiso (derivada) |
| C-05 | `abierta` → `borrador` (desactivar) | Administración (SIGME) | `convocatoria.*` **no existe** | — | **PENDIENTE** (hueco §2.7) |
| C-06 | `borrador` → `archivada` | Administrador/Superadmin (propuesto) | `convocatoria.*` **no existe** | Soft delete | **PENDIENTE** (hueco §2.7) |
| C-07 | `cerrada` → `archivada` | Administrador/Superadmin (propuesto) | `convocatoria.*` **no existe** | `hoy > fecha_fin` (propuesta) | **PENDIENTE** (hueco §2.7) |
| C-08 | `archivada` → `cerrada` (restaurar) | Administrador/Superadmin (propuesto) | Sin fuente | — | **PENDIENTE** (sin endpoint) |
| ME-01 | — → `planificada` (alta masiva en un grupo) | Secretario/a (SIGME) | `mesa.crear` (Secretario/Admin/Super: S) | Grupo con fecha + hora, `materias[]` × `condiciones[]`, `uq_mesa_unica` | **Real** (RB-28); PD-12 abierto; PD-13 cerrado (2026-10-06) |
| ME-03 | `planificada` → `cerrada` | **El calendario** (regla temporal, 2026-10-06) — constatación al leer | No aplica (constatación, sin escritura) | `fecha`/`hora` vencidas en `America/Argentina/Buenos_Aires` | Sin permiso (derivada); frontera `cerrada`/`realizada` sin separar |
| ME-04 | `cerrada` → `realizada` | **El calendario** — misma constatación | No aplica (constatación, sin escritura) | Mismo disparador que ME-03 | Sin permiso (derivada) |
| ME-05 | `realizada` → `acta cerrada` | **El calendario** — sólo con la opción (ii) | No aplica (constatación) | Opciones (i)/(ii) en 4.2 | **Real** (derivada, contingente) |
| ME-06 | `realizada` → `planificada` (fila nueva) | Secretario/a (SIGME) — alta masiva del nuevo ciclo | `mesa.crear` (Secretario: S) | Nueva convocatoria y grupo nuevo (RB-16, RB-28) | **Real** |
| ME-07 | `acta cerrada` → `planificada` (fila nueva) | Secretario/a (SIGME) | `mesa.crear` (Secretario: S) | Sólo si existe el estado (opción ii) | **Real** (contingente) |
| INS-01 | — → `inscripto` | Alumno (SIGME-M) | `inscripcion.crear` (Alumno: S) | Ventana + unicidad + límite + mesa existente (RB-31) | Real; en nombre de otro: **PENDIENTE** (hueco de la matriz); rechazo sin mesa: **PD-19** |
| INS-02 | `inscripto` → `anulado` (propia) | Alumno (SIGME-M) | `inscripcion.anular` (Alumno: S) | Dentro de la ventana (RB-08b) | **Real** |
| INS-03 | `inscripto` → `anulado` (por gestión) | Secretario/a (SIGME) | `inscripcion.anular` (Secretario: S) | ¿Ventana también para el secretario? | Permiso real, precondición **PENDIENTE** |
| INS-04 | `anulado` → `inscripto` (fila nueva) | Alumno (SIGME-M) | `inscripcion.crear` (Alumno: S) | Ventana + límite (RB-08c) + unicidad libre | **Real** |
| US-01 | — → `activo` (alta) | Administrador/Superadmin | `usuario.gestionar` (S) | Persona existente + username único | **Real** |
| US-02 | `activo` → `bloqueado` (rate limit) | Backend | No aplica | 5 fallos en 15 min (§2.4) | Sin permiso (automática) |
| US-03 | `bloqueado` → `activo` (vencimiento) | Reloj del sistema | No aplica | `hoy ≥ bloqueado_hasta` | Sin permiso (derivada) |
| US-04 | `activo` → `bloqueado` (gestión) | Administrador/Superadmin | `usuario.gestionar` (S) | Detalle: **PENDIENTE** | Real, detalle PENDIENTE |
| US-05 | `bloqueado` → `activo` (desbloqueo) | Administrador/Superadmin | `usuario.gestionar` (propuesto) | Sin fuente | **PENDIENTE** |
| US-06 | `activo` → `inactivo` | Administrador/Superadmin | `usuario.gestionar` (propuesto) | Sin fuente | **PENDIENTE** |
| US-07 | `inactivo` → `activo` | Administrador/Superadmin | `usuario.gestionar` (propuesto) | Sin fuente | **PENDIENTE** |
| US-08 | cualquier → `baja lógica` | Administrador/Superadmin | `usuario.gestionar` (propuesto) | No hay `DELETE /usuarios` en §6 | **PENDIENTE** |
| US-09 | `baja lógica` → `activo` | Administrador/Superadmin | Sin fuente | — | **PENDIENTE** |
| SES-01 | — → `activo` (login) | Usuario con credenciales | No aplica (autenticación) | Credenciales + rate limit + módulo | Sin permiso |
| SES-02 | `activo` → `revocado` (logout) | Dueño de la sesión | No aplica (autenticación) | Sesión propia | Sin permiso |
| SES-03 | `activo` → `revocado` (logout-all) | Dueño del usuario | No aplica (autenticación) | Todas sus sesiones | Sin permiso |
| SES-04 | `activo` → `revocado` (reuse detection) | Backend | No aplica | Refresh ya usado → familia entera | Sin permiso |
| SES-05 | `revocado` → `activo` (login nuevo) | Usuario con credenciales | No aplica (autenticación) | Fila nueva | Sin permiso |
| GR-01 | — → `vigente` (grupo + N mesas) | Secretario/a (SIGME) | `mesa.crear` (Secretario/Admin/Super: S) | `fecha` + `hora` NOT NULL; ventana abierta: **PD-12**; unicidad: cerrada (**PD-16**, 2026-10-06); zona de `hora`: **PD-17** | **Real**; precondiciones **PD-12/PD-17 abiertos** |
| GR-02 | `vigente` → `borrada` | **PENDIENTE (hueco de la matriz)** — propuesta: rol con `mesa.eliminar` | `mesa.eliminar` (Secretario: **PENDIENTE**; Admin/Super: S) | Cascada lógica transaccional: cerrada (**PD-18**, 2026-10-06) | Permiso real parcial, dueño **PENDIENTE** |
| GR-03 | `borrada` → `vigente` (restaurar) | Administrador/Superadmin (propuesto) | Sin fuente | — | **PENDIENTE** |

**ME-02 no figura en el índice:** su alta quedó retirada con el modelo de
grupos y el ID se conserva sin renumerar (ver 4.2).

### 4.6.2 G-05 — quién y cómo cambia la convocatoria, la mesa y el grupo

**Estado: RESUELTO el 2026-10-06 (regla temporal, §7) en su mitad de la
mesa; el permiso `convocatoria.*` y la ventana de creación del grupo siguen
PENDIENTE.** G-05 (doc 01 §1.5.2; doc 03 §3.2) se abre en cuatro mitades:

| Mitad | Respuesta | Fundamento |
|---|---|---|
| **Convocatoria: ventana** (`abierta` ↔ `cerrada`) | **No la cambia nadie: se deriva del calendario** (C-02, C-04). No hay scheduler en v1 y los cierres *se constatan en cada request*, igual que ya está escrito en doc 03 §3.2. | RB-23, RB-17, RB-16; doc 03 §3.2; RB-24 |
| **Convocatoria: `activa`** | Sí hay disparador humano declarado: **E-06**, edición desde SIGME (`POST /convocatorias`). **Pero el catálogo §2.7 no tiene ningún código `convocatoria.*`**, así que el permiso de C-01/C-03/C-05/C-06/C-07/C-08 queda **PENDIENTE** (hueco de §2.7; el cierre de PD-03 el 2026-10-06 fijó el reparto desde la matriz 2.4 pero no creó el código), con propuesta de crear `convocatoria.gestionar`. | E-06; §2.7, §6; doc 02 §2.4 |
| **Mesa** (`planificada` → `cerrada` → `realizada`) | **RESUELTA el 2026-10-06 (§7): el disparador es el calendario, no un usuario.** Las mesas cuya `fecha`/`hora` pasó dejan de listarse; la constatación se calcula **al leer** en `America/Argentina/Buenos_Aires`, no se graba en `estado` y no hay job (coherente con RN-005). Era la alternativa (04) ya escrita acá: estados derivados por fecha — el `estado` almacenado de §3.18 conserva `DEFAULT 'planificada'` y queda sin escritura temporal. ME-03…ME-05 son la formalización de esa constatación. | RB-16; §3.18; S-10; G-05; §7 (2026-10-06); RN-005 |
| **Grupo** (nacimiento y fecha/hora) | El **nacimiento sí está declarado**: E-15/S-01 con permiso `mesa.crear` (RB-27, RB-28; GR-01 y ME-01). Mover la fecha u hora también tiene endpoint y permiso (`PATCH /grupos/{id}`, `mesa.modificar`, RB-29). Lo que **no** está declarado es si se puede crear o mover **con la ventana de inscripción abierta**: **PD-12 abierto** (bloquea docs 04, 05 y 06). | RB-27, RB-28, RB-29; E-15, E-16; §6; PD-12 |

**Lo que la mitad de la mesa ya no bloquea (y lo que queda:** con la regla
temporal, el CU "cerrar / marcar realizada la mesa" del doc 05, los estados
críticos del doc 07 y las invariantes del doc 08 quedan **desbloqueados**
(CU-22, EX-05, EX-20, ME-03…ME-05); el cuerpo del `PATCH /mesas/{id}` sigue
sólo con edición de asignación (E-07). Queda sin decidir, por falta de fuente,
la frontera entre `cerrada` y `realizada` (S-10 los encadena siempre) y si
`cerrada` es obligatoria o saltable (plan §3.04 la escribe entre paréntesis).

### 4.6.3 G-03 — el rol "docente" no existe

No se usa como actor en ninguna transición de este documento. El comentario
`-- admin, docente, alumno` del DDL de `us_rol` (§3.6) **no** es un rol del
sistema: la lista cerrada es P-08 (plan §6; doc 02 §2.2) y el profesor
evaluador sólo recibe el acta volante **en papel** (RB-19). G-03 queda
**PENDIENTE** en doc 01 §1.5.2 y doc 02 §2.2, sin arrastrarse acá como
supuesto.

### 4.6.4 Huecos de permisos y endpoints referenciados y no resueltos aquí

Tomados de doc 02 §2.4 y `analisis.txt` (§7). **PD-03 se cerró el
2026-10-06**: el reparto definitivo sale de la matriz doc 02 §2.4 (semilla de
roles, permisos y usuarios en la migración inicial), pero las celdas
`PENDIENTE` de esa matriz y los endpoints de esta tabla **no los cubrió**:
siguen abiertos, sin dueño nuevo. Este documento **los referencia, no los
resuelve**:

| Permiso / endpoint | Qué queda abierto | Dónde toca esta máquina |
|---|---|---|
| `mesa.eliminar` | Quién elimina mesas o grupos completos (Secretario: **PENDIENTE** en doc 02 §2.4) | Superposición de soft delete de 4.2 (no es estado) y GR-02 |
| `inscripcion.crear` | Si el secretario puede inscribir **en nombre de un alumno** (Secretario/Administrador/Superadmin: **PENDIENTE**) | INS-01 |
| `reporte.exportar` | Reparto exacto por rol (**PENDIENTE**) | **No toca ninguna transición**: los tres reportes (RB-19, RB-32) son lecturas filtradas por RB-22 y no cambian estados |
| `convocatoria.*` (no existe en §2.7) | Código de permiso para crear, editar y archivar convocatorias | C-01, C-03, C-05, C-06, C-07, C-08 |
| `POST /mesas` (§6) | Alcance del alta **individual** de una mesa: ninguna regla la declara fuera de la alta masiva del grupo (RB-28). Si se mantiene, requiere grupo (RB-27) y `mesa.crear` | ME-01 (nacimiento) |

### 4.6.5 PD de diseño que este documento modela

Tomados de `analisis.txt` §7. Los **cerrados** (PD-13, PD-16, PD-18 el
2026-10-06) se listan con su decisión, tomada de §7 — este documento no los
cierra, sólo los refleja. Los **abiertos** siguen marcados como preguntas en
la fila correspondiente.

| PD | Pregunta abierta / decisión cerrada | Dónde toca |
|---|---|---|
| **PD-12** | ¿Se pueden crear o mover grupos con la ventana de inscripción abierta? (y el efecto sobre alumnos ya inscriptos) | GR-01; edición de grupo (4.5, S-21); ME-01 |
| **PD-13** | **[CERRADO — 2026-10-06]** `uq_mesa_unica` pasa a `UNIQUE (convocatoria_id, materia_id, condicion_id, fecha) WHERE deleted_at IS NULL`: gana `convocatoria_id` (RN-007), sigue sin `hora` (RB-15); el índice se encripta en el nombre por exceder 63 bytes | ME-01, INS-01 |
| **PD-15** | De dónde sale el conjunto esperado de pares materia × condición para la cobertura RB-31 (la convocatoria no tiene FK directa al catálogo) | Consulta de cobertura (4.2); INS-01 |
| **PD-16** | **[CERRADO — 2026-10-06]** `UNIQUE (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` en `es_grupo_horario` (`uq_grupo_unico`, §3.22); la colisión responde **409** (§6) | GR-01 |
| **PD-17** | Interpretación de `grupo.hora` (`time` sin zona) al combinarse con `fecha` y RB-23 | GR-01 |
| **PD-18** | **[CERRADO — 2026-10-06]** cascada lógica transaccional: borrar el grupo borra lógicamente sus mesas en la misma transacción; si alguna tiene inscripciones activas, la operación entera falla (§3.22); el FK `RESTRICT` sólo cubre el borrado físico | GR-02 |
| **PD-19** | Código HTTP del rechazo de `POST /inscripciones` cuando la combinación no tiene mesa (RB-31) | INS-01 |

### 4.6.6 Exclusiones explícitas (verificación anti-regresión)

Ninguna de estas ideas aparece como estado ni como transición en este
documento, y ninguna debe aparecer en los docs 05–08:

| Idea excluida | Regla que la excluye | Fuente |
|---|---|---|
| Nota, resultado, aprobado/desaprobado, rectificación | El sistema no guarda el resultado | RB-21 |
| Asistencia, presente, ausente, inasistencia | No se registra quién faltó | RB-18 |
| Etapa de aprobación de inscripciones | Anotarse es directo | RB-02 |
| Cupo / cupo agotado | No hay cupo por mesa | RB-01 |
| División, turno | `es_curso` identifica el año, no la letra | RB-15 |
| Revalidación el día de la mesa | La lista queda fija al cerrar la ventana | RB-17, RB-03 |
| Que el alumno cree mesas | La creación es del secretario, en bloque y dentro de un grupo | RB-28, RB-27 |
| Una única fecha de rendición por convocatoria, o excepciones de fecha | Cada grupo declara su propia fecha y su hora; una fecha inusual es otro grupo | RB-27, RB-29; PD-14 (resuelto) |
| Aula, profesor o rol docente en la planificación | El grupo es sólo `fecha` + `hora`; la lista de roles es cerrada | RB-27, P-08 |

---

## Checklist de cierre (4 · Máquinas de estados)

**Criterio de cierre del plan (plan §3.04): *ningún estado sin transición de
salida, ninguna transición sin dueño* — verificación mecánica:**

- [x] **Estados declarados: 18** — `es_convocatoria` 4 (borrador, abierta,
       cerrada, archivada) · `es_mesa_examen` 4 (planificada, cerrada,
       realizada, acta cerrada*) · `es_mesa_inscripcion` 2 (inscripto,
       anulado) · `es_grupo_horario` 2 (vigente, borrada) · `us_usuario` 4
       (activo, bloqueado, inactivo, baja lógica) · `us_sesion` 2 (activo,
       revocado).
- [x] **Estados con ≥ 1 transición de salida: 18 de 18.** Detalle por máquina:
       convocatoria 4/4 (borrador C-02/C-03/C-06 · abierta C-04/C-05 ·
       cerrada C-07 · archivada C-08); mesa 4/4 (planificada ME-03 · cerrada
       ME-04 · realizada ME-06 · acta cerrada ME-07); grupo 2/2 (vigente
       GR-02 · borrada GR-03); inscripción 2/2 (inscripto INS-02/INS-03 ·
       anulado INS-04); usuario 4/4 (activo US-02/US-04/US-06/US-08 ·
       bloqueado US-03/US-05/US-08 · inactivo US-07/US-08 · baja lógica
       US-09); sesión 2/2 (activo SES-02/SES-03/SES-04 · revocado SES-05).
- [x] **Transiciones: 35** — C-01…C-08 = 8 · ME-01, ME-03…ME-07 = 6 ·
       INS-01…INS-04 = 4 · US-01…US-09 = 9 · SES-01…SES-05 = 5 ·
       GR-01…GR-03 = 3. **ME-02 no cuenta**: su alta quedó retirada con el
       modelo de grupos y el ID se conserva sin renumerar (4.2).
- [x] **Transiciones con dueño declarado: 35 de 35.** Ninguna queda sin actor:
       o nombra al dueño, o deja la fila PENDIENTE con su propuesta y su
       bloqueo (ME-03, ME-04, ME-05, GR-02).
- [x] **Permiso: 12 con código real de §2.7** (ME-01, ME-03, ME-04, ME-06,
       ME-07, GR-01, INS-01, INS-02, INS-03, INS-04, US-01, US-04) ·
       **9 sin permiso aplicable por diseño** — reloj, backend o
       autenticación (C-02, C-04, US-02, US-03, SES-01…SES-05) ·
       **13 con permiso PENDIENTE** (C-01, C-03, C-05, C-06, C-07, C-08,
       GR-02, GR-03, US-05, US-06, US-07, US-08, US-09) · **1 sin permiso
       asignado** porque la transición misma está PENDIENTE (ME-05). Total:
       12 + 9 + 13 + 1 = 35. ✔
- [x] **Estados cuya única salida tiene el permiso PENDIENTE: 5**
       (convocatoria `cerrada` vía C-07 y `archivada` vía C-08; grupo
       `borrada` vía GR-03; usuario `inactivo` vía US-07/US-08 y `baja lógica`
       vía US-09). El grupo `vigente` **no** entra en esta lista: su única
       salida (GR-02) tiene `mesa.eliminar` con dueños reales
       (Administrador/Superadmin en S); lo que sigue PENDIENTE es el reparto
       del Secretario y el endpoint — PD-03. **Estados cuya única salida es
       una transición misma PENDIENTE: 2** (mesa `planificada` vía ME-03 y
       mesa `cerrada` vía ME-04, ambas G-05). Declarados, no escondidos: se
       listan en 4.6.1.
- [x] `acta cerrada` (`acta_cerrada`) **no existe en el `CHECK` de §3.18**:
       marcada PENDIENTE en 4.2 con sus dos opciones; ME-05 y ME-07 dependen de
       esa decisión.
- [x] **Nacimiento de mesa acorde al modelo vigente:** ME-01 es la alta
       **masiva del secretario** en un grupo (RB-28), el Alumno no aparece
       como creador en ninguna transición (RB-28, RB-31) y ME-06/ME-07 del
       ciclo también son altas del secretario (4.2).
- [x] **Máquina del grupo (4.5):** estados, transiciones y notas modelan
       RB-27, RB-28, RB-29 y RB-30; PD-12, PD-16, PD-17 y PD-18 aparecen como
       **preguntas abiertas** (4.5 y 4.6.5), no como resoluciones.
- [x] **RB-32 presente en las lecturas de reporte:** la planilla de grupos
       figura junto a permiso de examen y acta volante en la tabla "no son
       transiciones" de 4.2 y en la fila `reporte.exportar` de 4.6.4.
- [x] **Sin vocabulario retirado del doc 01 §1.3:** ninguna referencia a la
       columna de fecha eliminada por PD-14, al concepto de excepción de fecha
       retirado por RB-27, ni a la regla de nacimiento que RB-28 reemplazó.
       Verificación mecánica por búsqueda de patrón sobre este archivo:
       **0 coincidencias**.
- [x] **G-05** tratado en 4.6.2: convocatoria resuelta por derivación
       (RB-23, doc 03 §3.2) + permiso de `activa` PENDIENTE (no existe
       `convocatoria.*` en §2.7); la mitad de la mesa queda PENDIENTE con
       propuesta y con lo que bloquea; el grupo queda con nacimiento
       declarado y PD-12 abierto.
- [x] **G-03**: el rol "docente" **no** aparece como actor en ninguna
       transición (4.6.3).
- [x] **Sin estados de nota/asistencia/ausencia/aprobación:** verificado en
       4.3 y 4.6.6 (RB-21, RB-18, RB-02, RB-01, RB-17); el `CHECK` de
       `es_mesa_inscripcion` sólo admite `inscripto` y `anulado` (§3.19).
- [x] Toda cita `RB-xx`/`PD-xx` corresponde a un identificador existente en
       `analisis.txt`; `E-xx`, `T-xx` y `S-xx` existen en doc 03 (§3.1–§3.3);
       `G-03` y `G-05` existen en doc 01 §1.5.2; `P-08` existe en plan §6.
       Lo no determinado está marcado **PENDIENTE** con su propuesta.
- [x] Decisiones confirmadas por el cliente respetadas sin cuestionar:
       unicidad por materia × convocatoria (RB-08); anulación propia sólo
       dentro de la ventana, con fila `anulado` que no ocupa el índice
       (RB-08b); condición y límite validados sólo al inscribirse y lista fija
       después (RB-03, RB-08c, RB-17, RB-18); cierre inclusivo 23:59:59 en
       `America/Argentina/Buenos_Aires` (RB-23); alta de mesas del secretario
       en bloque dentro de un grupo de fecha + hora, con copia sincronizada a
       las mesas (RB-27, RB-28, RB-29); el alumno no crea mesas y una
       combinación sin mesa se rechaza sin ruido (RB-30, RB-31); sin cupo
       (RB-01); sin aprobación (RB-02); reportes sólo con ≥ 1 inscripción
       activa (RB-22) y **tres** reportes de cierre (RB-19, RB-32); snapshot
       con política RB-11; soft delete con índices parciales en todas las
       tablas (§1.4, §1.7).

**Saldo de pendientes que deja este documento:** G-05 (mitad de la mesa),
representación de los estados de `es_convocatoria`, existencia de
`acta_cerrada`, código de permiso `convocatoria.*`, alcance del alta individual
`POST /mesas`, si la ventana limita también al secretario que anula (INS-03),
las transiciones de gestión de usuario US-05…US-09, y los PD de diseño
**PD-12, PD-13, PD-15, PD-16, PD-17, PD-18 y PD-19** — todos marcados con su
pregunta y con dónde tocan, ninguno resuelto acá.

## Siguiente paso

`05-casos-de-uso-sigme.md`: los casos de uso del cliente SIGME, tomando como
entrada las transiciones de 4.1, 4.2, 4.4 y 4.5 (grupos) con sus permisos y
precondiciones ya fijados acá, y el índice consolidado de 4.6.
