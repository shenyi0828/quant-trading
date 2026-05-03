import { useMemo } from 'react';
import { Activity } from 'lucide-react';
import type { FactorHeatmapData } from '../data/mock';

interface FactorHeatmapProps {
  data: FactorHeatmapData;
}

export function FactorHeatmap({ data }: FactorHeatmapProps) {
  const { stocks, factors, scores } = data;

  const colorScale = useMemo(() => {
    const allScores = scores.flat();
    const min = Math.min(...allScores);
    const max = Math.max(...allScores);
    return { min, max };
  }, [scores]);

  const getCellColor = (score: number) => {
    const { min, max } = colorScale;
    const range = max - min;
    if (range === 0) return 'bg-bg-secondary';

    const normalized = (score - min) / range;

    if (score > 0) {
      const intensity = Math.min(1, normalized * 2);
      return `rgba(34, 197, 94, ${0.2 + intensity * 0.6})`;
    } else {
      const intensity = Math.min(1, (1 - normalized) * 2);
      return `rgba(239, 68, 68, ${0.2 + intensity * 0.6})`;
    }
  };

  const getCellTextColor = (score: number) => {
    const absScore = Math.abs(score);
    return absScore > 0.5 ? 'text-white' : score > 0 ? 'text-profit' : 'text-loss';
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent-blue" />
            Factor Heatmap
          </h2>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-profit/60" />
              <span className="text-text-secondary">Positive</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-loss/60" />
              <span className="text-text-secondary">Negative</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 overflow-x-auto">
        <div className="inline-block">
          <div className="grid" style={{ gridTemplateColumns: `100px repeat(${factors.length}, minmax(60px, 1fr))` }}>
            <div className="sticky left-0 bg-bg-secondary/80 border-b border-r border-border p-2 text-xs font-medium text-text-secondary">
              Stock / Factor
            </div>
            {factors.map((factor, idx) => (
              <div
                key={idx}
                className="p-2 text-xs font-medium text-text-secondary border-b border-border text-center truncate"
                style={{ minWidth: '60px' }}
              >
                {factor.split(' ')[0]}
              </div>
            ))}

            {stocks.map((stock, stockIdx) => (
              <>
                <div
                  key={`stock-${stockIdx}`}
                  className="sticky left-0 bg-bg-secondary/80 border-r border-border p-2 text-xs font-medium text-text-primary truncate"
                  style={{ maxWidth: '100px' }}
                >
                  {stock.split('.')[0]}
                </div>
                {scores[stockIdx]?.map((score, factorIdx) => (
                  <div
                    key={`cell-${stockIdx}-${factorIdx}`}
                    className="p-2 border-b border-border border-r border-border/50 text-center cursor-pointer hover:opacity-80 transition-opacity"
                    style={{ backgroundColor: getCellColor(score) }}
                  >
                    <span className={`text-xs font-medium ${getCellTextColor(score)}`}>
                      {score.toFixed(2)}
                    </span>
                  </div>
                ))}
              </>
            ))}
          </div>
        </div>
      </div>

      <div className="px-5 py-3 border-t border-border bg-bg-secondary/30">
        <div className="flex items-center justify-between text-xs text-text-muted">
          <span>{stocks.length} stocks × {factors.length} factors</span>
          <span>Click cells to view detailed factor exposure</span>
        </div>
      </div>
    </div>
  );
}
