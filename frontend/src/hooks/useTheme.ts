import { useCallback, useEffect } from 'react';
import { THEME_STORAGE_KEY } from '@/lib/constants';
import { useUiStore } from '@/store/uiStore';

export function useTheme() {
  const theme = useUiStore((s) => s.theme);
  const setTheme = useUiStore((s) => s.setTheme);

  const apply = useCallback(
    (next: 'light' | 'dark') => {
      const root = document.documentElement;
      if (next === 'dark') root.classList.add('dark');
      else root.classList.remove('dark');
      localStorage.setItem(THEME_STORAGE_KEY, next);
      setTheme(next);
    },
    [setTheme],
  );

  useEffect(() => {
    const stored = (localStorage.getItem(THEME_STORAGE_KEY) as 'light' | 'dark' | null) ?? null;
    if (stored) apply(stored);
  }, [apply]);

  const toggle = useCallback(() => apply(theme === 'dark' ? 'light' : 'dark'), [apply, theme]);

  return { theme, setTheme: apply, toggle };
}
