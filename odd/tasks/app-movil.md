# Feature: App mÃ³vil Android (React Native + Expo)

**Objetivo:** APK descargable real (no HTML) que reemplaza al prototipo web, con
roles alumno y tutor, notas y asistencias. **Rama:** `feat/app-movil` sobre
`main` de `iaprogramaeze-hash/appmexamen`. **Estrategia de entrega:**
`ask-on-risk` (se pide cadena si pasa ~400 lÃ­neas). **Tests:** Jest + React
Testing Library (scaffold Expo); verificaciÃ³n manual en Expo Go / emulator.

**Reparto:** nosotros solo frontend + informe; backend/BD los hace el colega
(`informes/informe-para-colega-modalidades-tutor-notas.md`).

---

## Specs

### S1 â€” Plataforma y repo
- React Native + Expo SDK actual, `minSdk` 24 (Android 7+), APK universal.
- Proyecto nuevo en este repo (carpeta `mobile/`), no se toca `docs/prototipo/`.
- Desarrollo en `origin` = `iaprogramaeze-hash/appmexamen`; al final, push a
  `original` (`formulariosepetn36-ai/appmexamen`).

### S2 â€” Estructura de pantallas (varias, no una sola)
- Usuario: "entonces varias pantallas en ves de una sola seria mejor?"
- Flujo de acceso aparte: Login, Recuperar, Registro.
- Rol alumno con pestaÃ±as: **Inicio** (inscripciÃ³n), **Permisos**,
  **Notas**, **Perfil**.
- Rol tutor con pestaÃ±as: **Notas** (del alumno vinculado),
  **Asistencias**, **Perfil**.
- **Sin panel admin** en la app: "eliminaremos el rol de admin en nustra app".

### S3 â€” Rol tutor / padre
- Usuario: "armaremos un rol padre o tutor".
- El tutor **solo lee**: "el rol a tutor o padre solo podra ver las notas y
  asisitencias a clases del alumno, no podra incribirse a materias a rendir".
- `/auth/yo` con `roles` incluyendo `tutor` â†’ la app ramifica pantallas.

### S4 â€” VÃ­nculo tutor â†” alumno por cÃ³digo del alumno
- Usuario eligiÃ³: **"CÃ³digo del alumno"**.
- Alumno genera cÃ³digo desde **Perfil**; tutor lo ingresa al registrarse o
  desde su Perfil para vincularse.
- El backend implementa el flujo (Â§3.3 del informe); la app solo lo consume.

### S5 â€” Notas trimestrales
- Usuario: "lo nuevo que el alumno podra ver es sus notas trimistrales que
  estaran cargas por materia".
- Alumno: `GET /notas` â€” lista por materia con `trimestre` 1|2|3.
- Tutor: `GET /tutor/alumnos/{id}/notas` solo de alumnos vinculados.
- Los datos **no se cargan en la app**; vienen del otro sistema (SIGME) vÃ­a
  backend: "estÃ¡ cargado del lado del otro sistema".

### S6 â€” Asistencias
- Tutor: `GET /tutor/alumnos/{id}/asistencias`.
- Alumno: `GET /asistencias` solo si el backend lo expone (opcional).

### S7 â€” Backend solo por informe
- Usuario: "el pedido de la actualicacion de backend solo lo hacemos por
  informe, nosotros no lo modificamos, el colega es encargado de BD y backend".
- **Prohibido** editar `backend-epet-n36-main/` en este feature.
- Contratos: `informes/informe-para-colega-modalidades-tutor-notas.md`.

### S8 â€” Pantallas existentes del prototipo a portar
- Login, Recuperar (token por correo), Registro: cablear a los endpoints
  `auth/*` ya probados en el prototipo.
- Inicio + InscripciÃ³n: `GET /mesas-disponibles` + `POST /inscripciones`
  (flujo ya validado en prototipo).
- Permisos: vista de permisos de examen (PDF cuando backend lo exponga;
  por ahora lectura del listado).
- Perfil: datos read-only, cambiar clave, cerrar sesiÃ³n, **generar cÃ³digo de
  tutor** (S4).

### S9 â€” Entorno
- Node OK en la mÃ¡quina; JDK 17 + Android SDK solo si build local de APK;
  desarrollo inicial con **Expo Go** (recarga en el celular).
- `API_BASE` configurable (hoy hardcodeado `http://localhost:8000` en el
  prototipo; en la app: variable de entorno / config).

### S10 â€” Estilo visual (referencia Dribbble)
- Usuario (2026-11-13): "mira el diseÃ±o que nos muestra la siguiente paguina:
  dribbble.com/short/26993647-Kids-Learning-App-UI-Gamified-Education-Internative-Lessons
  y me gustaria que nuestro diseÃ±o se asejado a eso" + "con las imagenes que
  tenemos en el repositorio, pero los vamos biendo como queda".
- DecisiÃ³n de fork: aplicar el estilo **directo en la app Expo** (no en el
  prototipo HTML), iterando pantalla por pantalla.
- DNA del shot: fondos lavanda con gradientes suaves; tarjetas y botones muy
  redondeados; CTA durazno; tab bar flotante oscura tipo pÃ­ldora; un
  personaje ilustrado por tarjeta; estÃ©tica gamificada (nivel, barra de
  progreso, badges tipo `0/5`).
- Paleta del shot: `#C9AEFA`, `#B0B8D7`, `#B6C8D3`, `#9BA2AE`, `#815680`,
  texto `#0A090D`, marrÃ³n `#48303B` (los 7 tags de color del shot).
- ImÃ¡genes del repo como personajes (procesadas a PNG con mÃ¡scara circular):
  `tatu-estudia` â†’ login/inicio, `mesas-examen` â†’ Inicio (inscripciÃ³n),
  `calificaciones` â†’ Notas, `asistencia` â†’ Asistencias (tutor).
- Los textos funcionales no cambian por el estilo (siguen valiendo los de
  S2/S3/S5/S6/S8).

---

## Tasks

| ID | S# | Tarea | Ruta | Estado | Commit |
|----|----|-------|------|--------|--------|
| T1 | S1 | Scaffold Expo en `mobile/` + rama `feat/app-movil` | inline | **Hecho** | 598d2b4 |
| T2 | S9 | Capa API (`API_BASE`, cliente auth con token) | inline | **Hecho** (clientes mesas, inscripciones, notas, asistencias en `src/api.ts`) | 598d2b4 |
| T3 | S8 | Pantallas de acceso: Login, Recuperar, Registro | inline | **Hecho** (iteraciÃ³n visual aplicada: mascot con mÃ¡scara circular en acceso) | 598d2b4 |
| T4 | S2,S8 | NavegaciÃ³n por roles (tabs alumno / tutor) | inline | **Hecho** | 598d2b4 |
| T5 | S8 | Inicio + InscripciÃ³n (mesas) | inline | **Hecho**: `GET /mesas-disponibles` + `GET /mis-inscripciones` + `POST /inscripciones` cableados; demo/errores con estado claro | |
| T6 | S5,S6 | Pantalla Notas (alumno) | inline | Pendiente de backend: `GET /notas` no existe aÃºn en el snapshot (va en el informe) | 598d2b4 |
| T7 | S8 | Permisos + Perfil (con generar cÃ³digo tutor) | inline | Parcial: cambiar clave y recuperar cableados a `auth/*`; Permisos espera endpoint; cÃ³digo tutor sigue local | |
| T8 | S3,S4,S6 | Pantallas tutor: vÃ­nculo, Notas, Asistencias | inline | Notas y Asistencias en esqueleto visual vacÃ­o; sin datos de backend | 598d2b4 |
| T9 | S2 | Quitar rastro de admin; menÃº solo segÃºn rol | inline | **Hecho** | 598d2b4 |
| T10 | S1 | VerificaciÃ³n: tests + Expo Go + flujo loginâ†’inscripciÃ³n | inline | Pendiente | |
| T11 | S7 | Informe colega entregado (ya redactado) | docs | **Hecho** | 27f68c2 |

---

## Log

- **L1** (peticiÃ³n original del usuario, verbatim): convertir el prototipo en
  app Android descargable real con React Native + Expo; "no quiero que copies
  el html prefiero que generes una apliacion descargable"; "vamos viendo las
  vistas para mejorar la apariencia".
- **L2** (2026-11-13): "son nuevas modalidades que se deberan actualizar al
  backend".
- **L3** (2026-11-13): "el pedido de la actualicacion de backend solo lo
  ahcemos por informe, nosostros no lo modificamos, el colega es encargado de
  BD y backend".
- **L4** (2026-11-13): roles â€” "eliminaremos el rol de admin en nustra app y
  armaremos un rol padre o tutor"; alumno ve "sus notas trimistrales que
  estaran cargas por materia"; tutor "solo podra ver las notas y asisitencias
  a clases del alumno, no podra incribirse a materias a rendir".
- **L5** (2026-11-13): vÃ­nculo â€” usuario elige **"CÃ³digo del alumno"**;
  notas/asistencias "estÃ¡ cargado del lado del otro sistema".
- **L6** (2026-11-13): repo â€” guardar en `github.com/iaprogramaeze-hash`
  (creado `iaprogramaeze-hash/appmexamen`); "luego que este todo terminado y
  funcional subiremos al repositorio original"; copia original â†’ nuevo: hecha
  (mismo `47b1af3`).
- **L7** (2026-11-13): "seria bueno visualizar el frontend para ir viendo las
  partes que debemos hacer y su funcionalidad para la actualizacion de backend
  de pendiendo de los nuevos pedidos" â†’ prototipo abierto + mapa de pantallas
  + informe T11 redactado.
- **L8** (2026-11-13): "estarÃ­a eliminar lo que no nos sirve para el proyecto
  que quedÃ³ inÃºtil por las nuevas acciones" â†’ commit `79c7cd2` retira mockups
  `docs/prototipo/v2/`, `pantallas.op`, `pantallas-diseno.docx`,
  comparativa vieja, `.rar` de setup, `cloudflare_test.js`,
  `node_modules/` raÃ­z; se conservan `prototipo.html`, formularios fuente,
  `data/materias.csv`, `pront app.txt`, instructivos e informes.
- **L9** (2026-11-13): unidad 1 commiteada (`598d2b4`); preview web resuelto
  (react-dom fijado a 19.3.0, caches de Metro limpiados, cuadriculado
  removido de las 4 mascotas) â€” usuario: "si se ve la ventana del login";
  reafirma referencia de diseÃ±o: "toma como ejemplo la paguina que te pase
  para el diseÃ±o del sistema" (shot Dribbble de S10).
- **L10** (2026-11-13): "sigue con las lista de acciones una por una" â€”
  orden acordado: 1 commit unidad 1 â†’ 2 iteraciÃ³n visual â†’ 3 capa API real â†’
  4 tests â†’ 5 APK â†’ 6 push/cierre.
- **L15** (2026-11-14): iteraciÃ³n visual Paso 1 aplicada a todas las pantallas
  de acceso y pestaÃ±as: mascot con mÃ¡scara circular (tatu-estudia en acceso,
  mesas-examen/calificaciones/asistencia segÃºn pantalla), fondo lavanda con
  gradiente, CTA durazno, tab bar flotante oscuro tipo pÃ­ldora, nivel y barra
  de progreso en Inicio. Referencia: imÃ¡genes de `imagenes/diseÃ±o app/`
  (1.webp a 4.webp). `tsc --noEmit` limpio.
- **L16** (2026-11-14): Paso 2 capa API real â€” creado `mobile/src/api.ts` con
  `fetchMesasDisponibles`, `postInscripcion`, `fetchNotasAlumno`,
  `fetchNotasTutor`, `fetchAsistenciasTutor`. `API_BASE` exportado desde
  `src/auth.tsx`. `tsc --noEmit` limpio. Pendiente: cablear pantallas (Paso 3).
- **L17** (2026-11-14): Paso 3 pantallas vaciadas de datos demo â€” Inicio,
  Permisos (alumno) y Notas + Asistencias (tutor) quedan como esqueleto visual
  vacÃ­o (sin datos inventados, sin llamadas a API). Se conectan al backend
  cuando el colega exponga los endpoints. `tsc --noEmit` limpio.
- **L18** (2026-11-14): Tema oscuro aplicado â€” referencia `imagenes/diseÃ±o app/`
  (5.jpg aÃ±adido: inputs pill oscuros, CTA gradiente rosaâ†’azul, links pÃºrpura).
  Actualizado `theme.ts` (paleta oscura #1B0F29/#28263B/#BA98F2/#D14E8A),
  `ui.tsx` (inputs pill oscuros, CTA gradiente, chips pÃºrpura), tab bars
  (activo pÃºrpura), StatusBar `light`. `tsc --noEmit` limpio.
- **L19** (2026-11-14): "hagas las demas pantallas que falta" + "el boton de
  iniciar o crear usuario se deba deslizar" â€” creado `SlideToConfirm.tsx`
  (Animated + PanResponder, sin deps extra); integrado en Login, Registro
  (pasos 1 y 2) y nueva pantalla Cambiar contraseÃ±a. Nuevas pantallas:
  `(alumno)/mesa.tsx` (detalle + inscripciÃ³n deslizante), `cambiar-password.tsx`
  (raÃ­z, compartida). NavegaciÃ³n: Inicioâ†’mesa (ejemplo), Perfilâ†’cambiar
  contraseÃ±a (alumno y tutor). `tsc --noEmit` limpio; Expo bundling OK.
- **L20** (2026-11-14): "utiliza las nuevas imagenes que tienen aÃ±adidos neon"
  â€” las 4 mascotas neon (`imagenes/* neon.webp`) convertidas a PNG con sharp y
  reemplazadas en `mobile/assets/mascots/` (tatu-estudia, mesas-examen,
  calificaciones, asistencia). Bug del SlideToConfirm corregido: PanResponder
  retenÃ­a closures viejos de `maxD`/`disabled`/`confirmed` (knob casi no se
  movÃ­a) â€” ahora se leen vÃ­a refs + interpolaciÃ³n de translateX para el knob.
  Mascotas agregadas a pantallas que no tenÃ­an: Permisos (alumno) y Cambiar
  contraseÃ±a. `tsc --noEmit` limpio.
- **L21** (2026-11-15, verbatim): "necesitos que sigamos con el pryecto de la
  app cosa que sean para despues la dejamos para lo ultimo miestras se pueda
  desarrolar la aplicion, quiero que sigas con las conexion de las api a al
  backend con las cosas que tenemos, y lo demas queda para proximas conexion
  cuando el colega nos provea de las nuevas actualizaciones de backend y base
  de datos, mistra seguimos con lo que tenmos" + "has eso pero si cuelga
  termina el proceso,y seguimos con otra cosa, antes no pasaba eso" (la copia
  local de PostgreSQL se abortÃ³: cluster portable crasheaba con 0xC0000142).
  Hecho: contrato real del snapshot cableado â€” `login` (`{username, password,
  modulo:'sigme_mobile'}` â†’ `{access, refresh}`), roles vÃ­a `GET /auth/yo`,
  `GET /mesas-disponibles`, `GET /mis-inscripciones`, `POST /inscripciones`
  (`{materia_id, condicion_id}`), `GET /convocatoria-vigente`,
  `POST /auth/olvido-clave`, `POST /auth/restablecer-clave`,
  `POST /auth/cambiar-clave` (renueva el access). Corregido bug de contrato:
  el login mandaba `{usuario, password}` y leÃ­a `access_token/roles/nombre`
  (no existen). `API_BASE` movido a `src/config.ts` (evita ciclo authâ†”api).
  SesiÃ³n v2 con `access/refresh/roles/permisos`; demo solo si el backend no
  responde. `tsc --noEmit` limpio; Expo web HTTP 200. Pendiente: Notas,
  Permisos, tutor (endpoints nuevos del colega), tests T10 y APK T9.
- **L22** (2026-11-15): verificación independiente del contrato (gentle-ai-verify)
  sobre 83cca7c: los 11 endpoints implementados coinciden exactos (path,
  método, body, campos de respuesta, códigos de error). Observaciones: los 3
  endpoints de notas/tutor siguen pendientes (documentado); isTutor() espera
  el rol tutor que el informe pide al colega y aún no existe en el seed.
