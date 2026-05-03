import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Activity, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import type { Signal } from '../data/mock';

interface SignalChartProps {
  signals: Signal[];
}

export function SignalChart({ signals }: SignalChartProps) {
  const chartData = useMemo(() => {
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;

    const priceData: { timestamp: number; date: string; price: number }[] = [];
    let price = 50;

    for (let i = 30; i >= 0; i--) {
      const timestamp = now - i * oneDay;
      const date = new Date(timestamp).toISOString().split('T')[0];
      price *= 1 + (Math.random() - 0.48) * 0.03;
      priceData.push({ timestamp, date, price: Math.round(price * 100) / 100 });
    }

    const signalPoints = signals.slice(0, 20).map((signal) => {
      const signalTime = new Date(signal.timestamp).getTime();
      const closestPricePoint = priceData.reduce((closest, point) => {
        return Math.abs(point.timestamp - signalTime) < Math.abs(closest.timestamp - signalTime)
          ? point
          : closest;
      }, priceData[0]);

      return {
        timestamp: signalTime,
        date: signal.timestamp.slice(5, 10),
        price: closestPricePoint.price,
        action: signal.action,
        symbol: signal.symbol,
        name: signal.name,
      };
    });

    return { priceData, signalPoints };
  }, [signals]);

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent-purple" />
            Signal Timeline
          </h2>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <ArrowUpCircle className="w-4 h-4 text-profit" />
              <span className="text-text-secondary">Buy Signal</span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowDownCircle className="w-4 h-4 text-loss" />
              <span className="text-text-secondary">Sell Signal</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-5">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData.priceData} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={{ stroke: '#334155' }}
              tickLine={false}
              minTickGap={30}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#64748b', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => `¥${value.toFixed(0)}`}
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const point = payload[0].payload;
                  return (
                    <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                      <p className="text-xs text-text-muted mb-1">{point.date}</p>
                      <p className="text-sm font-semibold text-text-primary">
                        Price: ¥{point.price?.toFixed(2) || point.value?.toFixed(2)}
                      </p>
                      {point.action && (
                        <p className={`text-xs mt-1 font-medium ${
                          point.action === 'buy' ? 'text-profit' : 'text-loss'
                        }`}>
                          {point.action.toUpperCase()} - {point.name || point.symbol}
                        </p>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={chartData.priceData[0]?.price || 50} stroke="#334155" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#3b82f6' }}
            />
            <Scatter
              data={chartData.signalPoints.filter((s) => s.action === 'buy')}
              fill="#22c55e"
              shape="circle"
            />
            <Scatter
              data={chartData.signalPoints.filter((s) => s.action === 'sell')}
              fill="#ef4444"
              shape="circle"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
