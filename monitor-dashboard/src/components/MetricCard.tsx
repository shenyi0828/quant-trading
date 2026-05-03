import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  prefix?: string;
  suffix?: string;
  icon?: ReactNode;
  color?: 'default' | 'profit' | 'loss';
}

export function MetricCard({
  title,
  value,
  change,
  changeLabel = 'vs yesterday',
  prefix = '',
  suffix = '',
  icon,
  color = 'default',
}: MetricCardProps) {
  const formattedValue = typeof value === 'number'
    ? value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : value;

  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  const getColorClass = () => {
    if (color === 'profit') return 'text-profit';
    if (color === 'loss') return 'text-loss';
    return 'text-text-primary';
  };

  return (
    <div className="glass-card rounded-xl p-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-text-secondary mb-1">{title}</p>
          <div className="flex items-baseline gap-1">
            {prefix && <span className="text-lg text-text-muted">{prefix}</span>}
            <span className={`text-2xl font-bold ${getColorClass()}`}>
              {formattedValue}
            </span>
            {suffix && <span className="text-sm text-text-muted">{suffix}</span>}
          </div>

          {change !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {isPositive ? (
                <TrendingUp className="w-3.5 h-3.5 text-profit" />
              ) : isNegative ? (
                <TrendingDown className="w-3.5 h-3.5 text-loss" />
              ) : null}
              <span className={`text-xs font-medium ${isPositive ? 'text-profit' : isNegative ? 'text-loss' : 'text-text-muted'}`}>
                {isPositive ? '+' : ''}{change.toFixed(2)}%
              </span>
              <span className="text-xs text-text-muted">{changeLabel}</span>
            </div>
          )}
        </div>

        {icon && (
          <div className="w-10 h-10 rounded-lg bg-bg-hover flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
