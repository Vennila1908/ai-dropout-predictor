import { ArrowDown, ArrowUp, Minus } from 'lucide-react';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import type { Prediction } from '@/types';
import { cn } from '@/lib/utils';

export function ExplainabilityPanel({ prediction }: { prediction: Prediction | null }) {
  if (!prediction) return null;
  const factors = prediction.explanation?.top_factors ?? [];

  return (
    <Card>
      <CardHeader title="Why this risk" subtitle="Top contributing factors for this student." />
      <CardBody>
        {factors.length === 0 ? (
          <p className="text-sm text-ink-muted">No contribution data available.</p>
        ) : (
          <ul className="space-y-2.5">
            {factors.map((f) => (
              <li key={f.feature} className="flex items-center justify-between gap-3 rounded-lg bg-surface-subtle/60 px-3 py-2">
                <div className="min-w-0">
                  <div className="font-medium">{f.feature}</div>
                  <div className="text-xs text-ink-muted">value: {String(f.value)}</div>
                </div>
                <div
                  className={cn(
                    'flex items-center gap-1 text-sm font-semibold',
                    f.direction === 'increases_risk' && 'text-risk-high',
                    f.direction === 'decreases_risk' && 'text-risk-low',
                    f.direction === 'neutral' && 'text-ink-muted',
                  )}
                >
                  {f.direction === 'increases_risk' && <ArrowUp className="h-4 w-4" />}
                  {f.direction === 'decreases_risk' && <ArrowDown className="h-4 w-4" />}
                  {f.direction === 'neutral' && <Minus className="h-4 w-4" />}
                  {f.contribution >= 0 ? '+' : ''}
                  {f.contribution.toFixed(3)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
