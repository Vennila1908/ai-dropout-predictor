import { api, unwrap } from '@/lib/api';
import type { LoginPayload, LoginResponse, User } from '@/types';

export const authApi = {
  login: (payload: LoginPayload) => unwrap(api.post<LoginResponse>('/auth/login', payload)),
  me: () => unwrap(api.get<User>('/auth/me')),
  refresh: (refresh_token: string) =>
    unwrap(api.post<{ access_token: string; token_type: string }>('/auth/refresh', { refresh_token })),
  bootstrapRegister: (payload: { email: string; password: string; full_name: string; role: string }) =>
    unwrap(api.post<User>('/auth/register', payload)),
};
