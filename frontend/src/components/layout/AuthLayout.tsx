import type { ReactNode } from 'react';

import { CollegeBrand } from '@/components/branding/CollegeBrand';

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid min-h-screen w-full place-items-center bg-gradient-to-br from-primary-50 via-surface to-violet-100 px-4 py-8 dark:from-surface dark:via-surface dark:to-primary-900/30">
      <div className="card w-full max-w-md p-7">
        <CollegeBrand variant="auth" className="mb-6" />
        {children}
      </div>
    </div>
  );
}
