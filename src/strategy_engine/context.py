"""策略上下文 - 资金、持仓、订单管理"""
from datetime import date
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from strategy_engine.types import Order, Trade, Position, Direction, OrderStatus, OrderType


@dataclass
class StrategyContext:
    initial_capital: float
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: List[Order] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    current_date: date = field(default=None)
    
    def __post_init__(self):
        self.cash = self.initial_capital
    
    @property
    def total_value(self) -> float:
        return self.cash + sum(p.market_value for p in self.positions.values())
    
    @property
    def total_profit(self) -> float:
        return self.total_value - self.initial_capital
    
    @property
    def return_rate(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital
    
    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        return symbol in self.positions and self.positions[symbol].quantity > 0
    
    def update_position_price(self, symbol: str, current_price: float):
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
    
    def create_order(
        self, 
        symbol: str, 
        direction: Direction, 
        quantity: int, 
        price: float,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        order_id = f"ORD_{len(self.orders)+1}_{symbol}"
        order = Order(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            order_type=order_type,
            price=price,
            quantity=quantity,
            created_at=self.current_date
        )
        self.orders.append(order)
        return order
    
    def fill_order(self, order: Order, filled_price: float, commission: float = 0.0) -> Trade:
        order.status = OrderStatus.FILLED
        order.filled_at = self.current_date
        order.filled_price = filled_price
        
        trade_id = f"TRD_{len(self.trades)+1}_{order.symbol}"
        trade = Trade(
            trade_id=trade_id,
            order_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            price=filled_price,
            quantity=order.quantity,
            timestamp=self.current_date,
            commission=commission
        )
        self.trades.append(trade)
        
        self._update_position_from_trade(trade)
        self._update_cash_from_trade(trade)
        
        return trade
    
    def _update_position_from_trade(self, trade: Trade):
        symbol = trade.symbol
        
        if trade.direction == Direction.LONG:
            cost = trade.price * trade.quantity + trade.commission
            
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_cost = pos.avg_cost * pos.quantity + cost
                pos.quantity += trade.quantity
                pos.avg_cost = total_cost / pos.quantity
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    direction=Direction.LONG,
                    quantity=trade.quantity,
                    avg_cost=trade.price + trade.commission / trade.quantity
                )
        else:
            if symbol in self.positions:
                pos = self.positions[symbol]
                pos.quantity -= trade.quantity
                
                if pos.quantity <= 0:
                    del self.positions[symbol]
    
    def _update_cash_from_trade(self, trade: Trade):
        if trade.direction == Direction.LONG:
            self.cash -= trade.price * trade.quantity + trade.commission
        else:
            self.cash += trade.price * trade.quantity - trade.commission