import { useState } from 'react';
import { History, BarChart3 } from 'lucide-react';
import { BacktestConfig } from '../components/BacktestConfig';
import { BacktestResults } from '../components/BacktestResults';
import { PerformanceMetrics } from '../components/PerformanceMetrics';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { getBacktestResult, getAllBacktestResults, type BacktestResult } from '../data/mock';

export function BacktestAnalysis() {
  const [currentResult, setCurrentResult] = useState<BacktestResult | null>(null);
  const [pastResults] = useState<BacktestResult[]>(() => getAllBacktestResults());

  const handleRunBacktest = (config: {
    strategyId: string;
    startDate: string;
    endDate: string;
    initialCapital: number;
    benchmark: string;
  }) => {
    const result = getBacktestResult(config.strategyId.replace('strat-', 'bt-'));
    if (result) {
      setCurrentResult({
        ...result,
        startDate: config.startDate,
        endDate: config.endDate,
        initialCapital: config.initialCapital,
        benchmark: config.benchmark as 'CSI300' | 'CSI500' | 'None',
      });
    }
  };

  const handleSelectPastResult = (result: BacktestResult) => {
    setCurrentResult(result);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <History className="w-6 h-6 text-accent-cyan" />
            Backtest Analysis
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Historical strategy performance simulation
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div>
          <BacktestConfig onRunBacktest={handleRunBacktest} />
        </div>

        <div className="lg:col-span-2 space-y-6">
          {currentResult ? (
            <>
              <BacktestResults result={currentResult} />
              <PerformanceMetrics result={currentResult} />
              <TradeHistoryTable trades={currentResult.trades} />
            </>
          ) : (
            <div className="glass-card rounded-xl p-12 text-center">
              <History className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                Run a Backtest
              </h3>
              <p className="text-sm text-text-secondary">
                Configure parameters and click "Run Backtest" to see results
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-accent-purple" />
            <h2 className="text-lg font-semibold text-text-primary">Recent Backtests</h2>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-bg-secondary/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Strategy
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Period
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Benchmark
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Return
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Sharpe
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Max DD
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pastResults.map((result) => (
                <tr
                  key={result.id}
                  className="hover:bg-bg-hover transition-colors cursor-pointer"
                  onClick={() => handleSelectPastResult(result)}
                >
                  <td className="px-4 py-3 text-sm text-text-primary">{result.strategyName}</td>
                  <td className="px-4 py-3 text-xs text-text-muted">
                    {result.startDate} - {result.endDate}
                  </td>
                  <td className="px-4 py-3 text-xs text-text-muted">{result.benchmark}</td>
                  <td className={`px-4 py-3 text-right text-sm font-medium ${
                    result.annualReturn >= 0 ? 'text-profit' : 'text-loss'
                  }`}>
                    {result.annualReturn >= 0 ? '+' : ''}{result.annualReturn.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-text-primary">
                    {result.sharpeRatio.toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-loss">
                    -{result.maxDrawdown.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button className="text-xs text-accent-cyan hover:text-accent-cyan-light transition-colors">
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
