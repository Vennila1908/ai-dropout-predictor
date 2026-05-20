import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  UploadCloud,
  Brain,
  ClipboardList,
  BarChart3,
  MessageCircle,
  Settings,
  X,
  GraduationCap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUiStore } from '@/store/uiStore';
import { useAuth } from '@/hooks/useAuth';

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'faculty', 'student'] },
  { to: '/students', label: 'Students', icon: Users, roles: ['admin', 'faculty'] },
  { to: '/uploads', label: 'Uploads', icon: UploadCloud, roles: ['admin', 'faculty'] },
  { to: '/predictions', label: 'Predictions', icon: Brain, roles: ['admin', 'faculty'] },
  { to: '/counseling', label: 'Counseling', icon: ClipboardList, roles: ['admin', 'faculty'] },
  { to: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['admin', 'faculty'] },
  { to: '/chat', label: 'Assistant', icon: MessageCircle, roles: ['admin', 'faculty'] },
  { to: '/settings', label: 'Settings', icon: Settings, roles: ['admin', 'faculty', 'student'] },
] as const;

export function Sidebar() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const setSidebar = useUiStore((s) => s.setSidebar);
  const { user } = useAuth();

  const items = NAV.filter((n) => (user ? (n.roles as readonly string[]).includes(user.role) : false));

  return (
    <>
      <div
        className={cn('fixed inset-0 z-30 bg-black/50 lg:hidden', sidebarOpen ? 'block' : 'hidden')}
        onClick={() => setSidebar(false)}
        aria-hidden
      />
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 flex h-full w-64 flex-col border-r bg-surface transition-transform lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-14 items-center justify-between border-b px-4">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-gradient-to-br from-primary-500 to-violet-500 p-1.5 text-white">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold leading-tight">Dropout AI</div>
              <div className="text-[10px] uppercase tracking-wide text-ink-muted">v0.1</div>
            </div>
          </div>
          <button onClick={() => setSidebar(false)} className="btn-ghost p-1.5 lg:hidden">
            <X className="h-4 w-4" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 scrollbar-thin">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                    : 'text-ink-muted hover:bg-surface-subtle hover:text-ink',
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3 text-xs text-ink-muted">
          <p>Local-only AI · Your data never leaves this server.</p>
        </div>
      </aside>
    </>
  );
}
