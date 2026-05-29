import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { studentsApi } from '@/features/students/studentsApi';
import type { UserCreatePayload } from '@/features/users/usersApi';
import { formatError } from '@/lib/api';
import type { Role } from '@/lib/constants';
import { bindPersonNameField, personNameLongSchema, sanitizePersonName } from '@/lib/validation';

const schema = z
  .object({
    roll_no: z.string().max(40).optional(),
    email: z.string().email('Enter a valid email'),
    full_name: personNameLongSchema,
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
    if (data.role === 'student' && !data.roll_no?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Roll number is required for student accounts',
        path: ['roll_no'],
      });
    }
    if (data.role === 'student' && data.roll_no?.trim() && !/^[A-Za-z0-9]+$/.test(data.roll_no.trim())) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Roll number must contain letters and numbers only',
        path: ['roll_no'],
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
    departmentHint: 'Filled from the student record when a roll number is matched.',
  },
  faculty: {
    title: 'Faculty account',
    emailPlaceholder: 'faculty@college.edu',
    namePlaceholder: 'Jane Faculty',
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
  const [rollLookupError, setRollLookupError] = useState<string | null>(null);
  const [rollMatched, setRollMatched] = useState(false);
  const [rollLookupPending, setRollLookupPending] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onBlur',
    reValidateMode: 'onBlur',
    defaultValues: {
      roll_no: '',
      email: '',
      full_name: '',
      password: '',
      role: defaultRole,
      department_id: '',
    },
  });

  const role = watch('role');
  const activeCopy = ROLE_COPY[role];
  const isStudent = role === 'student';

  const lookupStudentByRoll = useCallback(
    async (rawRoll: string) => {
      const rollNo = rawRoll.trim();
      if (!isStudent || !rollNo) {
        setRollLookupError(null);
        setRollMatched(false);
        return;
      }

      setRollLookupPending(true);
      setRollLookupError(null);
      setRollMatched(false);

      try {
        const match = await studentsApi.lookupByRoll(rollNo);
        setValue('full_name', sanitizePersonName(match.name), { shouldValidate: true });
        setValue('department_id', match.department_id ? String(match.department_id) : '', {
          shouldValidate: true,
        });
        setRollMatched(true);
        setRollLookupError(null);
      } catch (err) {
        setRollMatched(false);
        if (formatError(err).status === 404) {
          setRollLookupError(null);
        } else {
          setRollLookupError(formatError(err).message || 'Could not look up roll number.');
        }
      } finally {
        setRollLookupPending(false);
      }
    },
    [isStudent, setValue],
  );

  const fieldsLocked = isStudent && rollMatched;
  const canSubmit = !isStudent || (!rollLookupPending && !rollLookupError);

  return (
    <form
      className="space-y-4"
      onSubmit={handleSubmit(async (v) => {
        await onSubmit({
          email: v.email,
          full_name: v.full_name,
          password: v.password,
          role: v.role,
          roll_no: v.roll_no?.trim() || null,
          department_id: v.department_id ? Number(v.department_id) : null,
          is_active: true,
        });
      })}
    >
      <p className="text-sm text-ink-muted">{copy.title} — share the email and password securely after creation.</p>

      {isStudent && (
        <Input
          label="Roll number"
          autoComplete="off"
          placeholder="e.g. BSCS040001"
          hint="Enter an existing student roll number to link this login, or type a new roll number."
          error={rollLookupError ?? errors.roll_no?.message}
          disabled={loading}
          {...register('roll_no', {
            onBlur: (event) => {
              void lookupStudentByRoll(event.target.value);
            },
          })}
        />
      )}

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
        disabled={fieldsLocked}
        {...bindPersonNameField(register('full_name'))}
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
        {...register('role', {
          onChange: () => {
            setRollLookupError(null);
            setRollMatched(false);
          },
        })}
      />
      <Select
        label="Department"
        placeholder={role === 'faculty' ? 'Select department' : 'None'}
        options={departmentOptions}
        hint={activeCopy.departmentHint}
        error={errors.department_id?.message}
        disabled={fieldsLocked}
        {...register('department_id')}
      />
      <div className="flex justify-end pt-2">
        <Button type="submit" loading={loading || rollLookupPending} disabled={loading || rollLookupPending || !canSubmit}>
          Create {role} account
        </Button>
      </div>
    </form>
  );
}
