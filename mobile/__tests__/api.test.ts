/**
 * Contract tests for the mobile API client (S9 / T10).
 *
 * They pin the exact URL, method, body keys and auth headers the backend
 * snapshot expects (`extra="forbid"` models reject any extra key), plus the
 * `{ code, detail }` error envelope mapping used by the screens.
 */
import { beforeEach, describe, expect, it, jest } from '@jest/globals';

import {
  ApiError,
  apiErrorMessage,
  fetchConvocatoriaVigente,
  fetchMisInscripciones,
  fetchMesasDisponibles,
  fetchYo,
  login,
  logout,
  postCambiarClave,
  postInscripcion,
  postOlvidoClave,
  postRestablecerClave,
  setRefreshHandler,
} from '../src/api';

const API_BASE = 'http://localhost:8000';

type Call = { url: string; init: RequestInit };

function mockFetch(status: number, payload?: unknown) {
  const calls: Call[] = [];
  const fn = jest.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => payload,
    };
  });
  (globalThis as unknown as { fetch: typeof fn }).fetch = fn;
  return calls;
}

function bodyOf(call: Call): Record<string, unknown> {
  return JSON.parse(String(call.init.body));
}

function headersOf(call: Call): Record<string, string> {
  return call.init.headers as Record<string, string>;
}

function mockFetchSequence(responses: Array<{ status: number; payload?: unknown }>) {
  const calls: Call[] = [];
  let index = 0;
  const fn = jest.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    const next = responses[Math.min(index, responses.length - 1)];
    index += 1;
    return {
      ok: next.status >= 200 && next.status < 300,
      status: next.status,
      json: async () => next.payload,
    };
  });
  (globalThis as unknown as { fetch: typeof fn }).fetch = fn;
  return calls;
}

beforeEach(() => {
  jest.restoreAllMocks();
  setRefreshHandler(null);
});

describe('login', () => {
  it('posts the sigme_mobile contract and returns the token pair', async () => {
    const calls = mockFetch(200, { access: 'a1', refresh: 'r1' });

    await expect(login('12345678', 'secret')).resolves.toEqual({
      access: 'a1',
      refresh: 'r1',
    });

    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/login`);
    expect(calls[0].init.method).toBe('POST');
    expect(bodyOf(calls[0])).toEqual({
      username: '12345678',
      password: 'secret',
      modulo: 'sigme_mobile',
    });
    expect(headersOf(calls[0]).Authorization).toBeUndefined();
  });
});

describe('session endpoints', () => {
  it('sends the bearer token on GET /auth/yo', async () => {
    const calls = mockFetch(200, {
      id: 'u1',
      username: '12345678',
      roles: ['alumno'],
      permisos: ['mesa.listar'],
      modulos: ['sigme_mobile'],
    });

    const yo = await fetchYo('tok');

    expect(yo.roles).toEqual(['alumno']);
    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/yo`);
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
    expect(calls[0].init.body).toBeUndefined();
  });

  it('treats 204 from logout as an empty success', async () => {
    const calls = mockFetch(204);

    await expect(logout('tok')).resolves.toBeUndefined();
    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/logout`);
    expect(calls[0].init.method).toBe('POST');
  });
});

describe('student queries', () => {
  it('gets available tables with the bearer token', async () => {
    const calls = mockFetch(200, []);

    await expect(fetchMesasDisponibles('tok')).resolves.toEqual([]);

    expect(calls[0].url).toBe(`${API_BASE}/api/v1/mesas-disponibles`);
    expect(calls[0].init.method).toBe('GET');
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
  });

  it('gets the current enrollment window', async () => {
    const calls = mockFetch(200, {
      id: 'c1',
      descripcion: 'Diciembre 2026',
      fecha_inicio_inscripcion: '2026-12-01',
      fecha_fin_inscripcion: '2026-12-10',
      activa: true,
      estado: 'abierta',
    });

    const ventana = await fetchConvocatoriaVigente('tok');

    expect(ventana.activa).toBe(true);
    expect(ventana.fecha_fin_inscripcion).toBe('2026-12-10');
    expect(calls[0].url).toBe(`${API_BASE}/api/v1/convocatoria-vigente`);
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
  });

  it('gets the student enrollments with the bearer token', async () => {
    const calls = mockFetch(200, []);

    await expect(fetchMisInscripciones('tok')).resolves.toEqual([]);

    expect(calls[0].url).toBe(`${API_BASE}/api/v1/mis-inscripciones`);
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
  });

  it('posts an enrollment with materia + condicion only', async () => {
    const calls = mockFetch(201, {
      id: 'i1',
      convocatoria_id: 'c1',
      mesa_examen_id: 'm1',
      materia_id: 'mat1',
      condicion_id: 'cond1',
      estado: 'confirmada',
      inscripto_en: null,
    });

    const created = await postInscripcion('tok', {
      materia_id: 'mat1',
      condicion_id: 'cond1',
    });

    expect(created.id).toBe('i1');
    expect(calls[0].url).toBe(`${API_BASE}/api/v1/inscripciones`);
    expect(bodyOf(calls[0])).toEqual({ materia_id: 'mat1', condicion_id: 'cond1' });
    expect(Object.keys(bodyOf(calls[0]))).toHaveLength(2);
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
  });
});

describe('password endpoints', () => {
  it('posts the recovery identifier', async () => {
    const calls = mockFetch(202, { status: 'ok' });

    await postOlvidoClave('12345678');

    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/olvido-clave`);
    expect(bodyOf(calls[0])).toEqual({ identificador: '12345678' });
  });

  it('posts token + clave_nueva to reset the password', async () => {
    const calls = mockFetch(200, { status: 'ok' });

    await postRestablecerClave('mail-token', 'unaClaveLarga1');

    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/restablecer-clave`);
    expect(bodyOf(calls[0])).toEqual({ token: 'mail-token', clave_nueva: 'unaClaveLarga1' });
  });

  it('posts clave_actual + clave_nueva and returns the fresh access token', async () => {
    const calls = mockFetch(200, { access: 'a2' });

    await expect(postCambiarClave('tok', 'vieja', 'nuevaClaveLarga1')).resolves.toEqual({
      access: 'a2',
    });

    expect(calls[0].url).toBe(`${API_BASE}/api/v1/auth/cambiar-clave`);
    expect(bodyOf(calls[0])).toEqual({ clave_actual: 'vieja', clave_nueva: 'nuevaClaveLarga1' });
    expect(headersOf(calls[0]).Authorization).toBe('Bearer tok');
  });

  it('surfaces clave-invalida as an ApiError code', async () => {
    mockFetch(400, { code: 'clave-invalida', detail: 'La clave actual no es correcta' });

    await expect(postCambiarClave('tok', 'mala', 'nuevaClaveLarga1')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      code: 'clave-invalida',
    });
  });
});

describe('error envelope', () => {
  it('exposes the backend code and keeps the raw body', async () => {
    mockFetch(409, { code: 'inscripcion-duplicada', detail: 'Ya estás inscripto' });

    const err = await postInscripcion('tok', {
      materia_id: 'mat1',
      condicion_id: 'cond1',
    }).catch((e: unknown) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(409);
    expect((err as ApiError).code).toBe('inscripcion-duplicada');
    expect((err as ApiError).body).toEqual({
      code: 'inscripcion-duplicada',
      detail: 'Ya estás inscripto',
    });
  });

  it('keeps body null when the response is not JSON', async () => {
    (globalThis as unknown as { fetch: unknown }).fetch = jest.fn(async () => ({
      ok: false,
      status: 502,
      json: async () => {
        throw new Error('not json');
      },
    }));

    const err = await fetchYo('tok').catch((e: unknown) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(502);
    expect((err as ApiError).body).toBeNull();
  });

  it('prefers the backend detail over the fallback message', async () => {
    mockFetch(409, { code: 'inscripcion-duplicada', detail: 'Ya estás inscripto' });

    const err = await fetchMisInscripciones('tok').catch((e: unknown) => e);

    expect(apiErrorMessage(err, 'No se pudo cargar')).toBe('Ya estás inscripto');
  });

  it('maps a bare 401 to the session message', async () => {
    mockFetch(401, null);

    const err = await fetchMisInscripciones('tok').catch((e: unknown) => e);

    expect(apiErrorMessage(err, 'No se pudo cargar')).toContain('sesión venció');
  });

  it('uses the fallback for a network failure', () => {
    expect(apiErrorMessage(new TypeError('Network request failed'), 'Sin conexión')).toBe(
      'Sin conexión',
    );
  });
});

describe('session refresh on 401', () => {
  it('retries once with the fresh access token', async () => {
    const calls = mockFetchSequence([{ status: 401 }, { status: 200, payload: [] }]);
    const handler = jest.fn<() => Promise<string | null>>(async () => 'fresh-token');
    setRefreshHandler(handler);

    await expect(fetchMesasDisponibles('expired')).resolves.toEqual([]);

    expect(handler).toHaveBeenCalledTimes(1);
    expect(calls).toHaveLength(2);
    expect(headersOf(calls[1]).Authorization).toBe('Bearer fresh-token');
  });

  it('surfaces the original 401 when the refresh fails', async () => {
    const calls = mockFetchSequence([{ status: 401 }]);
    setRefreshHandler(jest.fn<() => Promise<string | null>>(async () => null));

    const err = await fetchMesasDisponibles('expired').catch((e: unknown) => e);

    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).status).toBe(401);
    expect(calls).toHaveLength(1);
  });

  it('does not retry more than once', async () => {
    const calls = mockFetchSequence([{ status: 401 }, { status: 401 }]);
    setRefreshHandler(jest.fn<() => Promise<string | null>>(async () => 'fresh-token'));

    await expect(fetchMesasDisponibles('expired')).rejects.toMatchObject({ status: 401 });

    expect(calls).toHaveLength(2);
  });

  it('never refreshes a request that carries no token', async () => {
    const calls = mockFetchSequence([
      { status: 401, payload: { code: 'credenciales-invalidas', detail: 'Login failed' } },
    ]);
    const handler = jest.fn<() => Promise<string | null>>(async () => 'fresh-token');
    setRefreshHandler(handler);

    await expect(login('u', 'p')).rejects.toMatchObject({ status: 401 });

    expect(handler).not.toHaveBeenCalled();
    expect(calls).toHaveLength(1);
  });
});