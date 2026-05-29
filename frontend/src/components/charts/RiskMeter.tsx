import { motion } from 'framer-motion';
import { RISK_COLORS } from '@/lib/utils';
import type { RiskLevel } from '@/lib/constants';

export function RiskMeter({
  level,
  confidence,
  className,
}: {
  level: RiskLevel;
  confidence: number;
  className?: string;
}) {
  // Map level to a sensible needle position so even visually it conveys risk.
  const center = level === 'low' ? 18 : level === 'medium' ? 50 : 82;
  const value = Math.min(95, Math.max(5, center + (confidence - 0.7) * 10));

  return (
    <div className={`flex flex-col items-center gap-2 ${className ?? ''}`}>
      <div className="relative h-3 w-full max-w-[260px] overflow-hidden rounded-full bg-surface-inset">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ backgroundColor: RISK_COLORS[level] }}
        />
      </div>
      <div className="flex items-center gap-3 text-sm">
        <span className="font-semibold uppercase" style={{ color: RISK_COLORS[level] }}>
          {level} risk
        </span>
        <span className="text-ink-muted">confidence {(confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}
