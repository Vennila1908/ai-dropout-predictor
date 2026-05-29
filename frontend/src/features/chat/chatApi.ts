import { api, unwrap } from '@/lib/api';
import type { DepartmentRisk, OverviewStats, RiskBucket, Student } from '@/types';

export interface ChatArtifacts {
  overview?: OverviewStats | null;
  risk_distribution?: RiskBucket[] | null;
  department_risk?: DepartmentRisk[] | null;
  students?: Student[] | null;
  total_matching_students?: number;
  filters_applied?: Record<string, unknown> | null;
}

export interface ChatQuery {
  message: string;
  context_filters?: Record<string, unknown>;
  stream?: boolean;
}

export interface ChatResponse {
  answer: string;
  source: 'llm' | 'fallback';
  artifacts?: ChatArtifacts;
}

export const chatApi = {
  query: (payload: ChatQuery) => unwrap(api.post<ChatResponse>('/chat/query', payload)),
};
