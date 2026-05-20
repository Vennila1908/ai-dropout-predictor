import { api, unwrap } from '@/lib/api';
import type { BatchPredictionResult, MLStatus, Prediction } from '@/types';

export const predictionsApi = {
  run: (studentId: number) => unwrap(api.post<Prediction>(`/predictions/${studentId}`)),
  batch: (payload: { student_ids?: number[]; department_id?: number }) =>
    unwrap(api.post<BatchPredictionResult>('/predictions/batch', payload)),
  latest: (studentId: number) => unwrap(api.get<Prediction>(`/predictions/${studentId}/latest`)),
  history: (studentId: number) => unwrap(api.get<Prediction[]>(`/predictions/${studentId}/history`)),
  mlStatus: () => unwrap(api.get<MLStatus>('/ml/status')),
  trainModel: () => unwrap(api.post<{ job_id: string; status: string }>('/ml/train')),
};
