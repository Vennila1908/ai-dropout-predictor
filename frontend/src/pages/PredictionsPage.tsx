import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Brain, Layers, Wand2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { FeatureImportanceChart } from '@/components/charts/FeatureImportanceChart';
import { predictionsApi } from '@/features/predictions/predictionsApi';
import { formatDate } from '@/lib/utils';

export function PredictionsPage() {
  const qc = useQueryClient();
  const [batchRunning, setBatchRunning] = useState(false);

  const { data: status, isLoading } = useQuery({
    queryKey: ['ml', 'status'],
    queryFn: () => predictionsApi.mlStatus(),
  });

  const train = useMutation({
    mutationFn: () => predictionsApi.trainModel(),
    onSuccess: () => {
      toast.success('Training scheduled in the background.');
      setTimeout(() => qc.invalidateQueries({ queryKey: ['ml', 'status'] }), 4000);
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Training failed'),
  });

  const batch = useMutation({
    mutationFn: () => predictionsApi.batch({}),
    onMutate: () => setBatchRunning(true),
    onSettled: () => setBatchRunning(false),
    onSuccess: (res) => {
      toast.success(`Predicted ${res.succeeded} of ${res.total} students.`);
      qc.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Batch prediction failed'),
  });

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Predictions & Model</h1>
          <p className="text-sm text-ink-muted">Manage the ML model and run predictions across the cohort.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" icon={<Wand2 className="h-4 w-4" />} loading={train.isPending} onClick={() => train.mutate()}>
            Retrain model
          </Button>
          <Button icon={<Layers className="h-4 w-4" />} loading={batchRunning} onClick={() => batch.mutate()}>
            Run for all students
          </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Active model" subtitle="The artifact currently used for inference." />
          <CardBody className="space-y-2 text-sm">
            {isLoading ? (
              <Skeleton className="h-32" />
            ) : !status?.artifact_present ? (
              <p className="text-ink-muted">No model artifact yet. Click <strong>Retrain model</strong> to bootstrap one.</p>
            ) : (
              <>
                <Stat k="Model" v={status.model_name ?? '—'} />
                <Stat k="Trained" v={formatDate(status.trained_at ?? null)} />
                <Stat k="Macro-F1" v={String((status.metrics as { macro_f1?: number })?.macro_f1?.toFixed?.(3) ?? '—')} />
                <Stat k="Accuracy" v={String((status.metrics as { accuracy?: number })?.accuracy?.toFixed?.(3) ?? '—')} />
                <Stat k="Classes" v={status.class_labels.join(', ')} />
                <Stat k="# features" v={String(status.feature_list.length)} />
              </>
            )}
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Feature importance" subtitle="Cohort-level — which features matter most for risk." actions={<Brain className="h-4 w-4 text-ink-muted" />} />
          <CardBody>
            {isLoading ? (
              <Skeleton className="h-72" />
            ) : !status?.feature_importances?.length ? (
              <p className="text-sm text-ink-muted">No importances available.</p>
            ) : (
              <FeatureImportanceChart data={status.feature_importances} />
            )}
          </CardBody>
        </Card>
      </div>

      {status?.confusion_matrix?.length ? (
        <Card>
          <CardHeader title="Confusion matrix (held-out test split)" />
          <CardBody>
            <ConfusionMatrix matrix={status.confusion_matrix} labels={status.class_labels} />
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-ink-muted">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}

function ConfusionMatrix({ matrix, labels }: { matrix: number[][]; labels: string[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full border-collapse text-center text-xs">
        <thead className="bg-surface-subtle text-ink-muted">
          <tr>
            <th className="px-3 py-2"></th>
            {labels.map((l) => (
              <th key={l} className="px-3 py-2 font-mono">pred:{l}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i} className="border-t">
              <th className="bg-surface-subtle px-3 py-2 font-mono text-xs">true:{labels[i]}</th>
              {row.map((cell, j) => (
                <td key={j} className={`px-3 py-2 ${i === j ? 'bg-primary-500/10 font-semibold text-primary-700 dark:text-primary-300' : ''}`}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
