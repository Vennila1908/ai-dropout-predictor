import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import { Skeleton } from '@/components/ui/Skeleton';
import { StudentFilters, type StudentFiltersValue } from '@/components/students/StudentFilters';
import { StudentForm } from '@/components/students/StudentForm';
import { StudentTable } from '@/components/students/StudentTable';
import { studentsApi } from '@/features/students/studentsApi';
import { usePagination } from '@/hooks/usePagination';

export function StudentsListPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialQ = searchParams.get('q') ?? '';
  const [filters, setFilters] = useState<StudentFiltersValue>({ q: initialQ, risk: '' });
  const { page, pageSize, goto } = usePagination({ pageSize: 20 });
  const [createOpen, setCreateOpen] = useState(false);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['students', filters, page, pageSize],
    queryFn: () =>
      studentsApi.list({
        q: filters.q || undefined,
        risk: (filters.risk || undefined) as 'low' | 'medium' | 'high' | undefined,
        page,
        page_size: pageSize,
      }),
  });

  const create = useMutation({
    mutationFn: studentsApi.create,
    onSuccess: () => {
      toast.success('Student created');
      setCreateOpen(false);
      qc.invalidateQueries({ queryKey: ['students'] });
    },
    onError: (err: { message?: string }) => toast.error(err.message ?? 'Create failed'),
  });

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Students</h1>
          <p className="text-sm text-ink-muted">Browse, filter, predict, and manage students.</p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />} onClick={() => setCreateOpen(true)}>
          New student
        </Button>
      </header>

      <Card>
        <CardHeader title="Roster" subtitle={data ? `${data.total.toLocaleString()} students` : '…'} />
        <CardBody>
          <StudentFilters value={filters} onChange={setFilters} />
        </CardBody>
        <div className="border-t px-5 py-3">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10" />)}
            </div>
          ) : (
            <>
              <StudentTable rows={data?.items ?? []} onRowClick={(s) => navigate(`/students/${s.id}`)} />
              <div className="mt-3">
                <Pagination
                  page={page}
                  pageSize={pageSize}
                  total={data?.total ?? 0}
                  onPageChange={goto}
                />
              </div>
            </>
          )}
        </div>
      </Card>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New student" widthClass="max-w-3xl">
        <StudentForm onSubmit={(v) => create.mutateAsync(v)} loading={create.isPending} submitLabel="Create" />
      </Modal>
    </div>
  );
}
