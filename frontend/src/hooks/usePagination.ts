import { useMemo, useState } from 'react';

export interface PaginationState {
  page: number;
  pageSize: number;
}

export function usePagination(initial: Partial<PaginationState> = {}) {
  const [state, setState] = useState<PaginationState>({
    page: initial.page ?? 1,
    pageSize: initial.pageSize ?? 20,
  });

  const helpers = useMemo(
    () => ({
      next: () => setState((s) => ({ ...s, page: s.page + 1 })),
      prev: () => setState((s) => ({ ...s, page: Math.max(1, s.page - 1) })),
      goto: (page: number) => setState((s) => ({ ...s, page: Math.max(1, page) })),
      setPageSize: (pageSize: number) => setState({ page: 1, pageSize }),
      reset: () => setState({ page: 1, pageSize: state.pageSize }),
    }),
    [state.pageSize],
  );

  return { ...state, ...helpers, setState };
}
