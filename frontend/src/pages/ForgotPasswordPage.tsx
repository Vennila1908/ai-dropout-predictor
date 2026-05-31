import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, KeyRound } from 'lucide-react';

import { AuthLayout } from '@/components/layout/AuthLayout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { authApi, type ForgotPasswordResponse } from '@/features/auth/authApi';
import { useAuth } from '@/hooks/useAuth';
import { formatError, type ApiError } from '@/lib/api';

const requestSchema = z.object({
  email: z.string().email('Enter a valid email'),
});

const resetSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters').max(128),
    confirmPassword: z.string().min(8, 'Confirm your password'),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type RequestValues = z.infer<typeof requestSchema>;
type ResetValues = z.infer<typeof resetSchema>;

function authErrorMessage(err: ApiError): string {
  if (err.status === 400) return formatError(err).message || 'This reset link is invalid or expired.';
  if (err.status === 429) return 'Too many attempts. Please try again later.';
  return formatError(err).message || 'Something went wrong. Please try again.';
}

function localResetPath(resetUrl: string): string {
  const url = new URL(resetUrl);
  return `${url.pathname}${url.search}`;
}

export function ForgotPasswordPage() {
  const { isAuthenticated, isHydrated } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [formError, setFormError] = useState<string | null>(null);
  const [resetInfo, setResetInfo] = useState<ForgotPasswordResponse | null>(null);

  useEffect(() => {
    document.title = token ? 'Reset password · AI Dropout Predictor' : 'Forgot password · AI Dropout Predictor';
  }, [token]);

  const requestForm = useForm<RequestValues>({
    resolver: zodResolver(requestSchema),
    defaultValues: { email: '' },
  });

  const resetForm = useForm<ResetValues>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: '', confirmPassword: '' },
  });

  const requestReset = useMutation({
    mutationFn: (data: RequestValues) => authApi.forgotPassword(data.email),
    onSuccess: (res) => {
      setFormError(null);
      setResetInfo(res);
    },
    onError: (err: ApiError) => setFormError(authErrorMessage(err)),
  });

  const resetPassword = useMutation({
    mutationFn: (data: ResetValues) => authApi.resetPassword({ token, password: data.password }),
    onSuccess: () => {
      setFormError(null);
    },
    onError: (err: ApiError) => setFormError(authErrorMessage(err)),
  });

  if (isHydrated && isAuthenticated) return <Navigate to="/" replace />;

  if (token) {
    return (
      <AuthLayout>
        <div className="mb-4">
          <h1 className="text-lg font-semibold">Reset password</h1>
          <p className="mt-1 text-sm text-ink-muted">Choose a new password for your account.</p>
        </div>

        {resetPassword.isSuccess ? (
          <div className="space-y-4 text-center">
            <CheckCircle2 className="mx-auto h-10 w-10 text-risk-low" aria-hidden />
            <p className="text-sm text-ink-muted">Your password has been reset.</p>
            <Link to="/login" className="btn-primary block w-full text-center">
              Go to sign in
            </Link>
          </div>
        ) : (
          <form
            onSubmit={resetForm.handleSubmit((values) => {
              setFormError(null);
              resetPassword.mutate(values);
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
              label="New password"
              type="password"
              autoComplete="new-password"
              passwordToggle
              placeholder="Min. 8 characters"
              error={resetForm.formState.errors.password?.message}
              {...resetForm.register('password', { onChange: () => setFormError(null) })}
            />
            <Input
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              passwordToggle
              placeholder="Repeat password"
              error={resetForm.formState.errors.confirmPassword?.message}
              {...resetForm.register('confirmPassword', { onChange: () => setFormError(null) })}
            />
            <Button type="submit" className="w-full" loading={resetPassword.isPending}>
              {resetPassword.isPending ? 'Resetting password…' : 'Reset password'}
            </Button>
          </form>
        )}

        <p className="mt-5 text-center text-sm text-ink-muted">
          Remembered it?{' '}
          <Link to="/login" className="font-medium text-primary-600 hover:underline dark:text-primary-400">
            Sign in
          </Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mb-4">
        <h1 className="text-lg font-semibold">Forgot password</h1>
        <p className="mt-1 text-sm text-ink-muted">Enter your email to generate reset instructions.</p>
      </div>

      {resetInfo ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-risk-low/30 bg-risk-low/10 px-3 py-3 text-sm text-ink">
            <div className="mb-1 flex items-center gap-2 font-medium">
              <CheckCircle2 className="h-4 w-4 text-risk-low" aria-hidden />
              Reset instructions ready
            </div>
            <p className="text-ink-muted">{resetInfo.message}</p>
          </div>
          {resetInfo.reset_url && (
            <Link to={localResetPath(resetInfo.reset_url)} className="btn-primary block w-full text-center">
              Open reset form
            </Link>
          )}
          <Button variant="secondary" className="w-full" onClick={() => setResetInfo(null)}>
            Try another email
          </Button>
        </div>
      ) : (
        <form
          onSubmit={requestForm.handleSubmit((values) => {
            setFormError(null);
            requestReset.mutate(values);
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
            autoComplete="email"
            placeholder="you@college.edu"
            error={requestForm.formState.errors.email?.message}
            {...requestForm.register('email', { onChange: () => setFormError(null) })}
          />
          <Button
            type="submit"
            className="w-full"
            loading={requestReset.isPending}
            icon={<KeyRound className="h-4 w-4" />}
          >
            {requestReset.isPending ? 'Generating reset link…' : 'Generate reset link'}
          </Button>
        </form>
      )}

      <p className="mt-5 text-center text-sm text-ink-muted">
        Back to{' '}
        <Link to="/login" className="font-medium text-primary-600 hover:underline dark:text-primary-400">
          sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
