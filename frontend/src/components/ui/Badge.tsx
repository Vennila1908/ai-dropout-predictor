import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function Badge({
  children,
  className,
  variant = 'neutral',
}: {
  children: ReactNode;
  className?: string;
  variant?: 'low' | 'medium' | 'high' | 'neutral';
}) {
  const cls =
    variant === 'low'
      ? 'badge-low'
      : variant === 'medium'
      ? 'badge-medium'
      : variant === 'high'
      ? 'badge-high'
      : 'badge-neutral';
  return <span className={cn(cls, className)}>{children}</span>;
}
