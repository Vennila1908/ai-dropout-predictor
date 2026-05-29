import { cn } from '@/lib/utils';
import { APP_NAME, COLLEGE_LOGO, COLLEGE_NAME } from '@/lib/constants';

type CollegeBrandProps = {
  variant?: 'auth' | 'sidebar';
  className?: string;
  showAppName?: boolean;
};

export function CollegeBrand({ variant = 'auth', className, showAppName = true }: CollegeBrandProps) {
  const compact = variant === 'sidebar';

  return (
    <div
      className={cn(
        compact ? 'flex min-w-0 items-start gap-2.5' : 'flex flex-col items-center gap-3 text-center',
        className,
      )}
    >
      <img
        src={COLLEGE_LOGO}
        alt="S.E.A College logo"
        className={cn('shrink-0 object-contain', compact ? 'h-10 w-10' : 'h-20 w-20')}
      />
      <div className={cn(compact && 'min-w-0 flex-1')}>
        <p
          className={cn(
            'font-semibold leading-snug text-ink',
            compact
              ? 'text-[9px] uppercase leading-tight tracking-wide'
              : 'text-xs uppercase tracking-wide sm:text-sm',
          )}
        >
          {COLLEGE_NAME}
        </p>
        {showAppName && (
          <p
            className={cn(
              'text-ink-muted',
              compact ? 'mt-0.5 text-[10px] font-medium' : 'mt-1.5 text-sm font-medium',
            )}
          >
            {APP_NAME}
          </p>
        )}
        {/* {!compact && (
          <p className="mt-1 text-xs text-ink-muted">Local-only · privacy-first · explainable</p>
        )} */}
      </div>
    </div>
  );
}
