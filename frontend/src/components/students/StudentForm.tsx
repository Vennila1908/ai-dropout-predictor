import { zodResolver } from '@hookform/resolvers/zod';
import { useCallback, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Button } from '@/components/ui/Button';
import { usersApi } from '@/features/users/usersApi';
import { formatError } from '@/lib/api';
import { bindPersonNameField, personNameSchema, rollNoSchema, sanitizePersonName } from '@/lib/validation';
import type { Student, StudentCreatePayload } from '@/types';

const schema = z.object({
  roll_no: rollNoSchema,
  name: personNameSchema,
  age: z.coerce.number().int().min(10).max(80),
  gender: z.string().max(16).default('U'),
  department_id: z.string().optional(),
  semester: z.coerce.number().int().min(1).max(12),
  attendance_pct: z.coerce.number().min(0).max(100),
  internal_marks: z.coerce.number().min(0).max(100),
  semester_marks: z.coerce.number().min(0).max(100),
  backlogs: z.coerce.number().int().min(0).max(50),
  fee_paid: z.coerce.boolean(),
  fee_delay_days: z.coerce.number().int().min(0).max(730),
  financial_status: z.enum(['low', 'medium', 'high']),
  family_background: z.string().optional(),
  behavioral_indicators: z.string().optional(),
  extracurricular: z.string().optional(),
  placement_readiness: z.enum(['low', 'medium', 'high']),
  counselor_remarks: z.string().optional(),
});

export type StudentFormValues = z.infer<typeof schema>;

export function StudentForm({
  initial,
  onSubmit,
  loading,
  submitLabel = 'Save',
  courseOptions = [],
}: {
  initial?: Partial<Student>;
  onSubmit: (values: StudentCreatePayload) => Promise<void> | void;
  loading?: boolean;
  submitLabel?: string;
  courseOptions?: { value: number; label: string }[];
}) {
  const isCreate = !initial?.id;
  const [rollLookupError, setRollLookupError] = useState<string | null>(null);
  const [rollMatched, setRollMatched] = useState(!isCreate);
  const [rollLookupPending, setRollLookupPending] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<StudentFormValues>({
    resolver: zodResolver(schema),
    mode: 'onBlur',
    reValidateMode: 'onBlur',
    defaultValues: {
      roll_no: initial?.roll_no ?? '',
      name: initial?.name ?? '',
      age: initial?.age ?? 20,
      gender: initial?.gender ?? 'U',
      department_id: initial?.department_id ? String(initial.department_id) : '',
      semester: initial?.semester ?? 1,
      attendance_pct: initial?.attendance_pct ?? 75,
      internal_marks: initial?.internal_marks ?? 50,
      semester_marks: initial?.semester_marks ?? 50,
      backlogs: initial?.backlogs ?? 0,
      fee_paid: initial?.fee_paid ?? true,
      fee_delay_days: initial?.fee_delay_days ?? 0,
      financial_status: (initial?.financial_status as 'low' | 'medium' | 'high') ?? 'medium',
      family_background: initial?.family_background ?? '',
      behavioral_indicators: initial?.behavioral_indicators ?? '',
      extracurricular: initial?.extracurricular ?? '',
      placement_readiness: (initial?.placement_readiness as 'low' | 'medium' | 'high') ?? 'medium',
      counselor_remarks: initial?.counselor_remarks ?? '',
    },
  });

  const lookupAccountByRoll = useCallback(
    async (rawRoll: string) => {
      const rollNo = rawRoll.trim();
      if (!isCreate || !rollNo) {
        setRollLookupError(null);
        setRollMatched(!isCreate);
        return;
      }

      setRollLookupPending(true);
      setRollLookupError(null);
      setRollMatched(false);

      try {
        const match = await usersApi.lookupByRoll(rollNo);
        setValue('name', sanitizePersonName(match.full_name), { shouldValidate: true });
        setValue('department_id', match.department_id ? String(match.department_id) : '', {
          shouldValidate: true,
        });
        setRollMatched(true);
      } catch (err) {
        setValue('name', '');
        setValue('department_id', '');
        setRollMatched(false);
        setRollLookupError(
          formatError(err).message ||
            'No login account found for this roll number. Create a student account under User accounts first.',
        );
      } finally {
        setRollLookupPending(false);
      }
    },
    [isCreate, setValue],
  );

  const canSubmit = !isCreate || (rollMatched && !rollLookupPending && !rollLookupError);

  return (
    <form
      onSubmit={handleSubmit(async (v) => {
        if (isCreate && !rollMatched) return;
        await onSubmit({
          ...v,
          department_id: v.department_id ? Number(v.department_id) : null,
          family_background: v.family_background ?? '',
          behavioral_indicators: v.behavioral_indicators ?? '',
          extracurricular: v.extracurricular ?? '',
          counselor_remarks: v.counselor_remarks ?? '',
        });
      })}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2"
    >
      <Input
        label="Roll No"
        disabled={!isCreate}
        hint={isCreate ? 'Enter the roll number from the student login account.' : undefined}
        error={rollLookupError ?? errors.roll_no?.message}
        {...register('roll_no', {
          onBlur: (event) => {
            if (isCreate) void lookupAccountByRoll(event.target.value);
          },
        })}
      />
      <Input
        label="Full Name"
        disabled={isCreate && rollMatched}
        {...bindPersonNameField(register('name'))}
        error={errors.name?.message}
      />
      <Input type="number" label="Age" {...register('age')} error={errors.age?.message} />
      <Select
        label="Gender"
        {...register('gender')}
        options={[
          { value: 'M', label: 'Male' },
          { value: 'F', label: 'Female' },
          { value: 'U', label: 'Unspecified' },
        ]}
      />
      <Select
        label="Degree course"
        placeholder="Select course"
        options={courseOptions}
        hint={
          isCreate && rollMatched
            ? 'Filled from the student login account.'
            : courseOptions.length
              ? 'Assign the student to a degree program.'
              : 'No courses loaded — check Degree courses page.'
        }
        disabled={isCreate && rollMatched}
        {...register('department_id')}
      />
      <Input type="number" label="Semester" {...register('semester')} error={errors.semester?.message} />
      <Input type="number" step="0.1" label="Attendance %" {...register('attendance_pct')} error={errors.attendance_pct?.message} />
      <Input type="number" step="0.1" label="Internal marks" {...register('internal_marks')} error={errors.internal_marks?.message} />
      <Input type="number" step="0.1" label="Semester marks" {...register('semester_marks')} error={errors.semester_marks?.message} />
      <Input type="number" label="Backlogs" {...register('backlogs')} error={errors.backlogs?.message} />
      <Select
        label="Fee paid"
        {...register('fee_paid')}
        options={[
          { value: 'true', label: 'Yes' },
          { value: 'false', label: 'No' },
        ]}
      />
      <Input type="number" label="Fee delay (days)" {...register('fee_delay_days')} error={errors.fee_delay_days?.message} />
      <Select
        label="Financial status"
        {...register('financial_status')}
        options={[
          { value: 'low', label: 'Low' },
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
        ]}
      />
      <Select
        label="Placement readiness"
        {...register('placement_readiness')}
        options={[
          { value: 'low', label: 'Low' },
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
        ]}
      />
      <Textarea label="Family background" className="sm:col-span-2" {...register('family_background')} />
      <Textarea label="Behavioral indicators" className="sm:col-span-2" {...register('behavioral_indicators')} />
      <Textarea label="Extracurricular" className="sm:col-span-2" {...register('extracurricular')} />
      <Textarea label="Counselor remarks" className="sm:col-span-2" {...register('counselor_remarks')} />

      <div className="sm:col-span-2 flex justify-end pt-1">
        <Button type="submit" loading={loading || rollLookupPending} disabled={loading || rollLookupPending || !canSubmit}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
