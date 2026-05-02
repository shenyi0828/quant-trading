import type { Strategy, StrategyDetail, Holding, Trade, EquityPoint, DashboardMetrics } from '../types';

const A_SHARE_STOCKS = [
  { symbol: '000001.SZ', name: '平安银行' },
  { symbol: '000002.SZ', name: '万科A' },
  { symbol: '000063.SZ', name: '中兴通讯' },
  { symbol: '000333.SZ', name: '美的集团' },
  { symbol: '000538.SZ', name: '云南白药' },
  { symbol: '000568.SZ', name: '泸州老窖' },
  { symbol: '000651.SZ', name: '格力电器' },
  { symbol: '000725.SZ', name: '京东方A' },
  { symbol: '000858.SZ', name: '五粮液' },
  { symbol: '000895.SZ', name: '双汇发展' },
  { symbol: '002001.SZ', name: '新和成' },
  { symbol: '002007.SZ', name: '华兰生物' },
  { symbol: '002024.SZ', name: '苏宁易购' },
  { symbol: '002027.SZ', name: '分众传媒' },
  { symbol: '002142.SZ', name: '宁波银行' },
  { symbol: '002230.SZ', name: '科大讯飞' },
  { symbol: '002236.SZ', name: '大华股份' },
  { symbol: '002271.SZ', name: '东方雨虹' },
  { symbol: '002304.SZ', name: '洋河股份' },
  { symbol: '002352.SZ', name: '顺丰控股' },
  { symbol: '002415.SZ', name: '海康威视' },
  { symbol: '002460.SZ', name: '赣锋锂业' },
  { symbol: '002475.SZ', name: '立讯精密' },
  { symbol: '002594.SZ', name: '比亚迪' },
  { symbol: '002714.SZ', name: '牧原股份' },
  { symbol: '300003.SZ', name: '乐普医疗' },
  { symbol: '300014.SZ', name: '亿纬锂能' },
  { symbol: '300015.SZ', name: '爱尔眼科' },
  { symbol: '300033.SZ', name: '同花顺' },
  { symbol: '300059.SZ', name: '东方财富' },
  { symbol: '300122.SZ', name: '智飞生物' },
  { symbol: '300124.SZ', name: '汇川技术' },
  { symbol: '300142.SZ', name: '沃森生物' },
  { symbol: '300274.SZ', name: '阳光电源' },
  { symbol: '300408.SZ', name: '三环集团' },
  { symbol: '300413.SZ', name: '芒果超媒' },
  { symbol: '300433.SZ', name: '蓝思科技' },
  { symbol: '300498.SZ', name: '温氏股份' },
  { symbol: '300750.SZ', name: '宁德时代' },
  { symbol: '300760.SZ', name: '迈瑞医疗' },
  { symbol: '300999.SZ', name: '金龙鱼' },
  { symbol: '600000.SH', name: '浦发银行' },
  { symbol: '600009.SH', name: '上海机场' },
  { symbol: '600016.SH', name: '民生银行' },
  { symbol: '600028.SH', name: '中国石化' },
  { symbol: '600030.SH', name: '中信证券' },
  { symbol: '600031.SH', name: '三一重工' },
  { symbol: '600036.SH', name: '招商银行' },
  { symbol: '600048.SH', name: '保利发展' },
  { symbol: '600050.SH', name: '中国联通' },
  { symbol: '600104.SH', name: '上汽集团' },
  { symbol: '600276.SH', name: '恒瑞医药' },
  { symbol: '600309.SH', name: '万华化学' },
  { symbol: '600340.SH', name: '华夏幸福' },
  { symbol: '600519.SH', name: '贵州茅台' },
  { symbol: '600585.SH', name: '海螺水泥' },
  { symbol: '600588.SH', name: '用友网络' },
  { symbol: '600600.SH', name: '青岛啤酒' },
  { symbol: '600660.SH', name: '福耀玻璃' },
  { symbol: '600690.SH', name: '海尔智家' },
  { symbol: '600703.SH', name: '三安光电' },
  { symbol: '600745.SH', name: '闻泰科技' },
  { symbol: '600809.SH', name: '山西汾酒' },
  { symbol: '600837.SH', name: '海通证券' },
  { symbol: '600887.SH', name: '伊利股份' },
  { symbol: '600900.SH', name: '长江电力' },
  { symbol: '601012.SH', name: '隆基绿能' },
  { symbol: '601066.SH', name: '中信建投' },
  { symbol: '601088.SH', name: '中国神华' },
  { symbol: '601111.SH', name: '中国国航' },
  { symbol: '601138.SH', name: '工业富联' },
  { symbol: '601166.SH', name: '兴业银行' },
  { symbol: '601211.SH', name: '国泰君安' },
  { symbol: '601288.SH', name: '农业银行' },
  { symbol: '601318.SH', name: '中国平安' },
  { symbol: '601390.SH', name: '中国中铁' },
  { symbol: '601398.SH', name: '工商银行' },
  { symbol: '601628.SH', name: '中国人寿' },
  { symbol: '601668.SH', name: '中国建筑' },
  { symbol: '601688.SH', name: '华泰证券' },
  { symbol: '601766.SH', name: '中国中车' },
  { symbol: '601818.SH', name: '光大银行' },
  { symbol: '601888.SH', name: '中国中免' },
  { symbol: '601899.SH', name: '紫金矿业' },
  { symbol: '601919.SH', name: '中远海控' },
  { symbol: '601939.SH', name: '建设银行' },
  { symbol: '601988.SH', name: '中国银行' },
  { symbol: '601998.SH', name: '中信银行' },
  { symbol: '603288.SH', name: '海天味业' },
  { symbol: '603501.SH', name: '韦尔股份' },
  { symbol: '603986.SH', name: '兆易创新' },
  { symbol: '603993.SH', name: '洛阳钼业' },
];

function generateEquityCurve(baseEquity: number, days: number, volatility: number, trend: number): EquityPoint[] {
  const data: EquityPoint[] = [];
  let equity = baseEquity;
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  for (let i = days; i >= 0; i--) {
    const timestamp = now - i * oneDay;
    const date = new Date(timestamp).toISOString().split('T')[0];

    const dailyReturn = (Math.random() - 0.5) * volatility + trend / days;
    equity *= (1 + dailyReturn);

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
  activeStrategies: mockStrategies.filter(s => s.status === 'running').length,
  todayTrades: 156,
  openPositions: mockStrategies.filter(s => s.status === 'running').reduce((sum, s) => sum + s.activePositions, 0),
  dailyReturn: 1.24,
  totalCapital: 50000000,
};

export function getStrategyDetail(strategyId: string): StrategyDetail | null {
  const strategy = mockStrategies.find(s => s.id === strategyId);
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
