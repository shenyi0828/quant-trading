export type StrategyStatus = 'running' | 'stopped' | 'error';

export interface Strategy {
  id: string;
  name: string;
  status: StrategyStatus;
  totalPnL: number;
  winRate: number;
  totalTrades: number;
  activePositions: number;
  lastUpdated: string;
  runtime: string;
  description: string;
  sharpeRatio: number;
  maxDrawdown: number;
}

export interface Holding {
  symbol: string;
  name: string;
  quantity: number;
  costPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
}

export interface Trade {
  id: string;
  strategyId: string;
  time: string;
  symbol: string;
  name: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  totalAmount: number;
  realizedPnL?: number;
}

export interface EquityPoint {
  date: string;
  timestamp: number;
  equity: number;
  cumulativeReturn: number;
}

export interface StrategyDetail extends Strategy {
  equityCurve: EquityPoint[];
  holdings: Holding[];
  recentTrades: Trade[];
}

export interface DashboardMetrics {
  totalPnL: number;
  activeStrategies: number;
  todayTrades: number;
  openPositions: number;
  dailyReturn: number;
  totalCapital: number;
}

export interface Factor {
  id: string;
  name: string;
  category: 'technical' | 'fundamental' | 'sentiment' | 'risk';
  description: string;
  defaultWeight: number;
}

export interface FactorValue {
  date: string;
  timestamp: number;
  value: number;
  zScore: string;
}

export interface BacktestConfig {
  id: string;
  strategyId: string;
  strategyName: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  commission: number;
  slippage: number;
}

export interface BacktestResult {
  config: BacktestConfig;
  equityCurve: EquityPoint[];
  benchmarkCurve: EquityPoint[];
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
}

export interface BacktestTrade {
  id: string;
  time: string;
  symbol: string;
  name: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  totalAmount: number;
  realizedPnL?: number;
}

export interface Stock {
  symbol: string;
  name: string;
  industry: string;
  marketCap: number;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  pe: number;
  pb: number;
}

export interface StrategySignal {
  symbol: string;
  name: string;
  signal: 'buy' | 'sell' | 'hold';
  strength: number;
  timestamp: string;
}
