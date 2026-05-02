"""订单管理器

OrderManager 负责订单的创建、修改、撤销和生命周期管理，
参考 WonderTrader 的 M+1+N 执行架构中的订单管理设计。
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

from execution.gateway import ExecutionGateway
from execution.models import Order, OrderRequest, Trade, Position
from execution.types import OrderStatus, Direction, Offset, OrderType, TimeInForce, Exchange


class OrderManager:
    """订单生命周期管理
    
    负责：
    - 订单创建和提交
    - 订单状态追踪
    - 订单修改和撤销
    - 与 StrategyContext 集成
    """
    
    def __init__(self, gateway: ExecutionGateway):
        self._gateway = gateway
        self._pending_orders: Dict[str, OrderRequest] = {}
        self._active_orders: Dict[str, Order] = {}
        self._all_orders: Dict[str, Order] = {}
        self._order_counter = 0
        
        self._gateway.on_order_status(self._on_order_status)
        self._gateway.on_trade(self._on_trade)
        
        self._order_callbacks: List[Callable[[Order], None]] = []
        self._trade_callbacks: List[Callable[[Trade], None]] = []
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        self._order_callbacks.append(callback)
    
    def register_trade_callback(self, callback: Callable[[Trade], None]):
        self._trade_callbacks.append(callback)
    
    def create_order(
        self,
        symbol: str,
        exchange: Exchange,
        direction: Direction,
        offset: Offset,
        quantity: int,
        price: float = 0.0,
        order_type: OrderType = OrderType.MARKET,
        time_in_force: TimeInForce = TimeInForce.DAY,
        reference: str = "",
    ) -> Optional[str]:
        if quantity <= 0:
            return None
        
        if price < 0:
            return None
        
        request = OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            offset=offset,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            reference=reference,
        )
        
        order_id = self._gateway.submit_order(request)
        if order_id:
            self._order_counter += 1
            self._pending_orders[order_id] = request
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self._active_orders:
            return False
        
        return self._gateway.cancel_order(order_id)
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        cancelled_count = 0
        
        for order_id, order in list(self._active_orders.items()):
            if symbol and order.symbol != symbol:
                continue
            
            if self._gateway.cancel_order(order_id):
                cancelled_count += 1
        
        return cancelled_count
    
    def query_order(self, order_id: str) -> Optional[Order]:
        return self._gateway.query_order(order_id)
    
    def query_active_orders(self) -> List[Order]:
        return [o for o in self._all_orders.values() if o.is_active]
    
    def query_orders_by_status(self, status: OrderStatus) -> List[Order]:
        return [o for o in self._all_orders.values() if o.status == status]
    
    def query_orders_by_symbol(self, symbol: str) -> List[Order]:
        return [o for o in self._all_orders.values() if o.symbol == symbol]
    
    def query_positions(self) -> List[Position]:
        return self._gateway.query_positions()
    
    def query_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        return self._gateway.query_trades(order_id)
    
    def get_position(self, symbol: str, direction: Direction) -> Optional[Position]:
        positions = self._gateway.query_positions()
        for pos in positions:
            if pos.symbol == symbol and pos.direction == direction:
                return pos
        return None
    
    def has_position(self, symbol: str) -> bool:
        positions = self._gateway.query_positions()
        return any(pos.symbol == symbol and pos.quantity > 0 for pos in positions)
    
    def get_available_quantity(self, symbol: str, direction: Direction) -> int:
        pos = self.get_position(symbol, direction)
        if pos:
            return pos.available_quantity
        return 0
    
    def _on_order_status(self, order: Order):
        if order.order_id not in self._all_orders:
            self._all_orders[order.order_id] = order
        
        if order.order_id in self._pending_orders:
            del self._pending_orders[order.order_id]
        
        if order.is_active:
            self._active_orders[order.order_id] = order
        elif order.order_id in self._active_orders:
            del self._active_orders[order.order_id]
        
        for callback in self._order_callbacks:
            callback(order)
    
    def _on_trade(self, trade: Trade):
        for callback in self._trade_callbacks:
            callback(trade)
    
    def update_market_price(self, symbol: str, price: float):
        set_price_method = getattr(self._gateway, 'set_market_price', None)
        if set_price_method:
            set_price_method(symbol, price)