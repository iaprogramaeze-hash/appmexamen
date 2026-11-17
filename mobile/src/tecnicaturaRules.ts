/**
 * Tecnicatura rules (RB-02): a student belongs to exactly one tecnicatura,
 * and the enrollment list only shows tables of that tecnicatura.
 *
 * Pure helpers so the gate and the filter stay honest without touching
 * AsyncStorage or React (same pattern as `loginRules.ts`).
 */

/** The two fixed options of the school catalog (seed names, exact match). */
export const TECNICATURAS = [
  'TECNOLOGÍA DE LOS ALIMENTOS',
  'GESTIÓN ORGANIZACIONAL',
] as const;

export type Tecnicatura = (typeof TECNICATURAS)[number];

/** True when the value is one of the two official tecnicaturas. */
export function esTecnicatura(value: string): value is Tecnicatura {
  return (TECNICATURAS as readonly string[]).includes(value);
}

/**
 * RB-02 filter: only tables of the student's own tecnicatura.
 * Without a tecnicatura the list is empty — never another career's tables.
 */
export function filtraMesasPorTecnicatura<T extends { orientacion_nombre: string }>(
  mesas: readonly T[],
  tecnicatura: string | null | undefined,
): T[] {
  if (!tecnicatura || !esTecnicatura(tecnicatura)) return [];
  return mesas.filter((m) => m.orientacion_nombre === tecnicatura);
}
