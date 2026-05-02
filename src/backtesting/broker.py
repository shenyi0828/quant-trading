"""模拟撮合器"""
from datetime import date
from typing import Optional

from data_center.interfaces.data_source import DailyBar
from strategy_engine.types import Order, OrderStatus, Trade, Direction


class Broker:
    commission_rate: float = 0.001
    
    def __init__(self, commission_rate: float = 0.001):
        self.commission_rate = commission_rate
    
    def match_order(self, order: Order, next_bar: DailyBar) -> Optional[Trade]:
        if order.status != OrderStatus.PENDING:
            return None
        
        filled_price = next_bar.open
        
        commission = filled_price * order.quantity * self.commission_rate
        
        trade_id = f"TRD_{order.order_id}"
        trade = Trade(
            trade_id=trade_id,
            order_id=order.order_id,
            symbol=order.symbol,
            direction=order.direction,
            price=filled_price,
            quantity=order.quantity,
            timestamp=next_bar.date,
            commission=commission
        )
        
        order.status = OrderStatus.FILLED
        order.filled_at = next_bar.date
        order.filled_price = filled_price
        
        return trade