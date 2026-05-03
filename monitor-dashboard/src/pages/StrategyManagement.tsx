import { useState } from 'react';
import { Settings, Activity } from 'lucide-react';
import { StrategyCard } from '../components/StrategyCard';
import { StrategyConfigPanel } from '../components/StrategyConfigPanel';
import { SignalChart } from '../components/SignalChart';
import { HoldingsTable } from '../components/HoldingsTable';
import { getStrategyConfigs, type StrategyConfig } from '../data/mock';

export function StrategyManagement() {
  const [strategies, setStrategies] = useState<StrategyConfig[]>(getStrategyConfigs);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyConfig | null>(null);

  const handleToggle = (id: string, enabled: boolean) => {
    setStrategies((prev) =>
      prev.map((s) => (s.id === id ? { ...s, enabled } : s))
    );
    if (selectedStrategy?.id === id) {
      setSelectedStrategy((prev) => (prev ? { ...prev, enabled } : null));
    }
  };

  const handleUpdate = (updatedStrategy: StrategyConfig) => {
    setStrategies((prev) =>
      prev.map((s) => (s.id === updatedStrategy.id ? updatedStrategy : s))
    );
    if (selectedStrategy?.id === updatedStrategy.id) {
      setSelectedStrategy(updatedStrategy);
    }
  };

  const activeCount = strategies.filter((s) => s.enabled).length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Settings className="w-6 h-6 text-accent-cyan" />
            Strategy Management
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Configure and monitor trading strategies
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-2xl font-bold text-text-primary">{activeCount}</div>
            <div className="text-xs text-text-muted">Active Strategies</div>
          </div>
          <div className="h-10 w-px bg-border" />
          <div className="text-right">
            <div className="text-2xl font-bold text-text-primary">{strategies.length}</div>
            <div className="text-xs text-text-muted">Total</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map((strategy) => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            onSelect={setSelectedStrategy}
            isSelected={selectedStrategy?.id === strategy.id}
            onToggle={handleToggle}
          />
        ))}
      </div>

      {selectedStrategy && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <SignalChart signals={selectedStrategy.signals} />
            {selectedStrategy.holdings.length > 0 && (
              <HoldingsTable holdings={selectedStrategy.holdings.map((h) => ({
                symbol: h.symbol,
                name: h.name,
                quantity: h.quantity,
                costPrice: h.avgPrice,
                currentPrice: h.currentPrice,
                marketValue: h.marketValue,
                unrealizedPnL: h.unrealizedPnL,
                unrealizedPnLPercent: (h.unrealizedPnL / (h.avgPrice * h.quantity)) * 100,
              }))} />
            )}
          </div>
          <div>
            <StrategyConfigPanel
              strategy={selectedStrategy}
              onUpdate={handleUpdate}
            />
          </div>
        </div>
      )}

      {!selectedStrategy && (
        <div className="glass-card rounded-xl p-12 text-center">
          <Activity className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Select a Strategy
          </h3>
          <p className="text-sm text-text-secondary">
            Click on a strategy card to view details and configure parameters
          </p>
        </div>
      )}
    </div>
  );
}
