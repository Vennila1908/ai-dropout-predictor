import { api, unwrap } from '@/lib/api';
import type {
  PaginatedResponse,
  Student,
  StudentCreatePayload,
  StudentTimeline,
  StudentUpdatePayload,
} from '@/types';

export interface StudentsQuery {
  q?: string;
  department_id?: number;
  risk?: 'low' | 'medium' | 'high';
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface StudentRollLookup {
  roll_no: string;
  name: string;
  department_id: number | null;
}

export const studentsApi = {
  list: (params: StudentsQuery = {}) =>
    unwrap(api.get<PaginatedResponse<Student>>('/students', { params })),
  lookupByRoll: (rollNo: string) =>
    unwrap(api.get<StudentRollLookup>('/students/lookup-by-roll', { params: { roll_no: rollNo } })),
  get: (id: number) => unwrap(api.get<Student>(`/students/${id}`)),
  create: (payload: StudentCreatePayload) => unwrap(api.post<Student>('/students', payload)),
  update: (id: number, payload: StudentUpdatePayload) =>
    unwrap(api.patch<Student>(`/students/${id}`, payload)),
  remove: (id: number) => unwrap(api.delete<void>(`/students/${id}`)),
  timeline: (id: number) => unwrap(api.get<StudentTimeline>(`/students/${id}/timeline`)),
  bulk: (rows: StudentCreatePayload[]) =>
    unwrap(api.post<{ inserted: number; skipped: number }>('/students/bulk', rows)),
};
