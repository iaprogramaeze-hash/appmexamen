# Cerrar decisiones raíz que bloquean el backend

## Objetivo

Cerrar las 8 decisiones de diseño (`PD`) que bloquean estructura de datos,
migraciones y capa de autorización, para poder arrancar el backend con las
raíces plantadas. Cada decisión se resuelve con el usuario y se propaga a su
documento de origen más a los dependientes.

## Por qué

El análisis está escrito al 100 % (serie `00`–`11`, 6.697 líneas) y
autoverificado al 94,4 % (102/108 checklists de cierre), pero sólo 6 de los
80 ítems de cierre del doc 10 §10.3 están resueltos. De esos 80, **40 son
síntomas derivados** que se cierran solos al caer su decisión raíz: los 13
`EX` sin código HTTP, los 5 `CU` sin contrato, los 15 `PENDIENTE` del doc 11,
las 5 checklists sin marcar y las 2 transiciones sin cobertura.

## Alcance

### Dentro

- Las 8 decisiones raíz: `PD-02`, `PD-03`, `PD-04`, `PD-05`, `PD-06`,
  `PD-13`, `PD-16`, `PD-18`.
- Propagación de cada decisión a `analisis.txt` §7 (su fuente) y a los docs
  que la referencian: `04`, `05`, `07`, `08`, `09`, `11`.
- Recuento de §10.3 y de los checklists afectados después de cada cierre.

### Fuera

- Los otros ítems abiertos (`G-01`…`G-05`, `PD-10`, `PD-11`, `PD-12`, `PD-15`,
  `PD-17`, `PD-19`…`PD-23`, `PD-28`, `PD-29`): se cierran en una iteración
  posterior.
- Los 6 `CU-xx` sin `RN` y la edición del usuario en `analisis/01` §1.2.1
  (reserva de trabajo separada).
- Cualquier línea de código fuente del backend.

## Tareas

| ID | Tarea | Fuente | Docs a propagar | Estado |
|---|---|---|---|---|
| T-01 | `PD-03` — roles/permisos en la migración; superadmin por ENV | `analisis.txt` §7 | `02`, `05`, `09` (NFR-021), `11` | **cerrada 2026-10-06** |
| T-02 | `PD-04` — reset por email: SÍ, con tabla `us_password_reset` | `analisis.txt` §7 | `07` (EX-21), `08` (RN-050, RN-051) | **cerrada 2026-10-06** |
| T-03 | `PD-02` — Previa 3 / Regular 8 / Libre NULL; unidad **por convocatoria**; valores editables desde SIGME | `analisis.txt` §7 | `05`, `07` (EX-08), `08` (RN-013) | **cerrada 2026-10-06** |
| T-04 | `PD-16` — `UNIQUE (convocatoria_id, fecha, hora) WHERE deleted_at IS NULL` | `analisis.txt` §7 | §3.22, `07` (EX-18), `08` (RN-032) | **cerrada 2026-10-06** |
| T-05 | `PD-13` — `uq_mesa_unica` gana `convocatoria_id`; no gana `hora` | `analisis.txt` §7 | §3.18, `04`, `07` (EX-18), `08` (RN-031) | **cerrada 2026-10-06** |
| T-06 | `PD-18` — cascada lógica transaccional grupo → sus mesas | `analisis.txt` §7 | §3.22, `04` (GR-02), `08` (RN-033) | **cerrada 2026-10-06** |
| T-07 | `PD-05` — `aud_evento`: escrituras + denegaciones + reportes, sin lecturas | `analisis.txt` §7 | `09` (NFR-044) | **cerrada 2026-10-06** |
| T-08 | `PD-06` — Vercel + FastAPI; backend independiente; CORS obligatorio | `analisis.txt` §7 | `§0`, `01`, `09` (NFR-006, 011, 023, 042) | **cerrada 2026-10-06** |
| T-09 | Regla temporal: las mesas vencidas se descubren **al leer**; cierra `G-05`, `CU-22`, `EX-05`, `EX-20` y `ME-03`…`ME-05` | decisión del usuario 2026-10-06 | `01`, `04`, `05`, `07`, `10` | **propagada 2026-10-07** |
| T-10 | Recuento final: §10.3, checklists de cierre y verificación de la serie | doc 10 §10.3 | `10` | **cerrada 2026-10-07** |

## Criterios de aceptación

- [x] Las 8 `PD` pasan de `[PENDIENTE]` a `[CERRADO — <fecha>]` en
      `analisis.txt` §7, con la decisión redactada (no sólo el veredicto).
- [x] Cada doc referenciado cita la decisión en su sección de origen y su
      checklist correspondiente queda marcado donde corresponda.
- [x] §10.3 del doc 10 se reconta y refleja el nuevo estado; los ítems
      derivados que quedaron sin causa se marcan resueltos con su fecha.
- [x] `RN`, `EX` y `CU` afectados actualizan su fila sin romper trazabilidad
      (medir con los conteos de doc 10 §10.2).
- [x] Verificación por tarea: conteo de líneas `(Get-Content -Encoding UTF8).Count`,
      conteo `^## `, ausencia de `fecha_mesa|mesa especial|primero en anotarse|
      primer alumno`, cero `Ã|Â` en los docs 05–10, sin BOM, y `git status --short` limpio.

## Modo de trabajo

- **Ruta:** delegado directo (1 escritor por lote). Los disparadores de
  delegación aplican: 2+ archivos no triviales por decisión propagada.
- **TDD:** no aplica — no hay código fuente; los checks son de documento
  (verificación estructural arriba).
- **Entrega:** un commit por lote de decisiones, Conventional Commit en inglés,
  una línea, sin atribución a IA. Las ramas push/pull request siguen decisión
  del usuario.
- **Revisión RDD:** evaluar con `gentle-ai review assess` por commit de lote;
  registrar aquí el tier y el resultado.

## Evidencia

- **T-01…T-09, propagación a los docs (2026-10-06/07):** `analisis/04`…`analisis/11` modificados sobre HEAD `111f502` (sin tocar `analisis.txt`, `01`, `02`, `03`): 8 `PD-xx` + `G-05` con su decisión redactada en las filas de origen (docs 05–10), regla temporal en `04` §4.2/§4.6.2, `05` CU-22, `07` EX-05/EX-20, `10` filas `G-05`/`CU-22`/`PENDIENTE 5`; checklists de cierre de los docs marcados donde corresponde. Verificación: `h2` idéntico a HEAD en los 8 docs (10/15/12/12/9/12/5/12), `BOM=False`, `forbidden=0` y `mojibake=0` en `04`–`11`, `siguiente_paso=1` por doc.
- **T-10, recuento de §10.3 (2026-10-07):** el recuento consolidado de §10.3 (intros por tabla, "80 ítems", conteos del checklist del doc 10 y §10.4) quedó deliberadamente desactualizado tras los cierres — recuento final en T-10.
- **T-10 — revisión RDD de los commits de lote:**
  - `111f502` — `review assess --base-ref 139a5bc`: `medium` (`executable_change` en `analisis.txt`, 506 líneas) → revisión ejecutada: lente `review-reliability`, 10 hallazgos (`R3-01`…`R3-10`: 3 CRITICAL degradados a causalidad desconocida → escalada, 4 WARNING, 3 SUGGESTION), inspección `completed` sobre los 5 paths; transacción terminó en `escalated` / `stop (native_stop_required)` — la entrega la decide la política ordinaria del repo.
  - Rango combinado `139a5bc..cc8bf2d` (1010 líneas): `review start` falló en preflight con `lens_context_budget_exceeded`; no se creó autoría (`retry_safe`), el alcance se redujo al work unit.
  - `cc8bf2d` — `review assess --base-ref 111f502`: `passive` (`non_executable_only`), `review_due: false`.
  - `9413d49` — `review assess --base-ref cc8bf2d`: `passive` (`non_executable_only`), `review_due: false`.
  - Resultado del propio commit T-10 (7736ba0): **passive** (`non_executable_only`), `review_due: false` — sin revisión..
