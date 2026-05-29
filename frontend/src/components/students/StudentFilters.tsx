import { Search } from 'lucide-react';
import { Select } from '@/components/ui/Select';
import { useState, useEffect } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import type { RiskLevel } from '@/lib/constants';

export interface StudentFiltersValue {
  q: string;
  risk: RiskLevel | '';
}

export function StudentFilters({
  value,
  onChange,
}: {
  value: StudentFiltersValue;
  onChange: (next: StudentFiltersValue) => void;
}) {
  const [q, setQ] = useState(value.q);
  const debouncedQ = useDebounce(q, 350);

  useEffect(() => {
    onChange({ ...value, q: debouncedQ });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ]);

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <label className="relative w-full sm:max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
        <input
          className="input pl-9"
          placeholder="Search by roll or name"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </label>
      <Select
        label="Risk"
        value={value.risk}
        onChange={(e) => onChange({ ...value, risk: e.target.value as RiskLevel | '' })}
        options={[
          { value: '', label: 'Any' },
          { value: 'low', label: 'Low' },
          { value: 'medium', label: 'Medium' },
          { value: 'high', label: 'High' },
        ]}
      />
    </div>
  );
}
