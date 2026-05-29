import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { CourseForm } from '@/components/courses/CourseForm';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Skeleton } from '@/components/ui/Skeleton';
import { departmentsApi } from '@/features/departments/departmentsApi';
import { useDepartments } from '@/hooks/useDepartments';
import { formatError, type ApiError } from '@/lib/api';
import type { Department } from '@/types';

export function CoursesPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Department | null>(null);
  const qc = useQueryClient();

  const { data: courses, isLoading, isError, error, refetch, isFetching } = useDepartments();

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['departments'] });
    qc.invalidateQueries({ queryKey: ['analytics'] });
  };

  const create = useMutation({
    mutationFn: departmentsApi.create,
    onSuccess: (course) => {
      toast.success(`Added ${course.name}`);
      setCreateOpen(false);
      invalidate();
    },
    onError: (err: ApiError) => toast.error(err.message || 'Could not add course'),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof departmentsApi.update>[1] }) =>
      departmentsApi.update(id, payload),
    onSuccess: (course) => {
      toast.success(`Updated ${course.name}`);
      setEditTarget(null);
      invalidate();
    },
    onError: (err: ApiError) => toast.error(err.message || 'Could not update course'),
  });

  const remove = useMutation({
    mutationFn: departmentsApi.remove,
    onSuccess: () => {
      toast.success('Course removed');
      invalidate();
    },
    onError: (err: ApiError) => toast.error(err.message || 'Could not delete course'),
  });

  const loadError = isError ? formatError(error) : null;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Degree courses</h1>
          <p className="text-sm text-ink-muted">
            Manage degree programs (Science, Commerce, Arts). Courses with enrolled students cannot be deleted.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            icon={<RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Refresh
          </Button>
          <Button icon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
            Add course
          </Button>
        </div>
      </header>

      {loadError && (
        <div className="rounded-lg border border-risk-high/30 bg-risk-high/10 px-4 py-3 text-sm">
          <p className="font-medium text-risk-high">Could not load courses</p>
          <p className="mt-1 text-ink-muted">{loadError.message}</p>
          <p className="mt-2 text-xs text-ink-muted">
            Restart the backend (<code className="rounded bg-surface px-1">.\scripts\start_backend.ps1</code>) after
            updating the app so the <code className="rounded bg-surface px-1">/departments</code> API is available.
          </p>
          <Button variant="secondary" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      )}

      <Card>
        <CardHeader
          title="Courses"
          subtitle={
            isLoading
              ? 'Loading…'
              : loadError
                ? 'Load failed'
                : `${courses?.length ?? 0} program(s)`
          }
          actions={<BookOpen className="h-4 w-4 text-ink-muted" />}
        />
        <CardBody className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : loadError ? (
            <p className="px-5 py-8 text-center text-sm text-ink-muted">
              Fix the connection issue above, then click Refresh.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="bg-surface-subtle text-left text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th className="px-4 py-3 font-medium">Code</th>
                    <th className="px-4 py-3 font-medium">Name</th>
                    <th className="px-4 py-3 font-medium text-right">Students</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(courses ?? []).map((course) => {
                    const locked = (course.student_count ?? 0) >= 1;
                    return (
                      <tr key={course.id} className="border-t">
                        <td className="px-4 py-3 font-mono font-medium">{course.code}</td>
                        <td className="px-4 py-3">{course.name}</td>
                        <td className="px-4 py-3 text-right">
                          <Badge variant={locked ? 'medium' : 'low'}>{course.student_count ?? 0}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              icon={<Pencil className="h-3.5 w-3.5" />}
                              onClick={() => setEditTarget(course)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="ghost"
                              icon={<Trash2 className="h-3.5 w-3.5" />}
                              disabled={locked || remove.isPending}
                              title={
                                locked
                                  ? 'Cannot delete — at least one student is enrolled'
                                  : 'Delete course'
                              }
                              onClick={() => {
                                if (locked) return;
                                if (window.confirm(`Delete ${course.name} (${course.code})?`)) {
                                  remove.mutate(course.id);
                                }
                              }}
                              className={locked ? 'opacity-40' : 'text-risk-high hover:text-risk-high'}
                            >
                              Delete
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {!courses?.length && (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-ink-muted">
                        No courses in the database yet. Run setup or click Add course.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Add degree course">
        <CourseForm
          loading={create.isPending}
          submitLabel="Add course"
          onSubmit={async (values) => {
            await create.mutateAsync(values as Parameters<typeof departmentsApi.create>[0]);
          }}
        />
      </Modal>

      <Modal open={Boolean(editTarget)} onClose={() => setEditTarget(null)} title="Edit degree course">
        {editTarget && (
          <CourseForm
            initial={editTarget}
            loading={update.isPending}
            submitLabel="Save changes"
            onSubmit={async (values) => {
              await update.mutateAsync({ id: editTarget.id, payload: values });
            }}
          />
        )}
      </Modal>
    </div>
  );
}
