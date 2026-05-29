import { useQuery } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart';
import { DepartmentRiskChart } from '@/components/charts/DepartmentRiskChart';
import { AttendanceTrendChart } from '@/components/charts/AttendanceTrendChart';
import { analyticsApi } from '@/features/analytics/analyticsApi';

export function AnalyticsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['analytics', 'bundle'], queryFn: () => analyticsApi.bundle() });

  if (isLoading || !data) return <Skeleton className="h-96" />;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-ink-muted">Cohort-level insights at a glance.</p>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader title="Risk distribution" />
          <CardBody><RiskDistributionChart data={data.risk_distribution} /></CardBody>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader title="Department risk" />
          <CardBody><DepartmentRiskChart data={data.department_risk} /></CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Average attendance by semester" />
          <CardBody><AttendanceTrendChart data={data.attendance_trends} /></CardBody>
        </Card>
        <Card>
          <CardHeader title="Prediction confidence" subtitle="How sure was the model on its latest predictions?" />
          <CardBody>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.confidence_distribution}>
                <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
                <XAxis dataKey="bucket" stroke="hsl(var(--ink-muted))" />
                <YAxis stroke="hsl(var(--ink-muted))" allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
