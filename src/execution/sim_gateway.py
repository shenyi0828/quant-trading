"""模拟交易网关

用于开发测试的模拟交易网关，支持：
- 按当前市价立即成交（简化撮合）
- 手续费计算
- 持仓和账户管理
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable

from execution.gateway import ExecutionGateway
from execution.models import Order, OrderRequest, Trade, Position, AccountInfo
from execution.types import OrderStatus, OrderType, Direction, Offset, Exchange


class SimGateway(ExecutionGateway):
    name = "SIM"
    
    def __init__(
        self,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0,
    ):
        self._connected = False
        self._initial_capital = initial_capital
        self._commission_rate = commission_rate
        self._slippage_rate = slippage_rate
        
        self._orders: Dict[str, Order] = {}
        self._trades: List[Trade] = []
        self._positions: Dict[str, Position] = {}
        self._account: Optional[AccountInfo] = None
        
        self._market_prices: Dict[str, float] = {}
        self._order_counter = 0
        self._trade_counter = 0
    
    def set_market_price(self, symbol: str, price: float):
        self._market_prices[symbol] = price
    
    def connect(self, config: Dict[str, Any]) -> bool:
        self._connected = True
        self._account = AccountInfo(
            account_id="SIM_ACCOUNT",
            gateway_name=self.name,
            balance=self._initial_capital,
            available=self._initial_capital,
        )
        return True
    
    def disconnect(self) -> bool:
        self._connected = False
        return True
    
    def is_connected(self) -> bool:
        return self._connected
    
    def submit_order(self, order_request: OrderRequest) -> Optional[str]:
        if not self._connected:
            return None
        
        if order_request.quantity <= 0:
            return None
        
        if order_request.symbol not in self._market_prices:
            return None
        
        self._order_counter += 1
        order_id = f"SIM_ORD_{self._order_counter}"
        
        now = datetime.now()
        order = Order(
            order_id=order_id,
            symbol=order_request.symbol,
            exchange=order_request.exchange,
            direction=order_request.direction,
            offset=order_request.offset,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
            time_in_force=order_request.time_in_force,
            stop_price=order_request.stop_price,
            reference=order_request.reference,
            gateway_name=self.name,
            status=OrderStatus.SUBMITTED,
            created_at=now,
            submitted_at=now,
        )
        
        self._orders[order_id] = order
        
        self._emit_order_status(order)
        
        self._match_order(order)
        
        return order_id
    
    def cancel_order(self, order_id: str) -> bool:
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        if not order.is_active:
            return False
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now()
        order.updated_at = datetime.now()
        
        self._emit_order_status(order)
        
        return True
    
    def query_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)
    
    def query_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
    
    def query_positions(self) -> List[Position]:
        return list(self._positions.values())
    
    def query_account(self) -> Optional[AccountInfo]:
        if self._account:
            self._account.unrealized_pnl = sum(
                pos.unrealized_pnl for pos in self._positions.values()
            )
        return self._account
    
    def query_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        if order_id:
            return [t for t in self._trades if t.order_id == order_id]
        return self._trades
    
    def _match_order(self, order: Order):
        if order.status != OrderStatus.SUBMITTED:
            return
        
        market_price = self._market_prices.get(order.symbol)
        if market_price is None:
            order.status = OrderStatus.REJECTED
            order.rejected_reason = "No market price available"
            order.updated_at = datetime.now()
            self._emit_order_status(order)
            return
        
        if order.order_type == OrderType.MARKET:
            filled_price = market_price * (1 + self._slippage_rate)
            if order.direction == Direction.SHORT:
                filled_price = market_price * (1 - self._slippage_rate)
            
            self._execute_order(order, filled_price)
        
        elif order.order_type == OrderType.LIMIT:
            if order.direction == Direction.LONG and market_price <= order.price:
                self._execute_order(order, order.price)
            elif order.direction == Direction.SHORT and market_price >= order.price:
                self._execute_order(order, order.price)
    
    def _execute_order(self, order: Order, filled_price: float):
        commission = filled_price * order.quantity * self._commission_rate
        
        now = datetime.now()
        self._trade_counter += 1
        trade_id = f"SIM_TRD_{self._trade_counter}"
        
        trade = Trade(
            trade_id=trade_id,
            order_id=order.order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            direction=order.direction,
            offset=order.offset,
            price=filled_price,
            quantity=order.quantity,
            commission=commission,
            timestamp=now,
            gateway_name=self.name,
        )
        
        self._trades.append(trade)
        
        order.filled_quantity = order.quantity
        order.filled_price = filled_price
        order.average_price = filled_price
        order.commission = commission
        order.status = OrderStatus.FILLED
        order.filled_at = now
        order.updated_at = now
        
        self._emit_trade(trade)
        self._emit_order_status(order)
        
        self._update_position(trade)
        self._update_account(trade)
    
    def _update_position(self, trade: Trade):
        key = f"{trade.symbol}.{trade.exchange.value}"
        
        if trade.offset == Offset.OPEN:
            if trade.direction == Direction.LONG:
                if key in self._positions:
                    pos = self._positions[key]
                    total_cost = pos.avg_cost * pos.quantity + trade.price * trade.quantity
                    pos.quantity += trade.quantity
                    pos.avg_cost = total_cost / pos.quantity
                else:
                    self._positions[key] = Position(
                        symbol=trade.symbol,
                        exchange=trade.exchange,
                        direction=Direction.LONG,
                        quantity=trade.quantity,
                        avg_cost=trade.price,
                        current_price=self._market_prices.get(trade.symbol, trade.price),
                        gateway_name=self.name,
                    )
        elif trade.offset == Offset.CLOSE:
            if key in self._positions:
                pos = self._positions[key]
                pos.quantity -= trade.quantity
                if pos.quantity <= 0:
                    del self._positions[key]
        
        for pos in self._positions.values():
            if pos.symbol in self._market_prices:
                pos.current_price = self._market_prices[pos.symbol]
        
        if key in self._positions:
            self._emit_position(self._positions[key])
    
    def _update_account(self, trade: Trade):
        if self._account is None:
            return
        
        if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
            self._account.balance -= trade.price * trade.quantity + trade.commission
        elif trade.direction == Direction.SHORT and trade.offset == Offset.CLOSE:
            self._account.balance += trade.price * trade.quantity - trade.commission
        
        self._account.available = self._account.balance
        self._emit_account(self._account)