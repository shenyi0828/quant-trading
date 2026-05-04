import { useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot, PieChart as RePieChart, Pie, Cell, Legend } from 'recharts';
import { Target, TrendingUp, TrendingDown, DollarSign, RefreshCw } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { getEfficientFrontier, getOptimizationResult } from '../data/mock';
import type { EfficientFrontierPoint, OptimizationResult, PortfolioAsset } from '../types';

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

function EfficientFrontierChart({ data, currentPoint }: { data: EfficientFrontierPoint[]; currentPoint?: EfficientFrontierPoint }) {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">有效前沿</h3>
          <p className="text-xs text-text-secondary mt-1">风险-收益权衡曲线 (马科维茨优化)</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis 
            type="number" 
            dataKey="risk" 
            name="风险 (波动率)" 
            stroke="#64748b" 
            tick={{ fill: '#64748b', fontSize: 11 }} 
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            label={{ value: '风险 (波动率)', position: 'bottom', fill: '#64748b', fontSize: 12 }}
          />
          <YAxis 
            type="number" 
            dataKey="return" 
            name="预期收益" 
            stroke="#64748b" 
            tick={{ fill: '#64748b', fontSize: 11 }} 
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            label={{ value: '预期收益', angle: -90, position: 'left', fill: '#64748b', fontSize: 12 }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as EfficientFrontierPoint;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-3 shadow-lg">
                    <p className="text-xs text-text-muted">有效前沿点</p>
                    <p className="text-sm font-semibold text-text-primary">预期收益: {(point.return * 100).toFixed(1)}%</p>
                    <p className="text-sm text-text-secondary">风险: {(point.risk * 100).toFixed(1)}%</p>
                    <p className="text-xs text-accent-cyan mt-1">夏普比率: {point.sharpeRatio.toFixed(2)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="有效前沿" data={data} fill="#3b82f6">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.sharpeRatio === Math.max(...data.map(d => d.sharpeRatio)) ? '#22c55e' : '#3b82f6'} />
            ))}
          </Scatter>
          {currentPoint && (
            <ReferenceDot x={currentPoint.risk} y={currentPoint.return} r={6} fill="#f59e0b" stroke="#fff" />
          )}
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-4 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-text-secondary">最大夏普点</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-warning" />
          <span className="text-text-secondary">当前组合</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-accent-blue" />
          <span className="text-text-secondary">有效前沿</span>
        </div>
      </div>
    </div>
  );
}

function WeightPieChart({ assets }: { assets: PortfolioAsset[] }) {
  const data = assets.map((asset, idx) => ({
    name: asset.name,
    symbol: asset.symbol,
    value: Math.round(asset.weight * 100),
    color: COLORS[idx % COLORS.length]
  }));

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">权重配置</h3>
          <p className="text-xs text-text-secondary mt-1">各资产配置比例</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <RePieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                    <p className="text-sm font-semibold text-text-primary">{data.name}</p>
                    <p className="text-xs text-text-secondary">{data.symbol}</p>
                    <p className="text-sm text-accent-cyan">{data.value}%</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend verticalAlign="bottom" height={36} iconType="circle" />
        </RePieChart>
      </ResponsiveContainer>

      <div className="mt-4 space-y-2">
        {assets.map((asset, idx) => (
          <div key={asset.symbol} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
              <span className="text-text-secondary">{asset.name}</span>
              <span className="text-text-muted">({asset.symbol})</span>
            </div>
            <span className="text-text-primary font-medium">{(asset.weight * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function OptimizationStrategyCard({ result, selected, onSelect }: { 
  result: OptimizationResult; 
  selected: boolean; 
  onSelect: () => void;
}) {
  const strategyLabels: Record<string, string> = {
    max_sharpe: '最大夏普比率',
    min_volatility: '最小波动率',
    max_return: '最大收益',
    equal_weight: '等权重'
  };

  const strategyDesc: Record<string, string> = {
    max_sharpe: '在承担单位风险下追求最高收益',
    min_volatility: '最小化组合波动率，追求稳定',
    max_return: '追求最高预期收益，风险较高',
    equal_weight: '各资产平均分配，简单平衡'
  };

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border transition-all ${
        selected
          ? 'bg-accent-blue/10 border-accent-blue/50'
          : 'bg-bg-secondary/30 border-border hover:border-border-light'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h4 className={`text-sm font-medium ${selected ? 'text-accent-cyan' : 'text-text-primary'}`}>
            {strategyLabels[result.strategy]}
          </h4>
          <p className="text-xs text-text-muted mt-1">{strategyDesc[result.strategy]}</p>
        </div>
        <Target className={`w-5 h-5 ${selected ? 'text-accent-cyan' : 'text-text-muted'}`} />
      </div>
      <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t border-border">
        <div>
          <p className="text-xs text-text-muted">预期收益</p>
          <p className={`text-sm font-semibold ${result.expectedReturn > 0.1 ? 'text-profit' : 'text-text-primary'}`}>
            {(result.expectedReturn * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-text-muted">预期风险</p>
          <p className="text-sm font-semibold text-text-primary">{(result.expectedRisk * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-text-muted">夏普比率</p>
          <p className="text-sm font-semibold text-accent-cyan">{result.sharpeRatio.toFixed(2)}</p>
        </div>
      </div>
    </button>
  );
}

export function PortfolioOptimization() {
  const [selectedStrategy, setSelectedStrategy] = useState<'max_sharpe' | 'min_volatility' | 'max_return' | 'equal_weight'>('max_sharpe');
  
  const frontierData = getEfficientFrontier();
  const currentResult = getOptimizationResult(selectedStrategy);

  const currentPoint = frontierData.find(p => 
    Math.abs(p.return - currentResult.expectedReturn) < 0.01 && 
    Math.abs(p.risk - currentResult.expectedRisk) < 0.01
  ) || frontierData[Math.floor(frontierData.length / 2)];

  const allStrategies: ('max_sharpe' | 'min_volatility' | 'max_return' | 'equal_weight')[] = ['max_sharpe', 'min_volatility', 'max_return', 'equal_weight'];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">组合优化</h1>
          <p className="text-sm text-text-secondary mt-1">
            基于马科维茨现代投资组合理论的资产配置优化
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="预期年化收益"
          value={(currentResult.expectedReturn * 100).toFixed(2)}
          suffix="%"
          color="profit"
          icon={<TrendingUp className="w-5 h-5 text-profit" />}
        />
        <MetricCard
          title="预期波动率"
          value={(currentResult.expectedRisk * 100).toFixed(2)}
          suffix="%"
          color="loss"
          icon={<TrendingDown className="w-5 h-5 text-loss" />}
        />
        <MetricCard
          title="夏普比率"
          value={currentResult.sharpeRatio.toFixed(2)}
          icon={<Target className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="再平衡成本"
          value={(currentResult.rebalancingCost * 100).toFixed(3)}
          suffix="%"
          icon={<DollarSign className="w-5 h-5 text-accent-purple" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EfficientFrontierChart data={frontierData} currentPoint={currentPoint} />
        <WeightPieChart assets={currentResult.weights} />
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-accent-blue" />
          <h2 className="text-lg font-semibold text-text-primary">优化策略选择</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {allStrategies.map((strategy) => (
            <OptimizationStrategyCard
              key={strategy}
              result={getOptimizationResult(strategy)}
              selected={selectedStrategy === strategy}
              onSelect={() => setSelectedStrategy(strategy)}
            />
          ))}
        </div>
      </div>

      <div className="glass-card rounded-xl p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">资产详情</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-bg-secondary/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">资产</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">当前价格</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">预期收益</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">波动率</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">推荐权重</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">配置金额</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {currentResult.weights.map((asset) => (
                <tr key={asset.symbol} className="hover:bg-bg-hover transition-colors">
                  <td className="px-4 py-3">
                    <div>
                      <span className="text-sm font-medium text-text-primary">{asset.name}</span>
                      <span className="text-xs text-text-muted ml-2">({asset.symbol})</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-text-primary">¥{asset.currentPrice.toFixed(2)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`text-sm ${asset.expectedReturn > 0.1 ? 'text-profit' : 'text-text-primary'}`}>
                      {(asset.expectedReturn * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-text-primary">{(asset.volatility * 100).toFixed(1)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-medium text-accent-cyan">{(asset.weight * 100).toFixed(0)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm text-text-primary">¥{(asset.weight * 1000000).toFixed(0)}</span>
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
