import { Link, useNavigate } from 'react-router-dom';
import { ChevronDown, LogOut, Menu, Search } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useUiStore } from '@/store/uiStore';
import { ThemeToggle } from './ThemeToggle';
import { initials } from '@/lib/utils';

export function Topbar() {
  const navigate = useNavigate();
  const { user, clear } = useAuth();
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const [open, setOpen] = useState(false);

  const onLogout = () => {
    clear();
    navigate('/login', { replace: true });
  };

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-surface/80 px-4 backdrop-blur">
      <button onClick={toggleSidebar} className="btn-ghost p-2 lg:hidden" aria-label="Toggle navigation">
        <Menu className="h-5 w-5" />
      </button>
      <form
        className="hidden flex-1 sm:flex"
        onSubmit={(e) => {
          e.preventDefault();
          const value = new FormData(e.currentTarget).get('q')?.toString().trim();
          if (value) navigate(`/students?q=${encodeURIComponent(value)}`);
        }}
      >
        <label className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
          <input
            name="q"
            placeholder="Search students by roll, name…"
            className="input pl-9"
          />
        </label>
      </form>
      <div className="ml-auto flex items-center gap-2">
        <ThemeToggle />
        <div className="relative">
          <button onClick={() => setOpen((v) => !v)} className="btn-ghost flex items-center gap-2 px-2 py-1.5">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-primary-500/15 text-sm font-semibold text-primary-600 dark:text-primary-300">
              {initials(user?.full_name ?? 'U')}
            </span>
            <span className="hidden text-sm sm:inline">{user?.full_name ?? 'User'}</span>
            <ChevronDown className="h-4 w-4 text-ink-muted" />
          </button>
          {open && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl border bg-surface p-1 shadow-card-hover">
              <div className="border-b px-3 py-2 text-sm">
                <div className="font-medium">{user?.full_name}</div>
                <div className="text-xs text-ink-muted">{user?.email}</div>
                <div className="mt-1 inline-block rounded-full bg-surface-subtle px-2 py-0.5 text-[10px] uppercase tracking-wide">
                  {user?.role}
                </div>
              </div>
              <Link
                to="/settings"
                onClick={() => setOpen(false)}
                className="block rounded-md px-3 py-2 text-sm hover:bg-surface-subtle"
              >
                Settings
              </Link>
              <button
                onClick={onLogout}
                className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-risk-high hover:bg-surface-subtle"
              >
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
