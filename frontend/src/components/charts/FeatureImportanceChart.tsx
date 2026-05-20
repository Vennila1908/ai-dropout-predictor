import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export function FeatureImportanceChart({ data }: { data: FeatureImportance[] }) {
  const top = [...data].sort((a, b) => b.importance - a.importance).slice(0, 10);
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, top.length * 28 + 40)}>
      <BarChart data={top} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
        <XAxis type="number" stroke="hsl(var(--ink-muted))" tickLine={false} />
        <YAxis type="category" dataKey="feature" width={120} stroke="hsl(var(--ink-muted))" tickLine={false} />
        <Tooltip />
        <Bar dataKey="importance" fill="#6366f1" radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
