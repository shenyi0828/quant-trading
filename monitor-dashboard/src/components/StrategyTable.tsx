import { useNavigate } from 'react-router-dom';
import { TrendingUp, ArrowDownRight, Clock } from 'lucide-react';
import type { Strategy } from '../types';
import { StatusBadge } from './StatusBadge';

interface StrategyTableProps {
  strategies: Strategy[];
}

export function StrategyTable({ strategies }: StrategyTableProps) {
  const navigate = useNavigate();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Active Strategies</h2>
          <div className="flex items-center gap-4 text-sm text-text-muted">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-profit status-running" />
              <span>Running</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-text-muted" />
              <span>Stopped</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-loss" />
              <span>Error</span>
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Strategy
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Status
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Total P&L
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Win Rate
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Sharpe Ratio
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Trades
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Positions
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Runtime
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {strategies.map((strategy, index) => (
              <tr
                key={strategy.id}
                className="cursor-pointer transition-colors hover:bg-bg-hover"
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => navigate(`/strategy/${strategy.id}`)}
              >
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      strategy.totalPnL >= 0 ? 'bg-profit/10' : 'bg-loss/10'
                    }`}>
                      {strategy.totalPnL >= 0 ? (
                        <TrendingUp className={`w-5 h-5 ${strategy.totalPnL >= 0 ? 'text-profit' : 'text-loss'}`} />
                      ) : (
                        <ArrowDownRight className="w-5 h-5 text-loss" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">{strategy.name}</p>
                      <p className="text-xs text-text-muted">{strategy.description.slice(0, 40)}...</p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={strategy.status} />
                </td>
                <td className="px-5 py-4 text-right">
                  <div className={`text-sm font-semibold ${strategy.totalPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {strategy.totalPnL >= 0 ? '+' : ''}{formatCurrency(strategy.totalPnL)}
                  </div>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="text-sm text-text-primary">{formatPercent(strategy.winRate)}</div>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className={`text-sm font-medium ${strategy.sharpeRatio >= 1 ? 'text-profit' : strategy.sharpeRatio >= 0 ? 'text-text-secondary' : 'text-loss'}`}>
                    {strategy.sharpeRatio.toFixed(2)}
                  </div>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="text-sm text-text-primary">{strategy.totalTrades.toLocaleString()}</div>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="text-sm text-text-primary">{strategy.activePositions}</div>
                </td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{strategy.runtime}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
