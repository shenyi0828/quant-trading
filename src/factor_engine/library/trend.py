"""趋势因子"""
import pandas as pd
import numpy as np
from dataclasses import dataclass

from factor_engine.types import BaseFactor


@dataclass
class MACD(BaseFactor):
    name: str = "MACD"
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    
    def __post_init__(self):
        self.params = {
            "fast": self.fast_period,
            "slow": self.slow_period,
            "signal": self.signal_period
        }
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        histogram = macd_line - signal_line
        return histogram.fillna(0)


@dataclass
class RSI(BaseFactor):
    name: str = "RSI"
    period: int = 14
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(self.period).mean()
        avg_loss = loss.rolling(self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)


@dataclass  
class MACross(BaseFactor):
    name: str = "MACross"
    fast_period: int = 5
    slow_period: int = 20
    
    def __post_init__(self):
        self.params = {"fast": self.fast_period, "slow": self.slow_period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        
        ma_fast = close.rolling(self.fast_period).mean()
        ma_slow = close.rolling(self.slow_period).mean()
        
        cross_signal = (ma_fast - ma_slow) / ma_slow * 100
        return cross_signal.fillna(0)


@dataclass
class TrendStrength(BaseFactor):
    name: str = "TrendStrength"
    period: int = 20
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        
        up_days = (close > close.shift(1)).rolling(self.period).sum()
        total_days = self.period
        
        strength = up_days / total_days * 100
        return strength.fillna(50)