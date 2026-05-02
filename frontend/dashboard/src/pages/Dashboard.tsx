import { Activity, BarChart3, Package, TrendingUp, TrendingDown } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { StrategyTable } from '../components/StrategyTable';
import { getAllStrategies, getDashboardMetrics } from '../data/mock';

export function Dashboard() {
  const strategies = getAllStrategies();
  const metrics = getDashboardMetrics();

  const totalPnLPositive = metrics.totalPnL >= 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="text-sm text-text-secondary mt-1">
            System overview and strategy performance
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <div className="w-2 h-2 rounded-full bg-profit status-running" />
          <span>Live</span>
          <span className="text-text-secondary">|</span>
          <span>{new Date().toLocaleString('zh-CN')}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total P&L"
          value={Math.abs(metrics.totalPnL)}
          prefix={totalPnLPositive ? '+' : '-'}
          change={metrics.dailyReturn}
          changeLabel="today"
          icon={totalPnLPositive ? <TrendingUp className="w-5 h-5 text-profit" /> : <TrendingDown className="w-5 h-5 text-loss" />}
          color={totalPnLPositive ? 'profit' : 'loss'}
        />
        <MetricCard
          title="Active Strategies"
          value={metrics.activeStrategies}
          suffix={`/ ${strategies.length}`}
          icon={<Activity className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="Today's Trades"
          value={metrics.todayTrades}
          change={12.5}
          changeLabel="vs yesterday"
          icon={<BarChart3 className="w-5 h-5 text-accent-blue" />}
        />
        <MetricCard
          title="Open Positions"
          value={metrics.openPositions}
          icon={<Package className="w-5 h-5 text-accent-purple" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <StrategyTable strategies={strategies} />
        </div>

        <div className="space-y-4">
          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Portfolio Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-text-secondary">Total Capital</span>
                <span className="text-sm font-medium text-text-primary">
                  ¥{(metrics.totalCapital / 1000000).toFixed(2)}M
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-text-secondary">Total Return</span>
                <span className={`text-sm font-medium ${totalPnLPositive ? 'text-profit' : 'text-loss'}`}>
                  {totalPnLPositive ? '+' : ''}{(metrics.totalPnL / metrics.totalCapital * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-text-secondary">Active Strategies</span>
                <span className="text-sm font-medium text-text-primary">
                  {metrics.activeStrategies} running
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm text-text-secondary">Winning Strategies</span>
                <span className="text-sm font-medium text-profit">
                  {strategies.filter(s => s.totalPnL > 0).length} / {strategies.length}
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-text-secondary">Avg Win Rate</span>
                <span className="text-sm font-medium text-text-primary">
                  {(strategies.reduce((sum, s) => sum + s.winRate, 0) / strategies.length).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">Strategy Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-profit" />
                  <span className="text-sm text-text-secondary">Running</span>
                </div>
                <span className="text-sm font-medium text-profit">
                  {strategies.filter(s => s.status === 'running').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-text-muted" />
                  <span className="text-sm text-text-secondary">Stopped</span>
                </div>
                <span className="text-sm font-medium text-text-muted">
                  {strategies.filter(s => s.status === 'stopped').length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-loss" />
                  <span className="text-sm text-text-secondary">Error</span>
                </div>
                <span className="text-sm font-medium text-loss">
                  {strategies.filter(s => s.status === 'error').length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
