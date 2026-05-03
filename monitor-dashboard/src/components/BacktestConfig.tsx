import { useState } from 'react';
import { Settings, Calendar, DollarSign, BarChart3, Play, ChevronDown } from 'lucide-react';
import { mockStrategies } from '../data/mock';

interface BacktestConfigProps {
  onRunBacktest: (config: {
    strategyId: string;
    startDate: string;
    endDate: string;
    initialCapital: number;
    benchmark: string;
  }) => void;
}

export function BacktestConfig({ onRunBacktest }: BacktestConfigProps) {
  const [strategyId, setStrategyId] = useState(mockStrategies[0]?.id || '');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-06-30');
  const [initialCapital, setInitialCapital] = useState(10000000);
  const [benchmark, setBenchmark] = useState('CSI300');
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);
  const [showBenchmarkDropdown, setShowBenchmarkDropdown] = useState(false);

  const selectedStrategy = mockStrategies.find((s) => s.id === strategyId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunBacktest({
      strategyId,
      startDate,
      endDate,
      initialCapital,
      benchmark,
    });
  };

  const benchmarks = ['CSI300', 'CSI500', 'None'];

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Settings className="w-5 h-5 text-accent-cyan" />
          Backtest Configuration
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        <div>
          <label className="block text-sm text-text-secondary mb-2 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Strategy
          </label>
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowStrategyDropdown(!showStrategyDropdown)}
              className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-left text-sm text-text-primary hover:border-border-light transition-colors flex items-center justify-between"
            >
              <span>{selectedStrategy?.name || 'Select Strategy'}</span>
              <ChevronDown className="w-4 h-4 text-text-muted" />
            </button>

            {showStrategyDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-card border border-border rounded-lg shadow-lg z-10">
                {mockStrategies.map((strategy) => (
                  <button
                    key={strategy.id}
                    type="button"
                    onClick={() => {
                      setStrategyId(strategy.id);
                      setShowStrategyDropdown(false);
                    }}
                    className={`w-full px-3 py-2 text-sm text-left hover:bg-bg-hover transition-colors ${
                      strategy.id === strategyId ? 'bg-bg-hover' : ''
                    }`}
                  >
                    <span className="text-text-primary">{strategy.name}</span>
                    <span className="text-xs text-text-muted ml-2">({strategy.status})</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-secondary mb-2 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-cyan transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-2 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-cyan transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-2 flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Initial Capital (CNY)
          </label>
          <input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            min={100000}
            step={100000}
            className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:border-accent-cyan transition-colors"
          />
          <div className="mt-1 text-xs text-text-muted">
            ¥{(initialCapital / 10000).toFixed(0)}万
          </div>
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-2 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Benchmark
          </label>
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowBenchmarkDropdown(!showBenchmarkDropdown)}
              className="w-full px-3 py-2.5 bg-bg-secondary border border-border rounded-lg text-left text-sm text-text-primary hover:border-border-light transition-colors flex items-center justify-between"
            >
              <span>{benchmark}</span>
              <ChevronDown className="w-4 h-4 text-text-muted" />
            </button>

            {showBenchmarkDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-card border border-border rounded-lg shadow-lg z-10">
                {benchmarks.map((b) => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => {
                      setBenchmark(b);
                      setShowBenchmarkDropdown(false);
                    }}
                    className={`w-full px-3 py-2 text-sm text-left hover:bg-bg-hover transition-colors ${
                      b === benchmark ? 'bg-bg-hover' : ''
                    }`}
                  >
                    <span className="text-text-primary">{b}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          className="w-full py-3 bg-accent-cyan hover:bg-accent-cyan-light text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" />
          Run Backtest
        </button>
      </form>
    </div>
  );
}
