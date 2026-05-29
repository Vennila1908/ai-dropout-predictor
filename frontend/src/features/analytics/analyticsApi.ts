import { api, unwrap } from '@/lib/api';
import type {
  AttendanceTrendPoint,
  ConfidenceBucket,
  DepartmentRisk,
  OverviewStats,
  RiskBucket,
} from '@/types';

export const analyticsApi = {
  overview: () => unwrap(api.get<OverviewStats>('/analytics/overview')),
  riskDistribution: () => unwrap(api.get<RiskBucket[]>('/analytics/risk-distribution')),
  departmentRisk: () => unwrap(api.get<DepartmentRisk[]>('/analytics/department-risk')),
  attendanceTrends: () => unwrap(api.get<AttendanceTrendPoint[]>('/analytics/attendance-trends')),
  predictionConfidence: () => unwrap(api.get<ConfidenceBucket[]>('/analytics/prediction-confidence')),
  bundle: () =>
    unwrap(
      api.get<{
        overview: OverviewStats;
        risk_distribution: RiskBucket[];
        department_risk: DepartmentRisk[];
        attendance_trends: AttendanceTrendPoint[];
        confidence_distribution: ConfidenceBucket[];
      }>('/analytics/bundle'),
    ),
};
