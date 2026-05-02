"""回测引擎"""
from datetime import date
from typing import List, Type, Dict, Any, Optional

from data_center.api.data_api import DataAPI
from data_center.interfaces.data_source import DailyBar
from strategy_engine.base import BaseStrategy
from strategy_engine.context import StrategyContext
from strategy_engine.types import Order, OrderStatus
from backtesting.broker import Broker
from backtesting.result import BacktestResult


class BacktestEngine:
    def __init__(
        self, 
        data_api: DataAPI,
        initial_capital: float = 100000,
        commission_rate: float = 0.001
    ):
        self.data_api = data_api
        self.initial_capital = initial_capital
        self.broker = Broker(commission_rate=commission_rate)
        
        self.strategies: List[Dict[str, Any]] = []
        self.context: Optional[StrategyContext] = None
    
    def add_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        symbol: str,
        start_date: date,
        end_date: date,
        params: Optional[Dict[str, Any]] = None
    ):
        self.strategies.append({
            "strategy_class": strategy_class,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "params": params or {}
        })
    
    def run(self) -> BacktestResult:
        if not self.strategies:
            raise ValueError("No strategy added")
        
        config = self.strategies[0]
        strategy_class = config["strategy_class"]
        symbol = config["symbol"]
        start_date = config["start_date"]
        end_date = config["end_date"]
        params = config["params"]
        
        bars = self.data_api.get_daily_bar(symbol, start_date, end_date)
        if not bars:
            raise ValueError(f"No data for {symbol} from {start_date} to {end_date}")
        
        self.context = StrategyContext(initial_capital=self.initial_capital)
        
        strategy = strategy_class(
            name=strategy_class.__name__,
            params=params
        )
        strategy.set_context(self.context)
        strategy.set_symbol(symbol)
        strategy.on_init()
        
        daily_values = [self.initial_capital]
        pending_orders: List[Order] = []
        
        for i, bar in enumerate(bars):
            self.context.current_date = bar.date
            
            for order in pending_orders:
                if order.status == OrderStatus.PENDING:
                    trade = self.broker.match_order(order, bar)
                    if trade:
                        self.context.trades.append(trade)
                        self.context._update_position_from_trade(trade)
                        self.context._update_cash_from_trade(trade)
                        strategy.on_trade(trade)
            
            pending_orders = [o for o in pending_orders if o.status == OrderStatus.PENDING]
            
            strategy.on_bar(bar)
            
            for order in self.context.orders[-5:]:
                if order.status == OrderStatus.PENDING and order not in pending_orders:
                    pending_orders.append(order)
            
            self.context.update_position_price(symbol, bar.close)
            daily_values.append(self.context.total_value)
        
        result = BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_value=self.context.total_value,
            context=self.context,
            daily_values=daily_values
        )
        
        return result