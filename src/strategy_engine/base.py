"""策略基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from data_center.interfaces.data_source import DailyBar
from strategy_engine.context import StrategyContext
from strategy_engine.types import Direction, Order, Trade


@dataclass
class BaseStrategy(ABC):
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    context: Optional[StrategyContext] = field(default=None, init=False)
    symbol: str = field(default="", init=False)
    
    def set_context(self, context: StrategyContext):
        self.context = context
    
    def set_symbol(self, symbol: str):
        self.symbol = symbol
    
    @abstractmethod
    def on_init(self):
        pass
    
    @abstractmethod
    def on_bar(self, bar: DailyBar):
        pass
    
    def on_trade(self, trade: Trade):
        pass
    
    def buy(self, quantity: int, price: Optional[float] = None) -> Optional[Order]:
        if self.context is None:
            return None
        
        if price is None:
            price = 0.0
        
        required_cash = price * quantity
        if self.context.cash < required_cash:
            quantity = int(self.context.cash / price) if price > 0 else 0
        
        if quantity <= 0:
            return None
        
        order = self.context.create_order(
            symbol=self.symbol,
            direction=Direction.LONG,
            quantity=quantity,
            price=price
        )
        return order
    
    def sell(self, quantity: int, price: Optional[float] = None) -> Optional[Order]:
        if self.context is None:
            return None
        
        position = self.context.get_position(self.symbol)
        if position is None or position.quantity <= 0:
            return None
        
        if quantity > position.quantity:
            quantity = position.quantity
        
        if price is None:
            price = 0.0
        
        order = self.context.create_order(
            symbol=self.symbol,
            direction=Direction.SHORT,
            quantity=quantity,
            price=price
        )
        return order
    
    def get_position_quantity(self) -> int:
        if self.context is None:
            return 0
        position = self.context.get_position(self.symbol)
        return position.quantity if position else 0
    
    def has_position(self) -> bool:
        if self.context is None:
            return False
        return self.context.has_position(self.symbol)