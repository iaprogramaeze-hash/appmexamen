/**
 * Auth context: session state + login/logout against the backend API.
 *
 * The API base is configurable:
 *   - `EXPO_PUBLIC_API_BASE` env var (app config / .env), or
 *   - `http://localhost:8000` default (same as the prototype).
 *
 * Login follows the real backend contract: `POST /auth/login` with
 * `{ username, password, modulo: 'sigme_mobile' }` returns `{ access, refresh }`
 * and the roles/permissions come from `GET /auth/yo`.
 *
 * While the backend is unreachable the screens remain browsable (login
 * succeeds into a demo session with the requested identifier) so the UI can
 * be iterated; a `demo: true` flag marks that state and no API call is made
 * with a demo session.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { ApiError, apiErrorMessage, fetchYo, login as apiLogin } from './api';
import { API_BASE } from './config';

export { API_BASE };

export type Session = {
  access: string;
  refresh: string;
  usuario: string;
  roles: string[];
  permisos: string[];
  demo: boolean;
};

type AuthState = {
  session: Session | null;
  loading: boolean;
  signIn: (usuario: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  signOut: () => Promise<void>;
  /** Replaces the access token after a password change (token_version bump). */
  updateAccess: (access: string) => Promise<void>;
};

const STORAGE_KEY = 'session.v2';
const LEGACY_STORAGE_KEY = 'session.v1';

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore persisted session on boot.
  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw) as Partial<Session>;
          if (typeof parsed.access === 'string' && Array.isArray(parsed.roles)) {
            setSession({
              access: parsed.access,
              refresh: typeof parsed.refresh === 'string' ? parsed.refresh : '',
              usuario: typeof parsed.usuario === 'string' ? parsed.usuario : 'alumno',
              roles: parsed.roles,
              permisos: Array.isArray(parsed.permisos) ? parsed.permisos : [],
              demo: parsed.demo === true,
            });
          }
        }
        // Drop the pre-contract session shape (token/usuario only).
        await AsyncStorage.removeItem(LEGACY_STORAGE_KEY);
      } catch {
        // corrupted storage -> start signed out
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const persist = useCallback(async (s: Session | null) => {
    setSession(s);
    if (s) await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    else await AsyncStorage.removeItem(STORAGE_KEY);
  }, []);

  const signIn = useCallback<AuthState['signIn']>(
    async (usuario, password) => {
      const identificador = usuario.trim();
      if (!identificador || !password) {
        return { ok: false, error: 'Ingresá tu usuario y contraseña.' };
      }

      try {
        const pair = await apiLogin(identificador, password);

        let nombre = identificador;
        let roles: string[] = [];
        let permisos: string[] = [];
        try {
          const yo = await fetchYo(pair.access);
          nombre = yo.username || nombre;
          roles = yo.roles ?? [];
          permisos = yo.permisos ?? [];
        } catch {
          // Identity lookup failed (unexpected): the session is still valid,
          // the profile screen falls back to the typed identifier.
        }

        await persist({
          access: pair.access,
          refresh: pair.refresh,
          usuario: nombre,
          roles,
          permisos,
          demo: false,
        });
        return { ok: true };
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 401 || err.status === 422) {
            return { ok: false, error: 'Usuario o contraseña incorrectos.' };
          }
          if (err.status === 403) {
            return { ok: false, error: 'Tu cuenta no tiene acceso a la app móvil.' };
          }
          if (err.status === 429) {
            return {
              ok: false,
              error: 'Demasiados intentos fallidos. Esperá 15 minutos e intentá de nuevo.',
            };
          }
          return { ok: false, error: apiErrorMessage(err, 'No se pudo iniciar sesión.') };
        }

        // Backend unreachable -> demo session so the UI stays reviewable.
        await persist({
          access: '',
          refresh: '',
          usuario: identificador,
          roles: ['alumno'],
          permisos: [],
          demo: true,
        });
        return { ok: true };
      }
    },
    [persist],
  );

  const signOut = useCallback(async () => {
    await persist(null);
  }, [persist]);

  const updateAccess = useCallback(
    async (access: string) => {
      if (!session) return;
      await persist({ ...session, access });
    },
    [session, persist],
  );

  const value = useMemo(
    () => ({ session, loading, signIn, signOut, updateAccess }),
    [session, loading, signIn, signOut, updateAccess],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

/** True when the session carries the tutor role. */
export function isTutor(roles: string[]): boolean {
  return roles.includes('tutor');
}
