/**
 * Login gate rules: pure helpers that keep the slide-to-confirm honest.
 * The slider only becomes available once both identifiers have real content,
 * and the label tells the user exactly what is missing.
 */

const LABEL_READY = 'Deslizá para iniciar sesión';
const LABEL_MISSING = 'Completá usuario y contraseña';
const LABEL_BUSY = 'Ingresando…';

/**
 * True when both fields contain at least one non-whitespace character.
 * Whitespace-only input is treated as empty, without trimming the values
 * actually submitted.
 */
export function loginListo(usuario: string, password: string): boolean {
  return usuario.trim().length > 0 && password.trim().length > 0;
}

/** Label for the slide track, reflecting what still blocks the action. */
export function etiquetaSlider(
  usuario: string,
  password: string,
  busy: boolean,
): string {
  if (busy) return LABEL_BUSY;
  return loginListo(usuario, password) ? LABEL_READY : LABEL_MISSING;
}