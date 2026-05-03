import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { EquityPoint } from '../types';

interface EquityChartProps {
  data: EquityPoint[];
  height?: number;
}

export function EquityChart({ data, height = 300 }: EquityChartProps) {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const isPositive = data[data.length - 1]?.cumulativeReturn >= 0;

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-text-primary">Equity Curve</h3>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-accent-cyan/30" />
            <span className="text-text-secondary">Equity</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0.3} />
              <stop offset="95%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
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
            tickFormatter={(value) => `¥${(value / 10000).toFixed(0)}万`}
            domain={['auto', 'auto']}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as EquityPoint;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                    <p className="text-xs text-text-muted mb-1">{point.date}</p>
                    <p className="text-sm font-semibold text-text-primary">
                      {formatCurrency(point.equity)}
                    </p>
                    <p className={`text-xs mt-1 ${point.cumulativeReturn >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {point.cumulativeReturn >= 0 ? '+' : ''}{point.cumulativeReturn.toFixed(2)}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine y={data[0]?.equity} stroke="#334155" strokeDasharray="3 3" />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={isPositive ? '#22c55e' : '#ef4444'}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#equityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
