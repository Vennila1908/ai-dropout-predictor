import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import type { UploadPreview } from '@/types';

export function ColumnMappingStep({
  preview,
  mapping,
  onChange,
}: {
  preview: UploadPreview;
  mapping: Record<string, string>;
  onChange: (m: Record<string, string>) => void;
}) {
  const targetOptions = [
    { value: '', label: '— ignore —' },
    ...preview.target_fields.map((t) => ({ value: t, label: t })),
  ];

  return (
    <Card>
      <CardHeader
        title="Column mapping"
        subtitle="Suggested mappings come from a fuzzy match. Adjust any that look off."
      />
      <CardBody className="space-y-3">
        {preview.suggested_mapping.map((s) => (
          <div key={s.source} className="grid grid-cols-1 items-center gap-3 sm:grid-cols-[1fr,auto,1fr]">
            <div className="min-w-0">
              <div className="truncate font-medium">{s.source}</div>
              {s.candidates.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1 text-xs text-ink-muted">
                  Candidates: {s.candidates.map((c) => <Badge key={c} className="font-mono">{c}</Badge>)}
                </div>
              )}
            </div>
            <span className="hidden text-xs text-ink-muted sm:inline">→</span>
            <Select
              value={mapping[s.source] ?? ''}
              onChange={(e) => onChange({ ...mapping, [s.source]: e.target.value })}
              options={targetOptions}
              hint={s.target ? `Suggested: ${s.target} (${s.score.toFixed(0)})` : undefined}
            />
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
