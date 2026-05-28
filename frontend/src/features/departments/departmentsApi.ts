import { api, unwrap } from '@/lib/api';
import type { Department } from '@/types';

export interface CourseCreatePayload {
  name: string;
  code: string;
}

export interface CourseUpdatePayload {
  name?: string;
  code?: string;
}

export const departmentsApi = {
  list: () => unwrap(api.get<Department[]>('/departments')),
  create: (payload: CourseCreatePayload) => unwrap(api.post<Department>('/departments', payload)),
  update: (id: number, payload: CourseUpdatePayload) => unwrap(api.patch<Department>(`/departments/${id}`, payload)),
  remove: (id: number) => api.delete(`/departments/${id}`).then(() => undefined),
};
