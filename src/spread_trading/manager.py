"""SpreadManager — 价差定义管理、价差计算"""
from typing import Dict, List, Optional
from collections import deque, OrderedDict

from spread_trading.types import (
    SpreadDefinition,
    SpreadLeg,
    SpreadData,
    SpreadCalcMethod,
)


class SpreadManager:
    """价差管理器

    负责:
    - 注册价差定义 (多腿合约 + 配比)
    - 接收腿合约行情 -> 自动更新价差
    - 计算当前价差值、Z-Score
    """

    def __init__(self):
        self._definitions: Dict[str, SpreadDefinition] = {}
        self._spread_data: Dict[str, SpreadData] = {}
        self._history_window: int = 60  # 滚动窗口长度 (交易日)
        self._callbacks = {}  # spread_id -> callback

    def add_spread_definition(self, spread: SpreadDefinition):
        """注册价差定义"""
        self._definitions[spread.spread_id] = spread
        self._spread_data[spread.spread_id] = SpreadData(
            spread_id=spread.spread_id,
            spread_value=0.0,
        )

    def get_spread_definition(self, spread_id: str) -> Optional[SpreadDefinition]:
        return self._definitions.get(spread_id)

    def list_spreads(self) -> List[str]:
        return list(self._definitions.keys())

    def update_leg_price(self, spread_id: str, symbol: str, price: float, volume: float = 0.0):
        """更新价差腿的价格 — 触发价差重算"""
        spread_def = self._definitions.get(spread_id)
        if spread_def is None:
            return

        if symbol not in spread_def.legs:
            return

        # 更新腿价格
        leg = spread_def.legs[symbol]
        leg.price = price
        leg.volume = volume

        # 重新计算价差
        if spread_def.is_ready:
            self._calculate_spread(spread_def)

    def _calculate_spread(self, spread_def: SpreadDefinition):
        """计算当前价差"""
        spread_data = self._spread_data[spread_def.spread_id]
        # 使用 sorted keys 确保顺序一致
        sorted_legs = sorted(spread_def.legs.values(), key=lambda l: l.symbol)

        if spread_def.calc_method == SpreadCalcMethod.LINEAR:
            spread_value = sorted_legs[0].price + sorted_legs[0].ratio * sorted_legs[1].price
        elif spread_def.calc_method == SpreadCalcMethod.RATIO:
            spread_value = sorted_legs[0].price / sorted_legs[1].price if sorted_legs[1].price != 0 else 0.0
        elif spread_def.calc_method == SpreadCalcMethod.LOG_RATIO:
            import math
            if sorted_legs[0].price > 0 and sorted_legs[1].price > 0:
                spread_value = math.log(sorted_legs[0].price) - math.log(sorted_legs[1].price)
            else:
                spread_value = 0.0
        else:
            spread_value = 0.0

        spread_data.spread_value = spread_value
        spread_data.price_history.append(spread_value)

        if len(spread_data.price_history) > self._history_window:
            spread_data.price_history = spread_data.price_history[-self._history_window:]

        self._update_statistics(spread_data)

    def _update_statistics(self, spread_data: SpreadData):
        """计算滚动均值、标准差、Z-Score"""
        history = spread_data.price_history
        n = len(history)

        if n < 2:
            spread_data.spread_mean = history[0] if history else 0.0
            spread_data.spread_std = 0.0
            spread_data.z_score = 0.0
            return

        mean = sum(history) / n
        variance = sum((x - mean) ** 2 for x in history) / (n - 1)
        std = variance ** 0.5

        spread_data.spread_mean = mean
        spread_data.spread_std = std
        spread_data.z_score = (spread_data.spread_value - mean) / std if std > 0 else 0.0

    def get_spread_data(self, spread_id: str) -> Optional[SpreadData]:
        return self._spread_data.get(spread_id)

    def set_history_window(self, size: int):
        self._history_window = size

    def remove_spread(self, spread_id: str) -> bool:
        _definitions = self._definitions.pop(spread_id, None)
        self._spread_data.pop(spread_id, None)
        return _definitions is not None
