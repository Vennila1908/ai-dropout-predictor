import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import type { UserCreatePayload } from '@/features/users/usersApi';
import type { Role } from '@/lib/constants';

const schema = z
  .object({
    email: z.string().email('Enter a valid email'),
    full_name: z.string().min(1, 'Name is required').max(255),
    password: z.string().min(8, 'Password must be at least 8 characters').max(128),
    role: z.enum(['admin', 'faculty', 'student']),
    department_id: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.role === 'faculty' && !data.department_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Department is required for faculty accounts',
        path: ['department_id'],
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const ROLE_COPY: Record<
  Role,
  { title: string; emailPlaceholder: string; namePlaceholder: string; departmentHint: string }
> = {
  student: {
    title: 'Student account',
    emailPlaceholder: 'student@college.edu',
    namePlaceholder: 'Priya Sharma',
    departmentHint: 'Optional for students.',
  },
  faculty: {
    title: 'Faculty account',
    emailPlaceholder: 'faculty@college.edu',
    namePlaceholder: 'Dr. Jane Faculty',
    departmentHint: 'Required — assigns this faculty member to a department.',
  },
  admin: {
    title: 'Admin account',
    emailPlaceholder: 'admin@college.edu',
    namePlaceholder: 'System Administrator',
    departmentHint: 'Optional for admins.',
  },
};

export function UserForm({
  defaultRole = 'student',
  onSubmit,
  loading,
  departmentOptions,
}: {
  defaultRole?: Role;
  onSubmit: (values: UserCreatePayload) => Promise<void> | void;
  loading?: boolean;
  departmentOptions: { value: number; label: string }[];
}) {
  const copy = ROLE_COPY[defaultRole];

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: '',
      full_name: '',
      password: '',
      role: defaultRole,
      department_id: '',
    },
  });

  const role = watch('role');
  const activeCopy = ROLE_COPY[role];

  return (
    <form
      className="space-y-4"
      onSubmit={handleSubmit(async (v) => {
        await onSubmit({
          email: v.email,
          full_name: v.full_name,
          password: v.password,
          role: v.role,
          department_id: v.department_id ? Number(v.department_id) : null,
          is_active: true,
        });
      })}
    >
      <p className="text-sm text-ink-muted">{copy.title} — share the email and password securely after creation.</p>

      <Input
        label="Email"
        type="email"
        autoComplete="off"
        placeholder={activeCopy.emailPlaceholder}
        error={errors.email?.message}
        {...register('email')}
      />
      <Input
        label="Full name"
        autoComplete="off"
        placeholder={activeCopy.namePlaceholder}
        error={errors.full_name?.message}
        {...register('full_name')}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        placeholder="Min. 8 characters"
        error={errors.password?.message}
        {...register('password')}
      />
      <Select
        label="Role"
        options={[
          { value: 'student', label: 'Student — limited personal dashboard' },
          { value: 'faculty', label: 'Faculty — manage students, predictions, counseling' },
          { value: 'admin', label: 'Admin — full access including user accounts' },
        ]}
        error={errors.role?.message}
        {...register('role')}
      />
      <Select
        label="Department"
        placeholder={role === 'faculty' ? 'Select department' : 'None'}
        options={departmentOptions}
        hint={activeCopy.departmentHint}
        error={errors.department_id?.message}
        {...register('department_id')}
      />
      <div className="flex justify-end pt-2">
        <Button type="submit" loading={loading} disabled={loading}>
          Create {role} account
        </Button>
      </div>
    </form>
  );
}
