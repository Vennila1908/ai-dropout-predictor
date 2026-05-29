import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { AttendanceTrendPoint } from '@/types';

export function AttendanceTrendChart({ data }: { data: AttendanceTrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 10, right: 16, left: -8, bottom: 4 }}>
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
        <XAxis dataKey="semester" stroke="hsl(var(--ink-muted))" tickLine={false} />
        <YAxis stroke="hsl(var(--ink-muted))" tickLine={false} domain={[0, 100]} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="avg_attendance"
          name="Avg Attendance %"
          stroke="#6366f1"
          strokeWidth={2.5}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
