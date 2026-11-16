/**
 * Runtime configuration shared by the API client and the auth context.
 *
 * `EXPO_PUBLIC_API_BASE` (app config / .env) wins; otherwise the backend runs
 * on `http://localhost:8000` during development. On a physical device use the
 * machine's LAN IP instead of localhost.
 */
export const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'http://localhost:8000';
