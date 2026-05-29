import type { RiskLevel } from '@/lib/constants';

export type FinancialStatus = 'low' | 'medium' | 'high';
export type PlacementReadiness = 'low' | 'medium' | 'high';

export interface Student {
  id: number;
  roll_no: string;
  name: string;
  age: number;
  gender: string;
  department_id: number | null;
  department_code: string | null;
  department_name: string | null;
  semester: number;
  attendance_pct: number;
  internal_marks: number;
  semester_marks: number;
  backlogs: number;
  fee_paid: boolean;
  fee_delay_days: number;
  financial_status: FinancialStatus;
  family_background: string;
  behavioral_indicators: string;
  extracurricular: string;
  placement_readiness: PlacementReadiness;
  counselor_remarks: string;
  faculty_notes: string;
  created_at: string;
  updated_at: string;
  latest_risk: RiskLevel | null;
  latest_confidence: number | null;
}

export interface StudentCreatePayload {
  roll_no: string;
  name: string;
  age: number;
  gender: string;
  department_id: number | null;
  semester: number;
  attendance_pct: number;
  internal_marks: number;
  semester_marks: number;
  backlogs: number;
  fee_paid: boolean;
  fee_delay_days: number;
  financial_status: FinancialStatus;
  family_background?: string;
  behavioral_indicators?: string;
  extracurricular?: string;
  placement_readiness: PlacementReadiness;
  counselor_remarks?: string;
  faculty_notes?: string;
}

export type StudentUpdatePayload = Partial<StudentCreatePayload>;

export interface TimelineEvent {
  type: 'prediction' | 'counseling' | 'note' | 'risk_snapshot';
  timestamp: string;
  title: string;
  detail: Record<string, unknown>;
}

export interface StudentTimeline {
  student_id: number;
  events: TimelineEvent[];
}
