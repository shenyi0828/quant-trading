import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, TrendingUp, TrendingDown, AlertCircle, Activity, Target, Shield } from 'lucide-react';
import { EquityChart } from '../components/EquityChart';
import { HoldingsTable } from '../components/HoldingsTable';
import { TradesTable } from '../components/TradesTable';
import { StatusBadge } from '../components/StatusBadge';
import { MetricCard } from '../components/MetricCard';
import { getStrategyDetail } from '../data/mock';

export function StrategyDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const strategy = id ? getStrategyDetail(id) : null;

  if (!strategy) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="glass-card rounded-xl p-8 text-center">
          <AlertCircle className="w-12 h-12 text-loss mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">Strategy Not Found</h2>
          <p className="text-text-secondary mb-4">The strategy you're looking for doesn't exist.</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-accent-blue/20 text-accent-cyan rounded-lg hover:bg-accent-blue/30 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isPositive = strategy.totalPnL >= 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/')}
          className="p-2 rounded-lg bg-bg-hover text-text-secondary hover:text-text-primary hover:bg-bg-card transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-text-primary">{strategy.name}</h1>
            <StatusBadge status={strategy.status} />
          </div>
          <p className="text-sm text-text-secondary mt-1">{strategy.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total P&L"
          value={Math.abs(strategy.totalPnL)}
          prefix={isPositive ? '+' : '-'}
          icon={isPositive ? <TrendingUp className="w-5 h-5 text-profit" /> : <TrendingDown className="w-5 h-5 text-loss" />}
          color={isPositive ? 'profit' : 'loss'}
        />
        <MetricCard
          title="Win Rate"
          value={strategy.winRate}
          suffix="%"
          icon={<Target className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="Sharpe Ratio"
          value={strategy.sharpeRatio}
          icon={<Activity className="w-5 h-5 text-accent-blue" />}
          color={strategy.sharpeRatio >= 1 ? 'profit' : strategy.sharpeRatio >= 0 ? 'default' : 'loss'}
        />
        <MetricCard
          title="Max Drawdown"
          value={strategy.maxDrawdown}
          suffix="%"
          icon={<Shield className="w-5 h-5 text-loss-light" />}
          color="loss"
        />
      </div>

      <div className="glass-card rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Strategy Info</h2>
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Clock className="w-4 h-4" />
            <span>Runtime: {strategy.runtime}</span>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Strategy ID</p>
            <p className="text-sm font-medium text-text-primary font-mono">{strategy.id}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Total Trades</p>
            <p className="text-sm font-medium text-text-primary">{strategy.totalTrades.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Active Positions</p>
            <p className="text-sm font-medium text-text-primary">{strategy.activePositions}</p>
          </div>
          <div>
            <p className="text-xs text-text-muted uppercase tracking-wider mb-1">Last Updated</p>
            <p className="text-sm font-medium text-text-primary">
              {new Date(strategy.lastUpdated).toLocaleString('zh-CN')}
            </p>
          </div>
        </div>
      </div>

      <EquityChart data={strategy.equityCurve} height={350} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <HoldingsTable holdings={strategy.holdings} />
        <TradesTable trades={strategy.recentTrades} />
      </div>
    </div>
  );
}
