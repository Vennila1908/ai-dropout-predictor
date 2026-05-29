import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import type { Student } from '@/types';
import { formatDate, formatPercent, riskClass } from '@/lib/utils';

export function StudentDetailDrawer({
  open,
  onClose,
  student,
}: {
  open: boolean;
  onClose: () => void;
  student: Student | null;
}) {
  if (!student) return null;
  return (
    <Modal open={open} onClose={onClose} title={student.name} widthClass="max-w-2xl">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="font-mono text-xs">{student.roll_no}</span>
          <Badge>Sem {student.semester}</Badge>
          {student.department_code && <Badge>{student.department_code}</Badge>}
          {student.latest_risk && <span className={riskClass(student.latest_risk)}>{student.latest_risk} risk</span>}
        </div>
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <Row k="Attendance" v={formatPercent(student.attendance_pct)} />
          <Row k="Internal marks" v={student.internal_marks.toFixed(0)} />
          <Row k="Semester marks" v={student.semester_marks.toFixed(0)} />
          <Row k="Backlogs" v={String(student.backlogs)} />
          <Row k="Fee paid" v={student.fee_paid ? 'Yes' : 'No'} />
          <Row k="Fee delay (days)" v={String(student.fee_delay_days)} />
          <Row k="Financial status" v={student.financial_status} />
          <Row k="Placement readiness" v={student.placement_readiness} />
          <Row k="Updated" v={formatDate(student.updated_at)} />
        </dl>
        {student.counselor_remarks && (
          <section>
            <h4 className="mb-1 text-sm font-semibold">Counselor remarks</h4>
            <p className="text-sm text-ink-muted">{student.counselor_remarks}</p>
          </section>
        )}
      </div>
    </Modal>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-ink-muted">{k}</dt>
      <dd className="font-medium">{v}</dd>
    </div>
  );
}
