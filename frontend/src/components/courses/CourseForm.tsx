import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { CourseCreatePayload, CourseUpdatePayload } from '@/features/departments/departmentsApi';
import type { Department } from '@/types';

const schema = z.object({
  name: z.string().min(1, 'Course name is required').max(120),
  code: z
    .string()
    .min(2, 'Code must be at least 2 characters')
    .max(20)
    .regex(/^[A-Za-z0-9-]+$/, 'Use letters, numbers, or hyphens only'),
});

type FormValues = z.infer<typeof schema>;

export function CourseForm({
  initial,
  onSubmit,
  loading,
  submitLabel = 'Save course',
}: {
  initial?: Department | null;
  onSubmit: (values: CourseCreatePayload | CourseUpdatePayload) => Promise<void> | void;
  loading?: boolean;
  submitLabel?: string;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? '',
      code: initial?.code ?? '',
    },
  });

  useEffect(() => {
    reset({
      name: initial?.name ?? '',
      code: initial?.code ?? '',
    });
  }, [initial, reset]);

  return (
    <form
      className="space-y-4"
      onSubmit={handleSubmit(async (values) => {
        await onSubmit({
          name: values.name.trim(),
          code: values.code.trim().toUpperCase(),
        });
      })}
    >
      <Input label="Course name" placeholder="B.Com" error={errors.name?.message} {...register('name')} />
      <Input
        label="Course code"
        placeholder="BCOM"
        hint="Short code used in roll numbers and filters (e.g. BCOM, MCOM)."
        error={errors.code?.message}
        {...register('code')}
      />
      <div className="flex justify-end gap-2 pt-2">
        <Button type="submit" loading={loading}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
