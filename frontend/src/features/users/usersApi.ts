import { api, unwrap } from '@/lib/api';
import type { Role } from '@/lib/constants';
import type { User } from '@/types';

export interface UserCreatePayload {
  email: string;
  full_name: string;
  password: string;
  role: Role;
  roll_no?: string | null;
  department_id?: number | null;
  is_active?: boolean;
}

export interface UserRollLookup {
  roll_no: string;
  full_name: string;
  department_id: number | null;
}

export interface UserUpdatePayload {
  full_name?: string;
  role?: Role;
  department_id?: number | null;
  is_active?: boolean;
  password?: string;
}

export const usersApi = {
  list: () => unwrap(api.get<User[]>('/users')),
  lookupByRoll: (rollNo: string) =>
    unwrap(api.get<UserRollLookup>('/users/lookup-by-roll', { params: { roll_no: rollNo } })),
  create: (payload: UserCreatePayload) => unwrap(api.post<User>('/users', payload)),
  update: (id: number, payload: UserUpdatePayload) => unwrap(api.patch<User>(`/users/${id}`, payload)),
  deactivate: (id: number) => unwrap(api.delete<void>(`/users/${id}`)),
};
