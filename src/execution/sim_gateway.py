"""模拟交易网关"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from execution.gateway import ExecutionGateway
from execution.models import Order, OrderRequest, Trade, Position, AccountInfo
from execution.types import OrderStatus


class SimGateway(ExecutionGateway):
    name: str = "sim_gateway"

    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._trades: List[Trade] = []
        self._positions: List[Position] = []
        self._account: AccountInfo = AccountInfo(
            account_id="sim_account",
            gateway_name=self.name,
            balance=1000000.0,
            available=1000000.0,
        )
        self._market_prices: Dict[str, float] = {}
        self._connected: bool = False

    def connect(self, config: Dict[str, Any]) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def set_market_price(self, symbol: str, price: float):
        self._market_prices[symbol] = price

    def submit_order(self, order_request: OrderRequest) -> Optional[str]:
        if not self._connected:
            self._connected = True

        order_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
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
            status=OrderStatus.SUBMITTED,
            time_in_force=order_request.time_in_force,
            stop_price=order_request.stop_price,
            reference=order_request.reference,
            gateway_name=self.name,
            created_at=now,
            updated_at=now,
            submitted_at=now,
        )

        self._orders[order_id] = order

        if order_request.order_type.value == "market":
            price = self._market_prices.get(order_request.symbol, order_request.price or 10.0)
            self._fill_order(order_id, price, order_request.quantity)

        self._emit_order_status(order)
        return order_id

    def cancel_order(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if not order or not order.is_active:
            return False

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        order.cancelled_at = datetime.now()
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
        return self._positions

    def query_account(self) -> Optional[AccountInfo]:
        return self._account

    def query_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        if order_id:
            return [t for t in self._trades if t.order_id == order_id]
        return self._trades

    def _fill_order(self, order_id: str, price: float, quantity: int):
        order = self._orders.get(order_id)
        if not order:
            return

        now = datetime.now()
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

        trade = Trade(
            trade_id=trade_id,
            order_id=order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            direction=order.direction,
            offset=order.offset,
            price=price,
            quantity=quantity,
            commission=price * quantity * 0.0001,
            timestamp=now,
            gateway_name=self.name,
        )

        self._trades.append(trade)

        order.filled_quantity = quantity
        order.filled_price = price
        order.average_price = price
        order.status = OrderStatus.FILLED
        order.updated_at = now
        order.filled_at = now

        self._emit_order_status(order)
        self._emit_trade(trade)