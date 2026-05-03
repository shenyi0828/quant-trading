import { Activity, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import type { BacktestResult } from '../data/mock';

interface PerformanceMetricsProps {
  result: BacktestResult;
}

export function PerformanceMetrics({ result }: PerformanceMetricsProps) {
  const metrics = [
    {
      label: 'Annual Return',
      value: result.annualReturn,
      suffix: '%',
      color: result.annualReturn >= 0 ? 'text-profit' : 'text-loss',
      icon: result.annualReturn >= 0 ? TrendingUp : TrendingDown,
    },
    {
      label: 'Max Drawdown',
      value: Math.abs(result.maxDrawdown),
      prefix: '-',
      suffix: '%',
      color: 'text-loss',
      icon: BarChart3,
    },
    {
      label: 'Sharpe Ratio',
      value: result.sharpeRatio,
      color: result.sharpeRatio >= 1 ? 'text-profit' : result.sharpeRatio >= 0 ? 'text-text-secondary' : 'text-loss',
      icon: Activity,
    },
    {
      label: 'Win Rate',
      value: result.winRate,
      suffix: '%',
      color: result.winRate >= 50 ? 'text-profit' : 'text-loss',
      icon: TrendingUp,
    },
    {
      label: 'Total Trades',
      value: result.totalTrades,
      color: 'text-text-primary',
      icon: BarChart3,
    },
    {
      label: 'Profit Factor',
      value: result.profitFactor,
      color: result.profitFactor >= 1.5 ? 'text-profit' : result.profitFactor >= 1 ? 'text-text-secondary' : 'text-loss',
      icon: Activity,
    },
  ];

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Activity className="w-5 h-5 text-accent-cyan" />
          Performance Metrics
        </h2>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="bg-bg-secondary/50 rounded-lg p-4 border border-border hover:border-border-light transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <metric.icon className="w-4 h-4 text-text-muted" />
                <span className="text-xs text-text-secondary">{metric.label}</span>
              </div>
              <div className={`text-xl font-bold ${metric.color}`}>
                {metric.prefix || ''}
                {typeof metric.value === 'number' && metric.value % 1 !== 0
                  ? metric.value.toFixed(2)
                  : metric.value}
                {metric.suffix || ''}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-border">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-text-muted mb-1">Initial Capital</div>
              <div className="text-sm font-medium text-text-primary">
                ¥{(result.initialCapital / 10000).toFixed(0)}万
              </div>
            </div>
            <div>
              <div className="text-xs text-text-muted mb-1">Final Equity</div>
              <div className={`text-sm font-medium ${result.finalEquity >= result.initialCapital ? 'text-profit' : 'text-loss'}`}>
                ¥{(result.finalEquity / 10000).toFixed(0)}万
              </div>
            </div>
            <div>
              <div className="text-xs text-text-muted mb-1">Total Return</div>
              <div className={`text-sm font-medium ${result.finalEquity >= result.initialCapital ? 'text-profit' : 'text-loss'}`}>
                {((result.finalEquity - result.initialCapital) / result.initialCapital * 100).toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
