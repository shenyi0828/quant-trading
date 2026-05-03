import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Pause, TrendingUp, TrendingDown, Target, Activity, Shield, Grid, List } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import { mockStrategies, getStrategySignals } from '../data/mock';
import type { Strategy, StrategySignal } from '../types';

function StrategyCard({ strategy, onToggle }: { strategy: Strategy; onToggle: (id: string) => void }) {
  const navigate = useNavigate();
  const isPositive = strategy.totalPnL >= 0;
  const signals = getStrategySignals(strategy.id).slice(0, 5);

  return (
    <div className="glass-card rounded-xl p-5 hover:border-accent-blue/30 transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 
              className="text-lg font-semibold text-text-primary cursor-pointer hover:text-accent-cyan transition-colors"
              onClick={() => navigate(`/strategy/${strategy.id}`)}
            >
              {strategy.name}
            </h3>
            <StatusBadge status={strategy.status} />
          </div>
          <p className="text-sm text-text-secondary line-clamp-2">{strategy.description}</p>
        </div>
        <button
          onClick={() => onToggle(strategy.id)}
          className={`p-2 rounded-lg transition-colors ${
            strategy.status === 'running'
              ? 'bg-profit/10 text-profit hover:bg-profit/20'
              : strategy.status === 'error'
              ? 'bg-loss/10 text-loss hover:bg-loss/20'
              : 'bg-text-muted/10 text-text-muted hover:bg-text-muted/20'
          }`}
        >
          {strategy.status === 'running' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <p className="text-xs text-text-muted">总盈亏</p>
          <p className={`text-sm font-semibold ${isPositive ? 'text-profit' : 'text-loss'}`}>
            {isPositive ? '+' : ''}¥{strategy.totalPnL.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-muted">胜率</p>
          <p className="text-sm font-semibold text-text-primary">{strategy.winRate.toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">夏普比率</p>
          <p className={`text-sm font-semibold ${strategy.sharpeRatio >= 1 ? 'text-profit' : 'text-text-primary'}`}>
            {strategy.sharpeRatio.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="border-t border-border pt-3">
        <p className="text-xs text-text-muted mb-2">最新信号</p>
        <div className="flex gap-2">
          {signals.slice(0, 4).map((signal: StrategySignal, i: number) => (
            <SignalBadge key={i} signal={signal} />
          ))}
        </div>
      </div>
    </div>
  );
}

function SignalBadge({ signal }: { signal: StrategySignal }) {
  const colorClass = signal.signal === 'buy' ? 'bg-profit/20 text-profit' : 
                     signal.signal === 'sell' ? 'bg-loss/20 text-loss' : 
                     'bg-text-muted/20 text-text-muted';
  
  return (
    <div className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
      {signal.symbol}
    </div>
  );
}

function StrategyListView({ strategies, onToggle }: { strategies: Strategy[]; onToggle: (id: string) => void }) {
  const navigate = useNavigate();

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-bg-secondary/50">
            <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase">策略</th>
            <th className="px-5 py-3 text-left text-xs font-medium text-text-secondary uppercase">状态</th>
            <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase">总盈亏</th>
            <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase">胜率</th>
            <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase">夏普</th>
            <th className="px-5 py-3 text-right text-xs font-medium text-text-secondary uppercase">回撤</th>
            <th className="px-5 py-3 text-center text-xs font-medium text-text-secondary uppercase">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {strategies.map((strategy: Strategy) => {
            const isPositive = strategy.totalPnL >= 0;
            return (
              <tr key={strategy.id} className="hover:bg-bg-hover transition-colors">
                <td className="px-5 py-4">
                  <div 
                    className="cursor-pointer"
                    onClick={() => navigate(`/strategy/${strategy.id}`)}
                  >
                    <p className="text-sm font-medium text-text-primary hover:text-accent-cyan">{strategy.name}</p>
                    <p className="text-xs text-text-muted">{strategy.description.slice(0, 30)}...</p>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={strategy.status} />
                </td>
                <td className="px-5 py-4 text-right">
                  <span className={`text-sm font-semibold ${isPositive ? 'text-profit' : 'text-loss'}`}>
                    {isPositive ? '+' : ''}¥{strategy.totalPnL.toLocaleString()}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <span className="text-sm text-text-primary">{strategy.winRate.toFixed(1)}%</span>
                </td>
                <td className="px-5 py-4 text-right">
                  <span className={`text-sm font-semibold ${strategy.sharpeRatio >= 1 ? 'text-profit' : 'text-text-primary'}`}>
                    {strategy.sharpeRatio.toFixed(2)}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <span className="text-sm text-loss">{strategy.maxDrawdown}%</span>
                </td>
                <td className="px-5 py-4 text-center">
                  <button
                    onClick={() => onToggle(strategy.id)}
                    className={`p-2 rounded-lg transition-colors ${
                      strategy.status === 'running'
                        ? 'bg-profit/10 text-profit hover:bg-profit/20'
                        : 'bg-text-muted/10 text-text-muted hover:bg-text-muted/20'
                    }`}
                  >
                    {strategy.status === 'running' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function Strategies() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [strategies, setStrategies] = useState<Strategy[]>(mockStrategies);
  const [filter, setFilter] = useState<'all' | 'running' | 'stopped' | 'error'>('all');

  const handleToggle = (id: string) => {
    setStrategies(prev => prev.map((s: Strategy) => {
      if (s.id === id) {
        return {
          ...s,
          status: s.status === 'running' ? 'stopped' : 'running' as const,
        };
      }
      return s;
    }));
  };

  const filteredStrategies = filter === 'all' 
    ? strategies 
    : strategies.filter((s: Strategy) => s.status === filter);

  const runningCount = strategies.filter((s: Strategy) => s.status === 'running').length;
  const totalPnL = strategies.reduce((sum: number, s: Strategy) => sum + s.totalPnL, 0);
  const avgWinRate = strategies.reduce((sum: number, s: Strategy) => sum + s.winRate, 0) / strategies.length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">策略管理</h1>
          <p className="text-sm text-text-secondary mt-1">
            策略监控、配置与信号查看
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-accent-blue/20 text-accent-cyan' : 'text-text-secondary hover:text-text-primary'}`}
          >
            <Grid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-accent-blue/20 text-accent-cyan' : 'text-text-secondary hover:text-text-primary'}`}
          >
            <List className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="运行中策略"
          value={runningCount}
          suffix={`/ ${strategies.length}`}
          icon={<Activity className="w-5 h-5 text-profit" />}
        />
        <MetricCard
          title="总盈亏"
          value={Math.abs(totalPnL)}
          prefix={totalPnL >= 0 ? '+' : '-'}
          icon={totalPnL >= 0 ? <TrendingUp className="w-5 h-5 text-profit" /> : <TrendingDown className="w-5 h-5 text-loss" />}
          color={totalPnL >= 0 ? 'profit' : 'loss'}
        />
        <MetricCard
          title="平均胜率"
          value={avgWinRate.toFixed(1)}
          suffix="%"
          icon={<Target className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="最大回撤"
          value={Math.max(...strategies.map((s: Strategy) => s.maxDrawdown))}
          suffix="%"
          icon={<Shield className="w-5 h-5 text-loss" />}
          color="loss"
        />
      </div>

      <div className="flex items-center gap-2">
        {(['all', 'running', 'stopped', 'error'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-accent-blue/20 text-accent-cyan border border-accent-blue/30'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
            }`}
          >
            {f === 'all' ? '全部' : f === 'running' ? '运行中' : f === 'stopped' ? '已停止' : '错误'}
          </button>
        ))}
      </div>

      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredStrategies.map((strategy: Strategy) => (
            <StrategyCard 
              key={strategy.id} 
              strategy={strategy} 
              onToggle={handleToggle}
            />
          ))}
        </div>
      ) : (
        <StrategyListView 
          strategies={filteredStrategies} 
          onToggle={handleToggle}
        />
      )}
    </div>
  );
}
