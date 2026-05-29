import { type TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, error, className, id, ...rest },
  ref,
) {
  const tid = id ?? rest.name;
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={tid} className="block text-sm font-medium text-ink">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={tid}
        className={cn('input min-h-[88px] resize-y', error && 'border-risk-high focus:ring-risk-high/30', className)}
        {...rest}
      />
      {error && <p className="text-xs text-risk-high">{error}</p>}
    </div>
  );
});
