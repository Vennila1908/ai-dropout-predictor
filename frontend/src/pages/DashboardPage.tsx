import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, Brain, GraduationCap, ShieldAlert, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart';
import { DepartmentRiskChart } from '@/components/charts/DepartmentRiskChart';
import { AttendanceTrendChart } from '@/components/charts/AttendanceTrendChart';
import { analyticsApi } from '@/features/analytics/analyticsApi';
import { formatPercent } from '@/lib/utils';

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'bundle'],
    queryFn: () => analyticsApi.bundle(),
  });

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Overview</h1>
        <p className="text-sm text-ink-muted">A snapshot of cohort risk, attendance, and recent activity.</p>
      </header>

      {isLoading || !data ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Stat icon={<Users className="h-4 w-4" />} label="Total students" value={data.overview.total_students} />
          <Stat icon={<GraduationCap className="h-4 w-4" />} label="Faculty" value={data.overview.total_faculty} />
          <Stat icon={<Brain className="h-4 w-4" />} label="Predictions" value={data.overview.total_predictions} />
          <Stat
            icon={<ShieldAlert className="h-4 w-4" />}
            label="High-risk %"
            value={formatPercent(data.overview.high_risk_pct, 1)}
            tone="danger"
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Risk distribution" />
          <CardBody>
            {isLoading || !data ? <Skeleton className="h-60" /> : <RiskDistributionChart data={data.risk_distribution} />}
          </CardBody>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader
            title="Department risk"
            actions={
              <Link to="/analytics" className="btn-ghost text-xs">
                Open analytics <ArrowUpRight className="h-3 w-3" />
              </Link>
            }
          />
          <CardBody>
            {isLoading || !data ? <Skeleton className="h-72" /> : <DepartmentRiskChart data={data.department_risk} />}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Attendance by semester" subtitle="Average attendance % across all students grouped by semester." />
        <CardBody>
          {isLoading || !data ? <Skeleton className="h-60" /> : <AttendanceTrendChart data={data.attendance_trends} />}
        </CardBody>
      </Card>
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
  tone = 'default',
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  tone?: 'default' | 'danger';
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between text-xs text-ink-muted">
        <span>{label}</span>
        <span className={tone === 'danger' ? 'text-risk-high' : 'text-primary-500'}>{icon}</span>
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

export const FacultyDashboardPage = DashboardPage;
