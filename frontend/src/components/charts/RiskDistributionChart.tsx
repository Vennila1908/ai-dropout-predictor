import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { RISK_COLORS } from '@/lib/utils';
import type { RiskBucket } from '@/types';

export function RiskDistributionChart({ data }: { data: RiskBucket[] }) {
  const safe = data.filter((d) => ['low', 'medium', 'high'].includes(d.risk_level));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={safe}
          dataKey="count"
          nameKey="risk_level"
          innerRadius={60}
          outerRadius={92}
          paddingAngle={2}
          label={(e) => `${e.risk_level}: ${e.count}`}
        >
          {safe.map((entry) => (
            <Cell
              key={entry.risk_level}
              fill={RISK_COLORS[entry.risk_level as 'low' | 'medium' | 'high']}
            />
          ))}
        </Pie>
        <Tooltip />
        <Legend verticalAlign="bottom" height={24} />
      </PieChart>
    </ResponsiveContainer>
  );
}
