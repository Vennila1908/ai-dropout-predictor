import { useQuery } from '@tanstack/react-query';

import { departmentsApi } from '@/features/departments/departmentsApi';

export function useDepartments() {
  return useQuery({
    queryKey: ['departments'],
    queryFn: departmentsApi.list,
    staleTime: 60_000,
  });
}
