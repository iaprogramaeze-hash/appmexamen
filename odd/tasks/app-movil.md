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
- Permisos: vista de permisos de examen con **PDF generado en el dispositivo**
  sobre nuestra plantilla (S13); el colega solo aporta las materias
  inscriptas (`GET /mis-inscripciones`).
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

### S11 — Pantalla de Reportes (esqueleto) — 2026-11-16
- Usuario (verbatim): "revisa las pantallas de la app, el login, la de
  eincirpcion a mesas, la de reportes y generar reportes de la incripcion a la
  mesa, la de asistencia y la de notas de la libreta, no todas tiene conexion
  al backend, si no existen creamos la pantalla igual pero dejamos vacia para
  luego agragar lo que nos diga el proveedor del backend, pero si la tenemos en
  frontend para luego aplicarlas".
- Usuario (verbatim): "puedes usar el modelo de lo que estabamos haciendo
  antes, pero modifica segun nuestro nuevo modelo".
- Revisión de las pantallas pedidas: login ✅ cableado; inscripción a mesas ✅
  cableada; asistencia (tutor) ✅ y notas (alumno/tutor) ✅ esqueletos vacíos
  correctos — sin cambios.
- **Reportes no existía** → crear `mobile/app/(alumno)/reportes.tsx` como
  pestaña del grupo alumno: listado vacío + sección "Generar reporte de
  inscripción a la mesa" **sin llamadas a API** (botón deshabilitado con aviso
  de pendiente backend). Estilo: nuevo modelo oscuro, patrón de esqueleto de
  `permisos.tsx`.
- Decisión: una sola pantalla (listado + generación juntos); el acceso
  (`reporte.exportar`, hoy solo staff del backend) se pide al colega en el
  informe T13.

### S12 — Tecnicatura única del alumno y filtro RB-02 — 2026-11-17
- Usuario (verbatim): "la parte de incripcion,listado de materias para mesa de
  examen que esten hablitadas para rendicada una corresponditen a la tecnicatura
  ya especificada en la creacion del usuario, el alumno se incribe …" +
  "una vez que crea el usaurio el alumno, especifica todos sus datos y
  tecnicatura" + "un alumno solo puede tener una tecnicatura".
- RB-02 (`docs/diseno.md`): el alumno solo se inscribe en materias **de su
  propia tecnicatura**; una sola por alumno.
- El registro (paso 1, solo rol alumno) **exige** elegir una de las dos
  tecnicaturas oficiales del catálogo (nombres exactos del seed):
  `TECNOLOGÍA DE LOS ALIMENTOS` | `GESTIÓN ORGANIZACIONAL`.
- La elección se guarda en el dispositivo (`AsyncStorage`
  `perfil.tecnicatura.v1`) porque el snapshot de backend **no** persiste ni
  expone la tecnicatura (`GET /auth/yo` no la trae; `POST /auth/registro` no
  existe). Se pide al colega en el informe T15.
- `GET /mesas-disponibles` devuelve todas las mesas con `orientacion_nombre`;
  la app **filtra en cliente** con igualdad exacta sobre ese snapshot
  (`filtraMesasPorTecnicatura`). Sin tecnicatura → lista vacía + CTA (nunca
  muestra otra carrera).
- Perfil muestra la tecnicatura y permite cambiarla (una sola).
- Filtro de año de Inicio se aplica **encima** del filtro de tecnicatura.

### S13 — Permisos: listado real + PDF pendiente — 2026-11-17
- Usuario (verbatim, aceptación): "si" a "¿Seguamos con el permiso en PDF…?".
- Decisión previa del usuario sobre el PDF: **lo generamos nosotros**; solo
  SIGME se entera de la inscripción (materia + alumno); **no se persiste**
  el permiso ni el archivo (RB-09).
- Pantalla Permisos cableada a `GET /mis-inscripciones`: solo activas
  (`estado !== 'anulado'`), agrupadas **por condición** (RB-18: una condición
  → un permiso; mezcla → dos permisos). Cada grupo muestra materias con
  fecha/hora + botón **"Descargar PDF"** deshabilitado (pendiente endpoint).
- Referencia de generación para el colega: `tools/generar_permiso.py` +
  plantilla `imagenes/Permiso de examen alumno 2026 - A4 - nuevo modelo.pdf`;
  contrato propuesto en informe §8 (`GET /permiso-examen`, `Accept:
  application/pdf`, dueño = sub del JWT, stateless).
- **Corrección del usuario (misma fecha):** "la plantilla nos queda a
  nosotros, el colega no tiene que tener referencia de la plantilla solo en
  que materia se anoto el alumno". El informe §8 deja de pedir endpoint y no
  comparte la plantilla: al colega solo le importa `GET /mis-inscripciones`
  (ya existe). El PDF lo genera la **app** con nuestra plantilla (pendiente
  de cablear el botón con generación local).

---

## Tasks

| ID | S# | Tarea | Ruta | Estado | Commit |
|----|----|-------|------|--------|--------|
| T1 | S1 | Scaffold Expo en `mobile/` + rama `feat/app-movil` | inline | **Hecho** | 598d2b4 |
| T2 | S9 | Capa API (`API_BASE`, cliente auth con token) | inline | **Hecho** (clientes mesas, inscripciones, notas, asistencias en `src/api.ts`) | 598d2b4 |
| T3 | S8 | Pantallas de acceso: Login, Recuperar, Registro | inline | **Hecho** (iteración visual aplicada: mascot con máscara circular en acceso) | 598d2b4 |
| T4 | S2,S8 | Navegación por roles (tabs alumno / tutor) | inline | **Hecho** | 598d2b4 |
| T5 | S8 | Inicio + Inscripción (mesas) | inline | **Hecho**: `GET /mesas-disponibles` + `GET /mis-inscripciones` + `POST /inscripciones` + `GET /convocatoria-vigente` cableados (badge abierta/cerrada); marca "Inscripto" y evita reintentar una inscripción duplicada (6e4b264, 33fedcd, 3deb2e5) | 6e4b264+ |
| T6 | S5,S6 | Pantalla Notas (alumno) | inline | Pendiente de backend: `GET /notas` no existe aún en el snapshot (va en el informe) | 598d2b4 |
| T7 | S8 | Permisos + Perfil (con generar código tutor) | inline | Parcial: cambiar clave y recuperar cableados a `auth/*`; Permisos espera endpoint; código tutor sigue local | |
| T8 | S3,S4,S6 | Pantallas tutor: vínculo, Notas, Asistencias | inline | Notas y Asistencias en esqueleto visual vacío; sin datos de backend | 598d2b4 |
| T9 | S2 | Quitar rastro de admin; menú solo según rol | inline | **Hecho** | 598d2b4 |
| T10 | S1 | Verificación: tests + Expo Go + flujo login→inscripción | inline | Parcial: `npm test` 27/27 y `tsc --noEmit` exit 0 en `mobile/`; bundle Expo 200 OK; falta verificar el flujo login→inscripción con backend real y endpoints de notas/tutor del colega | |
| T11 | S7 | Informe colega entregado (ya redactado) | docs | **Hecho** | 27f68c2 |
| T12 | S11 | Pantalla Reportes (esqueleto) + pestaña grupo alumno | inline | **Hecho**: `app/(alumno)/reportes.tsx` + pestaña en `_layout.tsx` (sin llamadas API) | |
| T13 | S11 | Informe colega consolidado (reportes + pendientes de las pantallas) | docs | **Hecho**: `informes/informe-para-colega-pantallas-app.md` | |
| T14 | S12 | Tecnicatura única en registro + filtro RB-02 en Inicio + Perfil | inline | **Hecho**: `tecnicaturaRules.ts` (7 tests RED→GREEN), `tecnicatura.ts` (AsyncStorage), registro exige y guarda, Inicio filtra, Perfil muestra/cambia | |
| T15 | S12 | Informe al colega: persistir tecnicatura en la cuenta y exponerla | docs | **Hecho** (agregado a `informes/informe-para-colega-pantallas-app.md`) | |
| T16 | S13 | Permisos: listado real por condición (RB-18) + botón PDF pendiente | inline | **Hecho**: `permisoRules.ts` (5 tests RED→GREEN), `permisos.tsx` cableado a `fetchMisInscripciones` | |
| T17 | S13 | Informe §8: contrato PDF stateless con `tools/generar_permiso.py` como referencia | docs | **Hecho y corregido**: el usuario aclaró que plantilla/PDF son nuestros; §8 ya no pide endpoint ni comparte plantilla | |
| T18 | S13 | Generación local del PDF del permiso (plantilla + pdf-lib) y botón activo | inline | **Hecho**: `permisoPdfRules.ts` + `permisoPdf.ts` + `permisoShare.ts` + `identidad.ts`; registro guarda nombre/DNI; botón descarga y comparte; 20 tests nuevos; suite 59/59 | 3f7596c |

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
- **L21** (2026-11-15, verbatim): "necesitos que sigamos con el pryecto de la
  app cosa que sean para despues la dejamos para lo ultimo miestras se pueda
  desarrolar la aplicion, quiero que sigas con las conexion de las api a al
  backend con las cosas que tenemos, y lo demas queda para proximas conexion
  cuando el colega nos provea de las nuevas actualizaciones de backend y base
  de datos, mistra seguimos con lo que tenmos" + "has eso pero si cuelga
  termina el proceso,y seguimos con otra cosa, antes no pasaba eso" (la copia
  local de PostgreSQL se abortó: cluster portable crasheaba con 0xC0000142).
  Hecho: contrato real del snapshot cableado — `login` (`{username, password,
  modulo:'sigme_mobile'}` → `{access, refresh}`), roles vía `GET /auth/yo`,
  `GET /mesas-disponibles`, `GET /mis-inscripciones`, `POST /inscripciones`
  (`{materia_id, condicion_id}`), `GET /convocatoria-vigente`,
  `POST /auth/olvido-clave`, `POST /auth/restablecer-clave`,
  `POST /auth/cambiar-clave` (renueva el access). Corregido bug de contrato:
  el login mandaba `{usuario, password}` y leía `access_token/roles/nombre`
  (no existen). `API_BASE` movido a `src/config.ts` (evita ciclo auth↔api).
  Sesión v2 con `access/refresh/roles/permisos`; demo solo si el backend no
  responde. `tsc --noEmit` limpio; Expo web HTTP 200. Pendiente: Notas,
  Permisos, tutor (endpoints nuevos del colega), tests T10 y APK T9.
- **L22** (2026-11-15): verificación independiente del contrato
  (gentle-ai-verify) sobre `83cca7c`: los 11 endpoints implementados coinciden
  exactos (path, método, body, campos de respuesta, códigos de error).
  Observaciones: los 3 endpoints de notas/tutor siguen pendientes
  (documentado); `isTutor()` espera el rol `tutor` que el informe ya pide al
  colega y que aún no existe en el seed.
- **L23** (2026-11-15): T10 iniciado — suite de contratos del cliente API en
  `mobile/__tests__/api.test.ts` con `jest-expo` (15 tests: URL, método, body
  exacto, bearer, envelope `{code, detail}`, 204 y fallos de red). Script
  `npm test` agregado a `mobile/package.json`. RED demostrado por mutación
  (cambiar `modulo` en el login hace fallar el test) y GREEN tras revertir.
  `npm test` 15/15 y `tsc --noEmit` limpio. Nota: la corrección previa del doc
  con PowerShell lo re-codificó (mojibake); restaurado desde `83cca7c`.
- **L24** (2026-11-15): sesión que expira — `api.ts` reintenta **una sola vez**
  tras un `401` con token, pidiendo un access nuevo a un handler instalado con
  `setRefreshHandler()` (mantiene el módulo sin ciclo con `auth`).
  `AuthProvider` lo registra con `refreshSession()` + `sessionRef` (evita
  closures viejos) y `updateAccess` también usa el ref. 4 tests nuevos (19 en
  total); mutación que desactiva el reintento hace fallar 2 y se revierte.
  `npm test` 19/19 y `tsc --noEmit` limpio.
- **L25** (2026-11-15): Inicio muestra la **convocatoria vigente**
  (`GET /convocatoria-vigente`, hasta ahora el cliente lo tenía sin usar):
  descripción, rango de fechas y badge Abierta/Cerrada, con aviso cuando está
  cerrada. Si ese endpoint falla no se vacía la pantalla (las inscripciones
  propias siguen visibles). +1 test (20 en total). Salud del proyecto
  revisada: `compileall` + `import app.main` del snapshot OK, `.gitignore`
  cubre `.env`/logs/`node_modules`, sin artefactos rastreados, y se pushearon
  `feat/app-movil` y `main` (que tenía el snapshot del backend sin publicar).
- **L26** (2026-11-15): el listado de Inicio marca **Inscripto** cuando la
  materia ya figura en `mis-inscripciones` y pasa el flag a la pantalla de
  detalle, que muestra "Ya estás inscripto" en vez del deslizador (evita el
  intento de doble inscripción). También se unificó el texto de confirmación
  y se corrigió la formatting rota del aviso de demo. `tsc`, 20 tests y bundle
  web OK. El push de `6e4b264` quedó **pendiente de autenticación**: el
  credential helper de Windows se cuelga pidiendo login (sin `gh` ni token).
- **L27** (2026-11-16): verificación del "traslado" a disco `D:\mesas`. Hallazgos:
  el traslado nunca ocurrió: `D:/mesas/.git` es un **worktree enlazado**
  (`gitdir: D:/progamacion/app para inscrpcion a mesa/.git/worktrees/mesas`);
  todo el historial y las ramas viven en el repo viejo, que NO se borra.
  Restaurado el branch `feat/app-movil` en `D:/mesas` (estaba detached: el
  mismo branch no puede estar en dos worktrees, se liberó en el viejo con
  `git switch --detach`). Push de `3deb2e5` hecho tras fijar
  `credential.username=iaprogramaeze-hash` (el push daba 403 porque GCM elegía
  la cuenta vieja `formulariosepetn36-ai` aunque ya tiene ambas guardadas).
  `backend/.venv` recreado en `D:/mesas` (Python 3.14.7, `pip install -e
  ".[dev]"`): 290 tests pytest pasan. `.env` de la raíz (con
  `DATABASE_URL`/claves JWT reales) copiado a la raíz y a `backend/` (ambos
  cubiertos por `.gitignore`); `backend-epet-n36-main/` verificado idéntico al
  `backend/` actual salvo 5 archivos más nuevos en el repo. Queda pendiente el
  APK (no existe ninguno en disco).
- **L28** (2026-11-16): dos arreglos del login pedidos por el usuario. (1) El
  deslizador ya no se completa sin usuario y contraseña: reglas puras en
  `mobile/src/loginRules.ts` (`loginListo` ignora whitespace, `etiquetaSlider`
  informa qué falta), `SlideToConfirm` ahora acepta un `onConfirm` que devuelve
  boolean y **resetea el knob** cuando devuelve `false` o lanza (los otros 4
  usos siguen igual porque solo `false` resetea). RED→GREEN con
  `mobile/__tests__/login-rules.test.ts` (7 tests); `npm test` 27/27 y
  `tsc --noEmit` limpio. (2) La imagen del login tenía un damero gris pintado
  **dentro** del PNG (fuera del círculo): se volvieron transparentes 88.329 px
  con System.Drawing (formato final 32bpp ARGB, 276 KB → 95 KB). Gotcha: GDI+
  guarda el PNG en 24bpp y pierde el alfa si el bitmap se cargó desde el mismo
  archivo; hay que crear el destino en `Format32bppArgb`, dibujar encima y
  guardar a un temporal antes de reemplazar. Metro quedó corriendo en
  `exp://192.168.1.8:8081` (backend apagado, modo demo). (3) El damero salió
  también de las otras 3 mascotas (`mesas-examen`, `calificaciones`,
  `asistencia`): script Python/Pillow con flood-fill desde los bordes (regla
  gris neutro: `max-min <= 14 y 95 <= max <= 185`), verificado con lectura
  visual — 108.216 / 110.269 / 155.809 px transparentes, dibujo intacto.
  Gotcha: PowerShell rompe con `@($x - 1, $y)` (parser lo lee como resta de
  arrays); usar Python, no GDI+.

- **L29** (2026-11-17): análisis completo del proyecto pedido por el usuario
  ("si se bloquea sigue al siguiente y soluciona lo que está mal"). Verde:
  `tsc` exit 0, `npm test` 27/27, backend **290/290** pytest (hay que correrlo
  con workdir `backend/`; desde la raíz del repo da 243 errors — falso
  negativo de imports), bundle Expo 200 OK en 24 s, rama `feat/app-movil`
  sincronizada. Commits de esta tanda: `d273f63` (gate de login) y `2658955`
  (damero de las 4 mascotas). Backend levantado en `0.0.0.0:8000` (uvicorn
  pid 1840) para conectar el frontend después. Sin APK en disco (salteado:
  requiere Android SDK).

- **L30** (2026-11-16, verbatim): "revisa las pantallas de la app, el login,
  la de eincirpcion a mesas, la de reportes y generar reportes de la incripcion
  a la mesa, la de asistencia y la de notas de la libreta, no todas tiene
  conexion al backend, si no existen creamos la pantalla igual pero dejamos
  vacia para luego agragar lo que nos diga el proveedor del backend, pero si la
  tenemos en frontend para luego aplicarlas" + "puedes usar el modelo de lo que
  estabamos haciendo antes, pero modifica segun nuestro nuevo modelo" + "has
  todo hasta hay y luego genera el informe". Revisión: login e inscripción
  cableados OK; asistencia y notas (alumno/tutor) esqueletos vacíos OK.
  Reportes no existía → S11/T12 (pestaña nueva en grupo alumno, esqueleto sin
  API) y T13 (informe consolidado al colega con los 5 endpoints `reportes/*`
  del snapshot + pendientes).
- **L31** (2026-11-16): T12+T13 hechos. Creada `mobile/app/(alumno)/reportes.tsx`
  (esqueleto: listado vacío + "Generar reporte de inscripción" deshabilitado,
  mascot `mesas-examen`, sin llamadas a API) y pestaña **Reportes** en
  `(alumno)/_layout.tsx` (5 tabs: Inicio · Permisos · Notas · Reportes ·
  Perfil, icono `stats-chart-outline`). Copia de UI en registro neutro (sin
  voseo). Informe nuevo `informes/informe-para-colega-pantallas-app.md`:
  verifica los 5 endpoints `reportes/*` del snapshot (gate
  `reporte.exportar`, JSON), pide decisión (a)/(b)/(c) de quién genera
  reportes en la app, formato JSON/PDF, historial, módulo `sigme_mobile` para
  staff, y   reitera los pendientes del informe T11. Verificación: `tsc --noEmit`
  exit 0 y `npm test` 27/27 en `mobile/`. Commit `a60e679`; assessment RDD
  nativo: riesgo **medium** (`executable_change` en `_layout.tsx`),
  `review_due: false` → **under_budget** (slice pendiente, sin review aún).

- **L32** (2026-11-17, verbatim): "la parte de incripcion,listado de materias
  para mesa de examen que esten hablitadas para rendicada una corresponditen a
  la tecnicatura ya especificada en la creacion del usuario, el alumno se
  incribe …" + "cualquier duda me consultas y vamos armando" + "una vez que crea
  el usaurio el alumno, especifica todos sus datos y tecnicatura" + "un alumno
  solo puede tener una tecnicatura". Bloqueo resuelto preguntando de dónde sale
  la tecnicatura: **en el registro**. S12/T14: una sola tecnicatura por alumno
  (RB-02), exigida en el paso 1 del registro (rol alumno), guardada en
  `AsyncStorage` (`perfil.tecnicatura.v1`) y filtrada en Inicio contra
  `orientacion_nombre` de cada mesa (igualdad exacta; sin tecnicatura → lista
  vacía + CTA, nunca otra carrera). Perfil la muestra y permite cambiarla.
  Catálogo fijo de 2 con los nombres del seed (`TECNICATURAS` en
  `tecnicaturaRules.ts`). RED→GREEN con mutación (7 tests en
  `__tests__/tecnicatura-rules.test.ts`); `tsc --noEmit` exit 0 y `npm test`
  34/34. Pendiente del colega (T15): persistir la tecnicatura en la cuenta y
  exponerla en `/auth/yo` para dejar de depender del storage local.

- **L33** (2026-11-17, verbatim): "si" (aceptación a seguir con el permiso en
  PDF). S13/T16-T17: pantalla Permisos cableada — `GET /mis-inscripciones`,
  solo activas, agrupadas por condición (RB-18) con materias fecha/hora y
  botón "Descargar PDF" deshabilitado. Reglas puras en `permisoRules.ts`
  (RED→GREEN por mutación, 5 tests; suite completa 39/39). Informe §8:
  contrato propuesto `GET /permiso-examen` + `Accept: application/pdf`,
  dueño = sub del JWT, stateless, referencia `tools/generar_permiso.py` y
  plantilla A4. `tsc --noEmit` exit 0.
- **L34** (2026-11-17, verbatim): "la plantilla nos queda a nosotros, el
  colega no tiene que tener referencia de la plantilla solo en que materia se
  anoto el alumno". Informe §8 corregido: **no** se pide endpoint de PDF ni se
  comparte la plantilla; solo importa `GET /mis-inscripciones` (materias
  inscriptas), que ya está cableado. El PDF se genera de nuestro lado (app);
  el botón sigue pendiente de la generación local con la plantilla nuestra.
- **L35** (2026-11-17): T18 — generación local del PDF en la app. Port de
  `tools/generar_permiso.py` a TypeScript con `pdf-lib` sobre
  `mobile/assets/permiso-plantilla.pdf` (copia de la plantilla de la escuela;
  no se comparte con el colega). Reglas puras en `permisoPdfRules.ts`
  (mapeo de condiciones al impreso, RB-13, fechas, año desde mesas) y
  armado en `permisoPdf.ts` (blanqueo de bandas fijas + overlay). Identidad
  (nombre/apellido/DNI) se guarda en el registro (`perfil.identidad.v1`) porque
  `/auth/yo` no los trae. Botón **Descargar PDF** activo: genera bytes,
  escribe en caché y abre `expo-sharing` (RB-09: nada se sube ni persiste en
  servidor). Dependencias: `pdf-lib`, `expo-asset`, `expo-file-system`,
  `expo-sharing`. Verificación: `tsc --noEmit` exit 0; `npm test` **59/59**
  (20 tests nuevos: reglas, generación sobre plantilla real, identidad).
  Commit `3f7596c`. Assessment RDD: riesgo **medium**
  (`executable_change` en tests), `review_due: false` → **under_budget**
  (slice pendiente, sin review aún). **Risk: none** en el sentido de la
  lista de alto riesgo del diff (no toca auth, BD, migraciones ni APIs
  públicas del backend; es añadido en la app).

## Pendientes (2026-11-16)

**Nosotros (mobile):**
- [ ] Build del APK: no existe ningún `.apk` en disco. En `mobile/android/`
  quedaron artefactos de builds anteriores (`.cxx/`, `build/intermediates`) sin
  salida final; revisar por qué no terminó (JDK/SDK o `npx expo run:android`).
- [ ] Verificación manual en Expo Go: login → convocatoria → inscripción.
- [ ] Decidir si `D:/mesas` pasa a ser el repo real (mover `.git`) o si se
  sigue trabajando sobre el worktree con el repo viejo como almacén.

**Bloqueado por el colega (backend/BD, informe T11 ya entregado):**
- [ ] `GET /notas` (alumno) → pantalla Notas (T6).
- [ ] `GET /tutor/alumnos/{id}/notas` y `.../asistencias` (T8).
- [ ] Vínculo tutor↔alumno por código del alumno: alta + vínculo + aceptación (S4).
- [ ] Endpoint de Permisos (listado/PDF) (T7).

**Cierre (Paso 6, cuando todo funcione):**
- [ ] Push a `original` (`formulariosepetn36-ai/appmexamen`) — hoy requiere
  credenciales de esa cuenta.
