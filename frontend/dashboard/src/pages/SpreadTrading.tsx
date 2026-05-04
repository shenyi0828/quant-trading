import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ComposedChart, Bar } from 'recharts';
import { Activity, TrendingUp, TrendingDown, ArrowRightLeft, Target, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { mockSpreadPairs, getSpreadHistory, getSpreadSignals } from '../data/mock';
import type { SpreadPair, SpreadPoint, SpreadSignal } from '../types';

function SpreadChart({ pairId, pairName }: { pairId: string; pairName: string }) {
  const data = getSpreadHistory(pairId);
  const latest = data[data.length - 1];
  const isPositive = latest?.zScore >= 0;

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">{pairName}</h3>
          <p className={`text-xs mt-1 ${isPositive ? 'text-profit' : 'text-loss'}`}>
            Z-Score: {latest?.zScore} | 价差: {latest?.spread}
          </p>
        </div>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isPositive ? 'bg-profit/10' : 'bg-loss/10'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4 text-profit" /> : <TrendingDown className="w-4 h-4 text-loss" />}
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="date" hide />
          <YAxis hide domain={['auto', 'auto']} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as SpreadPoint;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                    <p className="text-xs text-text-muted">{point.date}</p>
                    <p className="text-sm font-semibold text-text-primary">价差: {point.spread}</p>
                    <p className={`text-xs mt-1 ${point.zScore >= 0 ? 'text-profit' : 'text-loss'}`}>
                      Z-Score: {point.zScore}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine y={0} stroke="#334155" strokeDasharray="3 3" />
          <ReferenceLine y={2} stroke="#22c55e" strokeDasharray="3 3" opacity={0.5} />
          <ReferenceLine y={-2} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
          <Line
            type="monotone"
            dataKey="zScore"
            stroke={isPositive ? '#22c55e' : '#ef4444'}
            strokeWidth={2}
            dot={false}
          />
          <Bar dataKey="spread" fill={isPositive ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)'} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function SignalBadge({ signal }: { signal: SpreadSignal }) {
  const getIcon = () => {
    switch (signal.signal) {
      case 'long_spread': return <TrendingUp className="w-4 h-4" />;
      case 'short_spread': return <TrendingDown className="w-4 h-4" />;
      case 'close': return <CheckCircle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getLabel = () => {
    switch (signal.signal) {
      case 'long_spread': return '做多价差';
      case 'short_spread': return '做空价差';
      case 'close': return '平仓';
      default: return '持有';
    }
  };

  const getColor = () => {
    switch (signal.signal) {
      case 'long_spread': return 'text-profit bg-profit/20 border-profit/30';
      case 'short_spread': return 'text-loss bg-loss/20 border-loss/30';
      case 'close': return 'text-accent-cyan bg-accent-blue/20 border-accent-blue/30';
      default: return 'text-text-secondary bg-bg-hover';
    }
  };

  return (
    <div className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${getColor()}`}>
      {getIcon()}
      {getLabel()} ({(signal.strength * 100).toFixed(0)}%)
    </div>
  );
}

export function SpreadTrading() {
  const pairs = mockSpreadPairs;
  const signals = getSpreadSignals();

  const stats = {
    activePairs: pairs.length,
    longSignals: signals.filter((s: SpreadSignal) => s.signal === 'long_spread').length,
    shortSignals: signals.filter((s: SpreadSignal) => s.signal === 'short_spread').length,
    avgCorrelation: pairs.reduce((sum: number, p: SpreadPair) => sum + p.correlation, 0) / pairs.length
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">价差交易</h1>
          <p className="text-sm text-text-secondary mt-1">
            统计套利策略：配对交易价差监控与信号生成
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="活跃价差对"
          value={stats.activePairs}
          icon={<ArrowRightLeft className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="做多信号"
          value={stats.longSignals}
          color="profit"
          icon={<TrendingUp className="w-5 h-5 text-profit" />}
        />
        <MetricCard
          title="做空信号"
          value={stats.shortSignals}
          color="loss"
          icon={<TrendingDown className="w-5 h-5 text-loss" />}
        />
        <MetricCard
          title="平均相关性"
          value={stats.avgCorrelation.toFixed(2)}
          icon={<Activity className="w-5 h-5 text-accent-purple" />}
        />
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">价差对列表</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-bg-secondary/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">价差对</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">标的A</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">标的B</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">当前价差</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">Z-Score</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase">状态</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">相关性</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">半衰期</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {pairs.map((pair: SpreadPair) => (
                <tr key={pair.id} className="hover:bg-bg-hover transition-colors">
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-text-primary">{pair.name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm text-text-primary">{pair.nameA}</span>
                      <span className="text-xs text-text-muted ml-2">({pair.symbolA})</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm text-text-primary">{pair.nameB}</span>
                      <span className="text-xs text-text-muted ml-2">({pair.symbolB})</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div>
                      <span className="text-sm text-text-primary">{pair.currentSpread.toFixed(2)}</span>
                      <span className={`text-xs ml-2 ${pair.spreadChange >= 0 ? 'text-profit' : 'text-loss'}`}>
                        {pair.spreadChange >= 0 ? '+' : ''}{pair.spreadChangePercent.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`text-sm font-medium ${pair.zScore >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {pair.zScore.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs px-2 py-1 rounded ${
                      pair.status === 'oversold' ? 'bg-loss/20 text-loss' :
                      pair.status === 'overbought' ? 'bg-profit/20 text-profit' :
                      pair.status === 'extreme' ? 'bg-warning/20 text-warning' :
                      'bg-text-secondary/20 text-text-secondary'
                    }`}>
                      {pair.status === 'oversold' ? '超卖' :
                       pair.status === 'overbought' ? '超买' :
                       pair.status === 'extreme' ? '极端' : '正常'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-text-primary">{(pair.correlation * 100).toFixed(1)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-text-primary">{pair.halfLife}天</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">实时价差走势</h2>
          <div className="grid grid-cols-1 gap-4">
            {pairs.map((pair: SpreadPair) => (
              <SpreadChart key={pair.id} pairId={pair.id} pairName={pair.name} />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">策略信号</h2>
          <div className="glass-card rounded-xl p-5 space-y-4">
            {signals.map((signal: SpreadSignal) => (
              <div key={signal.pairId} className="border-b border-border last:border-0 pb-4 last:pb-0">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="text-sm font-medium text-text-primary">{signal.pairName}</h4>
                    <p className="text-xs text-text-muted mt-1">{signal.reason}</p>
                  </div>
                  <SignalBadge signal={signal} />
                </div>
                <div className="flex items-center gap-4 text-xs text-text-secondary">
                  <span>信号强度: {(signal.strength * 100).toFixed(0)}%</span>
                  <span>{signal.timestamp}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-text-primary mb-4">交易规则说明</h3>
            <div className="space-y-3 text-sm text-text-secondary">
              <div className="flex items-start gap-3">
                <Zap className="w-4 h-4 text-accent-cyan mt-0.5" />
                <span><strong className="text-text-primary">入场条件：</strong>Z-Score &gt; +2 做空价差，Z-Score &lt; -2 做多价差</span>
              </div>
              <div className="flex items-start gap-3">
                <Target className="w-4 h-4 text-accent-blue mt-0.5" />
                <span><strong className="text-text-primary">平仓条件：</strong>Z-Score回归至 [-0.5, 0.5] 区间时平仓</span>
              </div>
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-warning mt-0.5" />
                <span><strong className="text-text-primary">止损设置：</strong>价差继续偏离原始入场点超过1个标准差时止损</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
