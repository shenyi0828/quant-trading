import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import type { Trade } from '../types';

interface TradesTableProps {
  trades: Trade[];
}

export function TradesTable({ trades }: TradesTableProps) {
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

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h2 className="text-lg font-semibold text-text-primary">Recent Trades</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Time
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                Name
              </th>
              <th className="px-5 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                Side
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Quantity
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Price
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                Total
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                P&L
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {trades.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-5 py-8 text-center text-text-muted">
                  No recent trades
                </td>
              </tr>
            ) : (
              trades.slice(0, 15).map((trade, index) => (
                <tr
                  key={trade.id}
                  className="transition-colors hover:bg-bg-hover"
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  <td className="px-5 py-3">
                    <span className="text-sm text-text-secondary">{formatDateTime(trade.time)}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-sm font-medium text-accent-cyan">{trade.symbol}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-sm text-text-primary">{trade.name}</span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex justify-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                        trade.side === 'buy'
                          ? 'bg-profit/10 text-profit border border-profit/30'
                          : 'bg-loss/10 text-loss border border-loss/30'
                      }`}>
                        {trade.side === 'buy' ? (
                          <ArrowUpRight className="w-3 h-3" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3" />
                        )}
                        {trade.side.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-sm text-text-primary">{formatNumber(trade.quantity)}</span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-sm text-text-primary">{formatCurrency(trade.price)}</span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-sm font-medium text-text-primary">{formatCurrency(trade.totalAmount)}</span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {trade.realizedPnL !== undefined ? (
                      <span className={`text-sm font-semibold ${trade.realizedPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                        {trade.realizedPnL >= 0 ? '+' : ''}{formatCurrency(trade.realizedPnL)}
                      </span>
                    ) : (
                      <span className="text-sm text-text-muted">-</span>
                    )}
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
