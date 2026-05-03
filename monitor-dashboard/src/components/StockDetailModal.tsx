import { X, TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { StockPoolItem } from '../data/mock';

interface StockDetailModalProps {
  stock: StockPoolItem | null;
  onClose: () => void;
}

export function StockDetailModal({ stock, onClose }: StockDetailModalProps) {
  if (!stock) return null;

  const generateMiniChartData = () => {
    const data = [];
    let price = stock.price;
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;

    for (let i = 30; i >= 0; i--) {
      const timestamp = now - i * oneDay;
      const date = new Date(timestamp).toISOString().split('T')[0];
      price *= 1 + (Math.random() - 0.48) * 0.03;
      data.push({ date, price: Math.round(price * 100) / 100 });
    }
    return data;
  };

  const chartData = generateMiniChartData();
  const isPositive = stock.changePercent >= 0;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card rounded-xl w-full max-w-lg animate-fade-in">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-text-primary">{stock.name}</h2>
            <p className="text-sm text-text-muted">{stock.symbol}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-bg-hover transition-colors"
          >
            <X className="w-5 h-5 text-text-secondary" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-3xl font-bold text-text-primary">
                ¥{stock.price.toFixed(2)}
              </div>
              <div className={`flex items-center gap-1 mt-1 ${isPositive ? 'text-profit' : 'text-loss'}`}>
                {isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">
                  {isPositive ? '+' : ''}{stock.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-text-muted">Industry</div>
              <div className="text-sm font-medium text-text-primary">{stock.industry}</div>
            </div>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={false}
                  tickFormatter={(date) => date.slice(5)}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: '#64748b', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const point = payload[0].payload;
                      return (
                        <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                          <p className="text-xs text-text-muted">{point.date}</p>
                          <p className="text-sm font-semibold text-text-primary">
                            ¥{point.price.toFixed(2)}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke={isPositive ? '#22c55e' : '#ef4444'}
                  strokeWidth={2}
                  fill="url(#priceGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-bg-secondary/50 rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-text-muted" />
                <span className="text-xs text-text-secondary">Volume</span>
              </div>
              <div className="text-sm font-medium text-text-primary">
                {(stock.volume / 1000000).toFixed(2)}M
              </div>
            </div>
            <div className="bg-bg-secondary/50 rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-text-muted" />
                <span className="text-xs text-text-secondary">Market Cap</span>
              </div>
              <div className="text-sm font-medium text-text-primary">
                ¥{(stock.marketCap / 1000000000).toFixed(2)}B
              </div>
            </div>
            <div className="bg-bg-secondary/50 rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-text-muted" />
                <span className="text-xs text-text-secondary">P/E Ratio</span>
              </div>
              <div className="text-sm font-medium text-text-primary">{stock.pe.toFixed(2)}</div>
            </div>
            <div className="bg-bg-secondary/50 rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-text-muted" />
                <span className="text-xs text-text-secondary">P/B Ratio</span>
              </div>
              <div className="text-sm font-medium text-text-primary">{stock.pb.toFixed(2)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
