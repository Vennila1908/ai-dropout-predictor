import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { Link, Navigate } from 'react-router-dom';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { AlertCircle } from 'lucide-react';

import { AuthLayout } from '@/components/layout/AuthLayout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { authApi } from '@/features/auth/authApi';
import { useAuth } from '@/hooks/useAuth';
import { formatError, type ApiError } from '@/lib/api';
import { bindPersonNameField, personNameLongSchema } from '@/lib/validation';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  full_name: personNameLongSchema,
  password: z.string().min(8, 'Password must be at least 8 characters').max(128),
});

type FormValues = z.infer<typeof schema>;

function registerErrorMessage(err: ApiError): string {
  if (err.status === 403) {
    return 'Setup is already complete. Sign in or ask an admin to create your account.';
  }
  if (err.status === 409) {
    return 'That email is already registered.';
  }
  return formatError(err).message || 'Could not create account. Please try again.';
}

export function RegisterPage() {
  const { isAuthenticated, isHydrated } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    document.title = 'Set up admin · AI Dropout Predictor';
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onBlur',
    reValidateMode: 'onBlur',
    defaultValues: { email: '', full_name: '', password: '' },
  });

  const createAdmin = useMutation({
    mutationFn: (data: FormValues) =>
      authApi.bootstrapRegister({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        role: 'admin',
      }),
    onSuccess: () => {
      toast.success('Admin account created. You can sign in now.');
    },
    onError: (err: ApiError) => setFormError(registerErrorMessage(err)),
  });

  if (isHydrated && isAuthenticated) return <Navigate to="/" replace />;

  return (
    <AuthLayout>
      <div className="mb-4">
        <h1 className="text-lg font-semibold">First-time setup</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Create the first administrator account for this installation.
        </p>
      </div>

      {createAdmin.isSuccess ? (
        <div className="space-y-4 text-center">
          <p className="text-sm text-ink-muted">Your admin account is ready.</p>
          <Link to="/login" className="btn-primary block w-full text-center">
            Go to sign in
          </Link>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit((values) => {
            setFormError(null);
            createAdmin.mutate(values);
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
            placeholder="admin@college.edu"
            error={errors.email?.message}
            {...register('email', { onChange: () => setFormError(null) })}
          />
          <Input
            label="Full name"
            autoComplete="name"
            placeholder="System Administrator"
            error={errors.full_name?.message}
            {...bindPersonNameField(register('full_name'))}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            passwordToggle
            placeholder="Min. 8 characters"
            error={errors.password?.message}
            {...register('password', { onChange: () => setFormError(null) })}
          />
          <Button type="submit" className="w-full" loading={createAdmin.isPending} disabled={createAdmin.isPending}>
            {createAdmin.isPending ? 'Creating account…' : 'Create admin account'}
          </Button>
        </form>
      )}

      <p className="mt-5 text-center text-sm text-ink-muted">
        Already set up?{' '}
        <Link to="/login" className="font-medium text-primary-600 hover:underline dark:text-primary-400">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
