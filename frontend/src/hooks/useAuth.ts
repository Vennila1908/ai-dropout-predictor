import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const tokens = useAuthStore((s) => s.tokens);
  const user = useAuthStore((s) => s.user);
  const isHydrated = useAuthStore((s) => s.isHydrated);
  const setAuth = useAuthStore((s) => s.setAuth);
  const clear = useAuthStore((s) => s.clear);

  return {
    isAuthenticated: Boolean(tokens?.access_token && user),
    isHydrated,
    tokens,
    user,
    setAuth,
    clear,
  };
}
