import { api, unwrap } from '@/lib/api';
import type { BatchPredictionResult, MLStatus, Prediction } from '@/types';

export const predictionsApi = {
  run: (rollNo: string) => unwrap(api.post<Prediction>(`/predictions/${encodeURIComponent(rollNo)}`)),
  batch: (payload: { roll_nos?: string[]; department_id?: number } = {}) =>
    unwrap(api.post<BatchPredictionResult>('/predictions/batch', payload)),
  latest: (rollNo: string) =>
    unwrap(api.get<Prediction>(`/predictions/${encodeURIComponent(rollNo)}/latest`)),
  history: (rollNo: string) =>
    unwrap(api.get<Prediction[]>(`/predictions/${encodeURIComponent(rollNo)}/history`)),
  mlStatus: () => unwrap(api.get<MLStatus>('/ml/status')),
  trainModel: () => unwrap(api.post<{ job_id: string; status: string }>('/ml/train')),
};
