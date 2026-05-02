import { useState } from 'react';
import { Eye, Star, StarOff, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import type { StockPoolItem } from '../data/mock';

interface WatchlistTableProps {
  stocks: StockPoolItem[];
  onToggleWatchlist: (symbol: string) => void;
  onViewDetail: (stock: StockPoolItem) => void;
}

type SortKey = 'symbol' | 'name' | 'price' | 'changePercent' | 'volume' | 'marketCap';
type SortOrder = 'asc' | 'desc';

export function WatchlistTable({ stocks, onToggleWatchlist, onViewDetail }: WatchlistTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('marketCap');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedStocks = [...stocks].sort((a, b) => {
    let aVal = a[sortKey];
    let bVal = b[sortKey];

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = (bVal as string).toLowerCase();
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

  const formatNumber = (num: number) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('symbol')}
                  className="flex items-center gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Symbol
                  {getSortIcon('symbol')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Name
                  {getSortIcon('name')}
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('price')}
                  className="flex items-center justify-end gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Price
                  {getSortIcon('price')}
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('changePercent')}
                  className="flex items-center justify-end gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Change%
                  {getSortIcon('changePercent')}
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('volume')}
                  className="flex items-center justify-end gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Volume
                  {getSortIcon('volume')}
                </button>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('marketCap')}
                  className="flex items-center justify-end gap-1 text-xs font-medium text-text-secondary uppercase tracking-wider hover:text-text-primary transition-colors"
                >
                  Market Cap
                  {getSortIcon('marketCap')}
                </button>
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sortedStocks.map((stock) => (
              <tr key={stock.symbol} className="hover:bg-bg-hover transition-colors">
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-text-primary">{stock.symbol}</span>
                </td>
                <td className="px-4 py-3">
                  <div>
                    <span className="text-sm font-medium text-text-primary">{stock.name}</span>
                    <p className="text-xs text-text-muted">{stock.industry}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">
                  ¥{stock.price.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`text-sm font-medium ${
                    stock.changePercent >= 0 ? 'text-profit' : 'text-loss'
                  }`}>
                    {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">
                  {formatNumber(stock.volume)}
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">
                  {formatNumber(stock.marketCap)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => onViewDetail(stock)}
                      className="p-1.5 rounded-lg hover:bg-bg-hover transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4 text-text-secondary" />
                    </button>
                    <button
                      onClick={() => onToggleWatchlist(stock.symbol)}
                      className="p-1.5 rounded-lg hover:bg-bg-hover transition-colors"
                      title={stock.inWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
                    >
                      {stock.inWatchlist ? (
                        <Star className="w-4 h-4 text-accent-cyan fill-accent-cyan" />
                      ) : (
                        <StarOff className="w-4 h-4 text-text-muted" />
                      )}
                    </button>
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
