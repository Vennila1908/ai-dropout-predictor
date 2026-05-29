import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Tailwind-aware classnames helper. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number, digits = 1): string {
  if (Number.isNaN(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

export function formatNumber(value: number, digits = 0): string {
  if (Number.isNaN(value)) return '—';
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function formatDate(value: string | Date | undefined | null): string {
  if (!value) return '—';
  const d = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .slice(0, 2)
    .join('');
}

export const RISK_COLORS: Record<'low' | 'medium' | 'high', string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
};

export function riskClass(level: 'low' | 'medium' | 'high'): string {
  switch (level) {
    case 'low':
      return 'badge-low';
    case 'medium':
      return 'badge-medium';
    case 'high':
      return 'badge-high';
    default:
      return 'badge-neutral';
  }
}
