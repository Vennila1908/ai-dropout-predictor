import type { Role } from '@/lib/constants';

export * from './api';
export * from './student';
export * from './prediction';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  department_id: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface Department {
  id: number;
  name: string;
  code: string;
}

export interface Upload {
  id: number;
  filename: string;
  original_name: string;
  file_type: string;
  size_bytes: number;
  rows_imported: number;
  status: 'pending' | 'parsed' | 'imported' | 'failed';
  error: string | null;
  uploaded_by: number | null;
  created_at: string;
}

export interface ColumnSuggestion {
  source: string;
  target: string | null;
  score: number;
  candidates: string[];
}

export interface UploadPreview {
  upload_id: number;
  detected_columns: string[];
  suggested_mapping: ColumnSuggestion[];
  preview_rows: Record<string, unknown>[];
  total_rows: number;
  target_fields: string[];
}

export interface UploadConfirmResult {
  upload_id: number;
  rows_imported: number;
  rows_skipped: number;
  errors: string[];
}

export interface CounselingSession {
  id: number;
  student_id: number;
  faculty_id: number | null;
  notes: string;
  outcome: string | null;
  next_followup: string | null;
  created_at: string;
}

export interface OverviewStats {
  total_students: number;
  total_faculty: number;
  total_predictions: number;
  risk_split: Record<string, number>;
  avg_attendance: number;
  avg_internal_marks: number;
  high_risk_pct: number;
  last_trained_at: string | null;
}

export interface RiskBucket { risk_level: string; count: number }
export interface DepartmentRisk {
  department_id: number;
  department_name: string;
  department_code: string;
  low: number;
  medium: number;
  high: number;
}
export interface AttendanceTrendPoint { semester: number; avg_attendance: number; student_count: number }
export interface ConfidenceBucket { bucket: string; count: number }
