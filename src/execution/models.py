"""交易执行数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from execution.types import Direction, OrderType, OrderStatus, TimeInForce, Offset, Exchange


@dataclass
class OrderRequest:
    """订单请求（用于创建订单）"""
    symbol: str
    exchange: Exchange
    direction: Direction
    offset: Offset
    order_type: OrderType
    quantity: int
    price: float = 0.0
    time_in_force: TimeInForce = TimeInForce.DAY
    stop_price: float = 0.0
    reference: str = ""


@dataclass
class Order:
    """订单模型"""
    order_id: str
    symbol: str
    exchange: Exchange
    direction: Direction
    offset: Offset
    order_type: OrderType
    quantity: int
    price: float
    status: OrderStatus = OrderStatus.PENDING
    time_in_force: TimeInForce = TimeInForce.DAY
    stop_price: float = 0.0
    filled_quantity: int = 0
    filled_price: float = 0.0
    average_price: float = 0.0
    commission: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    rejected_reason: str = ""
    reference: str = ""
    gateway_name: str = ""
    
    @property
    def is_active(self) -> bool:
        return self.status in {OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL}
    
    @property
    def is_completed(self) -> bool:
        return self.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED}
    
    @property
    def unfilled_quantity(self) -> int:
        return self.quantity - self.filled_quantity
    
    def update_fill(self, filled_quantity: int, filled_price: float, commission: float = 0.0):
        self.filled_quantity += filled_quantity
        self.filled_price = filled_price
        self.total_filled_cost = (self.average_price * (self.filled_quantity - filled_quantity) + filled_price * filled_quantity)
        self.average_price = self.total_filled_cost / self.filled_quantity if self.filled_quantity > 0 else 0.0
        self.commission += commission
        
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    symbol: str
    exchange: Exchange
    direction: Direction
    offset: Offset
    price: float
    quantity: int
    commission: float = 0.0
    timestamp: Optional[datetime] = None
    gateway_name: str = ""


@dataclass
class Position:
    """持仓模型"""
    symbol: str
    exchange: Exchange
    direction: Direction
    quantity: int
    frozen_quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    pnl: float = 0.0
    realized_pnl: float = 0.0
    gateway_name: str = ""
    
    @property
    def available_quantity(self) -> int:
        return self.quantity - self.frozen_quantity
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        if self.direction == Direction.LONG:
            return (self.current_price - self.avg_cost) * self.quantity
        return (self.avg_cost - self.current_price) * self.quantity


@dataclass
class AccountInfo:
    """账户信息"""
    account_id: str
    gateway_name: str
    balance: float = 0.0
    frozen_balance: float = 0.0
    available: float = 0.0
    margin: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    @property
    def total_value(self) -> float:
        return self.balance + self.unrealized_pnl