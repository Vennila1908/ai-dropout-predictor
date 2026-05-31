import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { API_URL } from '@/lib/constants';
import { useAuthStore } from '@/store/authStore';

/**
 * Single axios instance for the whole app. Adds Bearer JWT, normalizes
 * error envelopes, refreshes once on 401, and clears auth on hard failure.
 */
export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().tokens?.access_token;
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().tokens?.refresh_token;
  if (!refresh) return null;
  try {
    const r = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh });
    const next = (r.data?.access_token as string | undefined) ?? null;
    if (next) {
      useAuthStore.getState().setAccessToken(next);
    }
    return next;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const original = error.config as AxiosRequestConfig & { _retried?: boolean };

    const url = String(original?.url ?? '');
    const isLoginRequest = url.includes('/auth/login');

    if (status === 401 && original && !original._retried && !isLoginRequest) {
      original._retried = true;
      refreshPromise ??= refreshAccessToken();
      const next = await refreshPromise;
      refreshPromise = null;
      if (next) {
        original.headers = original.headers ?? {};
        (original.headers as Record<string, string>).Authorization = `Bearer ${next}`;
        return api.request(original);
      }
      // Auth dead → sign out and let ProtectedRoute redirect.
      useAuthStore.getState().clear();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }
    return Promise.reject(formatError(error));
  },
);

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: unknown;
}

function messageFromDetail(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return undefined;

  const parts = detail
    .map((item) => {
      if (typeof item === 'string') return item;
      if (!item || typeof item !== 'object' || !('msg' in item)) return null;
      const msg = String((item as { msg: unknown }).msg);
      const loc = 'loc' in item && Array.isArray((item as { loc: unknown }).loc)
        ? (item as { loc: unknown[] }).loc.filter((part) => part !== 'body').join('.')
        : '';
      return loc ? `${loc}: ${msg}` : msg;
    })
    .filter((part): part is string => Boolean(part));

  return parts.length ? parts.join('; ') : undefined;
}

function isApiError(err: unknown): err is ApiError {
  return (
    typeof err === 'object' &&
    err !== null &&
    'status' in err &&
    'code' in err &&
    'message' in err &&
    typeof (err as ApiError).status === 'number' &&
    typeof (err as ApiError).code === 'string' &&
    typeof (err as ApiError).message === 'string'
  );
}

export function formatError(err: unknown): ApiError {
  if (isApiError(err)) {
    return err;
  }
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as
      | { error?: { code?: string; message?: string }; detail?: unknown }
      | undefined;
    const detailMessage = messageFromDetail(data?.detail);
    return {
      status: err.response?.status ?? 0,
      code: data?.error?.code ?? String(err.response?.status ?? 'NETWORK'),
      message:
        data?.error?.message ??
        detailMessage ??
        (typeof data?.detail === 'string' ? data.detail : undefined) ??
        err.message ??
        'Request failed',
      details: err.response?.data,
    };
  }
  return { status: 0, code: 'UNKNOWN', message: err instanceof Error ? err.message : 'Unknown error' };
}

export async function unwrap<T>(p: Promise<{ data: T }>): Promise<T> {
  return (await p).data;
}
