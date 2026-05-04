"""价差策略基类 — 参考 vnpy_spreadtrading 的 SpreadStrategyTemplate"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

from spread_trading.types import SpreadData, SpreadSignal, SpreadDefinition


class BaseSpreadStrategy(ABC):
    """价差策略基类

    子类需要实现:
    - on_spread_tick(): 价差 tick 更新时的信号生成
    """

    name: str = "BaseSpreadStrategy"

    def __init__(self, spread_def: SpreadDefinition):
        self.spread_def = spread_def
        self._spread_data: Optional[SpreadData] = None
        self._params: Dict = {}
        self.variables: Dict = {}

    def update_spread(self, spread_data: SpreadData):
        """接收到新的价差数据"""
        self._spread_data = spread_data
        self.on_spread_tick(spread_data)

    def update_leg(self, symbol: str, price: float, volume: float = 0.0):
        """更新价差腿的价格"""
        if symbol in self.spread_def.legs:
            leg = self.spread_def.legs[symbol]
            leg.price = price
            leg.volume = volume

    @abstractmethod
    def on_spread_tick(self, spread_data: SpreadData):
        """价差 tick 回调 — 子类在此生成交易信号"""
        pass

    def get_signal(self) -> Optional[SpreadSignal]:
        """获取当前信号"""
        return self._signal

    def _set_signal(self, signal: Optional[SpreadSignal]):
        self._signal = signal

    @property
    def spread_value(self) -> Optional[float]:
        return self._spread_data.spread_value if self._spread_data else None

    @property
    def z_score(self) -> Optional[float]:
        return self._spread_data.z_score if self._spread_data else None
