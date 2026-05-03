"""VWAP 算法 - 成交量加权平均价格

跟随市场成交量百分比执行，需要历史成交量数据作为参考。
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import math

from execution import OrderType
from algo_trading.base import BaseAlgo
from algo_trading.types import VWAPParams


class VWAPAlgo(BaseAlgo):
    """VWAP (Volume-Weighted Average Price) 算法
    
    策略逻辑:
    1. 根据目标参与率 (POV) 计算每个时间段应执行的数量
    2. 监控实时成交量，按比例下单
    3. 可设置最大参与率限制，避免过度冲击市场
    4. 需要历史成交量数据作为参考
    
    适用场景:
    - 需要跟随市场成交量分布执行
    - 目标接近 VWAP 价格
    - 成交量分布已知的市场
    """
    
    name: str = "VWAP"
    
    def __init__(
        self,
        params: VWAPParams,
        order_manager,
        on_complete=None,
        volume_profile: Optional[List[Dict]] = None,
    ):
        super().__init__(params, order_manager, on_complete)
        
        self._vwap_params = params
        self._volume_profile = volume_profile or []
        self._interval_seconds = 60
        self._current_interval_volume = 0
        self._last_interval_time: Optional[datetime] = None
        self._last_price = 0.0
        self._interval_target = 0
        self._interval_filled = 0
    
    def on_start(self):
        """初始化 VWAP 参数"""
        if self._volume_profile:
            self._init_from_profile()
        else:
            self._init_default()
        
        self._last_interval_time = datetime.now()
        self._variables["interval_volume"] = 0
        self._variables["interval_target"] = self._interval_target
    
    def on_tick(self, tick_data: Dict[str, Any]):
        """处理 Tick 数据"""
        if self._status.value != "running":
            return
        
        price = tick_data.get("price", 0.0)
        volume = tick_data.get("volume", 0)
        
        self._last_price = price
        self._current_interval_volume += volume
        
        if self._check_price_limit(price):
            return
        
        self._check_interval_execution()
    
    def on_trade(self, trade):
        """处理成交"""
        self._interval_filled += trade.quantity
        self._variables["interval_filled"] = self._interval_filled
    
    def _init_from_profile(self):
        """从历史成交量分布初始化"""
        total_interval = len(self._volume_profile)
        
        if total_interval <= 0:
            self._init_default()
            return
        
        self._interval_target = math.ceil(
            self._params.total_quantity / total_interval
        )
        
        self._variables["volume_profile_loaded"] = True
        self._variables["total_intervals"] = total_interval
    
    def _init_default(self):
        """默认初始化（无历史数据时）"""
        self._interval_target = math.ceil(
            self._params.total_quantity * self._vwap_params.target_pov
        )
        
        self._variables["volume_profile_loaded"] = False
    
    def _check_interval_execution(self):
        """检查是否需要执行订单"""
        now = datetime.now()
        
        if not self._last_interval_time:
            return
        
        elapsed = (now - self._last_interval_time).total_seconds()
        
        if elapsed >= self._interval_seconds:
            self._execute_interval()
            self._last_interval_time = now
            self._current_interval_volume = 0
            self._interval_filled = 0
    
    def _execute_interval(self):
        """执行当前时间段的订单"""
        if self.remaining <= 0:
            return
        
        target_quantity = self._calculate_target_quantity()
        remaining_for_interval = target_quantity - self._interval_filled
        
        if remaining_for_interval <= 0:
            return
        
        quantity = min(remaining_for_interval, self.remaining)
        
        price = self._calculate_execution_price()
        
        order_id = self.submit_order(
            quantity=quantity,
            price=price,
            order_type=OrderType.LIMIT if price > 0 else OrderType.MARKET,
            reference=f"vwap_interval"
        )
        
        if order_id:
            self._variables["interval_orders"] = self._variables.get("interval_orders", 0) + 1
    
    def _calculate_target_quantity(self) -> int:
        """计算当前时间段的目标执行量"""
        if self._volume_profile:
            return self._interval_target
        
        actual_volume = self._current_interval_volume
        
        if actual_volume <= 0:
            return self._interval_target
        
        target_quantity = math.ceil(actual_volume * self._vwap_params.target_pov)
        
        max_quantity = math.ceil(actual_volume * self._vwap_params.max_pov)
        
        target_quantity = min(target_quantity, max_quantity)
        
        target_quantity = min(target_quantity, self.remaining)
        
        return target_quantity
    
    def _calculate_execution_price(self) -> float:
        """计算执行价格"""
        if self._vwap_params.price_limit:
            return self._vwap_params.price_limit
        
        return self._last_price if self._last_price > 0 else 0.0
    
    def _check_price_limit(self, price: float) -> bool:
        """检查价格限制"""
        if not self._vwap_params.price_limit:
            return False
        
        if self._params.direction == "buy":
            return price > self._vwap_params.price_limit
        else:
            return price < self._vwap_params.price_limit
    
    def set_volume_profile(self, profile: List[Dict]):
        """设置历史成交量分布
        
        Args:
            profile: 成交量分布列表，每个元素包含:
                    - interval: 时间段索引
                    - volume: 该时段成交量
                    - percentage: 成交量占比
        """
        self._volume_profile = profile
        self._init_from_profile()
    
    @property
    def target_pov(self) -> float:
        return self._vwap_params.target_pov
    
    @property
    def current_interval_volume(self) -> int:
        return self._current_interval_volume