import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { BacktestResult } from '../data/mock';

interface BacktestResultsProps {
  result: BacktestResult;
}

export function BacktestResults({ result }: BacktestResultsProps) {
  const chartData = result.equityCurve.map((point, index) => ({
    date: point.date.slice(5),
    equity: point.equity,
    benchmark: result.benchmarkCurve[index]?.equity || point.equity,
  }));

  const isPositive = result.finalEquity >= result.initialCapital;

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            {isPositive ? (
              <TrendingUp className="w-5 h-5 text-profit" />
            ) : (
              <TrendingDown className="w-5 h-5 text-loss" />
            )}
            Equity Curve
          </h2>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-accent-cyan/60" />
              <span className="text-text-secondary">Strategy</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-sm bg-text-muted/60" />
              <span className="text-text-secondary">
                Benchmark {result.benchmark !== 'None' ? `(${result.benchmark})` : ''}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-5">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="strategyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0.3} />
                <stop offset="95%" stopColor={isPositive ? '#22c55e' : '#ef4444'} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="benchmarkGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#64748b" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#64748b" stopOpacity={0} />
              </linearGradient>
            </defs>
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
              tickFormatter={(value) => `¥${(value / 10000).toFixed(0)}万`}
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const equityPoint = payload.find((p) => p.dataKey === 'equity');
                  const benchmarkPoint = payload.find((p) => p.dataKey === 'benchmark');
                  return (
                    <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                      <p className="text-xs text-text-muted mb-2">{payload[0].payload.date}</p>
                      {equityPoint && (
                        <p className="text-sm font-semibold text-accent-cyan mb-1">
                          Strategy: ¥{(Number(equityPoint.value) / 10000).toFixed(2)}万
                        </p>
                      )}
                      {benchmarkPoint && result.benchmark !== 'None' && (
                        <p className="text-sm font-semibold text-text-muted">
                          Benchmark: ¥{(Number(benchmarkPoint.value) / 10000).toFixed(2)}万
                        </p>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke={isPositive ? '#22c55e' : '#ef4444'}
              strokeWidth={2}
              fill="url(#strategyGradient)"
            />
            {result.benchmark !== 'None' && (
              <Line
                type="monotone"
                dataKey="benchmark"
                stroke="#64748b"
                strokeWidth={1.5}
                strokeDasharray="5 5"
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
