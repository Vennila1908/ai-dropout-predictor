import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ClipboardList, Plus } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Modal } from '@/components/ui/Modal';
import { Badge } from '@/components/ui/Badge';
import { studentsApi } from '@/features/students/studentsApi';
import { api, unwrap } from '@/lib/api';
import type { CounselingSession } from '@/types';
import { formatDate } from '@/lib/utils';

const schema = z.object({
  student_id: z.coerce.number().int().min(1, 'Pick a student'),
  notes: z.string().min(3),
  outcome: z.string().optional(),
  next_followup: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export function CounselingPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [activeStudentId, setActiveStudentId] = useState<number | null>(null);

  const { data: students } = useQuery({
    queryKey: ['students', 'short'],
    queryFn: () => studentsApi.list({ page: 1, page_size: 200 }),
  });

  useEffect(() => {
    if (!activeStudentId && students?.items.length) setActiveStudentId(students.items[0].id);
  }, [students, activeStudentId]);

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['counseling', activeStudentId],
    queryFn: () =>
      activeStudentId
        ? unwrap(api.get<CounselingSession[]>(`/counseling/student/${activeStudentId}`))
        : Promise.resolve([] as CounselingSession[]),
    enabled: !!activeStudentId,
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { student_id: activeStudentId ?? 0, notes: '', outcome: '', next_followup: '' },
  });

  useEffect(() => {
    if (activeStudentId) reset({ student_id: activeStudentId, notes: '', outcome: '', next_followup: '' });
  }, [activeStudentId, reset]);

  const create = useMutation({
    mutationFn: (v: FormValues) =>
      unwrap(api.post<CounselingSession>('/counseling', {
        ...v,
        next_followup: v.next_followup || null,
        outcome: v.outcome || null,
      })),
    onSuccess: () => {
      toast.success('Session logged');
      setOpen(false);
      qc.invalidateQueries({ queryKey: ['counseling', activeStudentId] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Save failed'),
  });

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Counseling</h1>
          <p className="text-sm text-ink-muted">Log conversations and follow-ups against each student.</p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} onClick={() => setOpen(true)}>
          New session
        </Button>
      </header>

      <Card>
        <CardHeader title="Filter by student" />
        <CardBody>
          <select
            className="input max-w-md"
            value={activeStudentId ?? ''}
            onChange={(e) => setActiveStudentId(Number(e.target.value))}
          >
            {(students?.items ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.roll_no} — {s.name}
              </option>
            ))}
          </select>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Sessions" subtitle="Most recent first." actions={<ClipboardList className="h-4 w-4 text-ink-muted" />} />
        <CardBody>
          {isLoading ? (
            <p className="text-sm text-ink-muted">Loading…</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-ink-muted">No sessions logged for this student yet.</p>
          ) : (
            <ul className="space-y-3">
              {sessions.map((s) => (
                <li key={s.id} className="rounded-lg border bg-surface-subtle/40 p-3">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-ink-muted">
                    <Badge>{formatDate(s.created_at)}</Badge>
                    {s.next_followup && <Badge variant="medium">Follow-up: {s.next_followup}</Badge>}
                  </div>
                  <p className="mt-1 text-sm">{s.notes}</p>
                  {s.outcome && <p className="mt-1 text-xs text-ink-muted">Outcome: {s.outcome}</p>}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Modal open={open} onClose={() => setOpen(false)} title="Log counseling session" widthClass="max-w-xl">
        <form onSubmit={handleSubmit((v) => create.mutate(v))} className="space-y-3">
          <Input
            type="number"
            label="Student id"
            error={errors.student_id?.message}
            {...register('student_id')}
          />
          <Textarea label="Notes" error={errors.notes?.message} {...register('notes')} />
          <Input label="Outcome (optional)" {...register('outcome')} />
          <Input type="date" label="Next follow-up (optional)" {...register('next_followup')} />
          <div className="flex justify-end pt-1">
            <Button type="submit" loading={create.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
