/**
 * Permiso de examen rules (RB-18): active enrollments grouped by condition —
 * one permiso per condition group; mixed conditions emit two permisos.
 *
 * Pure helpers (same pattern as `loginRules` / `tecnicaturaRules`).
 */

export type InscripcionPermiso = {
  condicion_nombre: string;
  estado: string;
  materia_nombre: string;
  fecha: string;
  hora: string | null;
};

export type GrupoPermiso = {
  condicion: string;
  items: InscripcionPermiso[];
};

/** Active enrollments only (`estado !== 'anulado'`). */
export function inscripcionesActivas<T extends { estado: string }>(
  inscripciones: readonly T[],
): T[] {
  return inscripciones.filter((i) => i.estado !== 'anulado');
}

/**
 * RB-18: one permiso per condition; different conditions → two permisos.
 * Order follows first appearance of each condition.
 */
export function agrupaPorCondicion(
  inscripciones: readonly InscripcionPermiso[],
): GrupoPermiso[] {
  const activas = inscripcionesActivas(inscripciones);
  const orden: string[] = [];
  const porCondicion = new Map<string, InscripcionPermiso[]>();
  for (const ins of activas) {
    const key = ins.condicion_nombre;
    if (!porCondicion.has(key)) {
      porCondicion.set(key, []);
      orden.push(key);
    }
    porCondicion.get(key)!.push(ins);
  }
  return orden.map((condicion) => ({
    condicion,
    items: porCondicion.get(condicion)!,
  }));
}
