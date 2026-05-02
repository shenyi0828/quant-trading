"""量价因子"""
import pandas as pd
import numpy as np
from dataclasses import dataclass

from factor_engine.types import BaseFactor


@dataclass
class VolumeRatio(BaseFactor):
    name: str = "VolumeRatio"
    period: int = 20
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        volume = data["volume"]
        
        avg_volume = volume.rolling(self.period).mean()
        ratio = volume / avg_volume
        
        return ratio.fillna(1)


@dataclass
class OBV(BaseFactor):
    name: str = "OBV"
    
    def __post_init__(self):
        self.params = {}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        volume = data["volume"]
        
        direction = np.sign(close.diff())
        obv = (direction * volume).cumsum()
        
        obv_normalized = obv / obv.rolling(20).mean()
        return obv_normalized.fillna(1)


@dataclass
class VolumePriceTrend(BaseFactor):
    name: str = "VolumePriceTrend"
    period: int = 10
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        volume = data["volume"]
        
        price_change = close.pct_change()
        vpt = (price_change * volume).rolling(self.period).sum()
        vpt_normalized = vpt / volume.rolling(self.period).sum()
        
        return vpt_normalized.fillna(0)


@dataclass
class TurnoverRate(BaseFactor):
    name: str = "TurnoverRate"
    
    def __post_init__(self):
        self.params = {}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        if "turnover_rate" in data.columns:
            return data["turnover_rate"].fillna(0)
        
        volume = data["volume"]
        avg_volume = volume.rolling(20).mean()
        
        turnover = volume / avg_volume * 100
        return turnover.fillna(0)