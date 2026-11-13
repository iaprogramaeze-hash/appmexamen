# Informe para el colega — rol tutor, notas y asistencias (app móvil)

**Para:** equipo backend (`backend-epet-n36`)
**De:** equipo frontend (app móvil `appmexamen`)
**Fecha:** 2026-11-13
**Motivo:** la app móvil agrega **rol tutor/padre**, **notas trimestrales** y
**asistencias**. Nosotros **no tocamos backend ni BD**; este informe es el
pedido para que ustedes lo implementen. La app consume los contratos de §3.

---

## 1. Resumen ejecutivo

| Tema | Qué pedimos | Quién |
|---|---|---|
| Rol `tutor` | Rol nuevo de solo lectura (notas + asistencias de sus alumnos) | Uds |
| Vínculo tutor ↔ alumno | Tabla + flujo por **código que genera el alumno** | Uds |
| Notas trimestrales | Endpoint(s) de lectura; los datos **ya se cargan del otro sistema (SIGME)** | Uds |
| Asistencias a clases | Ídem: lectura; origen SIGME | Uds |
| `GET /auth/yo` | Que devuelva el rol `tutor` en `roles` (la app ramifica pantallas con eso) | Uds |
| Alta de cuenta tutor | Registro en la app con rol `tutor` (¿libre como alumno D10, o aprobación?) | **Decisión suya** |
| Panel admin en la app | **Se elimina** de la app; SIGME web no cambia | Nosotros |

**Fuera de alcance de este pedido:** inscripción a mesas por parte del tutor
(el tutor **no** se inscribe; no necesita `inscripcion.crear` ni `anular`).

---

## 2. Roles y permisos

### 2.1 Rol nuevo

| Rol | Módulo | Permisos (propuesta) |
|---|---|---|
| `tutor` | `sigme_mobile` (o módulo propio si prefieren) | `nota.listar`, `asistencia.listar`, `vinculo.gestionar` |

**No** asignar al tutor: `inscripcion.*`, `mesa.*` de escritura, `persona.*`,
`usuario.gestionar`, `reporte.exportar`.

### 2.2 Alumno (ya existe)

Agregar permiso de lectura propio si lo separan del de tutor:

| Rol | Permiso extra propuesto |
|---|---|
| `alumno` | `nota.listar` (solo las **propias**) |

El backend debe **acotar por dueño**: el alumno ve solo sus notas; el tutor,
solo las de los alumnos **vinculados**. Nunca un listado global.

### 2.3 Admin de la app

La app **ya no tendrá** panel admin. Los roles `secretario` / `director` /
`administrador` / `superadmin` de SIGME web **no cambian** en backend.

---

## 3. Contratos que la app va a consumir

Base: `/api/v1` (mismo prefijo que hoy). Auth: JWT bearer, igual que
`/auth/yo`. Errores en el estilo ya usado (`401`, `403`, `404`, `409`, `422`).

### 3.1 Sesión — ya existe, un requisito

| Método | Ruta | Nota |
|---|---|---|
| `GET` | `/auth/yo` | **Debe incluir** `"tutor"` en `roles` cuando corresponda. La app hace `roles.includes('tutor')`. |

### 3.2 Cuenta de tutor

| Método | Ruta | Body / salida | Estados |
|---|---|---|---|
| `POST` | `/auth/registro` *(si aún no existe, crear)* | `{ email, password, nombre, apellido, documento, rol: "tutor" }` → `201` | Registro de tutor. **Definan** si es libre o requiere aprobación (D10 es libre para alumno). |

### 3.3 Vínculo por código (alumno genera → tutor consume)

Flujo acordado: **el alumno controla quién ve sus datos**.

| Método | Ruta | Quién | Body / salida |
|---|---|---|---|
| `POST` | `/vinculos/codigo` | alumno | → `201 { codigo, expira_en }` — código de un solo uso, corta vida (sugerimos 10–30 min). Regenerar invalida el anterior. |
| `POST` | `/vinculos/consumir` | tutor | `{ codigo }` → `201 { alumno_id, alumno_nombre }` o `404`/`409` si inválido/usado/vencido. |
| `GET` | `/vinculos` | tutor | → `200 { alumnos: [ { id, nombre, documento } ] }` |
| `DELETE` | `/vinculos/{alumno_id}` | tutor | → `204` — desvincular (tutor o alumno, ver 3.6). |

### 3.4 Notas trimestrales

| Método | Ruta | Quién | Salida |
|---|---|---|---|
| `GET` | `/notas` | alumno | → `200 { notas: [ { materia_id, materia_nombre, trimestre, nota, anio_lectivo } ] }` — solo las propias. |
| `GET` | `/tutor/alumnos/{alumno_id}/notas` | tutor vinculado | → `200` mismo shape. `403` si no hay vínculo. |

`trimestre`: `1 \| 2 \| 3`. `nota`: numérica (escala que ya maneje SIGME).
`anio_lectivo`: para poder filtrar cuando haya más de uno.

### 3.5 Asistencias a clases

| Método | Ruta | Quién | Salida |
|---|---|---|---|
| `GET` | `/tutor/alumnos/{alumno_id}/asistencias` | tutor vinculado | → `200 { asistencias: [ { fecha, materia_nombre, presente: bool, motivo? } ] }` |
| `GET` | `/asistencias` *(opcional)* | alumno | Si también querés que el alumno vea las suyas; la app lo usa si existe. |

### 3.6 Alumno ve el estado de sus vínculos (opcional pero útil)

| Método | Ruta | Quién | Salida |
|---|---|---|---|
| `GET` | `/vinculos/mis-tutores` | alumno | → `200 { tutores: [ { id, nombre, email } ] }` — para mostrar en Perfil quién lo está viendo y poder sacarlo. |

---

## 4. Modelo de datos (sugerencia, lo diseñan ustedes)

No es mandatorio; es para que el pedido se entienda con tablas concretas.

| Tabla (sugerida) | Campos mínimos |
|---|---|
| `fa_vinculo_tutor` | `id`, `tutor_usuario_id` FK, `alumno_usuario_id` FK (o `persona_id`), `estado`, `created_at`, `deleted_at`. Índice único activo por par. |
| `fa_codigo_vinculo` | `id`, `codigo` (único), `alumno_usuario_id`, `expira_en`, `usado_en` (nullable), `created_at`. |
| Notas | Si SIGME ya las tiene: **exponerlas** (vista/proxy/sync como prefieran). Si hay que guardarlas acá: `alumno`, `materia`, `trimestre`, `nota`, `anio_lectivo`. |
| Asistencias | Ídem: origen SIGME; si se materializa acá: `alumno`, `fecha`, `materia`, `presente`, `motivo?`. |

**Origen de datos:** notas y asistencias **no se cargan en la app**. Vienen
del otro sistema (SIGME). Ustedes definen si es lectura directa, replica o
importación periódica; la app solo llama los endpoints de §3.

---

## 5. Seguridad (mínimo esperado)

- Código de vínculo: un solo uso, expiración, rate limit al consumir (mismo
  estilo que `olvido-clave`).
- `403` si un tutor pide notas/asistencias de un alumno **sin vínculo**.
- `403` si un alumno intenta las rutas `/tutor/*`.
- Auditoría de creación/baja de vínculos (como ya hacen con lo demás).
- No exponer en respuestas de tutor datos del alumno fuera de nombre,
  documento y lo pedido (notas/asistencias).

---

## 6. Checklist para ustedes

- [ ] Rol `tutor` en seed + matriz de permisos (§2)
- [ ] `GET /auth/yo` devuelve `tutor` en `roles`
- [ ] `POST /auth/registro` (o alta equivalente) para tutor
- [ ] Tablas + endpoints de vínculo por código (§3.3)
- [ ] `GET /notas` (alumno) y `GET /tutor/alumnos/{id}/notas` (§3.4)
- [ ] `GET /tutor/alumnos/{id}/asistencias` (§3.5)
- [ ] Acota por dueño/vínculo + tests de `403` (§5)
- [ ] Nos avisan cuando los contratos estén listos (o si cambia alguno)

---

## 7. Lo que nosotros hacemos con esto

1. Construimos la app móvil (React Native + Expo) contra estos contratos.
2. Si algún endpoint no está listo, la app puede mostrar la pantalla en modo
   “aún no disponible” sin bloquear el resto del flujo.
3. Cualquier cambio de contrato, lo re-emitimos por informe nuevo o por
   comentario en este mismo archivo.

**Contacto:** por este repo (`appmexamen`) o el canal que ya usemos para el
flujo de recuperación de clave.
