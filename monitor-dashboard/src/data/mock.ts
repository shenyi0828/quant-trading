import type {
  Strategy,
  StrategyDetail,
  Holding,
  Trade,
  EquityPoint,
  DashboardMetrics,
} from '../types';

export interface Factor {
  id: string;
  name: string;
  type: 'momentum' | 'trend' | 'volatility' | 'value';
  currentValue: number;
  trend: 'up' | 'down' | 'neutral';
  history: { date: string; value: number }[];
}

export interface FactorHeatmapData {
  stocks: string[];
  factors: string[];
  scores: number[][];
}

export interface BacktestConfig {
  id: string;
  strategyId: string;
  strategyName: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  benchmark: 'CSI300' | 'CSI500' | 'None';
}

export interface BacktestResult extends BacktestConfig {
  finalEquity: number;
  annualReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  totalTrades: number;
  profitFactor: number;
  equityCurve: EquityPoint[];
  benchmarkCurve: EquityPoint[];
  trades: BacktestTrade[];
}

export interface BacktestTrade {
  id: string;
  time: string;
  symbol: string;
  name: string;
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  pnl?: number;
}

export interface StrategyConfig {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  parameters: Record<string, number>;
  signals: Signal[];
  todayPnL: number;
  winRate: number;
  holdings: StrategyHolding[];
}

export interface Signal {
  timestamp: string;
  symbol: string;
  name: string;
  action: 'buy' | 'sell';
  price: number;
}

export interface StrategyHolding {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
}

export interface StockPoolItem {
  symbol: string;
  name: string;
  price: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  industry: string;
  pe: number;
  pb: number;
  inWatchlist: boolean;
}

const A_SHARE_STOCKS = [
  { symbol: '000001.SZ', name: '平安银行', industry: 'Finance' },
  { symbol: '000002.SZ', name: '万科A', industry: 'Real Estate' },
  { symbol: '000063.SZ', name: '中兴通讯', industry: 'Tech' },
  { symbol: '000333.SZ', name: '美的集团', industry: 'Consumer' },
  { symbol: '000538.SZ', name: '云南白药', industry: 'Healthcare' },
  { symbol: '000568.SZ', name: '泸州老窖', industry: 'Consumer' },
  { symbol: '000651.SZ', name: '格力电器', industry: 'Consumer' },
  { symbol: '000725.SZ', name: '京东方A', industry: 'Tech' },
  { symbol: '000858.SZ', name: '五粮液', industry: 'Consumer' },
  { symbol: '000895.SZ', name: '双汇发展', industry: 'Consumer' },
  { symbol: '002001.SZ', name: '新和成', industry: 'Healthcare' },
  { symbol: '002007.SZ', name: '华兰生物', industry: 'Healthcare' },
  { symbol: '002024.SZ', name: '苏宁易购', industry: 'Consumer' },
  { symbol: '002027.SZ', name: '分众传媒', industry: 'Media' },
  { symbol: '002142.SZ', name: '宁波银行', industry: 'Finance' },
  { symbol: '002230.SZ', name: '科大讯飞', industry: 'Tech' },
  { symbol: '002236.SZ', name: '大华股份', industry: 'Tech' },
  { symbol: '002271.SZ', name: '东方雨虹', industry: 'Materials' },
  { symbol: '002304.SZ', name: '洋河股份', industry: 'Consumer' },
  { symbol: '002352.SZ', name: '顺丰控股', industry: 'Logistics' },
  { symbol: '002415.SZ', name: '海康威视', industry: 'Tech' },
  { symbol: '002460.SZ', name: '赣锋锂业', industry: 'Energy' },
  { symbol: '002475.SZ', name: '立讯精密', industry: 'Tech' },
  { symbol: '002594.SZ', name: '比亚迪', industry: 'Auto' },
  { symbol: '002714.SZ', name: '牧原股份', industry: 'Agriculture' },
  { symbol: '300003.SZ', name: '乐普医疗', industry: 'Healthcare' },
  { symbol: '300014.SZ', name: '亿纬锂能', industry: 'Energy' },
  { symbol: '300015.SZ', name: '爱尔眼科', industry: 'Healthcare' },
  { symbol: '300033.SZ', name: '同花顺', industry: 'Finance' },
  { symbol: '300059.SZ', name: '东方财富', industry: 'Finance' },
  { symbol: '300122.SZ', name: '智飞生物', industry: 'Healthcare' },
  { symbol: '300124.SZ', name: '汇川技术', industry: 'Industrials' },
  { symbol: '300142.SZ', name: '沃森生物', industry: 'Healthcare' },
  { symbol: '300274.SZ', name: '阳光电源', industry: 'Energy' },
  { symbol: '300408.SZ', name: '三环集团', industry: 'Tech' },
  { symbol: '300413.SZ', name: '芒果超媒', industry: 'Media' },
  { symbol: '300433.SZ', name: '蓝思科技', industry: 'Tech' },
  { symbol: '300498.SZ', name: '温氏股份', industry: 'Agriculture' },
  { symbol: '300750.SZ', name: '宁德时代', industry: 'Energy' },
  { symbol: '300760.SZ', name: '迈瑞医疗', industry: 'Healthcare' },
  { symbol: '300999.SZ', name: '金龙鱼', industry: 'Consumer' },
  { symbol: '600000.SH', name: '浦发银行', industry: 'Finance' },
  { symbol: '600009.SH', name: '上海机场', industry: 'Transport' },
  { symbol: '600016.SH', name: '民生银行', industry: 'Finance' },
  { symbol: '600028.SH', name: '中国石化', industry: 'Energy' },
  { symbol: '600030.SH', name: '中信证券', industry: 'Finance' },
  { symbol: '600031.SH', name: '三一重工', industry: 'Industrials' },
  { symbol: '600036.SH', name: '招商银行', industry: 'Finance' },
  { symbol: '600048.SH', name: '保利发展', industry: 'Real Estate' },
  { symbol: '600050.SH', name: '中国联通', industry: 'Telecom' },
  { symbol: '600104.SH', name: '上汽集团', industry: 'Auto' },
  { symbol: '600276.SH', name: '恒瑞医药', industry: 'Healthcare' },
  { symbol: '600309.SH', name: '万华化学', industry: 'Materials' },
  { symbol: '600340.SH', name: '华夏幸福', industry: 'Real Estate' },
  { symbol: '600519.SH', name: '贵州茅台', industry: 'Consumer' },
  { symbol: '600585.SH', name: '海螺水泥', industry: 'Materials' },
  { symbol: '600588.SH', name: '用友网络', industry: 'Tech' },
  { symbol: '600600.SH', name: '青岛啤酒', industry: 'Consumer' },
  { symbol: '600660.SH', name: '福耀玻璃', industry: 'Auto' },
  { symbol: '600690.SH', name: '海尔智家', industry: 'Consumer' },
  { symbol: '600703.SH', name: '三安光电', industry: 'Tech' },
  { symbol: '600745.SH', name: '闻泰科技', industry: 'Tech' },
  { symbol: '600809.SH', name: '山西汾酒', industry: 'Consumer' },
  { symbol: '600837.SH', name: '海通证券', industry: 'Finance' },
  { symbol: '600887.SH', name: '伊利股份', industry: 'Consumer' },
  { symbol: '600900.SH', name: '长江电力', industry: 'Utilities' },
  { symbol: '601012.SH', name: '隆基绿能', industry: 'Energy' },
  { symbol: '601066.SH', name: '中信建投', industry: 'Finance' },
  { symbol: '601088.SH', name: '中国神华', industry: 'Energy' },
  { symbol: '601111.SH', name: '中国国航', industry: 'Transport' },
  { symbol: '601138.SH', name: '工业富联', industry: 'Tech' },
  { symbol: '601166.SH', name: '兴业银行', industry: 'Finance' },
  { symbol: '601211.SH', name: '国泰君安', industry: 'Finance' },
  { symbol: '601288.SH', name: '农业银行', industry: 'Finance' },
  { symbol: '601318.SH', name: '中国平安', industry: 'Finance' },
  { symbol: '601390.SH', name: '中国中铁', industry: 'Industrials' },
  { symbol: '601398.SH', name: '工商银行', industry: 'Finance' },
  { symbol: '601628.SH', name: '中国人寿', industry: 'Finance' },
  { symbol: '601668.SH', name: '中国建筑', industry: 'Industrials' },
  { symbol: '601688.SH', name: '华泰证券', industry: 'Finance' },
  { symbol: '601766.SH', name: '中国中车', industry: 'Industrials' },
  { symbol: '601818.SH', name: '光大银行', industry: 'Finance' },
  { symbol: '601888.SH', name: '中国中免', industry: 'Consumer' },
  { symbol: '601899.SH', name: '紫金矿业', industry: 'Materials' },
  { symbol: '601919.SH', name: '中远海控', industry: 'Transport' },
  { symbol: '601939.SH', name: '建设银行', industry: 'Finance' },
  { symbol: '601988.SH', name: '中国银行', industry: 'Finance' },
  { symbol: '601998.SH', name: '中信银行', industry: 'Finance' },
  { symbol: '603288.SH', name: '海天味业', industry: 'Consumer' },
  { symbol: '603501.SH', name: '韦尔股份', industry: 'Tech' },
  { symbol: '603986.SH', name: '兆易创新', industry: 'Tech' },
  { symbol: '603993.SH', name: '洛阳钼业', industry: 'Materials' },
];

function generateEquityCurve(
  baseEquity: number,
  days: number,
  volatility: number,
  trend: number
): EquityPoint[] {
  const data: EquityPoint[] = [];
  let equity = baseEquity;
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  for (let i = days; i >= 0; i--) {
    const timestamp = now - i * oneDay;
    const date = new Date(timestamp).toISOString().split('T')[0];

    const dailyReturn = (Math.random() - 0.5) * volatility + trend / days;
    equity *= 1 + dailyReturn;

    data.push({
      date,
      timestamp,
      equity: Math.round(equity * 100) / 100,
      cumulativeReturn: Math.round(((equity - baseEquity) / baseEquity) * 10000) / 100,
    });
  }

  return data;
}

function generateHoldings(_strategyId: string, count: number): Holding[] {
  const holdings: Holding[] = [];
  const shuffled = [...A_SHARE_STOCKS].sort(() => Math.random() - 0.5);

  for (let i = 0; i < count; i++) {
    const stock = shuffled[i % shuffled.length];
    const costPrice = Math.round((Math.random() * 100 + 10) * 100) / 100;
    const priceChange = (Math.random() - 0.45) * 0.2;
    const currentPrice = Math.round(costPrice * (1 + priceChange) * 100) / 100;
    const quantity = Math.floor(Math.random() * 5000 + 100);
    const marketValue = Math.round(currentPrice * quantity * 100) / 100;
    const unrealizedPnL = Math.round((currentPrice - costPrice) * quantity * 100) / 100;
    const unrealizedPnLPercent = Math.round(((currentPrice - costPrice) / costPrice) * 10000) / 100;

    holdings.push({
      symbol: stock.symbol,
      name: stock.name,
      quantity,
      costPrice,
      currentPrice,
      marketValue,
      unrealizedPnL,
      unrealizedPnLPercent,
    });
  }

  return holdings;
}

function generateTrades(strategyId: string, count: number): Trade[] {
  const trades: Trade[] = [];
  const now = Date.now();
  const shuffled = [...A_SHARE_STOCKS].sort(() => Math.random() - 0.5);

  for (let i = 0; i < count; i++) {
    const stock = shuffled[i % shuffled.length];
    const price = Math.round((Math.random() * 100 + 10) * 100) / 100;
    const quantity = Math.floor(Math.random() * 1000 + 100);
    const side: 'buy' | 'sell' = Math.random() > 0.5 ? 'buy' : 'sell';
    const totalAmount = Math.round(price * quantity * 100) / 100;
    const timestamp = now - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000);

    trades.push({
      id: `T-${strategyId}-${i}`,
      strategyId,
      time: new Date(timestamp).toISOString(),
      symbol: stock.symbol,
      name: stock.name,
      side,
      quantity,
      price,
      totalAmount,
      realizedPnL: side === 'sell' ? Math.round((Math.random() - 0.3) * 5000 * 100) / 100 : undefined,
    });
  }

  return trades.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
}

export const mockStrategies: Strategy[] = [
  {
    id: 'strat-001',
    name: 'Alpha Momentum',
    status: 'running',
    totalPnL: 2456789.56,
    winRate: 62.5,
    totalTrades: 1256,
    activePositions: 8,
    lastUpdated: new Date().toISOString(),
    runtime: '45d 12h 34m',
    description: 'Multi-factor momentum strategy targeting high-alpha stocks',
    sharpeRatio: 1.85,
    maxDrawdown: -8.3,
  },
  {
    id: 'strat-002',
    name: 'Mean Reversion',
    status: 'running',
    totalPnL: 1289456.23,
    winRate: 58.2,
    totalTrades: 2341,
    activePositions: 12,
    lastUpdated: new Date().toISOString(),
    runtime: '32d 8h 15m',
    description: 'Statistical arbitrage based on price deviation from moving average',
    sharpeRatio: 1.42,
    maxDrawdown: -5.7,
  },
  {
    id: 'strat-003',
    name: 'Breakout Hunter',
    status: 'stopped',
    totalPnL: 567234.89,
    winRate: 45.8,
    totalTrades: 892,
    activePositions: 0,
    lastUpdated: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    runtime: '15d 6h 22m',
    description: 'Volatility breakout detection with adaptive position sizing',
    sharpeRatio: 0.95,
    maxDrawdown: -12.4,
  },
  {
    id: 'strat-004',
    name: 'Pairs Trading',
    status: 'running',
    totalPnL: 876543.12,
    winRate: 67.3,
    totalTrades: 567,
    activePositions: 6,
    lastUpdated: new Date().toISOString(),
    runtime: '28d 14h 45m',
    description: 'Cointegration-based pairs trading across sector leaders',
    sharpeRatio: 2.12,
    maxDrawdown: -3.2,
  },
  {
    id: 'strat-005',
    name: 'Volatility Arbitrage',
    status: 'error',
    totalPnL: -123456.78,
    winRate: 38.5,
    totalTrades: 423,
    activePositions: 0,
    lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    runtime: '8d 3h 12m',
    description: 'Options implied vs realized volatility convergence',
    sharpeRatio: -0.45,
    maxDrawdown: -18.9,
  },
  {
    id: 'strat-006',
    name: 'Factor Model',
    status: 'running',
    totalPnL: 1567890.45,
    winRate: 59.8,
    totalTrades: 1876,
    activePositions: 15,
    lastUpdated: new Date().toISOString(),
    runtime: '56d 9h 18m',
    description: 'Multi-factor risk model with dynamic factor exposure',
    sharpeRatio: 1.68,
    maxDrawdown: -6.4,
  },
];

export const mockDashboardMetrics: DashboardMetrics = {
  totalPnL: mockStrategies.reduce((sum, s) => sum + s.totalPnL, 0),
  activeStrategies: mockStrategies.filter((s) => s.status === 'running').length,
  todayTrades: 156,
  openPositions: mockStrategies
    .filter((s) => s.status === 'running')
    .reduce((sum, s) => sum + s.activePositions, 0),
  dailyReturn: 1.24,
  totalCapital: 50000000,
};

function generateFactorHistory(baseValue: number, days: number, volatility: number): { date: string; value: number }[] {
  const data: { date: string; value: number }[] = [];
  let value = baseValue;
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  for (let i = days; i >= 0; i--) {
    const timestamp = now - i * oneDay;
    const date = new Date(timestamp).toISOString().split('T')[0];
    const change = (Math.random() - 0.5) * volatility;
    value *= 1 + change;
    data.push({ date, value: Math.round(value * 100) / 100 });
  }

  return data;
}

export const mockFactors: Factor[] = [
  {
    id: 'f-momentum-1m',
    name: '1M Momentum',
    type: 'momentum',
    currentValue: 1.25,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.05),
  },
  {
    id: 'f-momentum-3m',
    name: '3M Momentum',
    type: 'momentum',
    currentValue: 0.98,
    trend: 'down',
    history: generateFactorHistory(1.0, 30, 0.03),
  },
  {
    id: 'f-trend-sma',
    name: 'SMA20 Trend',
    type: 'trend',
    currentValue: 1.15,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.04),
  },
  {
    id: 'f-trend-ema',
    name: 'EMA12 Trend',
    type: 'trend',
    currentValue: 1.08,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.035),
  },
  {
    id: 'f-vol-atr',
    name: 'ATR Volatility',
    type: 'volatility',
    currentValue: 0.85,
    trend: 'down',
    history: generateFactorHistory(1.0, 30, 0.08),
  },
  {
    id: 'f-vol-bb',
    name: 'Bollinger Width',
    type: 'volatility',
    currentValue: 1.32,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.06),
  },
  {
    id: 'f-value-pe',
    name: 'PE Ratio',
    type: 'value',
    currentValue: 0.92,
    trend: 'neutral',
    history: generateFactorHistory(1.0, 30, 0.02),
  },
  {
    id: 'f-value-pb',
    name: 'PB Ratio',
    type: 'value',
    currentValue: 0.88,
    trend: 'down',
    history: generateFactorHistory(1.0, 30, 0.025),
  },
  {
    id: 'f-value-roe',
    name: 'ROE Quality',
    type: 'value',
    currentValue: 1.45,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.04),
  },
  {
    id: 'f-momentum-rs',
    name: 'Relative Strength',
    type: 'momentum',
    currentValue: 1.18,
    trend: 'up',
    history: generateFactorHistory(1.0, 30, 0.045),
  },
];

export function generateFactorHeatmap(): FactorHeatmapData {
  const stocks = A_SHARE_STOCKS.slice(0, 15).map((s) => s.symbol);
  const factors = mockFactors.map((f) => f.name);
  const scores: number[][] = [];

  for (let i = 0; i < stocks.length; i++) {
    const row: number[] = [];
    for (let j = 0; j < factors.length; j++) {
      row.push(Math.round((Math.random() * 2 - 1) * 100) / 100);
    }
    scores.push(row);
  }

  return { stocks, factors, scores };
}

export const mockBacktestConfigs: BacktestConfig[] = [
  {
    id: 'bt-001',
    strategyId: 'strat-001',
    strategyName: 'Alpha Momentum',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
    initialCapital: 10000000,
    benchmark: 'CSI300',
  },
  {
    id: 'bt-002',
    strategyId: 'strat-002',
    strategyName: 'Mean Reversion',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
    initialCapital: 5000000,
    benchmark: 'CSI500',
  },
  {
    id: 'bt-003',
    strategyId: 'strat-004',
    strategyName: 'Pairs Trading',
    startDate: '2024-02-01',
    endDate: '2024-07-31',
    initialCapital: 8000000,
    benchmark: 'None',
  },
  {
    id: 'bt-004',
    strategyId: 'strat-006',
    strategyName: 'Factor Model',
    startDate: '2024-01-01',
    endDate: '2024-08-31',
    initialCapital: 15000000,
    benchmark: 'CSI300',
  },
];

function generateBacktestTrades(strategyId: string, count: number): BacktestTrade[] {
  const trades: BacktestTrade[] = [];
  const now = Date.now();
  const shuffled = [...A_SHARE_STOCKS].sort(() => Math.random() - 0.5);

  for (let i = 0; i < count; i++) {
    const stock = shuffled[i % shuffled.length];
    const price = Math.round((Math.random() * 100 + 10) * 100) / 100;
    const quantity = Math.floor(Math.random() * 1000 + 100);
    const side: 'buy' | 'sell' = Math.random() > 0.5 ? 'buy' : 'sell';
    const timestamp = now - Math.floor(Math.random() * 180 * 24 * 60 * 60 * 1000);

    trades.push({
      id: `BT-${strategyId}-${i}`,
      time: new Date(timestamp).toISOString(),
      symbol: stock.symbol,
      name: stock.name,
      side,
      price,
      quantity,
      pnl: side === 'sell' ? Math.round((Math.random() - 0.35) * 10000 * 100) / 100 : undefined,
    });
  }

  return trades.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
}

export function getBacktestResult(configId: string): BacktestResult | null {
  const config = mockBacktestConfigs.find((c) => c.id === configId);
  if (!config) return null;

  const isPositive = config.strategyId !== 'strat-005';
  const volatility = isPositive ? 0.015 : 0.03;
  const trend = isPositive ? 0.12 : -0.08;

  const equityCurve = generateEquityCurve(config.initialCapital, 180, volatility, trend);
  const benchmarkCurve = generateEquityCurve(config.initialCapital, 180, 0.012, 0.08);

  const finalEquity = equityCurve[equityCurve.length - 1].equity;
  const totalReturn = (finalEquity - config.initialCapital) / config.initialCapital;
  const annualReturn = totalReturn * (365 / 180) * 100;

  let maxDrawdown = 0;
  let peak = config.initialCapital;
  for (const point of equityCurve) {
    if (point.equity > peak) peak = point.equity;
    const drawdown = (peak - point.equity) / peak;
    if (drawdown > maxDrawdown) maxDrawdown = drawdown;
  }

  const trades = generateBacktestTrades(config.strategyId, 50);
  const winningTrades = trades.filter((t) => t.pnl && t.pnl > 0).length;
  const totalTrades = trades.filter((t) => t.pnl !== undefined).length;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 50;

  const grossProfit = trades.filter((t) => t.pnl && t.pnl > 0).reduce((sum, t) => sum + (t.pnl || 0), 0);
  const grossLoss = Math.abs(trades.filter((t) => t.pnl && t.pnl < 0).reduce((sum, t) => sum + (t.pnl || 0), 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;

  const dailyReturns = equityCurve.map((p, i) => (i > 0 ? (p.equity - equityCurve[i - 1].equity) / equityCurve[i - 1].equity : 0));
  const avgReturn = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
  const variance = dailyReturns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / dailyReturns.length;
  const stdDev = Math.sqrt(variance);
  const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0;

  return {
    ...config,
    finalEquity,
    annualReturn: Math.round(annualReturn * 100) / 100,
    maxDrawdown: Math.round(maxDrawdown * 10000) / 100,
    sharpeRatio: Math.round(sharpeRatio * 100) / 100,
    winRate: Math.round(winRate * 100) / 100,
    totalTrades: trades.length,
    profitFactor: Math.round(profitFactor * 100) / 100,
    equityCurve,
    benchmarkCurve,
    trades,
  };
}

export function getAllBacktestResults(): BacktestResult[] {
  return mockBacktestConfigs.map((c) => getBacktestResult(c.id)!).filter(Boolean);
}

const strategyTypes = ['Momentum', 'Mean Reversion', 'Breakout', 'Arbitrage', 'Multi-Factor', 'ML Model'];

const strategyParameters: Record<string, Record<string, number>> = {
  'strat-001': { lookbackPeriod: 20, positionSize: 0.1, stopLoss: 0.05, takeProfit: 0.15, maxPositions: 10 },
  'strat-002': { lookbackPeriod: 50, zScoreThreshold: 2.0, positionSize: 0.08, stopLoss: 0.03, maxPositions: 15 },
  'strat-003': { volatilityWindow: 20, breakoutThreshold: 1.5, positionSize: 0.12, stopLoss: 0.04, maxPositions: 8 },
  'strat-004': { correlationWindow: 60, entryThreshold: 2.5, exitThreshold: 0.5, positionSize: 0.06, maxPairs: 5 },
  'strat-005': { ivWindow: 30, rvWindow: 20, spreadThreshold: 0.15, positionSize: 0.1, maxPositions: 6 },
  'strat-006': { factorLookback: 63, rebalanceFreq: 5, positionSize: 0.15, riskTarget: 0.1, maxPositions: 20 },
};

function generateSignals(_strategyId: string, count: number): Signal[] {
  const signals: Signal[] = [];
  const now = Date.now();
  const shuffled = [...A_SHARE_STOCKS].sort(() => Math.random() - 0.5);

  for (let i = 0; i < count; i++) {
    const stock = shuffled[i % shuffled.length];
    const price = Math.round((Math.random() * 100 + 10) * 100) / 100;
    const action: 'buy' | 'sell' = Math.random() > 0.5 ? 'buy' : 'sell';
    const timestamp = now - Math.floor(Math.random() * 7 * 24 * 60 * 60 * 1000);

    signals.push({
      timestamp: new Date(timestamp).toISOString(),
      symbol: stock.symbol,
      name: stock.name,
      action,
      price,
    });
  }

  return signals.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

function generateStrategyHoldings(strategyId: string, count: number): StrategyHolding[] {
  const holdings: StrategyHolding[] = [];
  const shuffled = [...A_SHARE_STOCKS].sort(() => Math.random() - 0.5);
  const strategy = mockStrategies.find((s) => s.id === strategyId);
  const activeCount = strategy?.status === 'running' ? count : 0;

  for (let i = 0; i < activeCount; i++) {
    const stock = shuffled[i % shuffled.length];
    const avgPrice = Math.round((Math.random() * 100 + 10) * 100) / 100;
    const priceChange = (Math.random() - 0.4) * 0.15;
    const currentPrice = Math.round(avgPrice * (1 + priceChange) * 100) / 100;
    const quantity = Math.floor(Math.random() * 2000 + 100);
    const marketValue = Math.round(currentPrice * quantity * 100) / 100;
    const unrealizedPnL = Math.round((currentPrice - avgPrice) * quantity * 100) / 100;

    holdings.push({
      symbol: stock.symbol,
      name: stock.name,
      quantity,
      avgPrice,
      currentPrice,
      marketValue,
      unrealizedPnL,
    });
  }

  return holdings;
}

export function getStrategyConfigs(): StrategyConfig[] {
  return mockStrategies.map((s, index) => ({
    id: s.id,
    name: s.name,
    type: strategyTypes[index % strategyTypes.length],
    enabled: s.status === 'running',
    parameters: strategyParameters[s.id] || {},
    signals: generateSignals(s.id, 15),
    todayPnL: Math.round((Math.random() - 0.4) * 50000 * 100) / 100,
    winRate: s.winRate,
    holdings: generateStrategyHoldings(s.id, s.activePositions),
  }));
}

export function getStrategyConfig(strategyId: string): StrategyConfig | null {
  const strategy = mockStrategies.find((s) => s.id === strategyId);
  if (!strategy) return null;

  const index = mockStrategies.findIndex((s) => s.id === strategyId);

  return {
    id: strategy.id,
    name: strategy.name,
    type: strategyTypes[index % strategyTypes.length],
    enabled: strategy.status === 'running',
    parameters: strategyParameters[strategy.id] || {},
    signals: generateSignals(strategy.id, 20),
    todayPnL: Math.round((Math.random() - 0.4) * 50000 * 100) / 100,
    winRate: strategy.winRate,
    holdings: generateStrategyHoldings(strategy.id, strategy.activePositions),
  };
}

const industries = ['Tech', 'Finance', 'Consumer', 'Healthcare', 'Energy', 'Materials', 'Industrials', 'Auto', 'Real Estate'];

export function getStockPool(): StockPoolItem[] {
  return A_SHARE_STOCKS.map((stock) => {
    const basePrice = Math.random() * 80 + 10;
    const changePercent = (Math.random() - 0.45) * 10;
    const price = Math.round(basePrice * 100) / 100;
    const volume = Math.floor(Math.random() * 10000000 + 1000000);
    const marketCap = Math.floor(Math.random() * 500000000000 + 10000000000);
    const pe = Math.round((Math.random() * 40 + 5) * 10) / 10;
    const pb = Math.round((Math.random() * 5 + 0.5) * 10) / 10;

    return {
      symbol: stock.symbol,
      name: stock.name,
      price,
      changePercent: Math.round(changePercent * 100) / 100,
      volume,
      marketCap,
      industry: stock.industry || industries[Math.floor(Math.random() * industries.length)],
      pe,
      pb,
      inWatchlist: Math.random() > 0.7,
    };
  });
}

export function getWatchlist(): StockPoolItem[] {
  return getStockPool().filter((s) => s.inWatchlist);
}

export function getStrategyDetail(strategyId: string): StrategyDetail | null {
  const strategy = mockStrategies.find((s) => s.id === strategyId);
  if (!strategy) return null;

  const baseEquity = 10000000;
  const volatility = strategy.status === 'error' ? 0.05 : 0.02;
  const trend = strategy.totalPnL > 0 ? 0.15 : -0.1;

  return {
    ...strategy,
    equityCurve: generateEquityCurve(baseEquity, 30, volatility, trend),
    holdings: strategy.status !== 'error' ? generateHoldings(strategyId, strategy.activePositions) : [],
    recentTrades: generateTrades(strategyId, 20),
  };
}

export function getAllStrategies(): Strategy[] {
  return mockStrategies;
}

export function getDashboardMetrics(): DashboardMetrics {
  return mockDashboardMetrics;
}
