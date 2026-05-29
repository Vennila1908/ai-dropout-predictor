import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

export function Table<T extends { id: number | string }>({
  columns,
  rows,
  empty = 'No rows',
  onRowClick,
}: {
  columns: Column<T>[];
  rows: T[];
  empty?: ReactNode;
  onRowClick?: (row: T) => void;
}) {
  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-dashed py-12 text-sm text-ink-muted">
        {empty}
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-xl border bg-surface">
      <table className="w-full text-sm">
        <thead className="bg-surface-subtle text-ink-muted">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn(
                  'whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide',
                  c.align === 'right' && 'text-right',
                  c.align === 'center' && 'text-center',
                  c.align !== 'right' && c.align !== 'center' && 'text-left',
                )}
                style={{ width: c.width }}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={String(row.id)}
              onClick={() => onRowClick?.(row)}
              className={cn(
                'border-t hover:bg-surface-subtle/60',
                onRowClick && 'cursor-pointer',
              )}
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    'px-4 py-2.5 align-middle',
                    c.align === 'right' && 'text-right',
                    c.align === 'center' && 'text-center',
                  )}
                >
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
