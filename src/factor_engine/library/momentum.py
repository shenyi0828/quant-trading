"""动量因子"""
import pandas as pd
import numpy as np
from dataclasses import dataclass

from factor_engine.types import BaseFactor


@dataclass
class ROC(BaseFactor):
    name: str = "ROC"
    period: int = 10
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        roc = (close - close.shift(self.period)) / close.shift(self.period) * 100
        return roc.fillna(0)


@dataclass
class PriceMomentum(BaseFactor):
    name: str = "PriceMomentum"
    period: int = 20
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        returns = close.pct_change()
        momentum = returns.rolling(self.period).mean() * 252
        return momentum.fillna(0)


@dataclass
class MomentumScore(BaseFactor):
    name: str = "MomentumScore"
    period: int = 12
    
    def __post_init__(self):
        self.params = {"period": self.period}
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        close = data["close"]
        
        returns_1m = close.pct_change(20)
        returns_3m = close.pct_change(60)
        returns_6m = close.pct_change(120)
        
        score = returns_1m * 12 + returns_3m * 4 + returns_6m * 2
        return score.fillna(0)