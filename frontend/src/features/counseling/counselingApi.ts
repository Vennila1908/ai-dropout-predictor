import { api, unwrap } from '@/lib/api';
import type { CounselingSession } from '@/types';

export const counselingApi = {
  forStudent: (studentId: number) =>
    unwrap(api.get<CounselingSession[]>(`/counseling/student/${studentId}`)),
};
