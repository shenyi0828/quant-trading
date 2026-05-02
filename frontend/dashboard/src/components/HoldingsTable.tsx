import { TrendingUp, TrendingDown } from 'lucide-react';
import type { Holding } from '../types';

interface HoldingsTableProps {
  holdings: Holding[];
}

export function HoldingsTable({ holdings }: HoldingsTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString('en-US');
  };

  const totalMarketValue = holdings.reduce((sum, h) => sum + h.marketValue, 0);
  const totalPnL = holdings.reduce((sum, h) => sum + h.unrealizedPnL, 0);

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">Current Holdings</h2>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-text-muted">Total Market Value</p>
              <p className="text-sm font-semibold text-text-primary">{formatCurrency(totalMarketValue)}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-text-muted">Unrealized P&L</p>
              <p className={`text-sm font-semibold ${totalPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Name
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Quantity
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Cost Price
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Current Price
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Market Value
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                P&L
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                P&L %
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {holdings.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-5 py-8 text-center text-text-muted">
                  No active positions
                </td>
              </tr>
            ) : (
              holdings.map((holding, index) => (
                <tr
                  key={holding.symbol}
                  className="transition-colors hover:bg-bg-hover"
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  <td className="px-5 py-4">
                    <span className="text-sm font-medium text-accent-cyan">{holding.symbol}</span>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-sm text-text-primary">{holding.name}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-sm text-text-primary">{formatNumber(holding.quantity)}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-sm text-text-secondary">{formatCurrency(holding.costPrice)}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-sm text-text-primary">{formatCurrency(holding.currentPrice)}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-sm font-medium text-text-primary">{formatCurrency(holding.marketValue)}</span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className={`flex items-center justify-end gap-1 ${holding.unrealizedPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {holding.unrealizedPnL >= 0 ? (
                        <TrendingUp className="w-3.5 h-3.5" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5" />
                      )}
                      <span className="text-sm font-semibold">
                        {holding.unrealizedPnL >= 0 ? '+' : ''}{formatCurrency(holding.unrealizedPnL)}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className={`text-sm font-semibold ${holding.unrealizedPnLPercent >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {holding.unrealizedPnLPercent >= 0 ? '+' : ''}{holding.unrealizedPnLPercent.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
