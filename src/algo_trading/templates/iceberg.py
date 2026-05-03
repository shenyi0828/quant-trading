"""Iceberg 算法 - 冰山单

在某个价位只挂部分数量，隐藏真实委托量，成交后自动补单。
"""
from datetime import datetime
from typing import Dict, Any, Optional
import random

from execution import OrderType, Order
from algo_trading.base import BaseAlgo
from algo_trading.types import IcebergParams


class IcebergAlgo(BaseAlgo):
    """Iceberg 冰山单算法
    
    策略逻辑:
    1. 在指定价位挂 display_quantity 数量的订单
    2. 成交后自动补充新的显示订单
    3. 可随机化显示数量，增加隐蔽性
    4. 直到 total_quantity 完全成交
    
    适用场景:
    - 需要隐藏真实委托量
    - 防止被市场识别大单意图
    - 减少对市场价格的冲击
    """
    
    name: str = "Iceberg"
    
    def __init__(self, params: IcebergParams, order_manager, on_complete=None):
        super().__init__(params, order_manager, on_complete)
        
        self._iceberg_params = params
        self._display_quantity = params.display_quantity
        self._price = params.price
        self._active_display_order: Optional[str] = None
        self._hidden_remaining = params.total_quantity
        self._randomize = params.randomize
    
    def on_start(self):
        """启动冰山单，提交第一个显示订单"""
        self._hidden_remaining = self._params.total_quantity
        self._variables["hidden_remaining"] = self._hidden_remaining
        
        self._submit_display_order()
    
    def on_tick(self, tick_data: Dict[str, Any]):
        """处理 Tick 数据
        
        冰山单主要依赖订单成交回调，Tick 用于价格监控
        """
        if self._status.value != "running":
            return
        
        price = tick_data.get("price", 0.0)
        
        if self._price <= 0:
            self._price = price
    
    def on_order(self, order: Order):
        """处理订单状态"""
        if order.order_id != self._active_display_order:
            return
        
        if order.is_completed:
            self._active_display_order = None
    
    def on_trade(self, trade):
        """处理成交，自动补单"""
        if trade.order_id != self._active_display_order:
            return
        
        self._hidden_remaining -= trade.quantity
        self._variables["hidden_remaining"] = self._hidden_remaining
        
        if self._hidden_remaining > 0:
            self._submit_display_order()
    
    def _submit_display_order(self):
        """提交显示订单"""
        if self._hidden_remaining <= 0:
            return
        
        display_quantity = self._calculate_display_quantity()
        
        if display_quantity <= 0:
            return
        
        price = self._calculate_price()
        
        order_id = self.submit_order(
            quantity=display_quantity,
            price=price,
            order_type=OrderType.LIMIT,
            reference=f"iceberg_display"
        )
        
        if order_id:
            self._active_display_order = order_id
            self._variables["display_orders"] = self._variables.get("display_orders", 0) + 1
            self._variables["last_display_quantity"] = display_quantity
    
    def _calculate_display_quantity(self) -> int:
        """计算本次显示数量
        
        如果随机化启用，显示数量在 50%~100% 之间随机
        """
        base_quantity = min(self._display_quantity, self._hidden_remaining)
        
        if self._randomize and base_quantity > 0:
            min_ratio = 0.5
            max_ratio = 1.0
            ratio = random.uniform(min_ratio, max_ratio)
            return max(1, int(base_quantity * ratio))
        
        return base_quantity
    
    def _calculate_price(self) -> float:
        """计算下单价格
        
        使用固定价格，可加偏移
        """
        if self._price <= 0:
            return 0.0
        
        return self._price + self._iceberg_params.price_offset
    
    def refresh_display_order(self):
        """刷新显示订单
        
        撤销当前显示订单，重新挂单
        """
        if self._active_display_order:
            self.cancel_order(self._active_display_order)
            self._active_display_order = None
        
        self._submit_display_order()
    
    def update_price(self, new_price: float):
        """更新下单价格"""
        self._price = new_price
        
        if self._active_display_order:
            self.refresh_display_order()
    
    @property
    def hidden_remaining(self) -> int:
        return self._hidden_remaining
    
    @property
    def display_quantity(self) -> int:
        return self._display_quantity
    
    @property
    def active_display_order(self) -> Optional[str]:
        return self._active_display_order