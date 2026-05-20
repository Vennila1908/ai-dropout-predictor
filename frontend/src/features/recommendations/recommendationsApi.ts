import { api, unwrap } from '@/lib/api';
import type { Recommendation } from '@/types';

export const recommendationsApi = {
  generate: (studentId: number) =>
    unwrap(api.post<Recommendation>(`/recommendations/${studentId}/generate`)),
  forStudent: (studentId: number) =>
    unwrap(api.get<Recommendation[]>(`/recommendations/${studentId}`)),
  update: (id: number, body: { status?: Recommendation['status']; summary?: string }) =>
    unwrap(api.patch<Recommendation>(`/recommendations/${id}`, body)),
};
