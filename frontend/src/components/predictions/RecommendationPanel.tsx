import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Sparkles, CheckCircle2, Circle, PauseCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { recommendationsApi } from '@/features/recommendations/recommendationsApi';
import type { Recommendation } from '@/types';
import { formatDate } from '@/lib/utils';

const STATUS_ICONS: Record<Recommendation['status'], React.ComponentType<{ className?: string }>> = {
  pending: Circle,
  in_progress: PauseCircle,
  completed: CheckCircle2,
  dismissed: XCircle,
};

export function RecommendationPanel({ studentId }: { studentId: number }) {
  const qc = useQueryClient();

  const { data: list = [], isLoading } = useQuery({
    queryKey: ['recommendations', studentId],
    queryFn: () => recommendationsApi.forStudent(studentId),
  });

  const generate = useMutation({
    mutationFn: () => recommendationsApi.generate(studentId),
    onSuccess: () => {
      toast.success('Recommendation generated');
      qc.invalidateQueries({ queryKey: ['recommendations', studentId] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Generation failed'),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: Recommendation['status'] }) =>
      recommendationsApi.update(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations', studentId] }),
  });

  const latest = list[0] ?? null;

  return (
    <Card>
      <CardHeader
        title="Recommendation"
        subtitle="Personalized intervention plan."
        actions={
          <Button icon={<Sparkles className="h-4 w-4" />} loading={generate.isPending} onClick={() => generate.mutate()}>
            Generate
          </Button>
        }
      />
      <CardBody>
        {isLoading && <p className="text-sm text-ink-muted">Loading recommendations…</p>}
        {!isLoading && !latest && (
          <p className="text-sm text-ink-muted">
            No recommendation yet. Click <strong>Generate</strong> to create one (uses local Ollama if running, falls back to a deterministic plan otherwise).
          </p>
        )}
        {latest && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={latest.source === 'llm' ? 'low' : 'neutral'}>
                {latest.source === 'llm' ? 'AI-generated' : 'offline fallback'}
              </Badge>
              <Badge>{latest.status}</Badge>
              <span className="text-xs text-ink-muted">{formatDate(latest.created_at)}</span>
            </div>
            <p className="text-sm">{latest.summary}</p>

            <Section title="Intervention plan">
              {latest.plan.intervention_plan.length === 0 ? (
                <p className="text-xs text-ink-muted">No actions.</p>
              ) : (
                <ul className="space-y-1.5">
                  {latest.plan.intervention_plan.map((a, i) => (
                    <li key={i} className="text-sm">
                      <span className="font-medium">{a.action}</span>
                      <span className="ml-2 text-xs text-ink-muted">
                        {a.owner} · {a.timeline}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {latest.plan.faculty_actions.length > 0 && (
              <Section title="Faculty actions">
                <ul className="list-inside list-disc text-sm text-ink-muted">
                  {latest.plan.faculty_actions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </Section>
            )}

            {latest.plan.student_roadmap.length > 0 && (
              <Section title="Student roadmap">
                <div className="grid gap-2 sm:grid-cols-2">
                  {latest.plan.student_roadmap.map((w) => (
                    <div key={w.week} className="rounded-lg border bg-surface-subtle/40 p-3">
                      <div className="text-xs font-semibold uppercase tracking-wide text-primary-600">
                        Week {w.week}
                      </div>
                      <div className="text-sm font-medium">{w.focus}</div>
                      <ul className="mt-1 list-inside list-disc text-xs text-ink-muted">
                        {w.activities.map((a, i) => (
                          <li key={i}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            <div className="flex flex-wrap items-center gap-2 pt-2">
              {(['pending', 'in_progress', 'completed', 'dismissed'] as const).map((s) => {
                const Icon = STATUS_ICONS[s];
                const active = latest.status === s;
                return (
                  <button
                    key={s}
                    className={`btn ${active ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setStatus.mutate({ id: latest.id, status: s })}
                  >
                    <Icon className="h-3.5 w-3.5" /> {s.replace('_', ' ')}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</h4>
      {children}
    </div>
  );
}
