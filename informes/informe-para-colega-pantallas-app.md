# Informe para el colega — reportes en la app móvil + pendientes de las pantallas

**Para:** equipo backend (`backend-epet-n36`)
**De:** equipo frontend (app móvil `appmexamen`)
**Fecha:** 2026-11-16
**Motivo:** la app móvil agrega la pantalla de **Reportes** (listado +
generación de reportes de inscripción a mesa). Consolidamos además los
endpoints que seguimos necesitando para las demás pantallas. Nosotros **no
tocamos backend ni BD**; este informe es el pedido para que ustedes lo
implementen.

Contratos detallados de tutor/notas/asistencias/vínculo:
`informes/informe-para-colega-modalidades-tutor-notas.md` (se reiteran en §4).

---

## 1. Resumen ejecutivo

| Tema | Qué pedimos | Quién |
|---|---|---|
| Reportes en la app | Definir **quién** genera reportes desde la app y **qué endpoint** usa (§2) | **Decisión suya** |
| Formato de reportes | Hoy el snapshot devuelve JSON; ¿la app renderiza JSON o agregan export a PDF? | **Decisión suya** |
| Historial de reportes | Si esperan listado persistente, hace falta `GET /reportes` (§2.3) | Uds |
| Acceso staff a la app | Si los reportes los usa staff desde el celular: módulo `sigme_mobile` en esos roles (§3) | Uds |
| Notas / asistencias / vínculo / permisos | Sigue pendiente lo del informe anterior (§4) | Uds |

**Fuera de alcance:** no pedimos cambios en SIGME web ni en los endpoints de
reportes ya funcionando para el panel web; pedimos **acceso/variante para la
app móvil**.

---

## 2. Reportes (pantalla nueva de la app)

### 2.1 Qué ya existe en el snapshot (verificado en `backend/app/features/reportes/router.py`)

Cinco endpoints bajo `/api/v1`, todos con gate
`require_permiso("reporte.exportar")` — roles: **secretario, director, admin,
superadmin** (no alumno, no tutor) — y todos responden **JSON**
(`response_model`), no PDF:

| Método | Ruta | Para qué (docstring) |
|---|---|---|
| `GET` | `/reportes/permiso-examen/{usuario_id}` | Permiso individual: mesas con inscripción activa del alumno (RB-11/22) |
| `GET` | `/reportes/permisos-examen?convocatoria_id=` | Permisos masivos agrupados por mesa (por defecto convocatoria vigente) |
| `GET` | `/reportes/acta-volante/{mesa_id}` | Acta volante; `404 mesa-sin-inscriptos` si no hay inscripciones activas |
| `GET` | `/reportes/mesa/{mesa_id}` | Snapshot de mesa (columnas RB-11/12 + estado derivado) |
| `GET` | `/reportes/planilla-grupos/{convocatoria_id}` | Planilla de grupos (fecha/hora → mesas), sin detalle de alumnos (RB-32) |

### 2.2 Qué necesita la app

La pantalla **ya está creada** en la app (esqueleto, modo "aún no disponible"),
con dos áreas:

1. **Listado** de reportes generados (vacío hoy).
2. **"Generar reporte de inscripción"** — botón deshabilitado hasta que el
   backend exponga la acción.

Para cablearla necesitamos que definan:

1. **¿Quién genera reportes desde la app?** La app hoy solo tiene roles
   `alumno` y `tutor`, y ninguno tiene `reporte.exportar`. Opciones:
   - **(a)** Asignar `reporte.exportar` + módulo `sigme_mobile` a un rol staff
     (secretario/director) que se loguee en la app.
   - **(b)** Variante para alumno: endpoint(s) que devuelvan **solo el reporte
     de la inscripción del propio alumno** con un permiso propio (p. ej.
     `reporte.propio`), acotado por dueño como ya hacen con notas.
   - **(c)** Ambos.
2. **¿Qué endpoint cubre "reporte de inscripción a la mesa"?** Candidato
   natural: `/reportes/permiso-examen/{usuario_id}` (lista las mesas con
   inscripción activa). ¿Sirve tal cual cuando el alumno pide su propio
   `usuario_id`, o prefieren un endpoint dedicado?
3. **Formato:** ¿la app muestra el JSON como lista, o agregan export a PDF
   (ruta aparte o header `Accept: application/pdf`)?
4. **Historial:** si el listado debe persistir entre sesiones, hace falta un
   `GET /reportes` (por alumno, con estado/fecha). Si no, la app puede mostrar
   solo lo generado en la sesión.

### 2.3 Contrato mínimo que nos sirve (propuesta — lo ajustan ustedes)

| Método | Ruta | Quién | Salida |
|---|---|---|---|
| `GET` | `/reportes/mis-inscripciones` | alumno (dueño) | → `200 { reportes: [ { id, mesa_id, materia, fecha, hora, generado_en } ] }` |
| `POST` | `/reportes/mis-inscripciones` | alumno (dueño) | → `201 { id, … }` genera el reporte de su propia inscripción |

Alternativa mínima si reutilizan lo existente: que
`/reportes/permiso-examen/{usuario_id}` acepte al **propio alumno** cuando
`usuario_id == sub` del JWT, sin exigir `reporte.exportar` para ese caso.

---

## 3. Acceso staff a la app (si eligen la opción a)

- Recordar que el **login de la app exige** `modulo: "sigme_mobile"` en el
  body (`POST /auth/login`). Un usuario staff sin ese módulo asignado no puede
  entrar.
- Alta de módulo en `UsUsuarioModulo` para los roles que vayan a usar la app.
- `/auth/yo` debe devolver en `permisos` los que la app use para mostrar u
  ocultar la pestaña (la app ya lee `permisos` de esa respuesta).

---

## 4. Pendientes que siguen abiertos (del informe anterior)

Detalle de contratos en `informe-para-colega-modalidades-tutor-notas.md`;
resumen:

- [ ] `GET /notas` (alumno) → pantalla Notas del alumno.
- [ ] `GET /tutor/alumnos/{id}/notas` y `GET /tutor/alumnos/{id}/asistencias`
      → pantallas Notas y Asistencias del tutor.
- [ ] Vínculo tutor ↔ alumno por **DNI + aceptación** (§3.3 del informe
      anterior): alta con `dni_alumno`, aceptar/rechazar, listados, regla de
      1 tutor activo.
- [ ] `GET /auth/yo` con `"tutor"` en `roles` (la app ramifica pantallas con
      eso).
- [ ] Rol `tutor` en seed + matriz de permisos (§2 del informe anterior).
- [ ] Endpoint de **Permisos** de examen (listado/PDF) para la pantalla
      Permisos del alumno.

---

## 5. Checklist para ustedes

- [ ] Decidir opción **(a)/(b)/(c)** del §2.2 (quién genera reportes en la app)
- [ ] Confirmar endpoint del reporte de inscripción (o crear el dedicado)
- [ ] Definir formato: JSON renderizado por la app / PDF
- [ ] Si aplica historial: `GET /reportes`
- [ ] Si es (a): módulo `sigme_mobile` + `reporte.exportar` en el rol staff
- [ ] Los pendientes de §4
- [ ] Nos avisan los contratos finales (o si cambia alguno)

---

## 6. Lo que nosotros hacemos con esto

1. La pantalla de Reportes ya está en la app en modo "aún no disponible", sin
   bloquear el resto del flujo.
2. Cuando definan los contratos del §2, cableamos listado + generación en una
   iteración.
3. Los pendientes de §4 siguen con las pantallas en esqueleto esperando.
4. Cualquier cambio de contrato, lo re-emitimos por informe nuevo o por
   comentario en este mismo archivo.

**Contacto:** por este repo (`appmexamen`) o el canal que ya usemos para el
flujo de recuperación de clave.
