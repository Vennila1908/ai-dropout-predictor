import { useMemo, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, Check, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { FileDropzone } from '@/components/ui/FileDropzone';
import { uploadsApi } from '@/features/uploads/uploadsApi';
import type { UploadPreview } from '@/types';
import { ColumnMappingStep } from './ColumnMappingStep';
import { PreviewStep } from './PreviewStep';

type Step = 'pick' | 'map' | 'review';

export function UploadWizard({ onDone }: { onDone?: (rows: number) => void }) {
  const [step, setStep] = useState<Step>('pick');
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});

  const previewMut = useMutation({
    mutationFn: (file: File) => uploadsApi.preview(file),
    onSuccess: (data) => {
      setPreview(data);
      const seed: Record<string, string> = {};
      for (const s of data.suggested_mapping) if (s.target) seed[s.source] = s.target;
      setMapping(seed);
      setStep('map');
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Upload failed'),
  });

  const confirmMut = useMutation({
    mutationFn: () => uploadsApi.confirm(preview!.upload_id, mapping),
    onSuccess: (res) => {
      toast.success(`Imported ${res.rows_imported} rows (${res.rows_skipped} skipped)`);
      onDone?.(res.rows_imported);
      reset();
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Import failed'),
  });

  const mappedCount = useMemo(() => Object.values(mapping).filter(Boolean).length, [mapping]);

  function reset() {
    setStep('pick');
    setPreview(null);
    setMapping({});
  }

  return (
    <div className="space-y-4">
      <Stepper step={step} />
      {step === 'pick' && (
        <FileDropzone onFile={(f) => previewMut.mutate(f)} disabled={previewMut.isPending} />
      )}
      {step === 'map' && preview && (
        <ColumnMappingStep preview={preview} mapping={mapping} onChange={setMapping} />
      )}
      {step === 'review' && preview && <PreviewStep preview={preview} mapping={mapping} />}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button variant="ghost" icon={<RotateCcw className="h-4 w-4" />} onClick={reset}>
          Start over
        </Button>
        <div className="flex items-center gap-2">
          {step === 'map' && (
            <>
              <Button variant="secondary" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => setStep('pick')}>
                Back
              </Button>
              <Button
                onClick={() => setStep('review')}
                disabled={mappedCount < 2}
                icon={<ArrowRight className="h-4 w-4" />}
              >
                Review ({mappedCount} cols)
              </Button>
            </>
          )}
          {step === 'review' && (
            <>
              <Button variant="secondary" icon={<ArrowLeft className="h-4 w-4" />} onClick={() => setStep('map')}>
                Back
              </Button>
              <Button onClick={() => confirmMut.mutate()} loading={confirmMut.isPending} icon={<Check className="h-4 w-4" />}>
                Import
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Stepper({ step }: { step: Step }) {
  const steps: { id: Step; label: string }[] = [
    { id: 'pick', label: '1. Drop file' },
    { id: 'map', label: '2. Map columns' },
    { id: 'review', label: '3. Review & import' },
  ];
  return (
    <ol className="flex items-center gap-2 text-xs">
      {steps.map((s, i) => {
        const idx = steps.findIndex((x) => x.id === step);
        const active = i <= idx;
        return (
          <li
            key={s.id}
            className={`flex items-center gap-2 rounded-full px-3 py-1 ${
              active ? 'bg-primary-500/10 text-primary-700 dark:text-primary-300' : 'bg-surface-subtle text-ink-muted'
            }`}
          >
            {s.label}
          </li>
        );
      })}
    </ol>
  );
}
