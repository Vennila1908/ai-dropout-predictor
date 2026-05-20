import { Link } from 'react-router-dom';
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart';
import { Badge } from '@/components/ui/Badge';
import { formatPercent, riskClass } from '@/lib/utils';
import type { ChatArtifacts as ChatArtifactsData } from '@/features/chat/chatApi';
import type { Student } from '@/types';

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: 'danger' }) {
  return (
    <div className="rounded-lg border bg-surface px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-ink-muted">{label}</div>
      <div className={`mt-0.5 text-lg font-semibold ${tone === 'danger' ? 'text-risk-high' : ''}`}>{value}</div>
    </div>
  );
}

function MetricBadge({
  label,
  value,
  warn,
}: {
  label: string;
  value: string | number;
  warn?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs ${
        warn ? 'border-risk-high/30 bg-risk-high/10 text-risk-high' : 'bg-surface-subtle text-ink-muted'
      }`}
    >
      <span className="font-medium text-ink">{value}</span>
      <span>{label}</span>
    </span>
  );
}

function ChatStudentTable({ rows, total }: { rows: Student[]; total: number }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
          Matching students ({rows.length}
          {total > rows.length ? ` of ${total}` : ''})
        </h4>
      </div>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[520px] text-xs">
          <thead className="bg-surface-subtle text-ink-muted">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Roll</th>
              <th className="px-3 py-2 text-left font-medium">Name</th>
              <th className="px-3 py-2 text-left font-medium">Dept</th>
              <th className="px-3 py-2 text-right font-medium">Attend.</th>
              <th className="px-3 py-2 text-right font-medium">Internal</th>
              <th className="px-3 py-2 text-right font-medium">Backlogs</th>
              <th className="px-3 py-2 text-left font-medium">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id} className="border-t hover:bg-surface-subtle/60">
                <td className="px-3 py-2 font-mono">{s.roll_no}</td>
                <td className="px-3 py-2">
                  <Link to={`/students/${s.id}`} className="font-medium text-primary-600 hover:underline dark:text-primary-400">
                    {s.name}
                  </Link>
                  <div className="text-[10px] text-ink-muted">Sem {s.semester}</div>
                </td>
                <td className="px-3 py-2">{s.department_code ?? '—'}</td>
                <td className={`px-3 py-2 text-right ${s.attendance_pct < 60 ? 'text-risk-high font-medium' : ''}`}>
                  {formatPercent(s.attendance_pct, 0)}
                </td>
                <td className={`px-3 py-2 text-right ${s.internal_marks < 40 ? 'text-risk-high font-medium' : ''}`}>
                  {s.internal_marks.toFixed(0)}
                </td>
                <td className={`px-3 py-2 text-right ${s.backlogs >= 3 ? 'text-risk-high font-medium' : ''}`}>
                  {s.backlogs}
                </td>
                <td className="px-3 py-2">
                  {s.latest_risk ? (
                    <span className={riskClass(s.latest_risk)}>{s.latest_risk}</span>
                  ) : (
                    <Badge>—</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DepartmentRiskTable({ rows }: { rows: NonNullable<ChatArtifactsData['department_risk']> }) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Department risk</h4>
      <div className="space-y-2">
        {rows.map((d) => {
          const total = d.low + d.medium + d.high || 1;
          return (
            <div key={d.department_id} className="rounded-lg border px-3 py-2">
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-medium">{d.department_code}</span>
                <span className="text-ink-muted">{total} students</span>
              </div>
              <div className="flex h-2 overflow-hidden rounded-full bg-surface-subtle">
                <div className="bg-risk-low" style={{ width: `${(d.low / total) * 100}%` }} title={`Low: ${d.low}`} />
                <div className="bg-risk-medium" style={{ width: `${(d.medium / total) * 100}%` }} title={`Medium: ${d.medium}`} />
                <div className="bg-risk-high" style={{ width: `${(d.high / total) * 100}%` }} title={`High: ${d.high}`} />
              </div>
              <div className="mt-1 flex gap-2 text-[10px] text-ink-muted">
                <span>L {d.low}</span>
                <span>M {d.medium}</span>
                <span>H {d.high}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function ChatArtifactsView({ artifacts }: { artifacts: ChatArtifactsData }) {
  const hasOverview = Boolean(artifacts.overview);
  const hasStudents = Boolean(artifacts.students?.length);
  const hasRisk = Boolean(artifacts.risk_distribution?.length);
  const hasDepartments = Boolean(artifacts.department_risk?.length);

  if (!hasOverview && !hasStudents && !hasRisk && !hasDepartments) return null;

  return (
    <div className="mt-3 space-y-3 rounded-xl border bg-surface p-3">
      {artifacts.filters_applied && Object.keys(artifacts.filters_applied).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {'min_backlogs' in artifacts.filters_applied && (
            <MetricBadge label="backlogs" value={`≥ ${artifacts.filters_applied.min_backlogs}`} warn />
          )}
          {'max_attendance' in artifacts.filters_applied && (
            <MetricBadge label="attendance" value={`≤ ${artifacts.filters_applied.max_attendance}%`} warn />
          )}
        </div>
      )}

      {hasOverview && artifacts.overview && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <StatCard label="Students" value={artifacts.overview.total_students} />
          <StatCard label="Avg attendance" value={formatPercent(artifacts.overview.avg_attendance, 1)} />
          <StatCard label="Avg internal" value={artifacts.overview.avg_internal_marks.toFixed(1)} />
          <StatCard label="High risk" value={formatPercent(artifacts.overview.high_risk_pct, 1)} tone="danger" />
        </div>
      )}

      {hasStudents && artifacts.students && (
        <ChatStudentTable rows={artifacts.students} total={artifacts.total_matching_students ?? artifacts.students.length} />
      )}

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {hasRisk && artifacts.risk_distribution && (
          <div>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">Risk distribution</h4>
            <div className="h-[200px]">
              <RiskDistributionChart data={artifacts.risk_distribution} />
            </div>
          </div>
        )}
        {hasDepartments && artifacts.department_risk && <DepartmentRiskTable rows={artifacts.department_risk} />}
      </div>
    </div>
  );
}
