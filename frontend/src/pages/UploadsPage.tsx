import { useQuery } from '@tanstack/react-query';
import { History } from 'lucide-react';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { UploadWizard } from '@/components/uploads/UploadWizard';
import { uploadsApi } from '@/features/uploads/uploadsApi';
import { formatDate } from '@/lib/utils';

export function UploadsPage() {
  const { data: history, isLoading, refetch } = useQuery({
    queryKey: ['uploads', 'history'],
    queryFn: () => uploadsApi.history(),
  });

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Imports</h1>
        <p className="text-sm text-ink-muted">
          Upload CSV / Excel / PDF / DOCX files. Columns are auto-mapped via fuzzy matching, then you confirm before any
          row reaches the database.
        </p>
      </header>

      <Card>
        <CardHeader title="Upload wizard" subtitle="3 steps: drop file → map columns → preview & confirm." />
        <CardBody>
          <UploadWizard onDone={() => refetch()} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Recent uploads"
          subtitle="Audit trail of every file imported."
          actions={<History className="h-4 w-4 text-ink-muted" />}
        />
        <CardBody>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
            </div>
          ) : !history || history.length === 0 ? (
            <p className="text-sm text-ink-muted">No uploads yet.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead className="bg-surface-subtle text-ink-muted">
                  <tr>
                    <th className="px-3 py-2 text-left">When</th>
                    <th className="px-3 py-2 text-left">File</th>
                    <th className="px-3 py-2 text-left">Type</th>
                    <th className="px-3 py-2 text-right">Size</th>
                    <th className="px-3 py-2 text-right">Rows</th>
                    <th className="px-3 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((u) => (
                    <tr key={u.id} className="border-t">
                      <td className="px-3 py-2">{formatDate(u.created_at)}</td>
                      <td className="px-3 py-2"><span className="font-mono text-xs">{u.original_name}</span></td>
                      <td className="px-3 py-2 uppercase text-ink-muted">{u.file_type}</td>
                      <td className="px-3 py-2 text-right">{(u.size_bytes / 1024).toFixed(1)} KB</td>
                      <td className="px-3 py-2 text-right">{u.rows_imported}</td>
                      <td className="px-3 py-2">
                        <Badge
                          variant={u.status === 'imported' ? 'low' : u.status === 'failed' ? 'high' : 'neutral'}
                        >
                          {u.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
