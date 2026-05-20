import { create } from 'zustand';
import type { AuthTokens, User } from '@/types';
import { AUTH_STORAGE_KEY } from '@/lib/constants';

interface PersistedAuth {
  tokens: AuthTokens | null;
  user: User | null;
}

interface AuthState extends PersistedAuth {
  isHydrated: boolean;
  hydrate: () => void;
  setAuth: (tokens: AuthTokens, user: User) => void;
  setAccessToken: (access: string) => void;
  clear: () => void;
}

function readStorage(): PersistedAuth {
  if (typeof window === 'undefined') return { tokens: null, user: null };
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return { tokens: null, user: null };
    return JSON.parse(raw) as PersistedAuth;
  } catch {
    return { tokens: null, user: null };
  }
}

function writeStorage(value: PersistedAuth): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(value));
}

function clearStorage(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}

export const useAuthStore = create<AuthState>((set, get) => ({
  tokens: null,
  user: null,
  isHydrated: false,
  hydrate: () => {
    const persisted = readStorage();
    set({ ...persisted, isHydrated: true });
  },
  setAuth: (tokens, user) => {
    writeStorage({ tokens, user });
    set({ tokens, user });
  },
  setAccessToken: (access) => {
    const cur = get();
    if (!cur.tokens) return;
    const next = { ...cur.tokens, access_token: access };
    writeStorage({ tokens: next, user: cur.user });
    set({ tokens: next });
  },
  clear: () => {
    clearStorage();
    set({ tokens: null, user: null });
  },
}));
