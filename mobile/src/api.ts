/**
 * Real API client for the mobile app.
 * All requests go through `API_BASE` (configurable via EXPO_PUBLIC_API_BASE)
 * and carry the session token when available. While the backend is unreachable
 * calls reject so the caller can fall back to demo data — no fake grades or
 * enrollments are fabricated here.
 */
import { API_BASE } from './auth';

type Json = Record<string, unknown>;

async function apiFetch(
  path: string,
  { method = 'GET', body, token }: { method?: string; body?: Json; token?: string },
) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!resp.ok) {
    const err = new Error(`API ${method} ${path} failed (${resp.status})`);
    (err as any).status = resp.status;
    throw err;
  }
  return resp.json();
}

/** Available exam tables (alumno home / inscripción). */
export async function fetchMesasDisponibles(token: string) {
  return apiFetch('/api/v1/mesas-disponibles', { method: 'GET', token });
}

/** Enroll the student in an exam table (alumno home / inscripción). */
export async function postInscripcion(token: string, body: { mesaId: string }) {
  return apiFetch('/api/v1/inscripciones', { method: 'POST', body, token });
}

/** Trimestral grades per subject for the logged-in alumno. */
export async function fetchNotasAlumno(token: string) {
  return apiFetch('/api/v1/notas', { method: 'GET', token });
}

/** Trimestral grades of a linked student (tutor read-only). */
export async function fetchNotasTutor(token: string, alumnoId: string) {
  return apiFetch(`/api/v1/tutor/alumnos/${alumnoId}/notas`, {
    method: 'GET',
    token,
  });
}

/** Attendance of a linked student (tutor read-only). */
export async function fetchAsistenciasTutor(token: string, alumnoId: string) {
  return apiFetch(`/api/v1/tutor/alumnos/${alumnoId}/asistencias`, {
    method: 'GET',
    token,
  });
}
