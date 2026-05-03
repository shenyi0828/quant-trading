import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';
import { Play, RotateCcw, TrendingUp, TrendingDown, Calendar, DollarSign, Percent, Target, Activity } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { mockBacktestConfigs, getBacktestResult, getBacktestTrades } from '../data/mock';
import type { BacktestResult, BacktestTrade, BacktestConfig, EquityPoint } from '../types';

function BacktestConfigForm({ onRun }: { onRun: (configId: string) => void }) {
  const [selectedConfig, setSelectedConfig] = useState<string>('');

  return (
    <div className="glass-card rounded-xl p-5">
      <h3 className="text-lg font-semibold text-text-primary mb-4">回测配置</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm text-text-secondary mb-2">选择策略</label>
          <select 
            className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-text-primary"
            onChange={(e) => setSelectedConfig(e.target.value)}
          >
            <option value="">请选择策略</option>
            {mockBacktestConfigs.map((config: BacktestConfig) => (
              <option key={config.id} value={config.id}>
                {config.strategyName}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-text-secondary mb-2">时间范围</label>
          <div className="flex items-center gap-2">
            <input 
              type="date" 
              defaultValue="2024-01-01"
              className="flex-1 bg-bg-secondary border border-border rounded-lg px-3 py-2 text-text-primary text-sm"
            />
            <span className="text-text-secondary">至</span>
            <input 
              type="date" 
              defaultValue="2024-12-31"
              className="flex-1 bg-bg-secondary border border-border rounded-lg px-3 py-2 text-text-primary text-sm"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm text-text-secondary mb-2">初始资金</label>
          <input 
            type="number" 
            defaultValue={1000000}
            className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm text-text-secondary mb-2">手续费率</label>
          <input 
            type="number" 
            defaultValue={0.0003}
            step={0.0001}
            className="w-full bg-bg-secondary border border-border rounded-lg px-3 py-2 text-text-primary"
          />
        </div>
      </div>
      <button
        onClick={() => selectedConfig && onRun(selectedConfig)}
        disabled={!selectedConfig}
        className="flex items-center gap-2 px-6 py-2 bg-accent-blue/20 text-accent-cyan rounded-lg border border-accent-blue/30 hover:bg-accent-blue/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Play className="w-4 h-4" />
        运行回测
      </button>
    </div>
  );
}

function PerformanceMetrics({ result }: { result: BacktestResult }) {
  const isPositive = result.totalReturn >= 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <MetricCard
        title="总收益率"
        value={Math.abs(result.totalReturn)}
        prefix={isPositive ? '+' : '-'}
        suffix="%"
        icon={isPositive ? <TrendingUp className="w-5 h-5 text-profit" /> : <TrendingDown className="w-5 h-5 text-loss" />}
        color={isPositive ? 'profit' : 'loss'}
      />
      <MetricCard
        title="年化收益"
        value={result.annualizedReturn}
        suffix="%"
        icon={<Calendar className="w-5 h-5 text-accent-cyan" />}
        color={result.annualizedReturn >= 0 ? 'profit' : 'loss'}
      />
      <MetricCard
        title="最大回撤"
        value={result.maxDrawdown}
        suffix="%"
        icon={<TrendingDown className="w-5 h-5 text-loss" />}
        color="loss"
      />
      <MetricCard
        title="夏普比率"
        value={result.sharpeRatio}
        icon={<Target className="w-5 h-5 text-accent-blue" />}
        color={result.sharpeRatio >= 1 ? 'profit' : 'default'}
      />
      <MetricCard
        title="胜率"
        value={result.winRate}
        suffix="%"
        icon={<Percent className="w-5 h-5 text-accent-purple" />}
      />
      <MetricCard
        title="盈亏比"
        value={result.profitFactor}
        icon={<Activity className="w-5 h-5 text-warning" />}
      />
      <MetricCard
        title="交易次数"
        value={result.totalTrades}
        icon={<DollarSign className="w-5 h-5 text-accent-cyan" />}
      />
      <MetricCard
        title="最终资金"
        value={Math.round(result.equityCurve[result.equityCurve.length - 1]?.equity || 0)}
        prefix="¥"
        icon={<DollarSign className="w-5 h-5 text-profit" />}
      />
    </div>
  );
}

function BacktestChart({ result }: { result: BacktestResult }) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const chartData = result.equityCurve.map((point: EquityPoint, i: number) => ({
    date: point.date,
    equity: point.equity,
    benchmark: result.benchmarkCurve[i]?.equity ?? point.equity,
    strategyReturn: point.cumulativeReturn,
    benchmarkReturn: result.benchmarkCurve[i]?.cumulativeReturn ?? 0,
  }));

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">收益曲线</h3>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-accent-cyan" />
            <span className="text-text-secondary">策略收益</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded bg-text-muted" />
            <span className="text-text-secondary">基准收益</span>
          </div>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#64748b"
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            minTickGap={30}
          />
          <YAxis
            yAxisId="equity"
            stroke="#64748b"
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `¥${(value / 10000).toFixed(0)}万`}
            domain={['auto', 'auto']}
          />
          <YAxis
            yAxisId="return"
            orientation="right"
            stroke="#64748b"
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(value) => `${value.toFixed(0)}%`}
            domain={['auto', 'auto']}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                    <p className="text-xs text-text-muted mb-1">{data.date}</p>
                    <p className="text-sm font-semibold text-accent-cyan">
                      策略: {formatCurrency(data.equity)}
                    </p>
                    <p className="text-sm font-semibold text-text-muted">
                      基准: {formatCurrency(data.benchmark)}
                    </p>
                    <p className="text-xs mt-1 text-profit">
                      策略收益: {data.strategyReturn >= 0 ? '+' : ''}{data.strategyReturn.toFixed(2)}%
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <ReferenceLine yAxisId="equity" y={result.config.initialCapital} stroke="#334155" strokeDasharray="3 3" />
          <Line
            yAxisId="equity"
            type="monotone"
            dataKey="equity"
            name="策略收益"
            stroke="#06b6d4"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="equity"
            type="monotone"
            dataKey="benchmark"
            name="基准收益"
            stroke="#64748b"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function BacktestTradesTable({ trades }: { trades: BacktestTrade[] }) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-lg font-semibold text-text-primary">交易记录</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-bg-secondary/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">时间</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">股票</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase">方向</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">数量</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">价格</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">金额</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">盈亏</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {trades.slice(0, 20).map((trade) => (
              <tr key={trade.id} className="hover:bg-bg-hover transition-colors">
                <td className="px-4 py-3 text-sm text-text-secondary">{formatDateTime(trade.time)}</td>
                <td className="px-4 py-3">
                  <div>
                    <span className="text-sm font-medium text-accent-cyan">{trade.symbol}</span>
                    <span className="text-xs text-text-secondary ml-2">{trade.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                    trade.side === 'buy' ? 'bg-profit/10 text-profit' : 'bg-loss/10 text-loss'
                  }`}>
                    {trade.side === 'buy' ? '买入' : '卖出'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">{trade.quantity.toLocaleString()}</td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">{formatCurrency(trade.price)}</td>
                <td className="px-4 py-3 text-right text-sm text-text-primary">{formatCurrency(trade.totalAmount)}</td>
                <td className="px-4 py-3 text-right">
                  {trade.realizedPnL !== undefined ? (
                    <span className={`text-sm font-semibold ${trade.realizedPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {trade.realizedPnL >= 0 ? '+' : ''}{formatCurrency(trade.realizedPnL)}
                    </span>
                  ) : (
                    <span className="text-sm text-text-muted">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Backtest() {
  const [result, setResult] = useState<BacktestResult | null>(getBacktestResult('bt-001'));
  const [trades, setTrades] = useState<BacktestTrade[]>(getBacktestTrades('bt-001'));

  const handleRunBacktest = (configId: string) => {
    setResult(getBacktestResult(configId));
    setTrades(getBacktestTrades(configId));
  };

  const handleReset = () => {
    setResult(getBacktestResult('bt-001'));
    setTrades(getBacktestTrades('bt-001'));
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">回测分析</h1>
          <p className="text-sm text-text-secondary mt-1">
            策略历史回测与绩效分析
          </p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-4 py-2 bg-bg-secondary text-text-secondary rounded-lg hover:text-text-primary hover:bg-bg-hover transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          重置
        </button>
      </div>

      <BacktestConfigForm onRun={handleRunBacktest} />

      {result && (
        <>
          <PerformanceMetrics result={result} />
          
          <BacktestChart result={result} />
          
          <BacktestTradesTable trades={trades} />
        </>
      )}
    </div>
  );
}
