import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';

export function StudentDashboardPage() {
  const { user } = useAuth();
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Welcome, {user?.full_name?.split(' ')[0] ?? 'student'}</h1>
        <p className="text-sm text-ink-muted">Your personal performance and recommendations.</p>
      </header>
      <Card>
        <CardHeader title="Your status" subtitle="Aggregated by your registered roll number." />
        <CardBody>
          <p className="text-sm text-ink-muted">
            Detailed student view is part of future scope. For now, please use the Settings tab to update your profile,
            or ask your faculty to share your latest risk report.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
