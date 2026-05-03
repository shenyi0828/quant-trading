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
