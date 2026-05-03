import { useState } from 'react';
import { History, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import type { BacktestTrade } from '../data/mock';

interface TradeHistoryTableProps {
  trades: BacktestTrade[];
}

type SortKey = 'time' | 'symbol' | 'side' | 'price' | 'quantity' | 'pnl';
type SortOrder = 'asc' | 'desc';

export function TradeHistoryTable({ trades }: TradeHistoryTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('time');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedTrades = [...trades].sort((a, b) => {
    let aVal: string | number = a[sortKey] || '';
    let bVal: string | number = b[sortKey] || '';

    if (sortKey === 'time') {
      aVal = new Date(a.time).getTime();
      bVal = new Date(b.time).getTime();
    }

    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const getSortIcon = (key: SortKey) => {
    if (sortKey !== key) return <ArrowUpDown className="w-3 h-3 text-text-muted" />;
    return sortOrder === 'asc' ? (
      <ArrowUp className="w-3 h-3 text-accent-cyan" />
    ) : (
      <ArrowDown className="w-3 h-3 text-accent-cyan" />
    );
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <History className="w-5 h-5 text-accent-purple" />
            Trade History
          </h2>
          <span className="text-xs text-text-muted">{trades.length} trades</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th
                className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('time')}
              >
                <div className="flex items-center gap-1">
                  Time
                  {getSortIcon('time')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('symbol')}
              >
                <div className="flex items-center gap-1">
                  Symbol
                  {getSortIcon('symbol')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('side')}
              >
                <div className="flex items-center justify-center gap-1">
                  Side
                  {getSortIcon('side')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('price')}
              >
                <div className="flex items-center justify-end gap-1">
                  Price
                  {getSortIcon('price')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('quantity')}
              >
                <div className="flex items-center justify-end gap-1">
                  Quantity
                  {getSortIcon('quantity')}
                </div>
              </th>
              <th
                className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                onClick={() => handleSort('pnl')}
              >
                <div className="flex items-center justify-end gap-1">
                  P&L
                  {getSortIcon('pnl')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sortedTrades.map((trade) => (
              <tr key={trade.id} className="hover:bg-bg-hover transition-colors">
                <td className="px-4 py-3 text-xs text-text-muted">
                  {formatDate(trade.time)}
                </td>
                <td className="px-4 py-3">
                  <div>
                    <span className="text-sm font-medium text-text-primary">{trade.symbol}</span>
                    <p className="text-xs text-text-muted">{trade.name}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    trade.side === 'buy'
                      ? 'bg-profit/10 text-profit border border-profit/30'
                      : 'bg-loss/10 text-loss border border-loss/30'
                  }`}>
                    {trade.side.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">
                  ¥{trade.price.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">
                  {trade.quantity.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  {trade.pnl !== undefined ? (
                    <span className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {trade.pnl >= 0 ? '+' : ''}¥{trade.pnl.toFixed(2)}
                    </span>
                  ) : (
                    <span className="text-xs text-text-muted">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
