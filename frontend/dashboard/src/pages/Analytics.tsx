import { useState } from 'react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { TrendingDown, Activity, PieChart, Target, AlertCircle, Percent, Zap } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { getDrawdownAnalysis, getRollingMetrics, getMonteCarloResult } from '../data/mock';
import type { DrawdownPoint, RollingMetric, MonteCarloResult } from '../types';

function DrawdownChart({ data }: { data: DrawdownPoint[] }) {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">回撤分析</h3>
          <p className="text-xs text-text-secondary mt-1">历史权益回撤与峰值对比</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-accent-cyan/30" />
            <span className="text-text-secondary">权益曲线</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-loss/30" />
            <span className="text-text-secondary">回撤</span>
          </div>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="equityGradient2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} minTickGap={30} />
          <YAxis yAxisId="left" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `¥${(value / 10000).toFixed(0)}万`} domain={['auto', 'auto']} />
          <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} domain={[0, 'auto']} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as DrawdownPoint;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                    <p className="text-xs text-text-muted mb-1">{point.date}</p>
                    <p className="text-sm font-semibold text-text-primary">权益: ¥{(point.equity / 10000).toFixed(2)}万</p>
                    <p className="text-xs text-loss mt-1">回撤: {point.drawdownPercent.toFixed(2)}% (¥{(point.drawdown / 10000).toFixed(1)}万)</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Area yAxisId="left" type="monotone" dataKey="equity" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#equityGradient2)" />
          <Area yAxisId="right" type="monotone" dataKey="drawdownPercent" stroke="#ef4444" strokeWidth={1} fillOpacity={1} fill="url(#drawdownGradient)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function RollingMetricsChart({ data, metric }: { data: RollingMetric[]; metric: 'sharpeRatio' | 'volatility' | 'maxDrawdown' | 'winRate' }) {
  const metricLabels: Record<string, string> = {
    sharpeRatio: '夏普比率',
    volatility: '波动率',
    maxDrawdown: '最大回撤',
    winRate: '胜率'
  };

  const colors: Record<string, string> = {
    sharpeRatio: '#22c55e',
    volatility: '#f59e0b',
    maxDrawdown: '#ef4444',
    winRate: '#3b82f6'
  };

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis dataKey="date" hide />
        <YAxis hide domain={['auto', 'auto']} />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const point = payload[0].payload as RollingMetric;
              return (
                <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                  <p className="text-xs text-text-muted">{point.date}</p>
                  <p className="text-sm font-semibold" style={{ color: colors[metric] }}>
                    {metricLabels[metric]}: {point[metric]}
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        <Line type="monotone" dataKey={metric} stroke={colors[metric]} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function MonteCarloVisualization({ result }: { result: MonteCarloResult }) {
  const simData = [
    { label: '均值', value: result.finalEquity.mean, color: '#3b82f6' },
    { label: '最坏', value: result.finalEquity.min, color: '#ef4444' },
    { label: '最好', value: result.finalEquity.max, color: '#22c55e' },
    { label: '95%下限', value: result.finalEquity.p5, color: '#f59e0b' },
    { label: '95%上限', value: result.finalEquity.p95, color: '#06b6d4' },
  ];

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">蒙特卡洛模拟结果</h3>
          <p className="text-xs text-text-secondary mt-1">{result.simulationCount.toLocaleString()}次模拟后的资金分布</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-bg-secondary/50 rounded-lg p-4 text-center">
          <p className="text-xs text-text-secondary mb-1">盈利概率</p>
          <p className="text-2xl font-bold text-profit">{(result.probabilityOfProfit * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-bg-secondary/50 rounded-lg p-4 text-center">
          <p className="text-xs text-text-secondary mb-1">亏损风险</p>
          <p className="text-2xl font-bold text-loss">{(result.probabilityOfRuin * 100).toFixed(1)}%</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={simData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={true} vertical={false} />
          <XAxis type="number" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(value) => `¥${(value / 10000).toFixed(0)}万`} />
          <YAxis type="category" dataKey="label" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} width={60} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                    <p className="text-xs text-text-muted">{point.label}</p>
                    <p className="text-sm font-semibold text-text-primary">¥{(point.value / 10000).toFixed(2)}万</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {simData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 space-y-2">
        <h4 className="text-xs font-medium text-text-secondary">置信区间</h4>
        {result.confidenceIntervals.map((ci, idx) => (
          <div key={idx} className="flex items-center justify-between text-xs">
            <span className="text-text-secondary">{ci.level}% CI:</span>
            <span className="text-text-primary">¥{(ci.min / 10000).toFixed(0)}万 - ¥{(ci.max / 10000).toFixed(0)}万</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Analytics() {
  const [windowSize, setWindowSize] = useState<number>(30);
  
  const drawdownData = getDrawdownAnalysis();
  const rollingData = getRollingMetrics(windowSize);
  const monteCarloResult = getMonteCarloResult();

  const maxDrawdown = Math.max(...drawdownData.map(d => d.drawdownPercent));
  const avgSharpe = rollingData.reduce((sum, r) => sum + r.sharpeRatio, 0) / rollingData.length;
  const avgVolatility = rollingData.reduce((sum, r) => sum + r.volatility, 0) / rollingData.length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">高级分析</h1>
          <p className="text-sm text-text-secondary mt-1">
            深度量化分析：回撤分析、滚动指标与蒙特卡洛模拟
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="最大回撤"
          value={maxDrawdown.toFixed(2)}
          suffix="%"
          color="loss"
          icon={<TrendingDown className="w-5 h-5 text-loss" />}
        />
        <MetricCard
          title="平均夏普比率"
          value={avgSharpe.toFixed(2)}
          icon={<Target className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="平均波动率"
          value={avgVolatility.toFixed(2)}
          suffix="%"
          icon={<Activity className="w-5 h-5 text-warning" />}
        />
        <MetricCard
          title="模拟置信度"
          value={monteCarloResult.probabilityOfProfit * 100}
          suffix="%"
          color="profit"
          icon={<PieChart className="w-5 h-5 text-accent-purple" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DrawdownChart data={drawdownData} />
        <MonteCarloVisualization result={monteCarloResult} />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">滚动指标分析</h2>
          <div className="flex items-center gap-2">
            {[30, 60, 90].map((w) => (
              <button
                key={w}
                onClick={() => setWindowSize(w)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  windowSize === w
                    ? 'bg-accent-blue/20 text-accent-cyan border border-accent-blue/30'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                }`}
              >
                {w}日
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-medium text-text-secondary">滚动夏普比率</h3>
              <Target className="w-4 h-4 text-profit" />
            </div>
            <RollingMetricsChart data={rollingData} metric="sharpeRatio" />
          </div>

          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-medium text-text-secondary">滚动波动率</h3>
              <Zap className="w-4 h-4 text-warning" />
            </div>
            <RollingMetricsChart data={rollingData} metric="volatility" />
          </div>

          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-medium text-text-secondary">滚动最大回撤</h3>
              <TrendingDown className="w-4 h-4 text-loss" />
            </div>
            <RollingMetricsChart data={rollingData} metric="maxDrawdown" />
          </div>

          <div className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-medium text-text-secondary">滚动胜率</h3>
              <Percent className="w-4 h-4 text-accent-blue" />
            </div>
            <RollingMetricsChart data={rollingData} metric="winRate" />
          </div>
        </div>
      </div>

      <div className="glass-card rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="w-4 h-4 text-warning" />
          <h3 className="text-sm font-semibold text-text-primary">分析说明</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-text-secondary">
          <div>
            <strong className="text-text-primary block mb-1">回撤分析</strong>
            监控账户权益相对于历史峰值的下降幅度，识别最大回撤和回撤持续时间
          </div>
          <div>
            <strong className="text-text-primary block mb-1">滚动指标</strong>
            基于滑动窗口计算夏普比率、波动率等指标，评估策略表现的稳定性
          </div>
          <div>
            <strong className="text-text-primary block mb-1">蒙特卡洛模拟</strong>
            通过随机模拟预测未来可能的资金路径，量化盈利概率和风险边界
          </div>
        </div>
      </div>
    </div>
  );
}
