import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Activity, TrendingUp, TrendingDown, BarChart3, Zap, Target } from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { mockFactors, getFactorValues, getFactorHeatmap } from '../data/mock';
import type { Factor } from '../types';

function FactorChart({ factorId, factorName }: { factorId: string; factorName: string }) {
  const data = getFactorValues(factorId, 30);
  const latestValue = data[data.length - 1]?.value ?? 0;
  const isPositive = latestValue >= 0;

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">{factorName}</h3>
          <p className={`text-xs mt-1 ${isPositive ? 'text-profit' : 'text-loss'}`}>
            当前值: {latestValue.toFixed(3)} (Z-Score: {data[data.length - 1]?.zScore})
          </p>
        </div>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isPositive ? 'bg-profit/10' : 'bg-loss/10'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4 text-profit" /> : <TrendingDown className="w-4 h-4 text-loss" />}
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="date" hide />
          <YAxis hide domain={['auto', 'auto']} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload;
                return (
                  <div className="bg-bg-card border border-border rounded-lg p-2 shadow-lg">
                    <p className="text-xs text-text-muted">{point.date}</p>
                    <p className={`text-sm font-semibold ${point.value >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {point.value.toFixed(3)}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine y={0} stroke="#334155" strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey="value"
            stroke={isPositive ? '#22c55e' : '#ef4444'}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function FactorHeatmap() {
  const { stocks, factors, values } = getFactorHeatmap();
  
  const getColor = (value: number) => {
    if (value > 0.5) return 'bg-profit';
    if (value > 0) return 'bg-profit/50';
    if (value > -0.5) return 'bg-loss/50';
    return 'bg-loss';
  };

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">因子得分热力图</h3>
        <div className="flex items-center gap-4 text-xs text-text-secondary">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-profit" />
            <span>强正相关</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-profit/50" />
            <span>弱正相关</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-loss/50" />
            <span>弱负相关</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-loss" />
            <span>强负相关</span>
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr>
              <th className="px-2 py-2 text-left text-xs text-text-secondary">股票</th>
              {factors.map((f: string) => (
                <th key={f} className="px-2 py-2 text-center text-xs text-text-secondary">{f.slice(0, 4)}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {stocks.map((stock: string, i: number) => (
              <tr key={stock}>
                <td className="px-2 py-2 text-sm text-text-primary font-medium">{stock}</td>
                {values[i]?.map((value: number, j: number) => (
                  <td key={j} className="px-2 py-2">
                    <div className={`w-full h-6 rounded ${getColor(value)} opacity-60`} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Factors() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  const categories = [
    { id: 'all', label: '全部', icon: Activity },
    { id: 'technical', label: '技术指标', icon: BarChart3 },
    { id: 'fundamental', label: '基本面', icon: Target },
    { id: 'risk', label: '风险指标', icon: Zap },
    { id: 'sentiment', label: '情绪', icon: TrendingUp },
  ];
  
  const filteredFactors = selectedCategory === 'all' 
    ? mockFactors 
    : mockFactors.filter((f: Factor) => f.category === selectedCategory);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">因子分析</h1>
          <p className="text-sm text-text-secondary mt-1">
            多因子选股模型分析与可视化
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="因子总数"
          value={mockFactors.length}
          icon={<Activity className="w-5 h-5 text-accent-cyan" />}
        />
        <MetricCard
          title="技术因子"
          value={mockFactors.filter((f: Factor) => f.category === 'technical').length}
          icon={<BarChart3 className="w-5 h-5 text-accent-blue" />}
        />
        <MetricCard
          title="基本面因子"
          value={mockFactors.filter((f: Factor) => f.category === 'fundamental').length}
          icon={<Target className="w-5 h-5 text-accent-purple" />}
        />
        <MetricCard
          title="风险因子"
          value={mockFactors.filter((f: Factor) => f.category === 'risk').length}
          icon={<Zap className="w-5 h-5 text-warning" />}
        />
      </div>

      <div className="flex items-center gap-2">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-accent-blue/20 text-accent-cyan border border-accent-blue/30'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
              }`}
            >
              <div className="flex items-center gap-2">
                <Icon className="w-4 h-4" />
                {cat.label}
              </div>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">因子走势</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredFactors.map((factor: Factor) => (
              <FactorChart 
                key={factor.id} 
                factorId={factor.id} 
                factorName={factor.name}
              />
            ))}
          </div>
        </div>
        
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">因子列表</h2>
          <div className="glass-card rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-bg-secondary/50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">因子名称</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">类别</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">描述</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">默认权重</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredFactors.map((factor: Factor) => (
                  <tr key={factor.id} className="hover:bg-bg-hover transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-text-primary">{factor.name}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded ${
                        factor.category === 'technical' ? 'bg-accent-blue/20 text-accent-cyan' :
                        factor.category === 'fundamental' ? 'bg-accent-purple/20 text-accent-purple' :
                        factor.category === 'risk' ? 'bg-warning/20 text-warning' :
                        'bg-profit/20 text-profit'
                      }`}>
                        {factor.category === 'technical' ? '技术指标' :
                         factor.category === 'fundamental' ? '基本面' :
                         factor.category === 'risk' ? '风险' : '情绪'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-text-secondary">{factor.description}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm text-text-primary">{(factor.defaultWeight * 100).toFixed(0)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <FactorHeatmap />
    </div>
  );
}
