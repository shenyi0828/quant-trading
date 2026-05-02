"""回测结果"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import date

from strategy_engine.types import Trade
from strategy_engine.context import StrategyContext
from backtesting.metrics import (
    calculate_total_return,
    calculate_annualized_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_trade_metrics,
)


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    final_value: float
    context: StrategyContext
    daily_values: List[float]
    
    @property
    def total_return(self) -> float:
        return calculate_total_return(self.final_value, self.initial_capital)
    
    @property
    def days(self) -> int:
        return len(self.daily_values)
    
    @property
    def annualized_return(self) -> float:
        return calculate_annualized_return(self.total_return, self.days)
    
    @property
    def max_drawdown(self) -> float:
        dd, _, _ = calculate_max_drawdown(self.daily_values)
        return dd
    
    @property
    def trades(self) -> List[Trade]:
        return self.context.trades
    
    @property
    def sharpe_ratio(self) -> float:
        if len(self.daily_values) < 2:
            return 0.0
        daily_returns = [
            (self.daily_values[i] - self.daily_values[i-1]) / self.daily_values[i-1]
            for i in range(1, len(self.daily_values))
            if self.daily_values[i-1] > 0
        ]
        return calculate_sharpe_ratio(daily_returns)
    
    @property
    def trade_metrics(self) -> Dict[str, Any]:
        return calculate_trade_metrics(self.trades)
    
    def print_summary(self):
        print("=" * 60)
        print(f"回测结果: {self.strategy_name} @ {self.symbol}")
        print("=" * 60)
        print(f"时间范围: {self.start_date} ~ {self.end_date} ({self.days} 天)")
        print(f"初始资金: {self.initial_capital:,.2f}")
        print(f"最终市值: {self.final_value:,.2f}")
        print("-" * 60)
        print(f"总收益率:   {self.total_return * 100:.2f}%")
        print(f"年化收益率: {self.annualized_return * 100:.2f}%")
        print(f"最大回撤:   {self.max_drawdown * 100:.2f}%")
        print(f"夏普比率:   {self.sharpe_ratio:.2f}")
        print("-" * 60)
        tm = self.trade_metrics
        print(f"交易次数:   {tm['total_trades']}")
        print(f"胜率:       {tm['win_rate'] * 100:.2f}%")
        print(f"盈亏比:     {tm['profit_loss_ratio']:.2f}")
        print("=" * 60)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "initial_capital": self.initial_capital,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "trade_metrics": self.trade_metrics,
        }