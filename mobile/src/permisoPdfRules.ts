/**
 * Pure helpers to build the exam-permit PDF (RB-09: never persisted).
 *
 * Port of the critical rules from `tools/generar_permiso.py` (ours — the
 * colleague never sees the template): condition mapping, RB-13 row cap,
 * date formatting, and the data shape the overlay needs.
 */

/** Backend / UI condition labels → keys of the printed form (D7). */
export type CondicionImpreso =
  | 'regular'
  | 'previa'
  | 'completar_estudio'
  | 'equivalencia';

/** RB-13: max subjects printed per permit sheet. */
export const MAX_MATERIAS_PERMISO = 6;

export type MateriaPermiso = {
  nombre: string;
  /** ISO date `YYYY-MM-DD` (mesa fecha) or already-formatted `DD/MM/YYYY`. */
  fecha: string;
};

export type DatosPermisoPdf = {
  /** Display name, preferably `APELLIDO, NOMBRE`. */
  alumno: string;
  dni: string;
  /** Raw condition label from the group (`Regular`, `Previas`, …). */
  condicion: string;
  carrera: string;
  /** Year as `1`..`6`; empty string omits the number (still prints `° año`). */
  anio: string;
  materias: readonly MateriaPermiso[];
  /** Overrides "today" for tests. */
  fechaEmision?: Date;
};

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
] as const;

/**
 * Maps a condition label from the API/UI onto the four printed options.
 * Returns null when the label is not on the form (e.g. seed `Libre`).
 */
export function mapearCondicionImpreso(nombre: string): CondicionImpreso | null {
  const n = nombre.trim().toLowerCase();
  if (n === 'regular') return 'regular';
  if (n === 'previa' || n === 'previas') return 'previa';
  if (n === 'completar estudio' || n === 'completar estudios') {
    return 'completar_estudio';
  }
  if (n === 'equivalencia') return 'equivalencia';
  return null;
}

/** Title fragment after "PERMISO DE EXAMEN - Alumno …". */
export function tituloAlumno(condicion: string): string {
  const mapped = mapearCondicionImpreso(condicion);
  const fallback: Record<CondicionImpreso, string> = {
    regular: 'Regular',
    previa: 'Previas',
    completar_estudio: 'Completar Estudio',
    equivalencia: 'Equivalencia',
  };
  if (mapped) return fallback[mapped];
  return condicion.trim() || '—';
}

/** `2026-12-15` → `15/12/2026`; passes through non-ISO values. */
export function fechaMesaTexto(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!m) return iso;
  const [, y, mo, d] = m;
  return `${d}/${mo}/${y}`;
}

/** Emission line: `17 de noviembre de 2026.` */
export function fechaEmisionTexto(fecha: Date = new Date()): string {
  const mes = MESES[fecha.getMonth()];
  return `${fecha.getDate()} de ${mes} de ${fecha.getFullYear()}.`;
}

/** Extracts the bare year from `curso_nombre` (`3er Año` → `3`). */
export function anioDeCurso(cursoNombre: string): string {
  const m = /(\d+)/.exec(cursoNombre);
  return m ? m[1] : '';
}

/**
 * Validates the payload before touching pdf-lib.
 * Throws `Error` with a Spanish message the UI can show as-is.
 */
export function validarDatosPermiso(datos: DatosPermisoPdf): void {
  if (!datos.alumno.trim()) throw new Error('Falta el nombre del alumno.');
  if (!datos.dni.trim()) throw new Error('Falta el D.N.I. del alumno.');
  if (!datos.carrera.trim()) throw new Error('Falta la tecnicatura.');
  if (!datos.condicion.trim()) throw new Error('Falta la condición.');
  if (!datos.materias.length) {
    throw new Error('El permiso no tiene materias.');
  }
  if (datos.materias.length > MAX_MATERIAS_PERMISO) {
    throw new Error(
      `RB-13: máximo ${MAX_MATERIAS_PERMISO} materias por permiso (hay ${datos.materias.length}).`,
    );
  }
  for (const m of datos.materias) {
    if (!m.nombre.trim()) throw new Error('Materia sin nombre.');
  }
}

/** Normalizes materias for the overlay (fecha already `DD/MM/YYYY`). */
export function materiasParaImpreso(
  materias: readonly MateriaPermiso[],
): MateriaPermiso[] {
  return materias.slice(0, MAX_MATERIAS_PERMISO).map((m) => ({
    nombre: m.nombre.trim(),
    fecha: fechaMesaTexto(m.fecha),
  }));
}

/**
 * Resolves `anio` for the permit by matching an enrollment against the
 * live mesa list (`curso_nombre` snapshot). Empty when nothing matches.
 */
export function resolverAnio(
  items: readonly { materia_nombre: string; fecha: string }[],
  mesas: readonly { materia_nombre: string; fecha: string; curso_nombre: string }[],
): string {
  for (const item of items) {
    const hit = mesas.find(
      (m) => m.materia_nombre === item.materia_nombre && m.fecha === item.fecha,
    );
    if (hit) {
      const anio = anioDeCurso(hit.curso_nombre);
      if (anio) return anio;
    }
  }
  return '';
}
