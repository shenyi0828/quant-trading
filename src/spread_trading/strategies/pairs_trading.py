"""配对交易策略 — 统计套利
"""
from typing import Optional

from spread_trading.base import BaseSpreadStrategy
from spread_trading.types import SpreadData, SpreadSignal, SpreadSide


class PairsTradingStrategy(BaseSpreadStrategy):
    """配对交易统计套利策略

    基于 Z-Score 的均值回归策略:
    - Z-Score < -entry_threshold -> 做多价差
    - Z-Score > +entry_threshold -> 做空价差
    - |Z-Score| < exit_threshold -> 平仓
    """

    name: str = "PairsTradingStrategy"

    def on_spread_tick(self, spread_data: SpreadData):
        z = spread_data.z_score

        entry_threshold = self._params.get("entry_threshold", 2.0)
        exit_threshold = self._params.get("exit_threshold", 0.5)

        if z < -entry_threshold:
            signal = SpreadSignal(
                spread_id=spread_data.spread_id,
                side=SpreadSide.LONG_SPREAD,
                strength=min(abs(z) / 5.0, 1.0),
                z_score=z,
                target_spread=spread_data.spread_value,
            )
            self._set_signal(signal)
        elif z > entry_threshold:
            signal = SpreadSignal(
                spread_id=spread_data.spread_id,
                side=SpreadSide.SHORT_SPREAD,
                strength=min(abs(z) / 5.0, 1.0),
                z_score=z,
                target_spread=spread_data.spread_value,
            )
            self._set_signal(signal)
        elif abs(z) < exit_threshold:
            self._set_signal(None)  # 离场信号
        else:
            self._set_signal(None)  # 无信号

        # 更新变量
        self.variables["z_score"] = z
        self.variables["spread_value"] = spread_data.spread_value
        self.variables["spread_mean"] = spread_data.spread_mean
        self.variables["spread_std"] = spread_data.spread_std
