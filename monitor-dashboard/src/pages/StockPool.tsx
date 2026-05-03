import { useState, useMemo } from 'react';
import { Database, Star } from 'lucide-react';
import { StockFilter } from '../components/StockFilter';
import { WatchlistTable } from '../components/WatchlistTable';
import { StockDetailModal } from '../components/StockDetailModal';
import { getStockPool, getWatchlist, type StockPoolItem } from '../data/mock';

export function StockPool() {
  const allStocks = useMemo(() => getStockPool(), []);
  const watchlistStocks = useMemo(() => getWatchlist(), []);

  const [filters, setFilters] = useState({
    industry: '',
    minMarketCap: 0,
    maxMarketCap: 10000000000000,
    minChange: -100,
    maxChange: 100,
    minVolume: 0,
  });

  const [watchlist, setWatchlist] = useState<Set<string>>(
    new Set(watchlistStocks.map((s) => s.symbol))
  );
  const [selectedStock, setSelectedStock] = useState<StockPoolItem | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'watchlist'>('all');

  const filteredStocks = useMemo(() => {
    const stocksToFilter = activeTab === 'watchlist'
      ? allStocks.filter((s) => watchlist.has(s.symbol))
      : allStocks;

    return stocksToFilter.filter((stock) => {
      if (filters.industry && stock.industry !== filters.industry) return false;
      if (stock.marketCap < filters.minMarketCap || stock.marketCap > filters.maxMarketCap) return false;
      if (stock.changePercent < filters.minChange || stock.changePercent > filters.maxChange) return false;
      if (stock.volume < filters.minVolume) return false;
      return true;
    }).map((stock) => ({
      ...stock,
      inWatchlist: watchlist.has(stock.symbol),
    }));
  }, [allStocks, watchlist, filters, activeTab]);

  const handleToggleWatchlist = (symbol: string) => {
    setWatchlist((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(symbol)) {
        newSet.delete(symbol);
      } else {
        newSet.add(symbol);
      }
      return newSet;
    });
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Database className="w-6 h-6 text-accent-cyan" />
            Stock Pool
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Browse and manage stock universe
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-bold text-text-primary">{allStocks.length}</div>
            <div className="text-xs text-text-muted">Total Stocks</div>
          </div>
          <div className="h-10 w-px bg-border" />
          <div className="text-right">
            <div className="text-2xl font-bold text-accent-cyan">{watchlist.size}</div>
            <div className="text-xs text-text-muted">In Watchlist</div>
          </div>
        </div>
      </div>

      <div className="flex gap-4 border-b border-border">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'all'
              ? 'text-accent-cyan border-accent-cyan'
              : 'text-text-secondary border-transparent hover:text-text-primary'
          }`}
        >
          All Stocks
        </button>
        <button
          onClick={() => setActiveTab('watchlist')}
          className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 ${
            activeTab === 'watchlist'
              ? 'text-accent-cyan border-accent-cyan'
              : 'text-text-secondary border-transparent hover:text-text-primary'
          }`}
        >
          <Star className="w-4 h-4" />
          Watchlist ({watchlist.size})
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div>
          <StockFilter filters={filters} onFilterChange={setFilters} />
        </div>
        <div className="lg:col-span-3">
          <WatchlistTable
            stocks={filteredStocks}
            onToggleWatchlist={handleToggleWatchlist}
            onViewDetail={setSelectedStock}
          />
        </div>
      </div>

      <StockDetailModal
        stock={selectedStock}
        onClose={() => setSelectedStock(null)}
      />
    </div>
  );
}
