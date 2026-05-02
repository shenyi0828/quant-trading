import { Activity, TrendingUp, BarChart3 } from 'lucide-react';
import { FactorTable } from '../components/FactorTable';
import { FactorHeatmap } from '../components/FactorHeatmap';
import { FactorTrendChart } from '../components/FactorTrendChart';
import { mockFactors, generateFactorHeatmap } from '../data/mock';

export function FactorAnalysis() {
  const heatmapData = generateFactorHeatmap();

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Activity className="w-6 h-6 text-accent-cyan" />
            Factor Analysis
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Multi-factor model analysis and risk exposure
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <div className="w-2 h-2 rounded-full bg-profit" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <FactorTrendChart factors={mockFactors} />
        </div>
        <div className="space-y-4">
          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Factor Types</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent-cyan" />
                  <span className="text-sm text-text-secondary">Momentum</span>
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {mockFactors.filter((f) => f.type === 'momentum').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent-blue" />
                  <span className="text-sm text-text-secondary">Trend</span>
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {mockFactors.filter((f) => f.type === 'trend').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-warning" />
                  <span className="text-sm text-text-secondary">Volatility</span>
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {mockFactors.filter((f) => f.type === 'volatility').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent-purple" />
                  <span className="text-sm text-text-secondary">Value</span>
                </div>
                <span className="text-sm font-medium text-text-primary">
                  {mockFactors.filter((f) => f.type === 'value').length}
                </span>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Factor Trends</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-profit" />
                  <span className="text-sm text-text-secondary">Bullish</span>
                </div>
                <span className="text-sm font-medium text-profit">
                  {mockFactors.filter((f) => f.trend === 'up').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-text-muted" />
                  <span className="text-sm text-text-secondary">Neutral</span>
                </div>
                <span className="text-sm font-medium text-text-muted">
                  {mockFactors.filter((f) => f.trend === 'neutral').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-loss rotate-180" />
                  <span className="text-sm text-text-secondary">Bearish</span>
                </div>
                <span className="text-sm font-medium text-loss">
                  {mockFactors.filter((f) => f.trend === 'down').length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <FactorTable factors={mockFactors} />
        <FactorHeatmap data={heatmapData} />
      </div>
    </div>
  );
}
