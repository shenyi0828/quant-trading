"""DualThrust 突破策略

经典 CTA 策略:
- 上轨 = Open + K1 * range
- 下轨 = Open - K2 * range
- range = max(HH-LC, HC-LL) (前N日)
"""
from typing import List, Dict, Any
from dataclasses import dataclass

from data_center.interfaces.data_source import DailyBar
from strategy_engine.base import BaseStrategy


@dataclass
class DualThrust(BaseStrategy):
    name: str = "DualThrust"
    params: Dict[str, Any] = None
    
    N: int = 4
    K1: float = 0.5
    K2: float = 0.5
    
    range_value: float = 0.0
    upper_track: float = 0.0
    lower_track: float = 0.0
    today_open: float = 0.0
    bars_history: List[DailyBar] = None
    
    def __post_init__(self):
        if self.params:
            self.N = self.params.get("N", 4)
            self.K1 = self.params.get("K1", 0.5)
            self.K2 = self.params.get("K2", 0.5)
        self.bars_history = []
    
    def on_init(self):
        self.bars_history = []
        self.range_value = 0.0
        self.upper_track = 0.0
        self.lower_track = 0.0
    
    def on_bar(self, bar: DailyBar):
        self.bars_history.append(bar)
        
        if len(self.bars_history) < self.N + 1:
            self.context.update_position_price(self.symbol, bar.close)
            return
        
        if len(self.bars_history) == self.N + 1:
            self._calculate_range()
            self.today_open = bar.open
            self.upper_track = self.today_open + self.K1 * self.range_value
            self.lower_track = self.today_open - self.K2 * self.range_value
        
        self.context.update_position_price(self.symbol, bar.close)
        
        if not self.has_position():
            if bar.close >= self.upper_track:
                self.buy(100, bar.close)
            elif bar.close <= self.lower_track:
                self.sell(100, bar.close)
        else:
            position_qty = self.get_position_quantity()
            if position_qty > 0:
                if bar.close <= self.today_open:
                    self.sell(position_qty, bar.close)
            elif position_qty < 0:
                if bar.close >= self.today_open:
                    self.buy(abs(position_qty), bar.close)
    
    def _calculate_range(self):
        lookback_bars = self.bars_history[-self.N:-1]
        
        HH = max(b.high for b in lookback_bars)
        LC = min(b.close for b in lookback_bars)
        HC = max(b.close for b in lookback_bars)
        LL = min(b.low for b in lookback_bars)
        
        self.range_value = max(HH - LC, HC - LL)