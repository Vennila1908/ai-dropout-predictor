import { type ReactNode } from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({
  title = 'Nothing here yet',
  description,
  icon,
  action,
}: {
  title?: string;
  description?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed py-12 px-6 text-center">
      <div className="mb-3 rounded-full bg-surface-subtle p-3 text-ink-muted">
        {icon ?? <Inbox className="h-6 w-6" />}
      </div>
      <h3 className="mb-1 text-base font-semibold">{title}</h3>
      {description && <p className="mb-4 max-w-md text-sm text-ink-muted">{description}</p>}
      {action}
    </div>
  );
}
