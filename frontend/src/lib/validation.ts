import type { UseFormRegisterReturn } from 'react-hook-form';
import { z } from 'zod';

/** Letters and digits only — no spaces or special characters. */
export const ROLL_NO_REGEX = /^[A-Za-z0-9]+$/;

/** Letters and spaces only — no digits or special characters. */
export const PERSON_NAME_REGEX = /^[A-Za-z ]+$/;

/** Strip digits and other characters invalid in a person name. */
export function sanitizePersonName(value: string): string {
  return value.replace(/[^A-Za-z ]/g, '');
}

/** Block invalid characters while typing; pair with `mode: 'onBlur'` for error messages. */
export function bindPersonNameField(field: UseFormRegisterReturn): UseFormRegisterReturn {
  const { onChange, ...rest } = field;
  return {
    ...rest,
    onChange: (event) => {
      const input = event.target as HTMLInputElement;
      const sanitized = sanitizePersonName(input.value);
      if (sanitized !== input.value) {
        input.value = sanitized;
      }
      return onChange(event);
    },
  };
}

export const rollNoSchema = z
  .string()
  .min(1, 'Roll number is required')
  .max(40)
  .regex(ROLL_NO_REGEX, 'Roll number must contain letters and numbers only');

export const personNameSchema = z
  .string()
  .min(1, 'Name is required')
  .max(160)
  .regex(PERSON_NAME_REGEX, 'Name must contain letters and spaces only');

export const personNameLongSchema = z
  .string()
  .min(1, 'Name is required')
  .max(255)
  .regex(PERSON_NAME_REGEX, 'Name must contain letters and spaces only');
