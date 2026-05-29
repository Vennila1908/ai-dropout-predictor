import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, Lock, Mail, Sparkles } from 'lucide-react';

import { AuthLayout } from '@/components/layout/AuthLayout';
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

function loginErrorMessage(err: ApiError): string {
  if (err.status === 429) {
    return 'Too many attempts. Please try again later.';
  }
  if (err.status === 401) {
    return 'Invalid email or password.';
  }
  return 'Unable to sign in. Please try again.';
}

export function LoginPage() {
  const { isAuthenticated, isHydrated, setAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: Location } };

  useEffect(() => {
    document.title = 'Sign in · AI Dropout Predictor';
  }, []);

  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  const login = useMutation({
    mutationFn: (data: FormValues) => authApi.login(data),
    onSuccess: (res) => {
      setFormError(null);
      setAuth(
        { access_token: res.access_token, refresh_token: res.refresh_token, token_type: res.token_type },
        res.user,
      );
      const dest = (location.state?.from?.pathname as string) ?? '/';

      document.title = 'S.E.A College · AI Dropout Predictor';
      navigate(dest, { replace: true });
    },
    onError: (err: ApiError) => setFormError(loginErrorMessage(err)),
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
    <AuthLayout>
      <h1 className="mb-4 text-lg font-semibold">Sign in</h1>

      <form
        onSubmit={handleSubmit((v) => {
          setFormError(null);
          login.mutate(v);
        })}
        className="space-y-4"
      >
        {formError && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-lg border border-risk-high/30 bg-risk-high/10 px-3 py-2.5 text-sm text-risk-high"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <p>{formError}</p>
          </div>
        )}
        <Input
          label="Email"
          type="email"
          autoComplete="username"
          error={errors.email?.message}
          {...register('email', { onChange: () => setFormError(null) })}
          placeholder="you@college.edu"
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          passwordToggle
          error={errors.password?.message}
          {...register('password', { onChange: () => setFormError(null) })}
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
          <button
            onClick={() => fillDemo('admin')}
            className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset"
          >
            admin@example.com
          </button>
          <button
            onClick={() => fillDemo('faculty')}
            className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset"
          >
            faculty@example.com
          </button>
          <button
            onClick={() => fillDemo('student')}
            className="rounded-md border bg-surface px-2 py-1 hover:bg-surface-inset"
          >
            student@example.com
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-ink-muted">
        <div className="flex items-center gap-1">
          <Mail className="h-3 w-3" /> SSO coming soon
        </div>
        <div className="flex items-center gap-1">
          <Lock className="h-3 w-3" /> bcrypt + JWT
        </div>
      </div>

      <p className="mt-5 text-center text-sm text-ink-muted">
        First install?{' '}
        <Link to="/register" className="font-medium text-primary-600 hover:underline dark:text-primary-400">
          Set up admin account
        </Link>
      </p>
    </AuthLayout>
  );
}
