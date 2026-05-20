import { Table, type Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { formatPercent, riskClass } from '@/lib/utils';
import type { Student } from '@/types';

const COLS: Column<Student>[] = [
  { key: 'roll_no', header: 'Roll', cell: (s) => <span className="font-mono text-xs">{s.roll_no}</span> },
  {
    key: 'name',
    header: 'Name',
    cell: (s) => (
      <div className="min-w-0">
        <div className="truncate font-medium">{s.name}</div>
        <div className="truncate text-xs text-ink-muted">
          Sem {s.semester} · {s.department_code ?? '—'}
        </div>
      </div>
    ),
  },
  { key: 'attendance', header: 'Attendance', cell: (s) => formatPercent(s.attendance_pct), align: 'right' },
  { key: 'internal', header: 'Internal', cell: (s) => s.internal_marks.toFixed(0), align: 'right' },
  { key: 'backlogs', header: 'Backlogs', cell: (s) => s.backlogs, align: 'right' },
  {
    key: 'risk',
    header: 'Risk',
    cell: (s) =>
      s.latest_risk ? (
        <span className={riskClass(s.latest_risk)}>{s.latest_risk}</span>
      ) : (
        <Badge>not predicted</Badge>
      ),
  },
];

export function StudentTable({ rows, onRowClick }: { rows: Student[]; onRowClick?: (s: Student) => void }) {
  return <Table columns={COLS} rows={rows} onRowClick={onRowClick} empty="No students match these filters." />;
}
