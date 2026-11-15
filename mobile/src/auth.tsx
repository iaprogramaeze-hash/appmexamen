/**
 * Auth context: session state + login/logout against the backend API.
 *
 * The API base is configurable:
 *   - `EXPO_PUBLIC_API_BASE` env var (app.config / .env), or
 *   - `http://localhost:8000` default (same as the prototype).
 *
 * While the backend is unreachable the screens remain browsable (login
 * succeeds into a demo session with the requested identifier) so the UI
 * can be iterated; a `demo: true` flag marks that state.
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

export const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'http://localhost:8000';

export type Session = {
  token: string;
  usuario: string;
  roles: string[];
  demo: boolean;
};

type AuthState = {
  session: Session | null;
  loading: boolean;
  signIn: (usuario: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  signOut: () => Promise<void>;
};

const STORAGE_KEY = 'session.v1';

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore persisted session on boot.
  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) setSession(JSON.parse(raw));
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
      if (!usuario.trim() || !password) {
        return { ok: false, error: 'Ingresá tu usuario y contraseña.' };
      }
      try {
        const resp = await fetch(`${API_BASE}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ usuario, password }),
        });
        if (resp.ok) {
          const data = await resp.json();
          const roles: string[] = data.roles ?? [];
          await persist({
            token: data.access_token ?? '',
            usuario: data.nombre ?? usuario,
            roles,
            demo: false,
          });
          return { ok: true };
        }
        if (resp.status === 401 || resp.status === 422) {
          return { ok: false, error: 'Usuario o contraseña incorrectos.' };
        }
        // Backend up but unexpected error: fall through to demo below.
      } catch {
        // Backend unreachable -> demo session so the UI stays reviewable.
      }
      await persist({ token: '', usuario, roles: ['alumno'], demo: true });
      return { ok: true };
    },
    [persist],
  );

  const signOut = useCallback(async () => {
    await persist(null);
  }, [persist]);

  const value = useMemo(
    () => ({ session, loading, signIn, signOut }),
    [session, loading, signIn, signOut],
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
