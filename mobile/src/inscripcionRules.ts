/**
 * Enrollment rules (S15): the student may cancel an enrollment only until
 * the day before the mesa ("solo se de baja si no es el dia de la mesa").
 *
 * Pure date logic with an injectable reference day so tests do not depend
 * on the day they run.
 */

/** "2026-12-15" -> Date at local midnight; null when the input is not a real date. */
function parseFechaIso(fecha: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fecha.trim());
  if (!m) return null;
  const [, y, mo, d] = m;
  const año = Number(y);
  const mes = Number(mo);
  const dia = Number(d);
  const fechaObj = new Date(año, mes - 1, dia);
  // Round-trip check: the Date constructor rolls over impossible dates
  // (2026-02-30 → 2026-03-02), so compare the components back.
  if (
    fechaObj.getFullYear() !== año ||
    fechaObj.getMonth() !== mes - 1 ||
    fechaObj.getDate() !== dia
  ) {
    return null;
  }
  return fechaObj;
}

/**
 * True only while today is strictly before the mesa day: the same day and
 * any later day are not eligible for cancellation.
 */
export function puedeDarDeBaja(fecha: string, hoy: Date = new Date()): boolean {
  const mesa = parseFechaIso(fecha);
  if (!mesa) return false;
  const hoy0 = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  return hoy0.getTime() < mesa.getTime();
}
