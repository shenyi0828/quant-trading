import type { StrategyStatus } from '../types';

interface StatusBadgeProps {
  status: StrategyStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    running: {
      label: 'Running',
      dotClass: 'bg-profit status-running',
      textClass: 'text-profit',
      bgClass: 'bg-profit/10 border-profit/30',
    },
    stopped: {
      label: 'Stopped',
      dotClass: 'bg-text-muted',
      textClass: 'text-text-muted',
      bgClass: 'bg-text-muted/10 border-text-muted/30',
    },
    error: {
      label: 'Error',
      dotClass: 'bg-loss',
      textClass: 'text-loss',
      bgClass: 'bg-loss/10 border-loss/30',
    },
  };

  const { label, dotClass, textClass, bgClass } = config[status];

  return (
    <div className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border ${bgClass}`}>
      <span className={`w-2 h-2 rounded-full ${dotClass}`} />
      <span className={`text-xs font-medium ${textClass}`}>{label}</span>
    </div>
  );
}
