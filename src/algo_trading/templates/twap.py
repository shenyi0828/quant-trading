"""TWAP 算法 - 时间加权平均价格

将委托数量平均分布在时间区域内，按固定间隔分批下单。
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import math

from execution import OrderType
from algo_trading.base import BaseAlgo
from algo_trading.types import TWAPParams


class TWAPAlgo(BaseAlgo):
    """TWAP (Time-Weighted Average Price) 算法
    
    策略逻辑:
    1. 计算总切片数 = total_duration / interval
    2. 每个切片数量 = total_quantity / slice_count
    3. 每隔 interval 分钟下单一个切片
    4. 可设置价格限制，超过限制则暂停下单
    
    适用场景:
    - 大单分批执行，减少市场冲击
    - 需要均匀分布在时间段内
    """
    
    name: str = "TWAP"
    
    def __init__(self, params: TWAPParams, order_manager, on_complete=None):
        super().__init__(params, order_manager, on_complete)
        
        self._twap_params = params
        
        self._slice_count = math.ceil(
            self._twap_params.total_duration / self._twap_params.interval
        )
        if self._slice_count <= 0:
            self._slice_count = 1
        
        self._slice_quantity = math.ceil(
            self._params.total_quantity / self._slice_count
        )
        
        self._next_slice_time: Optional[datetime] = None
        self._current_slice = 0
        self._last_price = 0.0
    
    def on_start(self):
        """初始化 TWAP 拆单参数"""
        self._variables["slice_count"] = self._slice_count
        self._variables["slice_quantity"] = self._slice_quantity
        self._variables["current_slice"] = 0
        
        self._current_slice = 0
        self._next_slice_time = datetime.now()
        
        self._submit_first_slice()
    
    def on_tick(self, tick_data: Dict[str, Any]):
        """处理 Tick 数据，检查是否需要下单"""
        if self._status.value != "running":
            return
        
        price = tick_data.get("price", 0.0)
        self._last_price = price
        
        if self._check_price_limit(price):
            return
        
        now = datetime.now()
        
        if self._next_slice_time and now >= self._next_slice_time:
            self._submit_next_slice()
    
    def on_trade(self, trade):
        """处理成交，更新剩余量"""
        self._variables["remaining"] = self.remaining
    
    def _submit_first_slice(self):
        """提交第一个切片"""
        self._submit_slice()
    
    def _submit_next_slice(self):
        """提交下一个切片"""
        if self.remaining <= 0:
            return
        
        self._submit_slice()
        
        self._next_slice_time = datetime.now() + timedelta(
            minutes=self._twap_params.interval
        )
    
    def _submit_slice(self):
        """提交一个切片订单"""
        quantity = min(self._slice_quantity, self.remaining)
        
        if quantity <= 0:
            return
        
        price = self._calculate_slice_price()
        
        order_id = self.submit_order(
            quantity=quantity,
            price=price,
            order_type=OrderType.LIMIT if price > 0 else OrderType.MARKET,
            reference=f"slice_{self._current_slice}"
        )
        
        if order_id:
            self._current_slice += 1
            self._variables["current_slice"] = self._current_slice
    
    def _calculate_slice_price(self) -> float:
        """计算切片下单价格
        
        使用当前最新价格，如果设置了价格限制则使用限制价格
        """
        if self._twap_params.price_limit:
            return self._twap_params.price_limit
        
        return self._last_price if self._last_price > 0 else 0.0
    
    def _check_price_limit(self, price: float) -> bool:
        """检查价格是否超过限制
        
        Returns:
            True 如果超过限制（暂停下单）
        """
        if not self._twap_params.price_limit:
            return False
        
        if self._params.direction == "buy":
            return price > self._twap_params.price_limit
        else:
            return price < self._twap_params.price_limit
    
    @property
    def slice_count(self) -> int:
        return self._slice_count
    
    @property
    def slice_quantity(self) -> int:
        return self._slice_quantity
    
    @property
    def current_slice(self) -> int:
        return self._current_slice