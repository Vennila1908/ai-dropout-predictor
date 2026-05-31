import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { api, unwrap } from '@/lib/api';

export function SettingsPage() {
  const { user } = useAuth();
  const { data: health } = useQuery({
    queryKey: ['health', 'core'],
    queryFn: () => unwrap(api.get<{ status: string; db: boolean; version: string }>('/health')),
  });

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-ink-muted">Account & system info.</p>
      </header>

      <Card>
        <CardHeader title="Account" />
        <CardBody className="space-y-1 text-sm">
          <p>{user?.full_name}</p>
          <p className="text-ink-muted">{user?.email}</p>
          <p className="py-2">
            Role: <Badge>{user?.role}</Badge>
          </p>
          {/* <p className="text-xs text-ink-muted">
            To rotate your password or change role, ask an administrator (admin-only via /users API).
          </p> */}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="System" />
        <CardBody className="text-sm space-y-1">
          <p>
            Backend: <span className="font-mono text-xs">v{health?.version ?? '?'}</span>
          </p>
          <p>
            Database:{' '}
            {health?.db ? <Badge variant="low">healthy</Badge> : <Badge variant="high">degraded</Badge>}
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
