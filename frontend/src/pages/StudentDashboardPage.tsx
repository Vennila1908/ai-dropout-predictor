import { useQuery } from '@tanstack/react-query';
import { CalendarClock, ClipboardCheck, GraduationCap, Percent, TrendingUp } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '@/components/ui/Badge';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { counselingApi } from '@/features/counseling/counselingApi';
import { studentsApi } from '@/features/students/studentsApi';
import { useAuth } from '@/hooks/useAuth';
import { formatDate, formatPercent } from '@/lib/utils';
import type { CounselingSession } from '@/types';

function metricTone(value: number, goodAt: number, warningAt: number): 'low' | 'medium' | 'high' {
  if (value >= goodAt) return 'low';
  if (value >= warningAt) return 'medium';
  return 'high';
}

function MetricCard({
  label,
  value,
  helper,
  icon,
  tone = 'neutral',
}: {
  label: string;
  value: string;
  helper: string;
  icon: ReactNode;
  tone?: 'low' | 'medium' | 'high' | 'neutral';
}) {
  const barClass =
    tone === 'low'
      ? 'bg-risk-low'
      : tone === 'medium'
        ? 'bg-risk-medium'
        : tone === 'high'
          ? 'bg-risk-high'
          : 'bg-primary-500';

  return (
    <div className="rounded-lg border bg-surface-subtle/40 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-sm font-medium text-ink-muted">{label}</div>
        <div className="rounded-md bg-surface p-2 text-primary-500">{icon}</div>
      </div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-inset">
        <div className={`h-full rounded-full ${barClass}`} style={{ width: value.endsWith('%') ? value : '100%' }} />
      </div>
      <p className="mt-2 text-xs text-ink-muted">{helper}</p>
    </div>
  );
}

function CounselingItem({ session }: { session: CounselingSession }) {
  return (
    <li className="rounded-lg border bg-surface-subtle/40 p-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-ink-muted">
        <Badge>{formatDate(session.created_at)}</Badge>
        {session.next_followup && <Badge variant="medium">Follow-up: {session.next_followup}</Badge>}
      </div>
      <p className="mt-2 text-sm text-ink">{session.outcome || 'Outcome pending'}</p>
      {session.notes && <p className="mt-1 text-xs text-ink-muted">{session.notes}</p>}
    </li>
  );
}

export function StudentDashboardPage() {
  const { user } = useAuth();

  const studentQuery = useQuery({
    queryKey: ['students', 'me'],
    queryFn: studentsApi.me,
    retry: false,
  });

  const student = studentQuery.data;
  const counselingQuery = useQuery({
    queryKey: ['counseling', student?.id],
    queryFn: () => counselingApi.forStudent(student!.id),
    enabled: !!student?.id,
  });

  const sessions = counselingQuery.data ?? [];
  const latestOutcome = sessions.find((session) => Boolean(session.outcome));

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold">Welcome, {user?.full_name?.split(' ')[0] ?? 'student'}</h1>
        <p className="text-sm text-ink-muted">Your personal performance and counseling reference.</p>
      </header>

      {studentQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      ) : !student ? (
        <EmptyState
          title="Student record not linked"
          description="Ask an administrator to connect your login account to your roll number, then this dashboard will show your attendance, internal marks, and counseling outcomes."
          icon={<GraduationCap className="h-6 w-6" />}
          action={
            <Link to="/settings" className="btn-secondary">
              Open settings
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard
              label="Attendance"
              value={formatPercent(student.attendance_pct, 1)}
              helper={`Semester ${student.semester} attendance`}
              tone={metricTone(student.attendance_pct, 75, 60)}
              icon={<Percent className="h-4 w-4" />}
            />
            <MetricCard
              label="Internal marks"
              value={formatPercent(student.internal_marks, 1)}
              helper="Latest internal assessment score"
              tone={metricTone(student.internal_marks, 70, 50)}
              icon={<ClipboardCheck className="h-4 w-4" />}
            />
            <MetricCard
              label="Semester marks"
              value={formatPercent(student.semester_marks, 1)}
              helper={`${student.backlogs} backlog${student.backlogs === 1 ? '' : 's'} recorded`}
              tone={metricTone(student.semester_marks, 70, 50)}
              icon={<TrendingUp className="h-4 w-4" />}
            />
          </div>

          <div className="grid gap-5 xl:grid-cols-[1fr_1.2fr]">
            <Card>
              <CardHeader title="Academic profile" subtitle={`${student.roll_no} · ${student.name}`} />
              <CardBody>
                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-ink-muted">Department</dt>
                    <dd className="mt-1 font-medium">{student.department_name ?? student.department_code ?? 'Not assigned'}</dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">Current risk</dt>
                    <dd className="mt-1">
                      {student.latest_risk ? (
                        <Badge variant={student.latest_risk}>{student.latest_risk} risk</Badge>
                      ) : (
                        <Badge>No prediction</Badge>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">Fee status</dt>
                    <dd className="mt-1 font-medium">{student.fee_paid ? 'Paid' : `${student.fee_delay_days} days delayed`}</dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">Placement readiness</dt>
                    <dd className="mt-1">
                      <Badge variant={student.placement_readiness}>{student.placement_readiness}</Badge>
                    </dd>
                  </div>
                </dl>
                {student.counselor_remarks && (
                  <div className="mt-4 rounded-lg border bg-surface-subtle/40 p-3 text-sm">
                    <div className="mb-1 font-medium">Counselor remarks</div>
                    <p className="text-ink-muted">{student.counselor_remarks}</p>
                  </div>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader
                title="Counseling outcomes"
                subtitle={latestOutcome ? `Latest outcome from ${formatDate(latestOutcome.created_at)}` : 'Most recent sessions first'}
                actions={<CalendarClock className="h-4 w-4 text-ink-muted" />}
              />
              <CardBody>
                {counselingQuery.isLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-20" />
                    <Skeleton className="h-20" />
                  </div>
                ) : sessions.length === 0 ? (
                  <p className="text-sm text-ink-muted">No counseling sessions have been logged for your profile yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {sessions.slice(0, 4).map((session) => (
                      <CounselingItem key={session.id} session={session} />
                    ))}
                  </ul>
                )}
              </CardBody>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
