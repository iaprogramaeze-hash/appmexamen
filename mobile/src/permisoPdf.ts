/**
 * Exam-permit PDF builder — fills our school template (RB-09: generated
 * on device, never uploaded). Port of `tools/generar_permiso.py`.
 *
 * Strategy (same as the Python tool, via pdf-lib):
 *   1. load the template bytes;
 *   2. white-out fixed copy-1 text (title, condition options, paragraph
 *      lines 3–4, date) and copies 2–3;
 *   3. draw the real values with Helvetica-Bold.
 *
 * Pure logic lives in `permisoPdfRules`; this module only does I/O-free
 * PDF assembly so tests can run under Node/jest.
 */
import { PDFDocument, StandardFonts, rgb, type PDFFont, type PDFPage } from 'pdf-lib';

import {
  MAX_MATERIAS_PERMISO,
  fechaEmisionTexto,
  materiasParaImpreso,
  mapearCondicionImpreso,
  tituloAlumno,
  validarDatosPermiso,
  type CondicionImpreso,
  type DatosPermisoPdf,
} from './permisoPdfRules';

// --- Template geometry (points; origin bottom-left) -------------------------
const FONT_KEY = 'Helvetica-Bold';

const BLANQUEOS: readonly (readonly [number, number, number, number])[] = [
  // Copies 2 + 3 (everything below copy 1's bottom rule at y≈520.53).
  [0, 0, 612, 520.4],
  [17, 520.4, 1, 1.2],
];

/** Bands of copy 1 whose fixed text is rewritten: [y, height, x, width]. */
const BANDAS: readonly (readonly [number, number, number, number])[] = [
  // Title row (template text sits ~745–753).
  [743.5, 12, 0, 612],
  // Condition options (keep rótulo at x < 48, y 697–698).
  [679, 33, 48, 217],
  // Paragraph lines 3–4 (year + career).
  [626, 4, 19, 246],
  [614, 4, 19, 246],
  // Emission date line.
  [566, 5, 19, 548],
];

const CONDICIONES_IMPRESO: readonly CondicionImpreso[] = [
  'regular',
  'previa',
  'completar_estudio',
  'equivalencia',
];

const CONDICION_LABELS: Record<CondicionImpreso, string> = {
  regular: 'REGULAR',
  previa: 'PREVIAS',
  completar_estudio: 'COMPLETAR ESTUDIO',
  equivalencia: 'EQUIVALENCIA',
};

// Wingdings GID-134 metrics (em) — hollow square used as checkbox.
const BOX_LADO = 1480 / 2048;
const BOX_X = 173 / 2048;
const BOX_AVANCE = 1911 / 2048;

const X_CONDICION = 48;
const Y_CONDICION = 697.4;

const COL_ASIG: readonly [number, number] = [368.5, 437.8];
const COL_FECHA: readonly [number, number] = [437.8, 472.4];
const FILAS_Y = [668.6, 652.4, 636.1, 620.0, 603.8, 587.5] as const;

const BLACK = rgb(0, 0, 0);
const WHITE = rgb(1, 1, 1);

function ajustarFs(
  texto: string,
  fs: number,
  anchoMax: number,
  font: PDFFont,
  fsMin = 3.5,
): number {
  while (fs > fsMin && font.widthOfTextAtSize(texto, fs) > anchoMax) {
    fs -= 0.1;
  }
  return fs;
}

function dibujarIzq(
  page: PDFPage,
  font: PDFFont,
  x: number,
  y: number,
  texto: string,
  fs: number,
  anchoMax: number,
  fsMin = 3.5,
): void {
  const size = ajustarFs(texto, fs, anchoMax, font, fsMin);
  page.drawText(texto, { x, y, size, font, color: BLACK });
}

function dibujarCentrado(
  page: PDFPage,
  font: PDFFont,
  x0: number,
  x1: number,
  y: number,
  texto: string,
  fs: number,
  anchoInterno = 4,
): void {
  const size = ajustarFs(texto, fs, x1 - x0 - anchoInterno, font);
  const w = font.widthOfTextAtSize(texto, size);
  const x = (x0 + x1) / 2 - w / 2;
  page.drawText(texto, { x, y, size, font, color: BLACK });
}

function blanquear(page: PDFPage): void {
  for (const [x, y, w, h] of [...BLANQUEOS, ...BANDAS]) {
    page.drawRectangle({ x, y, width: w, height: h, color: WHITE });
  }
}

function dibujarTitulo(page: PDFPage, font: PDFFont, condicion: string): void {
  const texto = `PERMISO DE EXAMEN - Alumno ${tituloAlumno(condicion)}`;
  const size = ajustarFs(texto, 10.8, 460, font);
  const w = font.widthOfTextAtSize(texto, size);
  page.drawText(texto, { x: 284.35 - w / 2, y: 749, size, font, color: BLACK });
}

function dibujarCondicion(
  page: PDFPage,
  font: PDFFont,
  condicion: string,
): void {
  const mapped = mapearCondicionImpreso(condicion);
  // Unknown label (e.g. `Libre`): keep rótulo, print the raw name only.
  if (!mapped) {
    dibujarIzq(
      page,
      font,
      X_CONDICION,
      Y_CONDICION,
      `: ${condicion.trim()}`,
      6,
      264.4 - X_CONDICION,
      4.4,
    );
    return;
  }

  type Pieza =
    | { k: 't'; t: string; idx: number | null }
    | { k: 'b'; idx: number };
  const piezas: Pieza[] = [
    { k: 't', t: `: ${CONDICION_LABELS[CONDICIONES_IMPRESO[0]]}`, idx: 0 },
    { k: 't', t: ' ', idx: null },
    { k: 'b', idx: 0 },
  ];
  for (let i = 1; i < CONDICIONES_IMPRESO.length; i++) {
    piezas.push({ k: 't', t: '   - ', idx: null });
    piezas.push({
      k: 't',
      t: CONDICION_LABELS[CONDICIONES_IMPRESO[i]],
      idx: i,
    });
    piezas.push({ k: 't', t: ' ', idx: null });
    piezas.push({ k: 'b', idx: i });
  }

  const disponible = 264.4 - X_CONDICION;
  const ancho0 = piezas.reduce((sum, p) => {
    if (p.k === 'b') return sum + 6 * BOX_AVANCE;
    return sum + font.widthOfTextAtSize(p.t, 6);
  }, 0);
  let fs = 6;
  if (ancho0 > disponible) {
    fs = Math.max(4.4, (6 * disponible) / ancho0);
  }

  const activo = CONDICIONES_IMPRESO.indexOf(mapped);
  let x = X_CONDICION;
  const y = Y_CONDICION;
  for (const p of piezas) {
    if (p.k === 'b') {
      const lado = fs * BOX_LADO;
      const bx = x + fs * BOX_X;
      page.drawRectangle({
        x: bx,
        y,
        width: lado,
        height: lado,
        borderColor: BLACK,
        borderWidth: Math.max(0.35, fs * 0.09),
        color: p.idx === activo ? BLACK : undefined,
      });
      x += fs * BOX_AVANCE;
    } else {
      page.drawText(p.t, { x, y, size: fs, font, color: BLACK });
      x += font.widthOfTextAtSize(p.t, fs);
    }
  }
}

function dibujarParrafo(
  page: PDFPage,
  font: PDFFont,
  anio: string,
  carrera: string,
): void {
  const lineas: readonly [number, string][] = [
    [627.4, `correspondientes a: ${anio}° año de`],
    [615.4, `${carrera}, que se indican a`],
  ];
  const anchoMax = 264.4 - 19.4;
  const peor = Math.max(
    ...lineas.map(([, t]) => font.widthOfTextAtSize(t, 9.8)),
  );
  const fs = peor <= anchoMax ? 9.8 : Math.max(4, (9.8 * anchoMax) / peor);
  for (const [y, texto] of lineas) {
    page.drawText(texto, { x: 19.4, y, size: fs, font, color: BLACK });
  }
}

function dibujarTabla(
  page: PDFPage,
  font: PDFFont,
  materias: readonly { nombre: string; fecha: string }[],
): void {
  for (let i = 0; i < FILAS_Y.length && i < materias.length; i++) {
    const item = materias[i];
    const y = FILAS_Y[i];
    dibujarCentrado(page, font, COL_ASIG[0], COL_ASIG[1], y, item.nombre, 6.6, 1.5);
    dibujarCentrado(page, font, COL_FECHA[0], COL_FECHA[1], y, item.fecha, 6.6, 1.5);
  }
}

/**
 * Builds a one-sheet permit PDF from template bytes.
 * Returns the finished PDF as bytes (caller writes/shares; nothing is stored).
 */
export async function generarPermisoPdf(
  datos: DatosPermisoPdf,
  plantilla: Uint8Array,
): Promise<Uint8Array> {
  validarDatosPermiso(datos);
  if (datos.materias.length > MAX_MATERIAS_PERMISO) {
    // Defensive: validar already checked; keeps the cap visible at the call site.
    throw new Error(`RB-13: máximo ${MAX_MATERIAS_PERMISO} materias.`);
  }

  const pdf = await PDFDocument.load(plantilla);
  const page = pdf.getPage(0);
  const font = await pdf.embedFont(StandardFonts.HelveticaBold);

  blanquear(page);
  dibujarTitulo(page, font, datos.condicion);
  if (datos.alumno) {
    dibujarIzq(page, font, 125.6, 724, datos.alumno.trim(), 6.6, 333.9 - 125.6 - 2);
  }
  if (datos.dni) {
    dibujarIzq(page, font, 373.1, 723, datos.dni.trim(), 6.6, 516.4 - 373.1 - 2);
  }
  dibujarCondicion(page, font, datos.condicion);
  dibujarParrafo(page, font, datos.anio, datos.carrera.trim());
  dibujarIzq(
    page,
    font,
    19.2,
    568,
    fechaEmisionTexto(datos.fechaEmision),
    8.6,
    567.2 - 19.2 - 2,
  );
  dibujarTabla(page, font, materiasParaImpreso(datos.materias));

  pdf.setTitle(`PERMISO DE EXAMEN - Alumno ${tituloAlumno(datos.condicion)}`);
  pdf.setAuthor('E.P.E.T. N° 36 - Posadas, Misiones');
  pdf.setSubject('Permiso de Examen');

  return pdf.save();
}

export { FONT_KEY };
