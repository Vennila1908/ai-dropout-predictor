import { api, unwrap } from '@/lib/api';
import type { Upload, UploadConfirmResult, UploadPreview } from '@/types';

export const uploadsApi = {
  preview: (file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return unwrap(
      api.post<UploadPreview>('/uploads', fd, { headers: { 'Content-Type': 'multipart/form-data' } }),
    );
  },
  confirm: (uploadId: number, mapping: Record<string, string>, skipInvalid = true) =>
    unwrap(
      api.post<UploadConfirmResult>(`/uploads/${uploadId}/confirm`, {
        mapping,
        skip_invalid: skipInvalid,
      }),
    ),
  history: () => unwrap(api.get<Upload[]>('/uploads')),
};
