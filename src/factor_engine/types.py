"""因子引擎类型定义"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class BaseFactor(ABC):
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        pass
    
    def validate_input(self, data: pd.DataFrame) -> bool:
        required = ["open", "high", "low", "close", "volume"]
        return all(col in data.columns for col in required)


@dataclass
class FactorResult:
    factor_name: str
    values: pd.Series
    normalized_values: Optional[pd.Series] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class SignalResult:
    date: pd.Timestamp
    score: float
    signal: int  # 1: buy, -1: sell, 0: hold
    rank: Optional[int] = None
    bucket: Optional[int] = None  # 十分位分组 1-10