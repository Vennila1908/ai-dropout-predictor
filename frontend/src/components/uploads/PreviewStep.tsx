import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import type { UploadPreview } from '@/types';

export function PreviewStep({ preview, mapping }: { preview: UploadPreview; mapping: Record<string, string> }) {
  const cols = preview.detected_columns.filter((c) => mapping[c]);
  const rows = preview.preview_rows.slice(0, 10);

  return (
    <Card>
      <CardHeader
        title="Preview"
        subtitle={`Showing ${rows.length} of ${preview.total_rows} rows. Mapped columns: ${cols.length}.`}
      />
      <CardBody>
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-xs">
            <thead className="bg-surface-subtle text-ink-muted">
              <tr>
                {cols.map((c) => (
                  <th key={c} className="whitespace-nowrap px-3 py-2 text-left">
                    <div className="font-mono">{c}</div>
                    <div className="text-[10px] text-ink-muted">→ {mapping[c]}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-t">
                  {cols.map((c) => (
                    <td key={c} className="px-3 py-1.5 align-top">
                      {String(r[c] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardBody>
    </Card>
  );
}
