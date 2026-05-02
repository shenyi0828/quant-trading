"""波动因子"""
import pandas as pd
import numpy as np
from dataclasses import dataclass

from factor_engine.types import BaseFactor


@dataclass
class ATR(BaseFactor):
    name: str = "ATR"
    period: int = 14
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        high = data["high"]
        low = data["low"]
        close = data["close"]
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.period).mean()
        
        atr_pct = atr / close * 100
        return atr_pct.fillna(0)


@dataclass
class HistoricalVolatility(BaseFactor):
    name: str = "HistVolatility"
    period: int = 20
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        returns = close.pct_change()
        
        volatility = returns.rolling(self.period).std() * np.sqrt(252) * 100
        return volatility.fillna(0)


@dataclass
class VolatilityRatio(BaseFactor):
    name: str = "VolatilityRatio"
    short_period: int = 5
    long_period: int = 20
    
    def __post_init__(self):
        self.params = {"short": self.short_period, "long": self.long_period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        returns = close.pct_change()
        
        short_vol = returns.rolling(self.short_period).std()
        long_vol = returns.rolling(self.long_period).std()
        
        ratio = short_vol / long_vol
        return ratio.fillna(1)