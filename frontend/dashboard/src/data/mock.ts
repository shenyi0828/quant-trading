import type { 
  Strategy, 
  StrategyDetail, 
  DashboardMetrics, 
  Factor, 
  FactorValue, 
  BacktestConfig, 
  BacktestResult, 
  BacktestTrade,
  Stock,
  StrategySignal,
  EquityPoint,
  Holding,
  Trade,
  SpreadPair,
  SpreadPoint,
  SpreadSignal,
  DrawdownPoint,
  RollingMetric,
  MonteCarloResult,
  EfficientFrontierPoint,
  PortfolioAsset,
  OptimizationResult
} from '../types';

// ========== Strategy Mock Data ==========

export const mockStrategies: Strategy[] = [
  {
    id: 'str-001',
    name: '动量策略 Alpha',
    status: 'running',
    totalPnL: 125680,
    winRate: 68.5,
    totalTrades: 156,
    activePositions: 5,
    lastUpdated: '2025-05-04 10:30:00',
    runtime: '45天',
    description: '基于多因子动量模型的量化策略,捕捉短期价格趋势信号',
    sharpeRatio: 1.85,
    maxDrawdown: 12.3
  },
  {
    id: 'str-002',
    name: '均值回归策略',
    status: 'running',
    totalPnL: 45320,
    winRate: 72.3,
    totalTrades: 89,
    activePositions: 3,
    lastUpdated: '2025-05-04 10:25:00',
    runtime: '30天',
    description: '利用价格偏离均值后的回归特性进行交易',
    sharpeRatio: 1.42,
    maxDrawdown: 8.5
  },
  {
    id: 'str-003',
    name: '事件驱动策略',
    status: 'stopped',
    totalPnL: -12500,
    winRate: 55.2,
    totalTrades: 45,
    activePositions: 0,
    lastUpdated: '2025-04-28 16:00:00',
    runtime: '15天',
    description: '基于财报公告、分析师评级等事件信号',
    sharpeRatio: 0.65,
    maxDrawdown: 18.7
  },
  {
    id: 'str-004',
    name: '因子轮动策略',
    status: 'running',
    totalPnL: 89450,
    winRate: 65.8,
    totalTrades: 112,
    activePositions: 8,
    lastUpdated: '2025-05-04 10:35:00',
    runtime: '60天',
    description: '根据市场环境动态调整因子权重配置',
    sharpeRatio: 1.68,
    maxDrawdown: 15.2
  },
  {
    id: 'str-005',
    name: '机器学习策略',
    status: 'error',
    totalPnL: 0,
    winRate: 0,
    totalTrades: 0,
    activePositions: 0,
    lastUpdated: '2025-05-03 09:00:00',
    runtime: '5天',
    description: '基于深度强化学习的自适应交易策略',
    sharpeRatio: 0,
    maxDrawdown: 0
  }
];

export function getAllStrategies(): Strategy[] {
  return mockStrategies;
}

export function getStrategyDetail(id: string): StrategyDetail | null {
  const strategy = mockStrategies.find(s => s.id === id);
  if (!strategy) return null;

  // Generate mock equity curve
  const equityCurve: EquityPoint[] = generateEquityCurve(strategy.totalPnL, 60);
  
  // Generate mock holdings
  const holdings: Holding[] = [
    { symbol: '600519', name: '贵州茅台', quantity: 100, costPrice: 1850.00, currentPrice: 1920.50, marketValue: 192050, unrealizedPnL: 7050, unrealizedPnLPercent: 3.8 },
    { symbol: '000858', name: '五粮液', quantity: 200, costPrice: 165.00, currentPrice: 172.30, marketValue: 34460, unrealizedPnL: 1460, unrealizedPnLPercent: 4.4 },
    { symbol: '601318', name: '中国平安', quantity: 500, costPrice: 45.00, currentPrice: 48.20, marketValue: 24100, unrealizedPnL: 1600, unrealizedPnLPercent: 7.1 },
    { symbol: '600036', name: '招商银行', quantity: 300, costPrice: 32.50, currentPrice: 35.80, marketValue: 10740, unrealizedPnL: 990, unrealizedPnLPercent: 10.2 },
  ];

  // Generate mock trades
  const recentTrades: Trade[] = [
    { id: 'trade-001', strategyId: id, time: '2025-05-04 09:30:00', symbol: '600519', name: '贵州茅台', side: 'buy', quantity: 50, price: 1918.00, totalAmount: 95900 },
    { id: 'trade-002', strategyId: id, time: '2025-05-03 14:15:00', symbol: '000858', name: '五粮液', side: 'sell', quantity: 100, price: 170.50, totalAmount: 17050, realizedPnL: 550 },
    { id: 'trade-003', strategyId: id, time: '2025-05-02 10:45:00', symbol: '601318', name: '中国平安', side: 'buy', quantity: 200, price: 47.80, totalAmount: 9560 },
  ];

  return {
    ...strategy,
    equityCurve,
    holdings,
    recentTrades
  };
}

export function getDashboardMetrics(): DashboardMetrics {
  const runningStrategies = mockStrategies.filter(s => s.status === 'running');
  return {
    totalPnL: mockStrategies.reduce((sum, s) => sum + s.totalPnL, 0),
    activeStrategies: runningStrategies.length,
    todayTrades: 23,
    openPositions: runningStrategies.reduce((sum, s) => sum + s.activePositions, 0),
    dailyReturn: 2.35,
    totalCapital: 1000000
  };
}

export function getStrategySignals(_strategyId: string): StrategySignal[] {
  const signals: StrategySignal[] = [
    { symbol: '600519', name: '贵州茅台', signal: 'buy', strength: 0.85, timestamp: '2025-05-04 10:00:00' },
    { symbol: '000858', name: '五粮液', signal: 'hold', strength: 0.45, timestamp: '2025-05-04 10:00:00' },
    { symbol: '601318', name: '中国平安', signal: 'sell', strength: 0.72, timestamp: '2025-05-04 09:55:00' },
    { symbol: '600036', name: '招商银行', signal: 'buy', strength: 0.68, timestamp: '2025-05-04 09:50:00' },
    { symbol: '000001', name: '平安银行', signal: 'hold', strength: 0.35, timestamp: '2025-05-04 09:45:00' },
  ];
  return signals;
}

// ========== Factor Mock Data ==========

export const mockFactors: Factor[] = [
  { id: 'fac-001', name: '动量因子', category: 'technical', description: '基于价格趋势的动量信号', defaultWeight: 0.25 },
  { id: 'fac-002', name: '价值因子', category: 'fundamental', description: 'P/E、P/B等估值指标', defaultWeight: 0.20 },
  { id: 'fac-003', name: '质量因子', category: 'fundamental', description: 'ROE、资产负债率等财务指标', defaultWeight: 0.15 },
  { id: 'fac-004', name: '波动率因子', category: 'risk', description: '历史波动率和Beta值', defaultWeight: 0.15 },
  { id: 'fac-005', name: '流动性因子', category: 'technical', description: '成交量和换手率指标', defaultWeight: 0.10 },
  { id: 'fac-006', name: '情绪因子', category: 'sentiment', description: '分析师评级和市场情绪', defaultWeight: 0.15 },
];

export function getFactorValues(_factorId: string, days: number): FactorValue[] {
  const values: FactorValue[] = [];
  const baseValue = 0.5;
  const volatility = 0.3;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const value = baseValue + (Math.random() - 0.5) * volatility + (days - i) * 0.01;
    const zScore = ((value - baseValue) / volatility).toFixed(2);
    values.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.getTime(),
      value: Number(value.toFixed(3)),
      zScore: zScore
    });
  }
  return values;
}

export function getFactorHeatmap(): { stocks: string[]; factors: string[]; values: number[][] } {
  const stocks = ['600519', '000858', '601318', '600036', '000001', '601166'];
  const factors = mockFactors.map(f => f.id);
  const values: number[][] = [];
  
  for (const _stock of stocks) {
    const row: number[] = [];
    for (const _factor of factors) {
      row.push(Math.random() * 2 - 1);
    }
    values.push(row);
  }
  return { stocks, factors, values };
}

// ========== Backtest Mock Data ==========

export const mockBacktestConfigs: BacktestConfig[] = [
  { id: 'bt-001', strategyId: 'str-001', strategyName: '动量策略 Alpha', startDate: '2024-01-01', endDate: '2024-12-31', initialCapital: 500000, commission: 0.0003, slippage: 0.0001 },
  { id: 'bt-002', strategyId: 'str-002', strategyName: '均值回归策略', startDate: '2024-01-01', endDate: '2024-12-31', initialCapital: 500000, commission: 0.0003, slippage: 0.0001 },
  { id: 'bt-003', strategyId: 'str-004', strategyName: '因子轮动策略', startDate: '2024-01-01', endDate: '2024-12-31', initialCapital: 500000, commission: 0.0003, slippage: 0.0001 },
];

export function getBacktestResult(configId: string): BacktestResult {
  const config = mockBacktestConfigs.find(c => c.id === configId);
  if (!config) {
    return {
      config: mockBacktestConfigs[0],
      equityCurve: [],
      benchmarkCurve: [],
      totalReturn: 0,
      annualizedReturn: 0,
      maxDrawdown: 0,
      sharpeRatio: 0,
      winRate: 0,
      profitFactor: 0,
      totalTrades: 0
    };
  }

  const equityCurve = generateEquityCurve(config.initialCapital * 0.25, 250);
  const benchmarkCurve = generateEquityCurve(config.initialCapital * 0.08, 250);

  return {
    config,
    equityCurve,
    benchmarkCurve,
    totalReturn: 25.6,
    annualizedReturn: 28.5,
    maxDrawdown: 12.3,
    sharpeRatio: 1.85,
    winRate: 68.5,
    profitFactor: 2.1,
    totalTrades: 156
  };
}

export function getBacktestTrades(_configId: string): BacktestTrade[] {
  const trades: BacktestTrade[] = [
    { id: 'bt-trade-001', time: '2024-01-15 09:30:00', symbol: '600519', name: '贵州茅台', side: 'buy', quantity: 100, price: 1850.00, totalAmount: 185000 },
    { id: 'bt-trade-002', time: '2024-01-20 14:15:00', symbol: '000858', name: '五粮液', side: 'buy', quantity: 200, price: 165.00, totalAmount: 33000 },
    { id: 'bt-trade-003', time: '2024-02-05 10:45:00', symbol: '600519', name: '贵州茅台', side: 'sell', quantity: 100, price: 1920.00, totalAmount: 192000, realizedPnL: 7000 },
    { id: 'bt-trade-004', time: '2024-02-10 09:30:00', symbol: '601318', name: '中国平安', side: 'buy', quantity: 500, price: 45.00, totalAmount: 22500 },
    { id: 'bt-trade-005', time: '2024-03-01 14:00:00', symbol: '000858', name: '五粮液', side: 'sell', quantity: 200, price: 172.00, totalAmount: 34400, realizedPnL: 1400 },
  ];
  return trades;
}

// ========== Stock Pool Mock Data ==========

export const mockStocks: Stock[] = [
  { symbol: '600519', name: '贵州茅台', industry: '食品饮料', marketCap: 2.1e12, price: 1920.50, change: 15.50, changePercent: 0.81, volume: 2850000, pe: 32.5, pb: 8.2 },
  { symbol: '000858', name: '五粮液', industry: '食品饮料', marketCap: 6.8e11, price: 172.30, change: 4.80, changePercent: 2.86, volume: 15600000, pe: 28.3, pb: 6.5 },
  { symbol: '601318', name: '中国平安', industry: '保险', marketCap: 9.5e11, price: 48.20, change: -0.80, changePercent: -1.63, volume: 45000000, pe: 8.5, pb: 1.2 },
  { symbol: '600036', name: '招商银行', industry: '银行', marketCap: 1.2e12, price: 35.80, change: 0.50, changePercent: 1.41, volume: 32000000, pe: 6.8, pb: 0.9 },
  { symbol: '000001', name: '平安银行', industry: '银行', marketCap: 2.5e11, price: 12.50, change: 0.15, changePercent: 1.21, volume: 85000000, pe: 5.5, pb: 0.6 },
  { symbol: '601166', name: '兴业银行', industry: '银行', marketCap: 3.8e11, price: 18.20, change: -0.35, changePercent: -1.89, volume: 42000000, pe: 5.2, pb: 0.5 },
  { symbol: '600276', name: '恒瑞医药', industry: '医药生物', marketCap: 3.2e11, price: 48.50, change: 1.20, changePercent: 2.53, volume: 12000000, pe: 45.8, pb: 6.8 },
  { symbol: '000333', name: '美的集团', industry: '电子', marketCap: 4.5e11, price: 65.80, change: -1.50, changePercent: -2.24, volume: 18000000, pe: 15.2, pb: 3.5 },
  { symbol: '002415', name: '海康威视', industry: '电子', marketCap: 3.8e11, price: 35.20, change: 0.80, changePercent: 2.32, volume: 25000000, pe: 22.5, pb: 4.2 },
  { symbol: '601888', name: '中国中免', industry: '商贸零售', marketCap: 1.8e11, price: 85.50, change: -2.30, changePercent: -2.62, volume: 8500000, pe: 35.8, pb: 5.5 },
  { symbol: '600887', name: '伊利股份', industry: '食品饮料', marketCap: 2.6e11, price: 32.50, change: 0.45, changePercent: 1.41, volume: 35000000, pe: 25.8, pb: 5.2 },
  { symbol: '002352', name: '顺丰控股', industry: '公用事业', marketCap: 2.1e11, price: 45.80, change: 1.80, changePercent: 4.07, volume: 15000000, pe: 28.5, pb: 3.8 },
  { symbol: '300750', name: '宁德时代', industry: '电力设备', marketCap: 9.5e11, price: 215.00, change: -5.50, changePercent: -2.50, volume: 8500000, pe: 55.2, pb: 12.5 },
  { symbol: '601012', name: '隆基绿能', industry: '电力设备', marketCap: 2.8e11, price: 38.50, change: 2.30, changePercent: 6.15, volume: 42000000, pe: 18.5, pb: 3.2 },
];

function generateEquityCurve(totalPnL: number, days: number): EquityPoint[] {
  const curve: EquityPoint[] = [];
  const baseEquity = 500000;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const progress = (days - i) / days;
    const randomFactor = Math.sin(progress * Math.PI * 2) * 0.1 + Math.random() * 0.05;
    const equity = baseEquity + totalPnL * progress + totalPnL * randomFactor;
    const cumulativeReturn = ((equity - baseEquity) / baseEquity) * 100;
    
    curve.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.getTime(),
      equity: Number(equity.toFixed(2)),
      cumulativeReturn: Number(cumulativeReturn.toFixed(2))
    });
  }
  return curve;
}

function generateSpreadHistory(pairId: string, days: number): SpreadPoint[] {
  const points: SpreadPoint[] = [];
  const basePriceA = pairId === 'spread-001' ? 1800 : (pairId === 'spread-002' ? 48 : 35);
  const basePriceB = pairId === 'spread-001' ? 165 : (pairId === 'spread-002' ? 12.5 : 18);
  const baseSpread = basePriceA - basePriceB * (pairId === 'spread-001' ? 10 : 1);
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const noise = Math.sin(i * 0.1) * 50 + (Math.random() - 0.5) * 30;
    const spread = baseSpread + noise;
    const priceA = basePriceA + (Math.random() - 0.5) * 20;
    const priceB = basePriceB + (Math.random() - 0.5) * 2;
    const zScore = (spread - baseSpread) / 50;
    
    points.push({
      timestamp: date.getTime(),
      date: date.toISOString().split('T')[0],
      spread: Number(spread.toFixed(2)),
      priceA: Number(priceA.toFixed(2)),
      priceB: Number(priceB.toFixed(2)),
      zScore: Number(zScore.toFixed(2))
    });
  }
  return points;
}

function generateDrawdownData(days: number): DrawdownPoint[] {
  const points: DrawdownPoint[] = [];
  const baseEquity = 1000000;
  let peak = baseEquity;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const trend = (days - i) * 200;
    const noise = Math.sin(i * 0.05) * 30000 + (Math.random() - 0.5) * 15000;
    const equity = baseEquity + trend + noise;
    peak = Math.max(peak, equity);
    const drawdown = peak - equity;
    const drawdownPercent = (drawdown / peak) * 100;
    
    points.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.getTime(),
      equity: Number(equity.toFixed(2)),
      drawdown: Number(drawdown.toFixed(2)),
      drawdownPercent: Number(drawdownPercent.toFixed(2))
    });
  }
  return points;
}

export const mockSpreadPairs: SpreadPair[] = [
  {
    id: 'spread-001',
    name: '白酒龙头价差',
    symbolA: '600519',
    nameA: '贵州茅台',
    symbolB: '000858',
    nameB: '五粮液',
    currentSpread: 150.5,
    spreadChange: -2.3,
    spreadChangePercent: -1.5,
    zScore: -1.8,
    status: 'oversold',
    correlation: 0.85,
    halfLife: 12,
    lastUpdated: '2025-05-04 10:30:00'
  },
  {
    id: 'spread-002',
    name: '银行同业价差',
    symbolA: '601318',
    nameA: '中国平安',
    symbolB: '000001',
    nameB: '平安银行',
    currentSpread: 35.7,
    spreadChange: 0.8,
    spreadChangePercent: 2.3,
    zScore: 2.1,
    status: 'overbought',
    correlation: 0.72,
    halfLife: 8,
    lastUpdated: '2025-05-04 10:28:00'
  },
  {
    id: 'spread-003',
    name: '新能源产业链',
    symbolA: '300750',
    nameA: '宁德时代',
    symbolB: '601012',
    nameB: '隆基绿能',
    currentSpread: 176.5,
    spreadChange: -5.2,
    spreadChangePercent: -2.8,
    zScore: -0.5,
    status: 'normal',
    correlation: 0.68,
    halfLife: 15,
    lastUpdated: '2025-05-04 10:25:00'
  },
  {
    id: 'spread-004',
    name: '食品饮料组合',
    symbolA: '600887',
    nameA: '伊利股份',
    symbolB: '002352',
    nameB: '顺丰控股',
    currentSpread: -13.3,
    spreadChange: 1.5,
    spreadChangePercent: -10.1,
    zScore: 2.8,
    status: 'extreme',
    correlation: 0.45,
    halfLife: 20,
    lastUpdated: '2025-05-04 10:20:00'
  }
];

export function getSpreadHistory(pairId: string): SpreadPoint[] {
  return generateSpreadHistory(pairId, 30);
}

export function getSpreadSignals(): SpreadSignal[] {
  return [
    { pairId: 'spread-001', pairName: '白酒龙头价差', signal: 'long_spread', strength: 0.82, timestamp: '2025-05-04 10:30:00', reason: 'Z-Score触及-2阈值，价差低估' },
    { pairId: 'spread-002', pairName: '银行同业价差', signal: 'short_spread', strength: 0.75, timestamp: '2025-05-04 10:28:00', reason: 'Z-Score突破+2，价差高估' },
    { pairId: 'spread-003', pairName: '新能源产业链', signal: 'hold', strength: 0.35, timestamp: '2025-05-04 10:25:00', reason: '价差处于均值附近，观望' },
    { pairId: 'spread-004', pairName: '食品饮料组合', signal: 'close', strength: 0.90, timestamp: '2025-05-04 10:20:00', reason: '极端偏离，建议平仓锁定收益' }
  ];
}

export function getDrawdownAnalysis(): DrawdownPoint[] {
  return generateDrawdownData(180);
}

export function getRollingMetrics(window: number): RollingMetric[] {
  const metrics: RollingMetric[] = [];
  const days = 90;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const baseSharpe = 1.5 + Math.sin(i * 0.1) * 0.3;
    
    metrics.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.getTime(),
      window,
      sharpeRatio: Number((baseSharpe + (Math.random() - 0.5) * 0.2).toFixed(2)),
      volatility: Number((0.15 + (Math.random() - 0.5) * 0.05).toFixed(3)),
      maxDrawdown: Number((0.12 + (Math.random() - 0.5) * 0.03).toFixed(3)),
      winRate: Number((65 + (Math.random() - 0.5) * 10).toFixed(1))
    });
  }
  return metrics;
}

export function getMonteCarloResult(): MonteCarloResult {
  return {
    simulationCount: 10000,
    finalEquity: { mean: 1250000, min: 850000, max: 1850000, p95: 1650000, p5: 920000 },
    maxDrawdown: { mean: 0.12, min: 0.05, max: 0.28, p95: 0.18, p5: 0.07 },
    probabilityOfProfit: 0.78,
    probabilityOfRuin: 0.02,
    confidenceIntervals: [
      { level: 95, min: 920000, max: 1650000 },
      { level: 90, min: 980000, max: 1580000 },
      { level: 80, min: 1050000, max: 1480000 },
      { level: 50, min: 1150000, max: 1350000 }
    ]
  };
}

export function getEfficientFrontier(): EfficientFrontierPoint[] {
  const points: EfficientFrontierPoint[] = [];
  const assets = ['600519', '000858', '601318', '600036', '300750'];
  
  for (let i = 0; i <= 20; i++) {
    const risk = 0.05 + (i / 20) * 0.25;
    const returnRate = 0.08 + risk * 0.4 + Math.sin(i * 0.3) * 0.02;
    const sharpe = (returnRate - 0.03) / risk;
    const weights: Record<string, number> = {};
    
    assets.forEach((asset, idx) => {
      weights[asset] = Number((0.1 + Math.sin((i + idx) * 0.5) * 0.1).toFixed(3));
    });
    const sum = Object.values(weights).reduce((a, b) => a + b, 0);
    Object.keys(weights).forEach(key => { weights[key] = Number((weights[key] / sum).toFixed(3)); });
    
    points.push({
      return: Number(returnRate.toFixed(3)),
      risk: Number(risk.toFixed(3)),
      sharpeRatio: Number(sharpe.toFixed(2)),
      weights
    });
  }
  return points;
}

export const mockPortfolioAssets: PortfolioAsset[] = [
  { symbol: '600519', name: '贵州茅台', expectedReturn: 0.12, volatility: 0.22, weight: 0.25, currentPrice: 1920.50 },
  { symbol: '000858', name: '五粮液', expectedReturn: 0.10, volatility: 0.25, weight: 0.15, currentPrice: 172.30 },
  { symbol: '601318', name: '中国平安', expectedReturn: 0.08, volatility: 0.18, weight: 0.20, currentPrice: 48.20 },
  { symbol: '600036', name: '招商银行', expectedReturn: 0.09, volatility: 0.16, weight: 0.20, currentPrice: 35.80 },
  { symbol: '300750', name: '宁德时代', expectedReturn: 0.15, volatility: 0.30, weight: 0.20, currentPrice: 215.00 }
];

export function getOptimizationResult(strategy: 'max_sharpe' | 'min_volatility' | 'max_return' | 'equal_weight'): OptimizationResult {
  const weights: PortfolioAsset[] = mockPortfolioAssets.map(asset => {
    let weight = 0.20;
    if (strategy === 'max_sharpe') {
      weight = asset.symbol === '600519' ? 0.35 : (asset.symbol === '300750' ? 0.25 : 0.10);
    } else if (strategy === 'min_volatility') {
      weight = asset.symbol === '600036' ? 0.40 : (asset.symbol === '601318' ? 0.30 : 0.075);
    } else if (strategy === 'max_return') {
      weight = asset.symbol === '300750' ? 0.50 : (asset.symbol === '600519' ? 0.30 : 0.05);
    } else {
      weight = 0.20;
    }
    return { ...asset, weight };
  });
  
  const expectedReturn = strategy === 'max_return' ? 0.135 : (strategy === 'min_volatility' ? 0.085 : 0.115);
  const expectedRisk = strategy === 'min_volatility' ? 0.12 : (strategy === 'max_return' ? 0.22 : 0.16);
  const sharpe = (expectedReturn - 0.03) / expectedRisk;
  
  return {
    strategy,
    expectedReturn: Number(expectedReturn.toFixed(3)),
    expectedRisk: Number(expectedRisk.toFixed(3)),
    sharpeRatio: Number(sharpe.toFixed(2)),
    weights,
    rebalancingCost: 0.0015
  };
}