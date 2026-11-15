# Feature: App móvil Android (React Native + Expo)

**Objetivo:** APK descargable real (no HTML) que reemplaza al prototipo web, con
roles alumno y tutor, notas y asistencias. **Rama:** `feat/app-movil` sobre
`main` de `iaprogramaeze-hash/appmexamen`. **Estrategia de entrega:**
`ask-on-risk` (se pide cadena si pasa ~400 líneas). **Tests:** Jest + React
Testing Library (scaffold Expo); verificación manual en Expo Go / emulator.

**Reparto:** nosotros solo frontend + informe; backend/BD los hace el colega
(`informes/informe-para-colega-modalidades-tutor-notas.md`).

---

## Specs

### S1 — Plataforma y repo
- React Native + Expo SDK actual, `minSdk` 24 (Android 7+), APK universal.
- Proyecto nuevo en este repo (carpeta `mobile/`), no se toca `docs/prototipo/`.
- Desarrollo en `origin` = `iaprogramaeze-hash/appmexamen`; al final, push a
  `original` (`formulariosepetn36-ai/appmexamen`).

### S2 — Estructura de pantallas (varias, no una sola)
- Usuario: "entonces varias pantallas en ves de una sola seria mejor?"
- Flujo de acceso aparte: Login, Recuperar, Registro.
- Rol alumno con pestañas: **Inicio** (inscripción), **Permisos**,
  **Notas**, **Perfil**.
- Rol tutor con pestañas: **Notas** (del alumno vinculado),
  **Asistencias**, **Perfil**.
- **Sin panel admin** en la app: "eliminaremos el rol de admin en nustra app".

### S3 — Rol tutor / padre
- Usuario: "armaremos un rol padre o tutor".
- El tutor **solo lee**: "el rol a tutor o padre solo podra ver las notas y
  asisitencias a clases del alumno, no podra incribirse a materias a rendir".
- `/auth/yo` con `roles` incluyendo `tutor` → la app ramifica pantallas.

### S4 — Vínculo tutor ↔ alumno por código del alumno
- Usuario eligió: **"Código del alumno"**.
- Alumno genera código desde **Perfil**; tutor lo ingresa al registrarse o
  desde su Perfil para vincularse.
- El backend implementa el flujo (§3.3 del informe); la app solo lo consume.

### S5 — Notas trimestrales
- Usuario: "lo nuevo que el alumno podra ver es sus notas trimistrales que
  estaran cargas por materia".
- Alumno: `GET /notas` — lista por materia con `trimestre` 1|2|3.
- Tutor: `GET /tutor/alumnos/{id}/notas` solo de alumnos vinculados.
- Los datos **no se cargan en la app**; vienen del otro sistema (SIGME) vía
  backend: "está cargado del lado del otro sistema".

### S6 — Asistencias
- Tutor: `GET /tutor/alumnos/{id}/asistencias`.
- Alumno: `GET /asistencias` solo si el backend lo expone (opcional).

### S7 — Backend solo por informe
- Usuario: "el pedido de la actualicacion de backend solo lo hacemos por
  informe, nosotros no lo modificamos, el colega es encargado de BD y backend".
- **Prohibido** editar `backend-epet-n36-main/` en este feature.
- Contratos: `informes/informe-para-colega-modalidades-tutor-notas.md`.

### S8 — Pantallas existentes del prototipo a portar
- Login, Recuperar (token por correo), Registro: cablear a los endpoints
  `auth/*` ya probados en el prototipo.
- Inicio + Inscripción: `GET /mesas-disponibles` + `POST /inscripciones`
  (flujo ya validado en prototipo).
- Permisos: vista de permisos de examen (PDF cuando backend lo exponga;
  por ahora lectura del listado).
- Perfil: datos read-only, cambiar clave, cerrar sesión, **generar código de
  tutor** (S4).

### S9 — Entorno
- Node OK en la máquina; JDK 17 + Android SDK solo si build local de APK;
  desarrollo inicial con **Expo Go** (recarga en el celular).
- `API_BASE` configurable (hoy hardcodeado `http://localhost:8000` en el
  prototipo; en la app: variable de entorno / config).

### S10 — Estilo visual (referencia Dribbble)
- Usuario (2026-11-13): "mira el diseño que nos muestra la siguiente paguina:
  dribbble.com/short/26993647-Kids-Learning-App-UI-Gamified-Education-Internative-Lessons
  y me gustaria que nuestro diseño se asejado a eso" + "con las imagenes que
  tenemos en el repositorio, pero los vamos biendo como queda".
- Decisión de fork: aplicar el estilo **directo en la app Expo** (no en el
  prototipo HTML), iterando pantalla por pantalla.
- DNA del shot: fondos lavanda con gradientes suaves; tarjetas y botones muy
  redondeados; CTA durazno; tab bar flotante oscura tipo píldora; un
  personaje ilustrado por tarjeta; estética gamificada (nivel, barra de
  progreso, badges tipo `0/5`).
- Paleta del shot: `#C9AEFA`, `#B0B8D7`, `#B6C8D3`, `#9BA2AE`, `#815680`,
  texto `#0A090D`, marrón `#48303B` (los 7 tags de color del shot).
- Imágenes del repo como personajes (procesadas a PNG con máscara circular):
  `tatu-estudia` → login/inicio, `mesas-examen` → Inicio (inscripción),
  `calificaciones` → Notas, `asistencia` → Asistencias (tutor).
- Los textos funcionales no cambian por el estilo (siguen valiendo los de
  S2/S3/S5/S6/S8).

---

## Tasks

| ID | S# | Tarea | Ruta | Estado | Commit |
|----|----|-------|------|--------|--------|
| T1 | S1 | Scaffold Expo en `mobile/` + rama `feat/app-movil` | inline | **Hecho** | 598d2b4 |
| T2 | S9 | Capa API (`API_BASE`, cliente auth con token) | inline | **Hecho** (clientes mesas, inscripciones, notas, asistencias en `src/api.ts`) | 598d2b4 |
| T3 | S8 | Pantallas de acceso: Login, Recuperar, Registro | inline | **Hecho** (iteración visual aplicada: mascot con máscara circular en acceso) | 598d2b4 |
| T4 | S2,S8 | Navegación por roles (tabs alumno / tutor) | inline | **Hecho** | 598d2b4 |
| T5 | S8 | Inicio + Inscripción (mesas) | inline | Esqueleto visual vacío; sin datos demo, sin cablear API (espera backend) | 598d2b4 |
| T6 | S5,S6 | Pantalla Notas (alumno) | inline | Esqueleto visual vacío; sin datos demo, sin `GET /notas` | 598d2b4 |
| T7 | S8 | Permisos + Perfil (con generar código tutor) | inline | Esqueleto visual vacío en Permisos; Perfil sin datos de backend | 598d2b4 |
| T8 | S3,S4,S6 | Pantallas tutor: vínculo, Notas, Asistencias | inline | Notas y Asistencias en esqueleto visual vacío; sin datos de backend | 598d2b4 |
| T9 | S2 | Quitar rastro de admin; menú solo según rol | inline | **Hecho** | 598d2b4 |
| T10 | S1 | Verificación: tests + Expo Go + flujo login→inscripción | inline | Pendiente | |
| T11 | S7 | Informe colega entregado (ya redactado) | docs | **Hecho** | 27f68c2 |

---

## Log

- **L1** (petición original del usuario, verbatim): convertir el prototipo en
  app Android descargable real con React Native + Expo; "no quiero que copies
  el html prefiero que generes una apliacion descargable"; "vamos viendo las
  vistas para mejorar la apariencia".
- **L2** (2026-11-13): "son nuevas modalidades que se deberan actualizar al
  backend".
- **L3** (2026-11-13): "el pedido de la actualicacion de backend solo lo
  ahcemos por informe, nosostros no lo modificamos, el colega es encargado de
  BD y backend".
- **L4** (2026-11-13): roles — "eliminaremos el rol de admin en nustra app y
  armaremos un rol padre o tutor"; alumno ve "sus notas trimistrales que
  estaran cargas por materia"; tutor "solo podra ver las notas y asisitencias
  a clases del alumno, no podra incribirse a materias a rendir".
- **L5** (2026-11-13): vínculo — usuario elige **"Código del alumno"**;
  notas/asistencias "está cargado del lado del otro sistema".
- **L6** (2026-11-13): repo — guardar en `github.com/iaprogramaeze-hash`
  (creado `iaprogramaeze-hash/appmexamen`); "luego que este todo terminado y
  funcional subiremos al repositorio original"; copia original → nuevo: hecha
  (mismo `47b1af3`).
- **L7** (2026-11-13): "seria bueno visualizar el frontend para ir viendo las
  partes que debemos hacer y su funcionalidad para la actualizacion de backend
  de pendiendo de los nuevos pedidos" → prototipo abierto + mapa de pantallas
  + informe T11 redactado.
- **L8** (2026-11-13): "estaría eliminar lo que no nos sirve para el proyecto
  que quedó inútil por las nuevas acciones" → commit `79c7cd2` retira mockups
  `docs/prototipo/v2/`, `pantallas.op`, `pantallas-diseno.docx`,
  comparativa vieja, `.rar` de setup, `cloudflare_test.js`,
  `node_modules/` raíz; se conservan `prototipo.html`, formularios fuente,
  `data/materias.csv`, `pront app.txt`, instructivos e informes.
- **L9** (2026-11-13): unidad 1 commiteada (`598d2b4`); preview web resuelto
  (react-dom fijado a 19.3.0, caches de Metro limpiados, cuadriculado
  removido de las 4 mascotas) — usuario: "si se ve la ventana del login";
  reafirma referencia de diseño: "toma como ejemplo la paguina que te pase
  para el diseño del sistema" (shot Dribbble de S10).
- **L10** (2026-11-13): "sigue con las lista de acciones una por una" —
  orden acordado: 1 commit unidad 1 → 2 iteración visual → 3 capa API real →
  4 tests → 5 APK → 6 push/cierre.
- **L15** (2026-11-14): iteración visual Paso 1 aplicada a todas las pantallas
  de acceso y pestañas: mascot con máscara circular (tatu-estudia en acceso,
  mesas-examen/calificaciones/asistencia según pantalla), fondo lavanda con
  gradiente, CTA durazno, tab bar flotante oscuro tipo píldora, nivel y barra
  de progreso en Inicio. Referencia: imágenes de `imagenes/diseño app/`
  (1.webp a 4.webp). `tsc --noEmit` limpio.
- **L16** (2026-11-14): Paso 2 capa API real — creado `mobile/src/api.ts` con
  `fetchMesasDisponibles`, `postInscripcion`, `fetchNotasAlumno`,
  `fetchNotasTutor`, `fetchAsistenciasTutor`. `API_BASE` exportado desde
  `src/auth.tsx`. `tsc --noEmit` limpio. Pendiente: cablear pantallas (Paso 3).
- **L17** (2026-11-14): Paso 3 pantallas vaciadas de datos demo — Inicio,
  Permisos (alumno) y Notas + Asistencias (tutor) quedan como esqueleto visual
  vacío (sin datos inventados, sin llamadas a API). Se conectan al backend
  cuando el colega exponga los endpoints. `tsc --noEmit` limpio.
- **L18** (2026-11-14): Tema oscuro aplicado — referencia `imagenes/diseño app/`
  (5.jpg añadido: inputs pill oscuros, CTA gradiente rosa→azul, links púrpura).
  Actualizado `theme.ts` (paleta oscura #1B0F29/#28263B/#BA98F2/#D14E8A),
  `ui.tsx` (inputs pill oscuros, CTA gradiente, chips púrpura), tab bars
  (activo púrpura), StatusBar `light`. `tsc --noEmit` limpio.
- **L19** (2026-11-14): "hagas las demas pantallas que falta" + "el boton de
  iniciar o crear usuario se deba deslizar" — creado `SlideToConfirm.tsx`
  (Animated + PanResponder, sin deps extra); integrado en Login, Registro
  (pasos 1 y 2) y nueva pantalla Cambiar contraseña. Nuevas pantallas:
  `(alumno)/mesa.tsx` (detalle + inscripción deslizante), `cambiar-password.tsx`
  (raíz, compartida). Navegación: Inicio→mesa (ejemplo), Perfil→cambiar
  contraseña (alumno y tutor). `tsc --noEmit` limpio; Expo bundling OK.
- **L20** (2026-11-14): "utiliza las nuevas imagenes que tienen añadidos neon"
  — las 4 mascotas neon (`imagenes/* neon.webp`) convertidas a PNG con sharp y
  reemplazadas en `mobile/assets/mascots/` (tatu-estudia, mesas-examen,
  calificaciones, asistencia). Bug del SlideToConfirm corregido: PanResponder
  retenía closures viejos de `maxD`/`disabled`/`confirmed` (knob casi no se
  movía) — ahora se leen vía refs + interpolación de translateX para el knob.
  Mascotas agregadas a pantallas que no tenían: Permisos (alumno) y Cambiar
  contraseña. `tsc --noEmit` limpio.
