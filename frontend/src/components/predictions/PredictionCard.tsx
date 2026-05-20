import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { RiskMeter } from '@/components/charts/RiskMeter';
import { formatDate } from '@/lib/utils';
import type { Prediction } from '@/types';

export function PredictionCard({ prediction }: { prediction: Prediction | null }) {
  if (!prediction) {
    return (
      <Card>
        <CardHeader title="Latest prediction" subtitle="No prediction has been generated yet." />
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader
        title="Latest prediction"
        subtitle={`Model: ${prediction.model_version} · ${formatDate(prediction.created_at)}`}
      />
      <CardBody>
        <RiskMeter level={prediction.risk_level} confidence={prediction.confidence} />
        {prediction.explanation?.narrative && (
          <p className="mt-4 text-sm text-ink-muted">{prediction.explanation.narrative}</p>
        )}
      </CardBody>
    </Card>
  );
}
