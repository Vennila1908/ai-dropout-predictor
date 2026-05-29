import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { DepartmentRisk } from '@/types';
import { RISK_COLORS } from '@/lib/utils';

export function DepartmentRiskChart({ data }: { data: DepartmentRisk[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
        <XAxis dataKey="department_code" stroke="hsl(var(--ink-muted))" tickLine={false} />
        <YAxis stroke="hsl(var(--ink-muted))" tickLine={false} allowDecimals={false} />
        <Tooltip />
        <Legend />
        <Bar dataKey="low" name="Low" stackId="risk" fill={RISK_COLORS.low} radius={[6, 6, 0, 0]} />
        <Bar dataKey="medium" name="Medium" stackId="risk" fill={RISK_COLORS.medium} />
        <Bar dataKey="high" name="High" stackId="risk" fill={RISK_COLORS.high} />
      </BarChart>
    </ResponsiveContainer>
  );
}
