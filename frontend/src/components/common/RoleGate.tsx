import { Navigate } from 'react-router-dom';
import { type ReactNode } from 'react';
import type { Role } from '@/lib/constants';
import { useAuth } from '@/hooks/useAuth';

export function RoleGate({ allow, children }: { allow: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return null;
  if (!allow.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
