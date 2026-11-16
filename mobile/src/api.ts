/**
 * Real API client for the mobile app.
 *
 * Every request goes through `API_BASE` (configurable via
 * `EXPO_PUBLIC_API_BASE`) and carries the session access token when
 * available. While the backend is unreachable calls reject with a typed
 * `ApiError` so callers can show a clear state — no fake grades, tables or
 * enrollments are fabricated here.
 *
 * Contracts mirror `backend/app/features` (snapshot): login returns
 * `{ access, refresh }`; roles/permissions come from `GET /auth/yo`; student
 * queries live at the root of `/api/v1` and are gated by session, not by
 * device module.
 */
import { API_BASE } from './config';

export { API_BASE };

type Json = Record<string, unknown>;

export type TokenPair = { access: string; refresh: string };

export type YoResponse = {
  id: string;
  username: string;
  roles: string[];
  permisos: string[];
  modulos: string[];
};

/** `GET /api/v1/mesas-disponibles` (CU-35). */
export type MesaDisponible = {
  materia_id: string;
  condicion_id: string;
  orientacion_nombre: string;
  curso_nombre: string;
  materia_nombre: string;
  condicion_nombre: string;
  /** ISO date (YYYY-MM-DD). */
  fecha: string;
  /** HH:MM:SS or null. */
  hora: string | null;
};

/** `GET /api/v1/mis-inscripciones` (CU-38). */
export type MisInscripcion = {
  id: string;
  mesa_examen_id: string;
  materia_id: string;
  condicion_id: string;
  estado: string;
  materia_nombre: string;
  condicion_nombre: string;
  fecha: string;
  hora: string | null;
  inscripto_en: string | null;
};

/** `GET /api/v1/convocatoria-vigente` (CU-34). */
export type ConvocatoriaVigente = {
  id: string;
  descripcion: string;
  fecha_inicio_inscripcion: string;
  fecha_fin_inscripcion: string;
  activa: boolean;
  estado: string;
};

export type InscripcionCreada = {
  id: string;
  convocatoria_id: string;
  mesa_examen_id: string;
  materia_id: string;
  condicion_id: string;
  estado: string;
  inscripto_en: string | null;
};

/**
 * Typed API failure. `status` is the HTTP status; `body` is the parsed
 * backend error envelope `{ code, detail }` when present. A plain network
 * failure is NOT an `ApiError` — it surfaces as the original fetch error.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }

  /** Backend error code (`ventana-cerrada`, `permiso-denegado`, ...). */
  get code(): string | undefined {
    const body = this.body as { code?: unknown } | null;
    return body && typeof body.code === 'string' ? body.code : undefined;
  }
}

type RequestOptions = {
  method?: string;
  body?: Json;
  token?: string;
  /** Internal: a 401 is retried at most once, after a token refresh. */
  retryOn401?: boolean;
};

/**
 * Installed by `AuthProvider`: rotates the pair and returns the fresh access
 * token, or `null` when the session cannot be recovered. Keeping it out of the
 * module graph lets the API layer stay acyclic (auth imports api, not the
 * other way round).
 */
type RefreshHandler = () => Promise<string | null>;

let refreshHandler: RefreshHandler | null = null;

export function setRefreshHandler(handler: RefreshHandler | null): void {
  refreshHandler = handler;
}

async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, retryOn401 = true } = options;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  if (resp.status === 401 && token && retryOn401 && refreshHandler) {
    const fresh = await refreshHandler();
    if (fresh) {
      return apiFetch<T>(path, { method, body, token: fresh, retryOn401: false });
    }
  }

  if (!resp.ok) {
    let parsed: unknown = null;
    try {
      parsed = await resp.json();
    } catch {
      // Non-JSON body (proxy/gateway error): keep null.
    }
    throw new ApiError(`API ${method} ${path} failed (${resp.status})`, resp.status, parsed);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

/** Human message for an API failure, preferring the backend `detail`. */
export function apiErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: unknown; message?: unknown } | null;
    if (body) {
      if (typeof body.detail === 'string' && body.detail.trim()) return body.detail;
      if (typeof body.message === 'string' && body.message.trim()) return body.message;
    }
    if (err.status === 401) return 'Tu sesión venció. Volvé a iniciar sesión.';
    if (err.status === 403) return 'Tu cuenta no tiene permiso para esta acción.';
    if (err.status === 503) return 'El servidor no está disponible en este momento.';
  }
  return fallback;
}

// --- Auth ------------------------------------------------------------------

/** `POST /api/v1/auth/login` — the mobile app logs in as `sigme_mobile`. */
export async function login(username: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>('/api/v1/auth/login', {
    method: 'POST',
    body: { username, password, modulo: 'sigme_mobile' },
  });
}

/** `GET /api/v1/auth/yo` — identity, roles, permissions and modules. */
export async function fetchYo(token: string): Promise<YoResponse> {
  return apiFetch<YoResponse>('/api/v1/auth/yo', { token });
}

/** `POST /api/v1/auth/refresh` — rotates the pair. */
export async function refreshSession(refresh: string): Promise<TokenPair> {
  return apiFetch<TokenPair>('/api/v1/auth/refresh', {
    method: 'POST',
    body: { refresh },
  });
}

/** `POST /api/v1/auth/logout` — revokes the current session (204). */
export async function logout(token: string): Promise<void> {
  await apiFetch<void>('/api/v1/auth/logout', { method: 'POST', token });
}

/** `POST /api/v1/auth/olvido-clave` — always 202 (anti-enumeration). */
export async function postOlvidoClave(identificador: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/api/v1/auth/olvido-clave', {
    method: 'POST',
    body: { identificador },
  });
}

/** `POST /api/v1/auth/restablecer-clave` — consumes the emailed token. */
export async function postRestablecerClave(
  token: string,
  claveNueva: string,
): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/api/v1/auth/restablecer-clave', {
    method: 'POST',
    body: { token, clave_nueva: claveNueva },
  });
}

/**
 * `POST /api/v1/auth/cambiar-clave` — requires the current password and
 * returns a fresh access token (the old one dies with the token_version bump).
 */
export async function postCambiarClave(
  token: string,
  claveActual: string,
  claveNueva: string,
): Promise<{ access: string }> {
  return apiFetch<{ access: string }>('/api/v1/auth/cambiar-clave', {
    method: 'POST',
    body: { clave_actual: claveActual, clave_nueva: claveNueva },
    token,
  });
}

// --- Student queries -------------------------------------------------------

/** `GET /api/v1/convocatoria-vigente` — current window + derived state. */
export async function fetchConvocatoriaVigente(token: string): Promise<ConvocatoriaVigente> {
  return apiFetch<ConvocatoriaVigente>('/api/v1/convocatoria-vigente', { token });
}

/** `GET /api/v1/mesas-disponibles` — live tables of the current window. */
export async function fetchMesasDisponibles(token: string): Promise<MesaDisponible[]> {
  return apiFetch<MesaDisponible[]>('/api/v1/mesas-disponibles', { token });
}

/** `GET /api/v1/mis-inscripciones` — the student's own enrollments. */
export async function fetchMisInscripciones(token: string): Promise<MisInscripcion[]> {
  return apiFetch<MisInscripcion[]>('/api/v1/mis-inscripciones', { token });
}

/** `POST /api/v1/inscripciones` — body is only materia + condicion (RB-30). */
export async function postInscripcion(
  token: string,
  body: { materia_id: string; condicion_id: string },
): Promise<InscripcionCreada> {
  return apiFetch<InscripcionCreada>('/api/v1/inscripciones', {
    method: 'POST',
    body,
    token,
  });
}

// --- Pending backend contracts (informe al colega) -------------------------

/**
 * `GET /api/v1/notas` — NOT exposed by the backend snapshot yet; it is part
 * of the informe to the colleague (S5). Kept here so the screen only needs
 * the data layer switch when the endpoint lands.
 */
export async function fetchNotasAlumno(token: string) {
  return apiFetch<Json>('/api/v1/notas', { method: 'GET', token });
}

/** `GET /api/v1/tutor/alumnos/{id}/notas` — pending backend (S5). */
export async function fetchNotasTutor(token: string, alumnoId: string) {
  return apiFetch<Json>(`/api/v1/tutor/alumnos/${alumnoId}/notas`, { method: 'GET', token });
}

/** `GET /api/v1/tutor/alumnos/{id}/asistencias` — pending backend (S6). */
export async function fetchAsistenciasTutor(token: string, alumnoId: string) {
  return apiFetch<Json>(`/api/v1/tutor/alumnos/${alumnoId}/asistencias`, {
    method: 'GET',
    token,
  });
}
