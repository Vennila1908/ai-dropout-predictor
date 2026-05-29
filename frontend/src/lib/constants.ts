export const APP_NAME = 'AI Dropout Predictor';

export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '');
export const API_PREFIX = '/api/v1';
export const API_URL = `${API_BASE}${API_PREFIX}`;

export const AUTH_STORAGE_KEY = 'dropout.auth.v1';
export const THEME_STORAGE_KEY = 'theme';

export const ROLES = ['admin', 'faculty', 'student'] as const;
export type Role = (typeof ROLES)[number];

export const RISK_LEVELS = ['low', 'medium', 'high'] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

export const FINANCIAL_STATUSES = ['low', 'medium', 'high'] as const;
export const PLACEMENT_READINESS = ['low', 'medium', 'high'] as const;

export const QUICK_PROMPTS = [
  'Show students with attendance below 60%',
  'How many students are at high risk?',
  'Summarize CSE department risk profile',
  'Which features matter most for risk?',
  'List students with 3+ backlogs',
];
