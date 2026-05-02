import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Activity, ChevronDown } from 'lucide-react';
import type { Factor } from '../data/mock';

interface FactorTrendChartProps {
  factors: Factor[];
}

export function FactorTrendChart({ factors }: FactorTrendChartProps) {
  const [selectedFactor, setSelectedFactor] = useState<Factor>(factors[0]);
  const [showDropdown, setShowDropdown] = useState(false);

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'momentum':
        return '#06b6d4';
      case 'trend':
        return '#3b82f6';
      case 'volatility':
        return '#f59e0b';
      case 'value':
        return '#8b5cf6';
      default:
        return '#64748b';
    }
  };

  const chartData = selectedFactor.history.map((h) => ({
    date: h.date.slice(5),
    value: h.value,
    displayValue: ((h.value - 1) * 100).toFixed(2),
  }));

  const isPositive = selectedFactor.currentValue >= 1;

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-accent-purple" />
            Factor Trend Analysis
          </h2>

          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary hover:border-border-light transition-colors"
            >
              <span className={`w-2 h-2 rounded-full`} style={{ backgroundColor: getTypeColor(selectedFactor.type) }} />
              {selectedFactor.name}
              <ChevronDown className="w-4 h-4 text-text-muted" />
            </button>

            {showDropdown && (
              <div className="absolute top-full right-0 mt-1 w-48 bg-bg-card border border-border rounded-lg shadow-lg z-10">
                {factors.map((factor) => (
                  <button
                    key={factor.id}
                    onClick={() => {
                      setSelectedFactor(factor);
                      setShowDropdown(false);
                    }}
                    className={`w-full px-3 py-2 text-sm text-left hover:bg-bg-hover transition-colors flex items-center gap-2 ${
                      factor.id === selectedFactor.id ? 'bg-bg-hover' : ''
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full`} style={{ backgroundColor: getTypeColor(factor.type) }} />
                    <span className="text-text-primary">{factor.name}</span>
                    <span className="text-xs text-text-muted capitalize ml-auto">{factor.type}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-center gap-4 mb-4">
          <div>
            <span className="text-xs text-text-muted">Current Value</span>
            <div className={`text-xl font-bold ${isPositive ? 'text-profit' : 'text-loss'}`}>
              {isPositive ? '+' : ''}{((selectedFactor.currentValue - 1) * 100).toFixed(2)}%
            </div>
          </div>
          <div>
            <span className="text-xs text-text-muted">Type</span>
            <div className="text-sm font-medium text-text-primary capitalize">
              {selectedFactor.type}
            </div>
          </div>
          <div>
            <span className="text-xs text-text-muted">Trend</span>
            <div className={`text-sm font-medium capitalize ${
              selectedFactor.trend === 'up' ? 'text-profit' :
              selectedFactor.trend === 'down' ? 'text-loss' : 'text-text-muted'
            }`}>
              {selectedFactor.trend}
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
              tickFormatter={(value) => `${((value - 1) * 100).toFixed(0)}%`}
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const point = payload[0].payload;
                  const value = point.value;
                  return (
                    <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                      <p className="text-xs text-text-muted mb-1">{point.date}</p>
                      <p className={`text-sm font-semibold ${value >= 1 ? 'text-profit' : 'text-loss'}`}>
                        {value >= 1 ? '+' : ''}{((value - 1) * 100).toFixed(2)}%
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={1} stroke="#334155" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="value"
              stroke={getTypeColor(selectedFactor.type)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: getTypeColor(selectedFactor.type) }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
