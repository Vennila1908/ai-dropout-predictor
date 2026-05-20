import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { GraduationCap, Lock, Mail, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { authApi } from '@/features/auth/authApi';
import { useAuth } from '@/hooks/useAuth';
import type { ApiError } from '@/lib/api';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(4, 'Password is required'),
});
type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const { isAuthenticated, isHydrated, setAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: Location } };

  useEffect(() => {
    document.title = 'Sign in · AI Dropout Predictor';
  }, []);

  const { register, handleSubmit, formState: { errors }, setValue } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  const login = useMutation({
    mutationFn: (data: FormValues) => authApi.login(data),
    onSuccess: (res) => {
      setAuth({ access_token: res.access_token, refresh_token: res.refresh_token, token_type: res.token_type }, res.user);
      const dest = (location.state?.from?.pathname as string) ?? '/';
      navigate(dest, { replace: true });
    },
    onError: (err: ApiError) => toast.error(err.message || 'Login failed'),
  });

  if (isHydrated && isAuthenticated) return <Navigate to="/" replace />;

  function fillDemo(role: 'admin' | 'faculty' | 'student') {
    if (role === 'admin') {
      setValue('email', 'admin@example.com');
      setValue('password', 'Admin@123');
    } else if (role === 'faculty') {
      setValue('email', 'faculty@example.com');
      setValue('password', 'Faculty@123');
    } else {
      setValue('email', 'student@example.com');
      setValue('password', 'Student@123');
    }
  }

  return (
    <div className="grid min-h-screen w-full place-items-center bg-gradient-to-br from-primary-50 via-surface to-violet-100 dark:from-surface dark:via-surface dark:to-primary-900/30">
      <div className="card w-full max-w-md p-7">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-gradient-to-br from-primary-500 to-violet-500 p-2.5 text-white">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">AI Dropout Predictor</h1>
            <p className="text-xs text-ink-muted">Local-only · privacy-first · explainable</p>
          </div>
        </div>

        <form onSubmit={handleSubmit((v) => login.mutate(v))} className="space-y-4">
          <Input
            label="Email"
            type="email"
            autoComplete="username"
            error={errors.email?.message}
            {...register('email')}
            placeholder="you@college.edu"
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register('password')}
            placeholder="••••••••"
          />
          <Button type="submit" className="w-full" loading={login.isPending} disabled={login.isPending}>
            {login.isPending ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>

        <div className="mt-5 rounded-lg border bg-surface-subtle/60 p-3 text-xs text-ink-muted">
          <div className="mb-2 flex items-center gap-1.5 font-medium text-ink">
            <Sparkles className="h-3.5 w-3.5 text-primary-500" /> Demo accounts
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => fillDemo('admin')} className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset">
              admin@example.com
            </button>
            <button onClick={() => fillDemo('faculty')} className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset">
              faculty@example.com
            </button>
            <button onClick={() => fillDemo('student')} className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset">
              student@example.com
            </button>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-ink-muted">
          <div className="flex items-center gap-1"><Mail className="h-3 w-3" /> SSO coming soon</div>
          <div className="flex items-center gap-1"><Lock className="h-3 w-3" /> bcrypt + JWT</div>
        </div>
      </div>
    </div>
  );
}
