import { useState } from 'react';
import { Settings, TrendingUp, TrendingDown } from 'lucide-react';
import type { StrategyConfig } from '../data/mock';

interface StrategyCardProps {
  strategy: StrategyConfig;
  onSelect: (strategy: StrategyConfig) => void;
  isSelected: boolean;
  onToggle: (id: string, enabled: boolean) => void;
}

export function StrategyCard({ strategy, onSelect, isSelected, onToggle }: StrategyCardProps) {
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsToggling(true);
    setTimeout(() => {
      onToggle(strategy.id, !strategy.enabled);
      setIsToggling(false);
    }, 300);
  };

  const getStatusBadge = () => {
    if (strategy.enabled) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-profit/10 text-profit border border-profit/30">
          <span className="w-1.5 h-1.5 rounded-full bg-profit status-running" />
          Active
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-text-muted/10 text-text-muted border border-text-muted/30">
        <span className="w-1.5 h-1.5 rounded-full bg-text-muted" />
        Inactive
      </span>
    );
  };

  return (
    <div
      onClick={() => onSelect(strategy)}
      className={`
        glass-card rounded-xl p-5 cursor-pointer transition-all duration-200
        ${isSelected ? 'ring-2 ring-accent-cyan ring-offset-2 ring-offset-bg-primary' : 'hover:border-border-light'}
      `}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-text-primary mb-1">{strategy.name}</h3>
          <p className="text-xs text-text-muted">{strategy.type}</p>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge()}
          <button
            onClick={handleToggle}
            disabled={isToggling}
            className={`
              w-10 h-6 rounded-full transition-colors duration-300 flex items-center px-1
              ${strategy.enabled ? 'bg-profit' : 'bg-bg-hover border border-border'}
            `}
          >
            <div
              className={`
                w-4 h-4 rounded-full bg-white transition-transform duration-300
                ${strategy.enabled ? 'translate-x-4' : 'translate-x-0'}
              `}
            />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-xs text-text-muted block mb-1">Today P&L</span>
          <div className={`text-lg font-bold flex items-center gap-1 ${
            strategy.todayPnL >= 0 ? 'text-profit' : 'text-loss'
          }`}>
            {strategy.todayPnL >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            {strategy.todayPnL >= 0 ? '+' : ''}¥{Math.abs(strategy.todayPnL).toLocaleString()}
          </div>
        </div>
        <div>
          <span className="text-xs text-text-muted block mb-1">Win Rate</span>
          <div className="text-lg font-bold text-text-primary">
            {strategy.winRate.toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="text-xs text-text-muted">
          {strategy.signals.length} recent signals
        </div>
        <button className="p-1.5 rounded-lg hover:bg-bg-hover transition-colors">
          <Settings className="w-4 h-4 text-text-secondary" />
        </button>
      </div>
    </div>
  );
}
