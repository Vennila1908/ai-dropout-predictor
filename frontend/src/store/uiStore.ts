import { create } from 'zustand';

interface UiState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  setTheme: (t: 'light' | 'dark') => void;
}

function initialTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  if (document.documentElement.classList.contains('dark')) return 'dark';
  return 'light';
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  theme: initialTheme(),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebar: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
}));
