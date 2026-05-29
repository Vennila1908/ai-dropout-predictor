import type { RiskLevel } from '@/lib/constants';

export interface FeatureContribution {
  feature: string;
  value: number | string;
  contribution: number;
  direction: 'increases_risk' | 'decreases_risk' | 'neutral';
}

export interface Explanation {
  top_factors: FeatureContribution[];
  narrative: string;
}

export interface Prediction {
  id: number;
  student_id: number;
  risk_level: RiskLevel;
  confidence: number;
  model_version: string;
  features: Record<string, number | string | boolean>;
  explanation: Explanation;
  created_at: string;
}

export interface BatchPredictionResult {
  total: number;
  succeeded: number;
  failed: number;
  predictions: Prediction[];
}

export interface MLStatus {
  model_name: string | null;
  trained_at: string | null;
  feature_list: string[];
  metrics: Record<string, unknown>;
  confusion_matrix: number[][];
  feature_importances: { feature: string; importance: number }[];
  class_labels: string[];
  artifact_present: boolean;
}

export interface InterventionAction {
  action: string;
  owner: 'faculty' | 'student' | 'admin' | 'parent' | 'counselor';
  timeline: string;
}

export interface RoadmapWeek {
  week: number;
  focus: string;
  activities: string[];
}

export interface RecommendationPlan {
  intervention_plan: InterventionAction[];
  faculty_actions: string[];
  student_roadmap: RoadmapWeek[];
}

export interface Recommendation {
  id: number;
  student_id: number;
  prediction_id: number | null;
  summary: string;
  plan: RecommendationPlan;
  source: 'llm' | 'fallback';
  status: 'pending' | 'in_progress' | 'completed' | 'dismissed';
  created_by: number | null;
  created_at: string;
  updated_at: string;
}
