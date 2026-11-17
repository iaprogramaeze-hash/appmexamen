/**
 * Local persistence for the student's single tecnicatura (RB-02).
 *
 * The backend snapshot does not store or expose the student's career yet
 * (`GET /auth/yo` has no orientation field), so the value chosen at
 * registration lives on the device until the colega adds it to the account.
 * Prefer a backend value first when that arrives — see `leerTecnicatura`.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

import { esTecnicatura, type Tecnicatura } from './tecnicaturaRules';

const STORAGE_KEY = 'perfil.tecnicatura.v1';

/** Reads the stored tecnicatura; returns null when missing or invalid. */
export async function leerTecnicatura(): Promise<Tecnicatura | null> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (raw && esTecnicatura(raw)) return raw;
    return null;
  } catch {
    return null;
  }
}

/** Persists the student's one tecnicatura. Rejects unknown values. */
export async function guardarTecnicatura(value: string): Promise<boolean> {
  if (!esTecnicatura(value)) return false;
  try {
    await AsyncStorage.setItem(STORAGE_KEY, value);
    return true;
  } catch {
    return false;
  }
}

/** Clears the stored tecnicatura (sign-out / account switch). */
export async function borrarTecnicatura(): Promise<void> {
  try {
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch {
    // best-effort cleanup
  }
}
