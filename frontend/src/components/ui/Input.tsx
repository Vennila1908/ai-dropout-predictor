import { type InputHTMLAttributes, forwardRef, useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  passwordToggle?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, passwordToggle, className, id, type, ...rest },
  ref,
) {
  const [passwordVisible, setPasswordVisible] = useState(false);
  const inputId = id ?? rest.name;
  const showPasswordToggle = passwordToggle && type === 'password';
  const inputType = showPasswordToggle ? (passwordVisible ? 'text' : 'password') : type;

  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-ink">
          {label}
        </label>
      )}
      <div className={cn(showPasswordToggle && 'relative')}>
        <input
          ref={ref}
          id={inputId}
          type={inputType}
          className={cn(
            'input',
            error && 'border-risk-high focus:ring-risk-high/30',
            showPasswordToggle && 'pr-10',
            className,
          )}
          {...rest}
        />
        {showPasswordToggle && (
          <button
            type="button"
            tabIndex={-1}
            aria-label={passwordVisible ? 'Hide password' : 'Show password'}
            aria-pressed={passwordVisible}
            onClick={() => setPasswordVisible((visible) => !visible)}
            className="absolute inset-y-0 right-0 flex items-center px-3 text-ink-muted hover:text-ink"
          >
            {passwordVisible ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
          </button>
        )}
      </div>
      {hint && !error && <p className="text-xs text-ink-muted">{hint}</p>}
      {error && <p className="text-xs text-risk-high">{error}</p>}
    </div>
  );
});
