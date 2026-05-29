import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { GraduationCap, UserCog, UserX, Users } from 'lucide-react';
import toast from 'react-hot-toast';

import { UserForm } from '@/components/users/UserForm';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Skeleton } from '@/components/ui/Skeleton';
import { analyticsApi } from '@/features/analytics/analyticsApi';
import { usersApi } from '@/features/users/usersApi';
import type { ApiError } from '@/lib/api';
import type { Role } from '@/lib/constants';
import type { User } from '@/types';

type RoleFilter = 'all' | Role;

const MODAL_TITLES: Record<Role, string> = {
  student: 'New student login',
  faculty: 'New faculty login',
  admin: 'New admin login',
};

function roleBadge(role: User['role']) {
  if (role === 'admin') return <Badge variant="high">admin</Badge>;
  if (role === 'faculty') return <Badge variant="medium">faculty</Badge>;
  return <Badge variant="low">student</Badge>;
}

export function UsersPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [createRole, setCreateRole] = useState<Role>('student');
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all');
  const qc = useQueryClient();

  function openCreate(role: Role) {
    setCreateRole(role);
    setCreateOpen(true);
  }

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  });

  const { data: deptRisk } = useQuery({
    queryKey: ['analytics', 'department-risk'],
    queryFn: analyticsApi.departmentRisk,
  });

  const departmentOptions = useMemo(
    () =>
      (deptRisk ?? []).map((d) => ({
        value: d.department_id,
        label: `${d.department_code} — ${d.department_name}`,
      })),
    [deptRisk],
  );

  const filteredUsers = useMemo(
    () => (users ?? []).filter((u) => roleFilter === 'all' || u.role === roleFilter),
    [users, roleFilter],
  );

  const counts = useMemo(
    () => ({
      all: users?.length ?? 0,
      admin: users?.filter((u) => u.role === 'admin').length ?? 0,
      faculty: users?.filter((u) => u.role === 'faculty').length ?? 0,
      student: users?.filter((u) => u.role === 'student').length ?? 0,
    }),
    [users],
  );

  const create = useMutation({
    mutationFn: usersApi.create,
    onSuccess: (user) => {
      toast.success(`Account created for ${user.email}`);
      setCreateOpen(false);
      qc.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: ApiError) => toast.error(err.message || 'Create failed'),
  });

  const deactivate = useMutation({
    mutationFn: usersApi.deactivate,
    onSuccess: () => {
      toast.success('Account deactivated');
      qc.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: ApiError) => toast.error(err.message || 'Deactivate failed'),
  });

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">User accounts</h1>
          <p className="text-sm text-ink-muted">
            Create login credentials for students, faculty, and admins. This is separate from student
            records used for ML predictions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" icon={<GraduationCap className="h-4 w-4" />} onClick={() => openCreate('student')}>
            Add student
          </Button>
          <Button variant="secondary" icon={<UserCog className="h-4 w-4" />} onClick={() => openCreate('faculty')}>
            Add faculty
          </Button>
          <Button variant="ghost" icon={<Users className="h-4 w-4" />} onClick={() => openCreate('admin')}>
            Add admin
          </Button>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ['all', 'All'],
            ['student', 'Students'],
            ['faculty', 'Faculty'],
            ['admin', 'Admins'],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setRoleFilter(key)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              roleFilter === key
                ? 'border-primary-500 bg-primary-500/10 text-primary-600 dark:text-primary-400'
                : 'border-transparent bg-surface-subtle text-ink-muted hover:text-ink'
            }`}
          >
            {label} ({counts[key]})
          </button>
        ))}
      </div>

      <Card>
        <CardHeader
          title="Accounts"
          subtitle={
            users
              ? `${filteredUsers.length} shown · ${users.length} total`
              : '…'
          }
        />
        <CardBody className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-surface-subtle/60 text-left text-xs uppercase tracking-wide text-ink-muted">
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">Email</th>
                    <th className="px-5 py-3 font-medium">Role</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b last:border-0">
                      <td className="px-5 py-3 font-medium">{user.full_name}</td>
                      <td className="px-5 py-3 font-mono text-xs">{user.email}</td>
                      <td className="px-5 py-3">{roleBadge(user.role)}</td>
                      <td className="px-5 py-3">
                        {user.is_active ? (
                          <Badge variant="low">active</Badge>
                        ) : (
                          <Badge variant="neutral">inactive</Badge>
                        )}
                      </td>
                      <td className="px-5 py-3 text-right">
                        {user.is_active && (
                          <Button
                            variant="ghost"
                            className="text-xs text-risk-high"
                            icon={<UserX className="h-3.5 w-3.5" />}
                            loading={deactivate.isPending}
                            onClick={() => {
                              if (window.confirm(`Deactivate ${user.email}? They will no longer be able to sign in.`)) {
                                deactivate.mutate(user.id);
                              }
                            }}
                          >
                            Deactivate
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!filteredUsers.length && (
                    <tr>
                      <td colSpan={5} className="px-5 py-8 text-center text-ink-muted">
                        {users?.length ? 'No accounts match this filter.' : 'No accounts yet. Add a student or faculty login to get started.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Quick reference" />
        <CardBody className="space-y-2 text-sm text-ink-muted">
          <p>
            <strong className="text-ink">Login account</strong> — lets someone sign in to this app
            (email + password).
          </p>
          <p>
            <strong className="text-ink">Student record</strong> — academic data for predictions
            (roll number, marks, attendance). Add those under <em>Students</em> or via CSV upload.
          </p>
          <p className="text-xs">
            Seeded demo logins: admin@example.com, faculty@example.com, student@example.com (passwords
            end with @123). Faculty accounts need a department and can access Students, Predictions,
            Counseling, and Analytics.
          </p>
        </CardBody>
      </Card>

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title={MODAL_TITLES[createRole]}
        widthClass="max-w-md"
      >
        <UserForm
          key={createRole}
          defaultRole={createRole}
          departmentOptions={departmentOptions}
          loading={create.isPending}
          onSubmit={async (values) => {
            await create.mutateAsync(values);
          }}
        />
      </Modal>
    </div>
  );
}
