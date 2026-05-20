import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ClipboardList, Edit3, Play, Trash2 } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingScreen } from '@/components/common/LoadingScreen';
import { StudentForm } from '@/components/students/StudentForm';
import { PredictionCard } from '@/components/predictions/PredictionCard';
import { ExplainabilityPanel } from '@/components/predictions/ExplainabilityPanel';
import { RecommendationPanel } from '@/components/predictions/RecommendationPanel';
import { studentsApi } from '@/features/students/studentsApi';
import { predictionsApi } from '@/features/predictions/predictionsApi';
import { formatDate, formatPercent, riskClass } from '@/lib/utils';

export function StudentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const sid = Number(id);
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', sid],
    queryFn: () => studentsApi.get(sid),
    enabled: !Number.isNaN(sid),
  });

  const { data: latest } = useQuery({
    queryKey: ['prediction', 'latest', sid],
    queryFn: () => predictionsApi.latest(sid),
    enabled: !!student,
    retry: false,
  });

  const { data: timeline } = useQuery({
    queryKey: ['student', sid, 'timeline'],
    queryFn: () => studentsApi.timeline(sid),
    enabled: !!student,
  });

  const update = useMutation({
    mutationFn: (v: Parameters<typeof studentsApi.update>[1]) => studentsApi.update(sid, v),
    onSuccess: () => {
      toast.success('Updated');
      setEditing(false);
      qc.invalidateQueries({ queryKey: ['student', sid] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Update failed'),
  });

  const remove = useMutation({
    mutationFn: () => studentsApi.remove(sid),
    onSuccess: () => {
      toast.success('Deleted');
      navigate('/students');
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Delete failed'),
  });

  const runPredict = useMutation({
    mutationFn: () => predictionsApi.run(sid),
    onSuccess: () => {
      toast.success('Prediction generated');
      qc.invalidateQueries({ queryKey: ['prediction', 'latest', sid] });
      qc.invalidateQueries({ queryKey: ['student', sid] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Prediction failed'),
  });

  if (isLoading) return <LoadingScreen />;
  if (!student) {
    return (
      <div className="text-sm">
        Student not found. <button className="text-primary-600 hover:underline" onClick={() => navigate(-1)}>Go back</button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button className="btn-ghost" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
        <div className="flex flex-wrap gap-2">
          <Button icon={<Play className="h-4 w-4" />} loading={runPredict.isPending} onClick={() => runPredict.mutate()}>
            Run prediction
          </Button>
          <Button variant="secondary" icon={<Edit3 className="h-4 w-4" />} onClick={() => setEditing(true)}>
            Edit
          </Button>
          <Button variant="danger" icon={<Trash2 className="h-4 w-4" />} onClick={() => setConfirmDelete(true)}>
            Delete
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader
          title={
            <div className="flex flex-wrap items-center gap-2">
              <span>{student.name}</span>
              <span className="font-mono text-xs text-ink-muted">{student.roll_no}</span>
              <Badge>Sem {student.semester}</Badge>
              {student.department_code && <Badge>{student.department_code}</Badge>}
              {student.latest_risk && <span className={riskClass(student.latest_risk)}>{student.latest_risk} risk</span>}
            </div>
          }
          subtitle={`Last updated ${formatDate(student.updated_at)}`}
        />
        <CardBody>
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3 md:grid-cols-4">
            <Cell k="Attendance" v={formatPercent(student.attendance_pct)} />
            <Cell k="Internal" v={String(student.internal_marks)} />
            <Cell k="Semester" v={String(student.semester_marks)} />
            <Cell k="Backlogs" v={String(student.backlogs)} />
            <Cell k="Fee paid" v={student.fee_paid ? 'Yes' : 'No'} />
            <Cell k="Fee delay" v={`${student.fee_delay_days}d`} />
            <Cell k="Financial" v={student.financial_status} />
            <Cell k="Placement" v={student.placement_readiness} />
          </dl>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <PredictionCard prediction={latest ?? null} />
        <ExplainabilityPanel prediction={latest ?? null} />
      </div>

      <RecommendationPanel studentId={sid} />

      <Card>
        <CardHeader
          title="Timeline"
          subtitle="Predictions, counseling sessions, and faculty notes — newest first."
          actions={<ClipboardList className="h-4 w-4 text-ink-muted" />}
        />
        <CardBody>
          {!timeline || timeline.events.length === 0 ? (
            <p className="text-sm text-ink-muted">No timeline events yet.</p>
          ) : (
            <ol className="relative space-y-4 border-l pl-5">
              {timeline.events.map((e, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[26px] top-1.5 h-3 w-3 rounded-full bg-primary-500 ring-4 ring-surface" />
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <Badge>{e.type}</Badge>
                    <span className="font-medium">{e.title}</span>
                    <span className="text-xs text-ink-muted">{formatDate(e.timestamp)}</span>
                  </div>
                  {e.detail?.narrative && <p className="mt-1 text-sm text-ink-muted">{String(e.detail.narrative)}</p>}
                  {e.detail?.notes && <p className="mt-1 text-sm">{String(e.detail.notes)}</p>}
                </li>
              ))}
            </ol>
          )}
        </CardBody>
      </Card>

      <Modal open={editing} onClose={() => setEditing(false)} title="Edit student" widthClass="max-w-3xl">
        <StudentForm
          initial={student}
          onSubmit={(v) => update.mutateAsync(v)}
          loading={update.isPending}
          submitLabel="Save changes"
        />
      </Modal>

      <ConfirmDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        onConfirm={() => remove.mutate()}
        loading={remove.isPending}
        title="Delete student?"
        description={`This will remove ${student.name} and all related history. This cannot be undone.`}
        confirmLabel="Delete"
        variant="danger"
      />
    </div>
  );
}

function Cell({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-ink-muted">{k}</dt>
      <dd className="font-medium">{v}</dd>
    </div>
  );
}
