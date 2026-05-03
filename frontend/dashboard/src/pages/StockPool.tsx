import { useState } from 'react';
import { Search, Filter, TrendingUp, TrendingDown, Star, StarOff, X, BarChart3, DollarSign, PieChart, Activity } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { mockStocks } from '../data/mock';
import type { Stock } from '../types';

const industries = ['全部', '银行', '房地产', '食品饮料', '电子', '保险', '医药生物', '汽车', '公用事业', '商贸零售', '非银金融', '电力设备'];

function StockDetailModal({ stock, onClose }: { stock: Stock; onClose: () => void }) {
  const formatMarketCap = (value: number) => {
    if (value >= 1000000000000) {
      return `¥${(value / 1000000000000).toFixed(2)}万亿`;
    }
    return `¥${(value / 100000000).toFixed(0)}亿`;
  };

  const formatVolume = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="glass-card rounded-xl w-full max-w-lg p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-2xl font-bold text-text-primary">{stock.name}</h2>
            <span className="text-sm text-text-secondary bg-bg-secondary px-2 py-1 rounded">{stock.symbol}</span>
            <span className="text-xs text-accent-cyan bg-accent-cyan/10 px-2 py-1 rounded">{stock.industry}</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-text-primary">¥{stock.price.toFixed(2)}</span>
            <span className={`text-lg ${stock.change >= 0 ? 'text-profit' : 'text-loss'}`}>
              {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
            </span>
            <span className={`text-sm px-2 py-1 rounded ${stock.change >= 0 ? 'bg-profit/10 text-profit' : 'bg-loss/10 text-loss'}`}>
              {stock.change >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-bg-secondary/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-text-secondary mb-1">
              <PieChart className="w-4 h-4" />
              <span className="text-sm">市值</span>
            </div>
            <span className="text-lg font-semibold text-text-primary">{formatMarketCap(stock.marketCap)}</span>
          </div>
          <div className="bg-bg-secondary/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-text-secondary mb-1">
              <BarChart3 className="w-4 h-4" />
              <span className="text-sm">成交量</span>
            </div>
            <span className="text-lg font-semibold text-text-primary">{formatVolume(stock.volume)}</span>
          </div>
          <div className="bg-bg-secondary/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-text-secondary mb-1">
              <DollarSign className="w-4 h-4" />
              <span className="text-sm">市盈率</span>
            </div>
            <span className="text-lg font-semibold text-text-primary">{stock.pe.toFixed(2)}</span>
          </div>
          <div className="bg-bg-secondary/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-text-secondary mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-sm">市净率</span>
            </div>
            <span className="text-lg font-semibold text-text-primary">{stock.pb.toFixed(2)}</span>
          </div>
        </div>

        <div className="flex gap-3">
          <button className="flex-1 py-3 bg-accent-cyan/20 text-accent-cyan rounded-lg font-medium hover:bg-accent-cyan/30 transition-colors">
            加入自选
          </button>
          <button className="flex-1 py-3 bg-bg-secondary text-text-primary rounded-lg font-medium hover:bg-bg-hover transition-colors">
            查看详情
          </button>
        </div>
      </div>
    </div>
  );
}

export function StockPool() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('全部');
  const [minMarketCap, setMinMarketCap] = useState<string>('');
  const [minChange, setMinChange] = useState<string>('');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set(['000001', '600519']));

  const filteredStocks = mockStocks.filter((stock: Stock) => {
    const matchesSearch = 
      stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.symbol.includes(searchQuery);
    const matchesIndustry = selectedIndustry === '全部' || stock.industry === selectedIndustry;
    const matchesMarketCap = !minMarketCap || stock.marketCap >= parseFloat(minMarketCap) * 100000000;
    const matchesChange = !minChange || stock.changePercent >= parseFloat(minChange);
    
    return matchesSearch && matchesIndustry && matchesMarketCap && matchesChange;
  });

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => {
      const next = new Set(prev);
      if (next.has(symbol)) {
        next.delete(symbol);
      } else {
        next.add(symbol);
      }
      return next;
    });
  };

  const avgChange = filteredStocks.reduce((sum: number, s: Stock) => sum + s.changePercent, 0) / filteredStocks.length;
  const upCount = filteredStocks.filter((s: Stock) => s.change >= 0).length;
  const downCount = filteredStocks.filter((s: Stock) => s.change < 0).length;
  const totalVolume = filteredStocks.reduce((sum: number, s: Stock) => sum + s.volume, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {selectedStock && (
        <StockDetailModal 
          stock={selectedStock} 
          onClose={() => setSelectedStock(null)} 
        />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">股票池</h1>
          <p className="text-sm text-text-secondary mt-1">
            自选股票管理与多维度筛选
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="上涨股票"
          value={upCount}
          icon={<TrendingUp className="w-5 h-5 text-profit" />}
          color="profit"
        />
        <MetricCard
          title="下跌股票"
          value={downCount}
          icon={<TrendingDown className="w-5 h-5 text-loss" />}
          color="loss"
        />
        <MetricCard
          title="平均涨跌幅"
          value={avgChange.toFixed(2)}
          suffix="%"
          icon={avgChange >= 0 ? <TrendingUp className="w-5 h-5 text-profit" /> : <TrendingDown className="w-5 h-5 text-loss" />}
          color={avgChange >= 0 ? 'profit' : 'loss'}
        />
        <MetricCard
          title="总成交量"
          value={Math.round(totalVolume / 1000000)}
          suffix="M"
          icon={<Activity className="w-5 h-5 text-accent-cyan" />}
        />
      </div>

      <div className="glass-card rounded-xl p-5 space-y-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 bg-bg-secondary rounded-lg px-3 py-2">
            <Search className="w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="搜索股票代码或名称"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-none text-sm text-text-primary w-48"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-text-muted" />
            <span className="text-sm text-text-secondary">行业:</span>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              className="bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm text-text-primary"
            >
              {industries.map((ind) => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-text-secondary">最小市值(亿):</span>
            <input
              type="number"
              value={minMarketCap}
              onChange={(e) => setMinMarketCap(e.target.value)}
              placeholder="不限"
              className="bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm text-text-primary w-24"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-text-secondary">最小涨幅(%):</span>
            <input
              type="number"
              value={minChange}
              onChange={(e) => setMinChange(e.target.value)}
              placeholder="不限"
              className="bg-bg-secondary border border-border rounded-lg px-3 py-2 text-sm text-text-primary w-24"
            />
          </div>

          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedIndustry('全部');
              setMinMarketCap('');
              setMinChange('');
            }}
            className="text-sm text-accent-cyan hover:text-accent-cyan-light transition-colors"
          >
            重置筛选
          </button>
        </div>

        <div className="text-sm text-text-secondary">
          共找到 {filteredStocks.length} 只股票
          {watchlist.size > 0 && ` | 自选股: ${watchlist.size}`}
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-4 py-3 text-center w-12">
                <span className="text-xs font-medium text-text-secondary">自选</span>
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">代码</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">名称</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">行业</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">最新价</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">涨跌额</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">涨跌幅</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">市值</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">PE</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">PB</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredStocks.map((stock: Stock) => (
              <tr 
                key={stock.symbol} 
                className="hover:bg-bg-hover transition-colors cursor-pointer"
                onClick={() => setSelectedStock(stock)}
              >
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleWatchlist(stock.symbol);
                    }}
                    className="text-text-secondary hover:text-warning transition-colors"
                  >
                    {watchlist.has(stock.symbol) ? (
                      <Star className="w-4 h-4 text-warning fill-warning" />
                    ) : (
                      <StarOff className="w-4 h-4" />
                    )}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-accent-cyan">{stock.symbol}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-text-primary">{stock.name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-text-secondary bg-bg-secondary px-2 py-1 rounded">
                    {stock.industry}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm font-medium text-text-primary">¥{stock.price.toFixed(2)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`text-sm ${stock.change >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`text-sm px-2 py-1 rounded ${
                    stock.changePercent >= 0 
                      ? 'bg-profit/10 text-profit' 
                      : 'bg-loss/10 text-loss'
                  }`}>
                    {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm text-text-secondary">
                    {stock.marketCap >= 1000000000000 
                      ? `¥${(stock.marketCap / 1000000000000).toFixed(2)}万亿`
                      : `¥${(stock.marketCap / 100000000).toFixed(0)}亿`
                    }
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm text-text-primary">{stock.pe.toFixed(1)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm text-text-primary">{stock.pb.toFixed(2)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredStocks.length === 0 && (
          <div className="text-center py-12 text-text-secondary">
            <p>没有找到符合条件的股票</p>
            <p className="text-sm mt-1">请调整筛选条件</p>
          </div>
        )}
      </div>
    </div>
  );
}
