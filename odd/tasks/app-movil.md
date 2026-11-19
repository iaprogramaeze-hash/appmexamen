# Feature: App móvil Android (React Native + Expo)

**Objetivo:** APK descargable real (no HTML) que reemplaza al prototipo web
(rol **tutor** y pestañas **Notas/Reportes** eliminados en L41; el alumno
queda con Inicio · Inscripción a mesas · Permisos · Perfil). **Rama:**
`feat/app-movil` sobre `main` de `iaprogramaeze-hash/appmexamen`.
**Estrategia de entrega:** `ask-on-risk` → **`feature-branch-chain`**
(elegida por el usuario el 2026-11-19: PR tracker draft/no-merge + PRs
hijos encadenados; no se mezclan estrategias). **Tests:** Jest + React
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

### S2 — Estructura de pantallas (varias, no una sola) — actualizada (L41)
- Usuario: "entonces varias pantallas en ves de una sola seria mejor?"
- Flujo de acceso aparte: Login, Recuperar, Registro.
- Rol alumno con pestañas: **Inicio** (inscripción), **Permisos**,
  **Notas**, **Perfil**.
  - **(L41)** Lista final del usuario: "alumnos queda con las siguientes
    pantallas, incripcion a mesas(mesas debe aparecer las mesas de las
    materias segun la tecnicatura, tiene filtrado por el año la materia,
    si es de 1ro,2do,3ro,4to,5to,6to, poder incirbirse como darse de
    baja(solo se de baja si no es el dia de la mesa) genera permiso de
    examen con el pdf que ya tenemos de permiso de examen), inicio,
    perfil, permisos(todos los permiso de examen que se hicieron y vulve
    a generar una copia del permiso si es que el alumno lo requiere)" →
    pestañas **Inicio · Permisos · Perfil**; Inscripción a mesas se entra
    desde la burbuja de Inicio; se eliminan las pestañas **Notas** y
    **Reportes** (archivos borrados; recuperables de git).
- Rol tutor con pestañas: **Notas** (del alumno vinculado),
  **Asistencias**, **Perfil**.
  - **(L41)** "se elimna de creacion de usuari al tutor y sus pantallas" →
    rol tutor **eliminado** (ver S3/S4).
- **Sin panel admin** en la app: "eliminaremos el rol de admin en nustra app".

### S3 — Rol tutor / padre — DESCARTADA (L41)
- Usuario: "armaremos un rol padre o tutor".
- El tutor **solo lee**: "el rol a tutor o padre solo podra ver las notas y
  asisitencias a clases del alumno, no podra incribirse a materias a rendir".
- `/auth/yo` con `roles` incluyendo `tutor` → la app ramifica pantallas.
- **(L41)** "se elimna de creacion de usuari al tutor y sus pantallas" →
  fuera: selector de rol en Registro, carpeta `app/(tutor)/`, entrada de
  Stack, textos de Login. El login siempre va a Inicio de alumno (L40).

### S4 — Vínculo tutor ↔ alumno por código del alumno — DESCARTADA (L41)
- Usuario eligió: **"Código del alumno"**.
- Alumno genera código desde **Perfil**; tutor lo ingresa al registrarse o
  desde su Perfil para vincularse.
- El backend implementa el flujo (§3.3 del informe); la app solo lo consume.
- **(L41)** con el tutor eliminado el código de vinculación no tiene
  destinatario → se quitó el generador de código de Perfil.

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
  de la generación local con la plantilla nuestra).

### S14 — Index/Inicio: hub de accesos a los sectores — 2026-11-19
- Usuario (verbatim, primera descripción): "bueno, vamos a la pantalla de
  index de la app, describo como debe ser y con que tiene que contar, debe
  tener el mismo que la imagen con nombre: 3, de la carpeta: diseño de app,
  esto va a mostra los sectores en las burbujas que se ven, que son
  animadas al precionar , y en ves del marcianito que tiene podrimos poner
  como mascota de esa parte un coatí parado, y si sebe reiniciar tienes el
  permiso y arracamos desde aca no desde una revicion ni nada mas"
- Usuario (verbatim, ampliación): "despues del loguin pasa al index,
  donde debera aparecer los acceso a diferentes sectores: … igual lo vamos
  hacindo juntos, debe tener los estilo que teniene diseño de app y si
  nolo vamos modificando segun el mismo estilo"
- Decisión de entrada (respuesta del usuario): **"Diseño en Inicio"** —
  `app/index.tsx` sigue redirigiendo según sesión como hoy; el hub es la
  pestaña **Inicio** del alumno.
- Los "sectores" eran los **4 accesos** (no las tecnicaturas): Inscripción
  a mesa, Registro de inscripción, Ver mis asistencias, Ver mi libreta.
  Cada burbuja **navega** a su sección al presionarla (con animación de
  press). **L39: el usuario descartó libreta y asistencias → quedan 2
  burbujas** (Inscripción a mesa, Registro de inscripción).
- Estructura (igual que `imagenes/diseño app/3.jpg`): fondo oscuro,
  título arriba centrado ("Tus sectores"), burbujas esféricas grandes en
  zigzag, coatí parado abajo a la derecha en lugar del marcianito, tab
  bar real del grupo alumno (es la pestaña).
- La inscripción actual de Inicio se **mueva** a `(alumno)/inscripcion.tsx`
  (destino de la primera burbuja); Inicio queda como hub puro.
- Estilo (verbatim): "debe tener los estilo que teniene diseño de app y
  si nolo vamos modificando segun el mismo estilo" → todas las pantallas
  nuevas usan el estilo de `imagenes/diseño app/`, iterando con el usuario.
- Checks: `tsc --noEmit`, suite completa, bundle Metro y verificación
  visual en Expo Go. **Excepción de test:** no hay infraestructura de
  render (sin `@testing-library/react-native`, `testMatch` solo `.ts`);
  el resultado es visual y se verifica manualmente.

### S15 — Sección Inscripción a mesa — 2026-11-19
- Usuario (verbatim): "incripcion a mesa(debe mostras la mesas habilitidas
  para rendir con fecha y hora pueda tambien dar de baja la incripcion si
  todavia no es el dia de la mesa, solo segun su Tecnicatura, de otra
  tecnicatura no muestra una vez anotada a todas las materias que se
  inscribio podra bajar el permiso de examen)"
- Muestra las mesas habilitadas para rendir **con fecha y hora** (hoy ya
  se muestra: listado de `GET /mesas-disponibles` filtrado por
  tecnicatura).
- **Dar de baja** la inscripción si todavía no es el día de la mesa →
  acción nueva; el endpoint de baja no existe en el snapshot → UI con
  aviso "pendiente backend" + pedido al colega (patrón de Reportes).
  - **(L41, hecho)** regla pura `puedeDarDeBaja(fecha, hoy)` en
    `src/inscripcionRules.ts` (5 tests RED→GREEN): solo hasta el día
    **anterior** a la mesa; mismo día o después → no. Botón "Dar de baja"
    por inscripción activa en "Mis inscripciones"; si no corresponde se
    muestra el motivo; al presionarlo → aviso honesto de que el endpoint
    sigue pendiente del colega.
- **Solo su tecnicatura**: de otra tecnicatura no muestra nada (RB-02,
  ya implementado con `filtraMesasPorTecnicatura`; se conserva).
- "una vez anotada a todas las materias que se inscribio podra bajar el
  permiso de examen" → el PDF del permiso queda ligado a tener
  inscripciones; regla exacta de "todas" a confirmar con el usuario.
  - **(L41, hecho)** en Inscripción se agregó **"Generar permiso ·
    {condición}"** por grupo de inscripciones activas, con el mismo flujo
    PDF en dispositivo que Permisos (extraído a `src/permisoFlow.ts`,
    una sola dueña; RB-09: nunca se sube al servidor).

### S16 — Sección Registro de inscripción — 2026-11-19
- Usuario (verbatim): "registro de inscripccion a mesa(podra ver el
  registro de incripcion donde tiene para poder descargar de nuevo el pdf
  de la incripcion a la mesa)"
- Ve el **registro** de sus inscripciones y puede **descargar de nuevo**
  el PDF de la inscripción a la mesa.
- Hoy la pantalla Permisos ya lista las inscripciones agrupadas y tiene
  "Descargar PDF" (T18) → primera versión: la burbuja abre esa pantalla;
  si el usuario quiere una pantalla propia, se separa (T21).

### S17 — Sección Ver mis asistencias — 2026-11-19 — DESCARTADA (L39)
- Usuario (verbatim): "ver mi asitencias(podra ver un calendario con
  todos los dias que asistio y que dias faltoy en la parte superior podra
  ver la cantidad de faltas acumuladas)"
- **Parte superior**: cantidad de **faltas acumuladas**.
- **Calendario** con los días que asistió y los que faltó.
- Backend pendiente (`GET /asistencias`, S6/T8) → pantalla con la UI
  (contador + calendario + leyenda) en esqueleto sin datos, aviso de
  pendiente.

### S18 — Sección Ver mi libreta — 2026-11-19 — DESCARTADA (L39)
- Usuario (verbatim): "ver mi libreta(podra ver sus notas trimstrales por
  materias, segun tecnicatura y año que este el alumno)"
- Notas **trimestrales** por materia, según la tecnicatura y el año del
  alumno.
- Es la pantalla Notas existente (T6): esqueleto ya creado, pendiente de
  `GET /notas`; la burbuja la abre y se le suman filtros de
  tecnicatura/año cuando haya datos (T23).

---

## Tasks

| ID | S# | Tarea | Ruta | Estado | Commit |
|----|----|-------|------|--------|--------|
| T1 | S1 | Scaffold Expo en `mobile/` + rama `feat/app-movil` | inline | **Hecho** | 598d2b4 |
| T2 | S9 | Capa API (`API_BASE`, cliente auth con token) | inline | **Hecho** (clientes mesas, inscripciones, notas, asistencias en `src/api.ts`) | 598d2b4 |
| T3 | S8 | Pantallas de acceso: Login, Recuperar, Registro | inline | **Hecho** (iteración visual aplicada: mascot con máscara circular en acceso) | 598d2b4 |
| T4 | S2,S8 | Navegación por roles (tabs alumno / tutor) | inline | **Hecho** (ramificación de tutor eliminada en L40/L41: solo quedan tabs alumno) | 598d2b4 |
| T5 | S8 | Inicio + Inscripción (mesas) | inline | **Hecho**: `GET /mesas-disponibles` + `GET /mis-inscripciones` + `POST /inscripciones` + `GET /convocatoria-vigente` cableados (badge abierta/cerrada); marca "Inscripto" y evita reintentar una inscripción duplicada (6e4b264, 33fedcd, 3deb2e5) | 6e4b264+ |
| T6 | S5,S6 | Pantalla Notas (alumno) | inline | Pendiente de backend: `GET /notas` no existe aún en el snapshot (va en el informe); **pestaña/archivo eliminados (L41)** | 598d2b4 |
| T7 | S8 | Permisos + Perfil (con generar código tutor) | inline | Parcial: cambiar clave y recuperar cableados a `auth/*`; **código tutor eliminado (L41)** | |
| T8 | S3,S4,S6 | Pantallas tutor: vínculo, Notas, Asistencias | inline | **Eliminada (L41)**: carpeta `app/(tutor)/` borrada junto con el rol | 598d2b4 |
| T9 | S2 | Quitar rastro de admin; menú solo según rol | inline | **Hecho** | 598d2b4 |
| T10 | S1 | Verificación: tests + Expo Go + flujo login→inscripción | inline | Parcial: `npm test` 27/27 y `tsc --noEmit` exit 0 en `mobile/`; bundle Expo 200 OK; falta verificar el flujo login→inscripción con backend real y endpoints de notas/tutor del colega | |
| T11 | S7 | Informe colega entregado (ya redactado) | docs | **Hecho** | 27f68c2 |
| T12 | S11 | Pantalla Reportes (esqueleto) + pestaña grupo alumno | inline | **Hecho** y luego **pestaña/archivo eliminados (L41)** (la pantalla sigue en git) | |
| T13 | S11 | Informe colega consolidado (reportes + pendientes de las pantallas) | docs | **Hecho**: `informes/informe-para-colega-pantallas-app.md` | |
| T14 | S12 | Tecnicatura única en registro + filtro RB-02 en Inicio + Perfil | inline | **Hecho**: `tecnicaturaRules.ts` (7 tests RED→GREEN), `tecnicatura.ts` (AsyncStorage), registro exige y guarda, Inicio filtra, Perfil muestra/cambia | |
| T15 | S12 | Informe al colega: persistir tecnicatura en la cuenta y exponerla | docs | **Hecho** (agregado a `informes/informe-para-colega-pantallas-app.md`) | |
| T16 | S13 | Permisos: listado real por condición (RB-18) + botón PDF pendiente | inline | **Hecho**: `permisoRules.ts` (5 tests RED→GREEN), `permisos.tsx` cableado a `fetchMisInscripciones` | |
| T17 | S13 | Informe §8: contrato PDF stateless con `tools/generar_permiso.py` como referencia | docs | **Hecho y corregido**: el usuario aclaró que plantilla/PDF son nuestros; §8 ya no pide endpoint ni comparte plantilla | |
| T18 | S13 | Generación local del PDF del permiso (plantilla + pdf-lib) y botón activo | inline | **Hecho**: `permisoPdfRules.ts` + `permisoPdf.ts` + `permisoShare.ts` + `identidad.ts`; registro guarda nombre/DNI; botón descarga y comparte; 20 tests nuevos; suite 59/59 | 3f7596c |
| T19 | S14 | Hub Inicio: 2 burbujas (estilo imagen 3 + coatí + animación bob), mueve el listado a `inscripcion.tsx`, destinos de las burbujas | inline | **Hecho** (burbujas centradas + bob con delay escalonado, L40; verificado tsc + tests + export) | `2fdac24` |
| T20 | S15 | Inscripción: botón "dar de baja" (pendiente backend) + regla del permiso de examen | inline | **Hecho (UI + regla + PDF en Inscripción)**: `inscripcionRules.ts` (5 tests RED→GREEN), botón "Dar de baja" con motivo cuando no corresponde, aviso de endpoint pendiente; botones "Generar permiso · {condición}" vía `permisoFlow.ts`; **el endpoint de baja sigue pendiente del colega** | `2fdac24` |
| T21 | S16 | Registro de inscripción: pantalla/destino propio + re-descarga del PDF | inline | Pendiente (v1: burbuja → Permisos) | |
| T22 | S17 | Mis asistencias: contador de faltas + calendario (esqueleto hasta `GET /asistencias`) | inline | **Descartada (L39)** (esqueleto creado y borrado) | |
| T23 | S18 | Mi libreta: burbuja → Notas + filtros tecnicatura/año cuando haya backend | inline | **Descartada (L39)** | |
| T24 | S2,S3,S4 | Recorte de pantallas (L41): eliminar tutor completo y podar tabs a Inicio · Permisos · Perfil | inline | **Hecho**: borrados `app/(tutor)/` (4 archivos), `notas.tsx`, `reportes.tsx`; sin selector de rol en Registro; sin código de tutor en Perfil; textos de Login/Perfil actualizados; `Stack.Screen "(tutor)"` fuera | `2fdac24` |

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

- **L36** (2026-11-19, verbatim): "bueno, vamos a la pantalla de index de
  la app, describo como debe ser y con que tiene que contar, debe tener el
  mismo que la imagen con nombre: 3, de la carpeta: diseño de app, esto va
  a mostra los sectores en las burbujas que se ven, que son animadas al
  precionar , y en ves del marcianito que tiene podrimos poner como mascota
  de esa parte un coatí parado, y si sebe reiniciar tienes el permiso y
  arracamos desde aca no desde una revicion ni nada mas". Pregunta de
  entrada (el index hoy es un salto automático según sesión): el usuario
  eligió **"Diseño en Inicio"** → S14/T19: el index no se toca; el diseño
  de `imagenes/diseño app/3.jpg` pasa a la pestaña Inicio del alumno con
  las burbujas de los 2 sectores (`TECNICATURAS`), animación al presionar
  y coatí parado; la inscripción actual queda debajo en el mismo scroll.
  Sin reinicio de OpenCode: el generador de imágenes gratuito por HTTP
  (Pollinations) ya funciona sin MCP.

- **L37** (2026-11-19, verbatim): "despues del loguin pasa al index,
  donde debera aparecer los acceso a diferentes sectores: incripcion a
  mesa(debe mostras la mesas habilitidas para rendir con fecha y hora
  pueda tambien dar de baja la incripcion si todavia no es el dia de la
  mesa, solo segun su Tecnicatura, de otra tecnicatura no muestra una vez
  anotada a todas las materias que se inscribio podra bajar el permiso de
  examen),registro de inscripccion a mesa(podra ver el registro de
  incripcion donde tiene para poder descargar de nuevo el pdf de la
  incripcion a la mesa), ver mi asitencias(podra ver un calendario con
  todos los dias que asistio y que dias faltoy en la parte superior podra
  ver la cantidad de faltas acumuladas), ver mi libreta(podra ver sus
  notas trimstrales por materias, segun tecnicatura y año que este el
  alumno). igual lo vamos hacindo juntos, debe tener los estilo que teniene
  diseño de app y si nolo vamos modificando segun el mismo estilo".
  Cambia el alcance de S14: los "sectores" de las burbujas son los **4
  accesos** (no las tecnicaturas) y presionar **navega** a cada sección →
  S14 reescrito + S15-S18 nuevos; T19 reabierto y T20-T23 creados.

- **L38** (2026-11-19, verbatim): "al parecer, no vamos a implentar lo de
  libreta y asistencias, pero si ya hiciste un modelo de fronted mustrme
  antes de sacarlo". Señal de cambio de alcance en S17/S18 (T22/T23):
  probablemente **no** se implementen libreta ni asistencias; el usuario
  pide **ver el modelo de frontend antes de quitarlo**. No se elimina nada
  todavía: Metro levantado (`exp://192.168.0.64:8081`) para la revisión
  visual del hub + pantalla de asistencias (esqueleto) + Notas (libreta,
  esqueleto preexistente). Queda pendiente el veredicto del usuario.

- **L39** (2026-11-19, verbatim): "la sacamos, pero las demas no se ven ni
  la pantala de las burbujas, que paso ?". Decisión: **se sacan del hub las
  burbujas de libreta y asistencias** (S17/S18 → descartadas; T22/T23 →
  descartadas; el hub queda con 2 burbujas: Inscripción a mesa y Registro
  de inscripción). Seguido de (verbatim): "por favor resuelve porque no se
  ven las pantallas, pero infroma cada 2 minutos, despues caundo se ve
  enalazamos con el backend" → prioridad: que el usuario **vea** las
  pantallas en Expo Go; el enlace con el backend queda para después.
  Diagnóstico de la incidencia: el celular sí conectó (log de Metro:
  "Android Bundled 6525ms") pero la app mostraba **Login** (sesión
  vencida), y Metro corría en **modo CI** (sin Fast Refresh) →
  reiniciado en modo normal; backend levantado en :8000 para el login
  real.

- **L40** (2026-11-19, verbatim): "el login tiene que terner conexion con
  el inicio de Alumno, ya que eliminamos tutor, y las 2 burbujas mejora el
  texto en el medio y con movimento de burbuja". Acción: (1) `index.tsx` ya
  no ramifica por rol — toda sesión autenticada cae en `/(alumno)`
  (Inicio); (2) `SectorBubble` con el texto **al centro** de la esfera y
  **movimiento de burbuja** (bob vertical con delay escalonado por burbuja,
  driver nativo; el press sigue funcionando). Verificación: `tsc` OK y
  59/59. **Aclaración con evidencia:** el tutor NO estaba eliminado en el
  código (4 pantallas en `app/(tutor)/`, selector "Soy tutor / padre" en
  Registro, texto en Login, `Stack.Screen "(tutor)"`) — solo se quitó la
  ramificación del login; queda pendiente la decisión de eliminarlo por
  completo.

- **L41** (2026-11-19, verbatim): "y alumnos queda con las siguientes
  pantallas, incripcion a mesas(mesas debe aparecer las mesas de las
  materias segun la tecnicatura, tiene filtrado por el año la materia,
  si es de 1ro,2do,3ro,4to,5to,6to, poder incirbirse como darse de
  baja(solo se de baja si no es el dia de la mesa) genera permiso de
  examen con el pdf que ya tenemos de permiso de examen, inicio, perfil,
  permisos(todos los permiso de examen que se hicieron y vulve a generar
  una copia del permiso si es que el alumno lo requiere). se elimna de
  creacion de usuari al tutor y sus pantallas. luego de logearse debe ir
  a la pantalla de incio del alumno, donde con las bubujas podra elegir
  la siguiente pantalla". Acciones: (1) **tutor eliminado completo**
  (S3/S4 descartadas): carpeta `app/(tutor)/` borrada, selector de rol
  fuera de Registro (siempre alumno + tecnicatura obligatoria), código de
  tutor fuera de Perfil, `Stack.Screen "(tutor)"` fuera, textos de Login
  actualizados; (2) **tabs del alumno podadas** a Inicio · Permisos ·
  Perfil (S2): fuera `notas.tsx` y `reportes.tsx` (lista final del
  usuario: "alumnos queda con las siguientes pantallas, incripcion a
  mesas... inicio, perfil, permisos"); (3) **Inscripción**: regla de
  baja `puedeDarDeBaja` (RED→GREEN, 5 tests: solo hasta el día anterior
  a la mesa), botón "Dar de baja" con aviso de endpoint pendiente, y
  botones **"Generar permiso · {condición}"** con el PDF que ya
  tenemos (flujo extraído a `src/permisoFlow.ts`, compartido con
  Permisos); (4) Permisos ya cubre "todos los permisos + volver a
  generar una copia" (botón activo, T18); (5) login → Inicio ya estaba
  (L40). Verificación: `tsc` OK y **64/64 tests**.

- **L42** (2026-11-19): decisión de entrega — al superar la rama las
  ~400 líneas (estrategia `ask-on-risk`), el usuario eligió
  **`feature-branch-chain`**: PR tracker draft/no-merge en
  `feat/app-movil` + PRs hijos encadenados cuando toque entregar;
  registrado en el encabezado (no se mezclan estrategias).

## Pendientes (2026-11-16)

**Nosotros (mobile):**
- [ ] Build del APK: no existe ningún `.apk` en disco. En `mobile/android/`
  quedaron artefactos de builds anteriores (`.cxx/`, `build/intermediates`) sin
  salida final; revisar por qué no terminó (JDK/SDK o `npx expo run:android`).
- [ ] Verificación manual en Expo Go: login → convocatoria → inscripción.
- [ ] Decidir si `D:/mesas` pasa a ser el repo real (mover `.git`) o si se
  sigue trabajando sobre el worktree con el repo viejo como almacén.

**Bloqueado por el colega (backend/BD, informe T11 ya entregado):**
- [ ] Endpoint de **baja de inscripción** (S15/T20): la app ya tiene la
  regla y el botón con aviso; falta que el colega exponga la baja.
- [ ] Persistir la **tecnicatura** en la cuenta y exponerla en `/auth/yo`
  (T15) — hoy vive en el dispositivo.
- [x] ~~`GET /notas` / endpoints de tutor~~ → **cancelado (L41)**: se
  eliminaron la libreta (L39) y el rol tutor (S3/S4).
- [x] ~~Endpoint de Permisos~~ → **resuelto (T18)**: el PDF se genera en
  el dispositivo; solo hace falta `GET /mis-inscripciones` (ya existe).

**Cierre (Paso 6, cuando todo funcione):**
- [ ] Push a `original` (`formulariosepetn36-ai/appmexamen`) — hoy requiere
  credenciales de esa cuenta.
