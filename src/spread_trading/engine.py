"""SpreadEngine — 价差引擎，管理价差策略生命周期"""
from typing import Dict, List, Optional, Callable, Type, Any
from datetime import datetime

from spread_trading.manager import SpreadManager
from spread_trading.base import BaseSpreadStrategy
from spread_trading.types import SpreadData, SpreadDefinition, SpreadSignal


class SpreadEngine:
    """价引擎

    管理价差策略:
    - 注册价差策略实例
    - 接收实时行情 -> 推送给策略
    - 收集交易信号
    """

    def __init__(self, spread_manager: SpreadManager):
        self._spread_manager = spread_manager
        self._strategies: Dict[str, BaseSpreadStrategy] = {}
        self._signals: List[SpreadSignal] = []
        self._signal_callback: Optional[Callable[[SpreadSignal], None]] = None

    def add_strategy(self, spread_id: str, strategy_class: Type[BaseSpreadStrategy], params: Optional[Dict] = None):
        """注册价差策略"""
        spread_def = self._spread_manager.get_spread_definition(spread_id)
        if spread_def is None:
            raise ValueError(f"Spread '{spread_id}' not defined")

        strategy = strategy_class(spread_def)
        if params:
            strategy._params = params

        self._strategies[spread_id] = strategy

    def on_tick(self, symbol: str, price: float, volume: float = 0.0):
        """接收实时行情数据"""
        # 传播到所有涉及该合约的价差
        for spread_id in self._spread_manager.list_spreads():
            spread_def = self._spread_manager.get_spread_definition(spread_id)
            if spread_def and symbol in spread_def.legs:
                self._spread_manager.update_leg_price(spread_id, symbol, price, volume)
                # 更新策略
                if spread_id in self._strategies:
                    spread_data = self._spread_manager.get_spread_data(spread_id)
                    if spread_data:
                        self._strategies[spread_id].update_spread(spread_data)
                        signal = self._strategies[spread_id].get_signal()
                        if signal:
                            self._signals.append(signal)
                            if self._signal_callback:
                                self._signal_callback(signal)

    def set_signal_callback(self, callback: Callable[[SpreadSignal], None]):
        """设置信号回调"""
        self._signal_callback = callback

    def pop_signals(self) -> List[SpreadSignal]:
        """获取并清空当前信号"""
        signals = self._signals[:]
        self._signals = []
        return signals

    def get_strategy(self, spread_id: str) -> Optional[BaseSpreadStrategy]:
        return self._strategies.get(spread_id)

    def get_strategy_variables(self, spread_id: str) -> Dict[str, Any]:
        strategy = self._strategies.get(spread_id)
        if strategy:
            return strategy.variables
        return {}

    @property
    def spread_manager(self) -> SpreadManager:
        return self._spread_manager
