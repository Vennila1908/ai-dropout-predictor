import { api, unwrap } from '@/lib/api';
import type { LoginPayload, LoginResponse, User } from '@/types';

export interface ForgotPasswordResponse {
  message: string;
  reset_token?: string;
  reset_url?: string;
}

export const authApi = {
  login: (payload: LoginPayload) => unwrap(api.post<LoginResponse>('/auth/login', payload)),
  me: () => unwrap(api.get<User>('/auth/me')),
  refresh: (refresh_token: string) =>
    unwrap(api.post<{ access_token: string; token_type: string }>('/auth/refresh', { refresh_token })),
  forgotPassword: (email: string) =>
    unwrap(api.post<ForgotPasswordResponse>('/auth/forgot-password', { email })),
  resetPassword: (payload: { token: string; password: string }) =>
    unwrap(api.post<{ message: string }>('/auth/reset-password', payload)),
  bootstrapRegister: (payload: { email: string; password: string; full_name: string; role: string }) =>
    unwrap(api.post<User>('/auth/register', payload)),
};
