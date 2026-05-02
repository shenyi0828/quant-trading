"""策略引擎类型定义"""
from enum import Enum
from dataclasses import dataclass
from datetime import date


class Direction(Enum):
    LONG = "long"
    SHORT = "short"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class EventType(Enum):
    BAR = "bar"
    TRADE = "trade"
    ORDER = "order"


@dataclass
class Order:
    order_id: str
    symbol: str
    direction: Direction
    order_type: OrderType
    price: float
    quantity: int
    status: OrderStatus = OrderStatus.PENDING
    created_at: date = None
    filled_at: date = None
    filled_price: float = 0.0


@dataclass
class Trade:
    trade_id: str
    order_id: str
    symbol: str
    direction: Direction
    price: float
    quantity: int
    timestamp: date
    commission: float = 0.0


@dataclass
class Position:
    symbol: str
    direction: Direction
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def profit(self) -> float:
        if self.direction == Direction.LONG:
            return (self.current_price - self.avg_cost) * self.quantity
        else:
            return (self.avg_cost - self.current_price) * self.quantity