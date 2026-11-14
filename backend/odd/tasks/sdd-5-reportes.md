# SDD-5 — Reportes de cierre (permiso de examen, acta volante, planilla de grupos)

**Rama:** `feat/sdd-5-reportes` (apilada sobre `feat/sdd-4-inscripciones` = `3bff040`).
**Base:** `main` = `6018204`.

## Objetivo

Implementar los 3 reportes de cierre (RB-19, RB-32) + 2 endpoints auxiliares,
todos bajo `/api/v1/reportes/` con permiso `reporte.exportar` (roles: secretario,
director, administrador, superadmin — NO alumno). Aplican RB-22 (solo mesas con
al menos una inscripción activa) y RB-19 (leer snapshots de la mesa, no nombres
actuales del catálogo).

## Fuentes

- **analisis.txt §6** (líneas 1121-1125): tabla de endpoints.
- **doc 01 §2.4** (líneas 74-76): glosario de los 3 reportes.
- **doc 02 §2.4** (línea 44): matriz de permisos (`reporte.exportar` en S para
  secretario/director/administrador/superadmin).
- **doc 03 §3.1** (E-09): gatillo de reporte impreso.
- **doc 05 §5.9** (CU-27..CU-30): casos de uso de reportes.
- **doc 08** (RB-19, RB-22, RB-32, RB-11): reglas de negocio.
- **doc 09 §3** (NFR-003): latencia p95 ≤ 2000 ms.

## Endpoints (verbatim §6)

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/reportes/permiso-examen/{usuario_id}` | `reporte.exportar` | Individual por alumno (CU-27) |
| GET | `/reportes/permisos-examen` | `reporte.exportar` | Masivo, agrupado por mesa (CU-27) |
| GET | `/reportes/acta-volante/{mesa_id}` | `reporte.exportar` | Por mesa de una materia (CU-28) |
| GET | `/reportes/mesa/{id}` | `reporte.exportar` | Snapshot de la mesa (CU-29) |
| GET | `/reportes/planilla-grupos/{convocatoria_id}` | `reporte.exportar` | Por convocatoria: grupos con mesas (CU-30) |

## Reglas transversales

- **RB-22 (vida)**: TODOS los reportes filtran `mesas` con `deleted_at IS NULL` Y que
  tengan al menos una `es_mesa_inscripcion` con `estado='inscripto'`,
  `deleted_at IS NULL`. Las mesas sin inscriptos activos NO aparecen.
- **RB-19 (snapshots)**: Los reportes leen `materia_nombre`, `condicion_nombre`,
  `orientacion_nombre`, `curso_nombre` desde las columnas snapshot de
  `es_mesa_examen`, NO desde el catálogo actual (los nombres pueden haber
  cambiado tras crear la mesa).
- **RB-11**: Los 4 nombres snapshot viajan en la respuesta donde corresponda.
- **RB-32**: Planilla de grupos confirmada 2026-10-04 para primera entrega.
- **Permiso**: `require_permiso("reporte.exportar")` — agnóstico de dispositivo
  (L2: rutas a raíz bajo `/api/v1/` sin prefijo de dispositivo).
- **Auditoría (PD-05)**: Cada descarga/impresión de reporte queda registrada en
  `aud_evento` (append-only, snapshot JSONB). Queda fuera de este feature
  (ya existe la tabla y el trigger; solo confirmar que se dispara).

## Fuera de alcance

- Templates de impresión (A4, 3 por carilla) — el usuario pasará diseños luego.
- Generación de PDF — los endpoints devuelven JSON estructurado listo para
  renderizar en frontend/PDF.
- Email de reportes — no hay infra de colas.

---

## Specs

### S1 — Permiso de examen individual (`GET /reportes/permiso-examen/{usuario_id}`)

**CU-27** (doc 05 §5.9, doc 01 §2.4 línea 74). Reporte individual por alumno:
lista las mesas en las que el alumno está inscripto (`estado='inscripto'`,
`deleted_at IS NULL`), con fecha y hora de cada mesa (de su grupo).
Orden: `fecha` asc, `hora` asc.

**Entrada**: `usuario_id` (UUID). Valida que exista y sea alumno (tiene módulo
`sigme_mobile` y permisos `inscripcion.*`).

**Salida**: JSON con `usuario_id`, `convocatoria_id`, `convocatoria_descripcion`,
y array `mesas` donde cada item tiene:
- `mesa_id`, `grupo_id`, `fecha`, `hora`
- `materia_id`, `materia_nombre` (snapshot), `condicion_id`, `condicion_nombre` (snapshot)
- `orientacion_nombre`, `curso_nombre` (snapshot)

**Errores**:
- 404 `usuario-no-encontrado` / `usuario-no-es-alumno`
- 404 `convocatoria-no-encontrada` (si no hay vigente/activa para ese alumno)

**RB-22**: Solo mesas donde el alumno tiene inscripción activa.

---

### S2 — Permisos de examen masivo (`GET /reportes/permisos-examen`)

**CU-27** (doc 05 §5.9). Impresión masiva: agrupa TODOS los permisos de examen
de la convocatoria vigente/activa por mesa. Para cada mesa con inscriptos
activos, devuelve la lista de alumnos inscriptos con sus materias/condiciones.

**Query params opcionales**: `?convocatoria_id=` (por defecto la vigente/activa
según A-SDD4-1). Si se pasa `convocatoria_id` inexistente → 404.

**Salida**: Array de `mesas`, cada una con:
- `mesa_id`, `grupo_id`, `fecha`, `hora`
- `materia_id`, `materia_nombre`, `condicion_id`, `condicion_nombre`
- `orientacion_nombre`, `curso_nombre`
- `alumnos`: array de `{ usuario_id, username, materias: [{materia_id, materia_nombre, condicion_id, condicion_nombre}] }`

**Errores**: 404 `convocatoria-no-encontrada`.

**RB-22**: Solo mesas con ≥ 1 inscripción activa.

---

### S3 — Acta volante (`GET /reportes/acta-volante/{mesa_id}`)

**CU-28** (doc 05 §5.9, doc 01 §2.4 línea 75). Reporte por mesa de una materia:
todos los alumnos inscriptos en esa mesa (`estado='inscripto'`). Para cada
alumno: nombre, documento, materia, condición.

**Entrada**: `mesa_id` (UUID). Valida que exista (`deleted_at IS NULL`).

**Salida**: `mesa_id`, `grupo_id`, `fecha`, `hora`, snapshots (materia/condición/
orientación/curso), y `alumnos` array con `{ usuario_id, username, persona_documento, materia_nombre, condicion_nombre }`.

**Errores**: 404 `mesa-no-encontrada`.

**RB-22**: La mesa debe tener ≥ 1 inscripción activa (si no, 404 o lista vacía
— decisión: 404 `mesa-sin-inscriptos` para que el secretario sepa que no hay
acta que imprimir).

---

### S4 — Snapshot de mesa (`GET /reportes/mesa/{id}`)

**CU-29** (doc 05 §5.9, doc 08 RB-11/12). Lee las columnas snapshot de la mesa:
`orientacion_nombre`, `curso_nombre`, `materia_nombre`, `condicion_nombre`,
`fecha`, `hora`, `estado` derivado (vencida → `cerrada` en BA).

**Entrada**: `mesa_id` (UUID). Valida vida (`deleted_at IS NULL`).

**Salida**: `mesa_id`, `grupo_id`, `convocatoria_id`, snapshots, `fecha`, `hora`,
`estado` derivado (usa `hoy_buenos_aires` + `fecha`/`hora`).

**Errores**: 404 `mesa-no-encontrada`.

---

### S5 — Planilla de grupos (`GET /reportes/planilla-grupos/{convocatoria_id}`)

**CU-30** (doc 05 §5.9, doc 01 §2.4 línea 76, RB-32). Por convocatoria: cada
grupo (fecha, hora) con las mesas que se rinden en él (materia, condición).
Vista de horario, NO detalle de alumnos.

**Entrada**: `convocatoria_id` (UUID). Valida vida (`deleted_at IS NULL`).

**Salida**: `convocatoria_id`, `convocatoria_descripcion`, y array `grupos`
ordenados por `fecha` asc, `hora` asc, cada uno con:
- `grupo_id`, `fecha`, `hora`, `nombre` (del grupo)
- `mesas`: array de `{ mesa_id, materia_id, materia_nombre, condicion_id, condicion_nombre }`

**RB-22**: Solo grupos que tengan al menos una mesa con inscriptos activos.

**Errores**: 404 `convocatoria-no-encontrada`.

---

## Tasks

| ID  | Specs    | Ruta    | Estado     | Commit / evidencia |
|-----|----------|---------|------------|--------------------|
| T1  | S1       | inline  | completado | RED 8 failed -> GREEN 8 passed; suite 243 passed; ruff limpio |
| T2  | S2       | inline  | completado | RED 7 failed -> GREEN 7 passed; suite 250 passed; ruff limpio |
| T3  | S3       | inline  | completado | RED 7 failed -> GREEN 7 passed; suite 257 passed; ruff limpio |
| T4  | S4       | inline  | completado | RED 7 failed -> GREEN 7 passed; suite 264 passed; ruff limpio |
| T5  | S5       | inline  | completado | RED 8 failed -> GREEN 8 passed; suite 272 passed; ruff limpio |
| T6  | S1..S5   | inline  | completado | README actualizado con sección Reportes; suite 272 passed; ruff limpio |

Rutas: una sola área nueva `app/features/reportes/` — un solo escritor (padre).
Sin Writer trigger (cambios secuenciales, misma feature). Exploración inline.

---

## Log

- **L1 (2026-11-02)** — Inicio SDD-5 (reportes). SDD-4 completado (7/7, `3bff040`),
  rama `feat/sdd-4-inscripciones` pusheada. Próximo SDD del roadmap.
- **L2 (2026-11-02)** — T1 completado (S1, `GET /api/v1/reportes/permiso-examen/{usuario_id}`,
  CU-27). Test-first: RED observado (8 failed, ruta inexistente -> 404) -> GREEN
  (8 passed). Service `permiso_examen_individual`: valida usuario alumno (módulo
  `sigme_mobile`), usa convocatoria vigente (A-SDD4-1), JOIN con inscripciones
  activas (RB-22), devuelve mesas con snapshots (RB-11/19) orden fecha/hora asc.
  Permiso `reporte.exportar` (secretario, director, admin, superadmin).
  Errores: 404 `usuario-no-encontrado`, `usuario-no-es-alumno`. Sin inscripciones
  -> array vacío. Suite 243 passed / ruff limpio. Archivos:
  `app/features/reportes/{schemas,service,router,models}.py`,
  `app/api/v1/api.py`, `tests/conftest.py`,
  `tests/unit/test_reportes_permiso_examen.py`.
- **L3 (2026-11-02)** — T2 completado (S2, `GET /api/v1/reportes/permisos-examen`,
  CU-27 masivo). Test-first: RED observado (7 failed, ruta inexistente -> 404) -> GREEN
  (7 passed). Service `permisos_examen_masivo`: agrupa por mesa con inscriptos
  activos (RB-22), lista alumnos con snapshots de materia/condición (RB-19).
  `convocatoria_id` opcional (por defecto vigente). Permiso `reporte.exportar`.
  Errores: 404 `convocatoria-no-encontrada`. Suite 250 passed / ruff limpio.
  Archivos: `app/features/reportes/service.py`,
  `tests/unit/test_reportes_permisos_masivo.py`.
- **L4 (2026-11-02)** — T3 completado (S3, `GET /api/v1/reportes/acta-volante/{mesa_id}`,
  CU-28). Test-first: RED observado (7 failed, ruta inexistente -> 404) -> GREEN
  (7 passed). Service `acta_volante`: valida mesa viva, RB-22 (mesa con ≥ 1
  inscripción activa -> 404 `mesa-sin-inscriptos` si no), devuelve snapshots de
  la mesa (RB-11/19) + lista de alumnos inscriptos con materia/condición.
  Permiso `reporte.exportar`. Errores: 404 `mesa-no-encontrada`,
  `mesa-sin-inscriptos`. Suite 257 passed / ruff limpio. Archivos:
  `app/features/reportes/service.py`,
  `tests/unit/test_reportes_acta_volante.py`.
- **L5 (2026-11-02)** — T4 completado (S4, `GET /api/v1/reportes/mesa/{mesa_id}`,
  CU-29). Test-first: RED observado (7 failed, ruta inexistente -> 404) -> GREEN
  (7 passed). Service `mesa_snapshot`: lee columnas snapshot de la mesa
  (RB-11/12) + estado derivado por fecha/hora BA vs `hoy_buenos_aires`
  (vencida -> "cerrada", inclusive hasta fin de día; sino "planificada").
  Permiso `reporte.exportar`. Errores: 404 `mesa-no-encontrada`. Suite 264
  passed / ruff limpio. Archivos: `app/features/reportes/service.py`,
  `tests/unit/test_reportes_mesa_snapshot.py`.
- **L6 (2026-11-03)** — T5 completado (S5, `GET /api/v1/reportes/planilla-grupos/{convocatoria_id}`,
  CU-30, RB-32). Test-first: RED observado (8 failed, ruta inexistente -> 404) -> GREEN
  (8 passed). Service `planilla_grupos`: por convocatoria, lista grupos ordenados
  por fecha/hora con sus mesas (materia, condición, snapshots RB-11/19).
  RB-22: solo grupos con al menos una mesa con inscriptos activos. Permiso
  `reporte.exportar`. Errores: 404 `convocatoria-no-encontrada`. Suite 272
  passed / ruff limpio. Archivos: `app/features/reportes/service.py`,
  `tests/unit/test_reportes_planilla_grupos.py`.
- **L7 (2026-11-04)** — T6 completado (S7, README + cierre SDD-5). Sección
  "Reportes de cierre (SDD-5)" agregada a `README.md` con tabla de 5
  endpoints, reglas transversales (RB-22, RB-19, PD-05, NFR-003) y PDs
  relacionadas. Suite 272 passed / ruff limpio. Archivos: `README.md`,
  `odd/tasks/sdd-5-reportes.md` (T6 + Log L7). **SDD-5 CERRADO (6/6 tasks).**