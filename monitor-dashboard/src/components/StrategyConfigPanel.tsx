import { useState } from 'react';
import { Settings, Save, RotateCcw } from 'lucide-react';
import type { StrategyConfig } from '../data/mock';

interface StrategyConfigPanelProps {
  strategy: StrategyConfig;
  onUpdate: (strategy: StrategyConfig) => void;
}

export function StrategyConfigPanel({ strategy, onUpdate }: StrategyConfigPanelProps) {
  const [parameters, setParameters] = useState(strategy.parameters);
  const [hasChanges, setHasChanges] = useState(false);

  const handleParamChange = (key: string, value: number) => {
    setParameters((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleReset = () => {
    setParameters(strategy.parameters);
    setHasChanges(false);
  };

  const handleSave = () => {
    onUpdate({ ...strategy, parameters });
    setHasChanges(false);
  };

  const paramLabels: Record<string, string> = {
    lookbackPeriod: 'Lookback Period',
    positionSize: 'Position Size',
    stopLoss: 'Stop Loss',
    takeProfit: 'Take Profit',
    maxPositions: 'Max Positions',
    zScoreThreshold: 'Z-Score Threshold',
    volatilityWindow: 'Volatility Window',
    breakoutThreshold: 'Breakout Threshold',
    correlationWindow: 'Correlation Window',
    entryThreshold: 'Entry Threshold',
    exitThreshold: 'Exit Threshold',
    maxPairs: 'Max Pairs',
    ivWindow: 'IV Window',
    rvWindow: 'RV Window',
    spreadThreshold: 'Spread Threshold',
    factorLookback: 'Factor Lookback',
    rebalanceFreq: 'Rebalance Freq',
    riskTarget: 'Risk Target',
  };

  const paramRanges: Record<string, { min: number; max: number; step: number }> = {
    lookbackPeriod: { min: 5, max: 100, step: 1 },
    positionSize: { min: 0.01, max: 0.5, step: 0.01 },
    stopLoss: { min: 0.01, max: 0.2, step: 0.01 },
    takeProfit: { min: 0.05, max: 0.5, step: 0.01 },
    maxPositions: { min: 1, max: 50, step: 1 },
    zScoreThreshold: { min: 1, max: 5, step: 0.1 },
    volatilityWindow: { min: 5, max: 50, step: 1 },
    breakoutThreshold: { min: 0.5, max: 5, step: 0.1 },
    correlationWindow: { min: 10, max: 120, step: 1 },
    entryThreshold: { min: 1, max: 4, step: 0.1 },
    exitThreshold: { min: 0, max: 2, step: 0.1 },
    maxPairs: { min: 1, max: 20, step: 1 },
    ivWindow: { min: 5, max: 60, step: 1 },
    rvWindow: { min: 5, max: 60, step: 1 },
    spreadThreshold: { min: 0.05, max: 0.5, step: 0.01 },
    factorLookback: { min: 20, max: 252, step: 1 },
    rebalanceFreq: { min: 1, max: 30, step: 1 },
    riskTarget: { min: 0.05, max: 0.3, step: 0.01 },
  };

  const formatValue = (key: string, value: number) => {
    if (['positionSize', 'stopLoss', 'takeProfit', 'spreadThreshold', 'riskTarget'].includes(key)) {
      return `${(value * 100).toFixed(0)}%`;
    }
    if (['zScoreThreshold', 'breakoutThreshold', 'entryThreshold', 'exitThreshold'].includes(key)) {
      return value.toFixed(1);
    }
    return value.toString();
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Settings className="w-5 h-5 text-accent-cyan" />
            Parameter Configuration
          </h2>
          {hasChanges && (
            <span className="text-xs text-warning">Unsaved changes</span>
          )}
        </div>
      </div>

      <div className="p-5 space-y-4">
        {Object.entries(parameters).map(([key, value]) => {
          const range = paramRanges[key] || { min: 0, max: 100, step: 1 };
          return (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm text-text-secondary">
                  {paramLabels[key] || key}
                </label>
                <span className="text-sm font-medium text-text-primary">
                  {formatValue(key, value)}
                </span>
              </div>
              <input
                type="range"
                min={range.min}
                max={range.max}
                step={range.step}
                value={value}
                onChange={(e) => handleParamChange(key, Number(e.target.value))}
                className="w-full h-2 bg-bg-secondary rounded-lg appearance-none cursor-pointer accent-accent-cyan"
              />
              <div className="flex justify-between text-xs text-text-muted">
                <span>{formatValue(key, range.min)}</span>
                <span>{formatValue(key, range.max)}</span>
              </div>
            </div>
          );
        })}

        {hasChanges && (
          <div className="flex gap-3 pt-4 border-t border-border">
            <button
              onClick={handleReset}
              className="flex-1 py-2 px-4 bg-bg-secondary hover:bg-bg-hover text-text-secondary rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button
              onClick={handleSave}
              className="flex-1 py-2 px-4 bg-accent-cyan hover:bg-accent-cyan-light text-white rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
