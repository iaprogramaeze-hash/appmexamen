/**
 * Local identity for the permit PDF (nombre + DNI), captured at registration.
 * The backend snapshot has no full name/DNI on `GET /auth/yo` yet, so the
 * device keeps what the student typed — same pattern as `tecnicatura.ts`.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

export type IdentidadAlumno = {
  nombre: string;
  apellido: string;
  dni: string;
};

const STORAGE_KEY = 'perfil.identidad.v1';

function soloTexto(v: unknown): string {
  return typeof v === 'string' ? v.trim() : '';
}

/** Reads the stored identity; null when incomplete. */
export async function leerIdentidad(): Promise<IdentidadAlumno | null> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<IdentidadAlumno>;
    const nombre = soloTexto(parsed.nombre);
    const apellido = soloTexto(parsed.apellido);
    const dni = soloTexto(parsed.dni);
    if (!nombre || !apellido || !dni) return null;
    return { nombre, apellido, dni };
  } catch {
    return null;
  }
}

/** Persists identity used on the permit. All three fields are required. */
export async function guardarIdentidad(value: IdentidadAlumno): Promise<boolean> {
  const nombre = soloTexto(value.nombre);
  const apellido = soloTexto(value.apellido);
  const dni = soloTexto(value.dni);
  if (!nombre || !apellido || !dni) return false;
  try {
    await AsyncStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ nombre, apellido, dni }),
    );
    return true;
  } catch {
    return false;
  }
}

/** Clears stored identity (sign-out / account switch). */
export async function borrarIdentidad(): Promise<void> {
  try {
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch {
    // best-effort cleanup
  }
}

/** `APELLIDO, NOMBRE` as printed on the school form. */
export function formatoAlumnoImpreso(id: IdentidadAlumno): string {
  return `${id.apellido.trim()}, ${id.nombre.trim()}`;
}
