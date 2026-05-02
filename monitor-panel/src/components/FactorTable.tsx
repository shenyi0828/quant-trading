import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';
import type { Factor } from '../data/mock';

interface FactorTableProps {
  factors: Factor[];
}

export function FactorTable({ factors }: FactorTableProps) {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-profit" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-loss" />;
      default:
        return <Minus className="w-4 h-4 text-text-muted" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'momentum':
        return 'text-accent-cyan';
      case 'trend':
        return 'text-accent-blue';
      case 'volatility':
        return 'text-warning';
      case 'value':
        return 'text-accent-purple';
      default:
        return 'text-text-secondary';
    }
  };

  const getTypeBg = (type: string) => {
    switch (type) {
      case 'momentum':
        return 'bg-accent-cyan/10 border-accent-cyan/30';
      case 'trend':
        return 'bg-accent-blue/10 border-accent-blue/30';
      case 'volatility':
        return 'bg-warning/10 border-warning/30';
      case 'value':
        return 'bg-accent-purple/10 border-accent-purple/30';
      default:
        return 'bg-bg-hover border-border';
    }
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent-cyan" />
            Factor Overview
          </h2>
          <span className="text-xs text-text-muted">{factors.length} factors</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Factor Name
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Type
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Current Value
              </th>
              <th className="px-5 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                Trend
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Last Updated
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {factors.map((factor) => (
              <tr
                key={factor.id}
                className="cursor-pointer transition-colors hover:bg-bg-hover"
              >
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${getTypeBg(factor.type)}`}>
                      <span className={`text-xs font-bold ${getTypeColor(factor.type)}`}>
                        {factor.name.charAt(0)}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-text-primary">
                      {factor.name}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full border ${getTypeBg(factor.type)} ${getTypeColor(factor.type)}`}>
                    {factor.type.charAt(0).toUpperCase() + factor.type.slice(1)}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className={`text-sm font-semibold ${factor.currentValue >= 1 ? 'text-profit' : 'text-loss'}`}>
                    {factor.currentValue >= 1 ? '+' : ''}{((factor.currentValue - 1) * 100).toFixed(2)}%
                  </div>
                </td>
                <td className="px-5 py-4">
                  <div className="flex items-center justify-center gap-2">
                    {getTrendIcon(factor.trend)}
                    <span className={`text-xs font-medium capitalize ${
                      factor.trend === 'up' ? 'text-profit' :
                      factor.trend === 'down' ? 'text-loss' : 'text-text-muted'
                    }`}>
                      {factor.trend}
                    </span>
                  </div>
                </td>
                <td className="px-5 py-4 text-right">
                  <span className="text-xs text-text-muted">
                    {new Date().toLocaleDateString()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
