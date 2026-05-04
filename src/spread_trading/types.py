"""价差交易类型定义"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


class SpreadCalcMethod(Enum):
    """价差计算方法"""
    LINEAR = "linear"          # 线性价差 = A + ratio * B
    RATIO = "ratio"            # 比值价差 = A / B
    LOG_RATIO = "log_ratio"    # 对数比值价差 = ln(A) - ln(B)


class SpreadSide(Enum):
    """价差交易方向"""
    LONG_SPREAD = "long_spread"    # 做多价差
    SHORT_SPREAD = "short_spread"  # 做空价差


@dataclass
class SpreadLeg:
    """价差腿 — 构成价差的单一合约"""
    symbol: str                # 合约代码
    price: float = 0.0         # 最新价
    volume: float = 0.0        # 成交量
    ratio: float = 1.0         # 配比系数


@dataclass
class SpreadDefinition:
    """价差定义"""
    spread_id: str             # 价差唯一标识
    name: str = ""             # 价差名称
    calc_method: SpreadCalcMethod = SpreadCalcMethod.LINEAR
    legs: Dict[str, SpreadLeg] = field(default_factory=dict)

    @property
    def is_ready(self) -> bool:
        return len(self.legs) >= 2 and all(
            leg.price > 0 for leg in self.legs.values()
        )


@dataclass
class SpreadData:
    """实时价差数据"""
    spread_id: str
    spread_value: float        # 当前价差
    spread_mean: float = 0.0   # 均值 (滚动)
    spread_std: float = 0.0    # 标准差 (滚动)
    z_score: float = 0.0       # Z-Score
    timestamp: Optional[datetime] = None
    price_history: List[float] = field(default_factory=list)  # 价差历史


@dataclass
class SpreadSignal:
    """价差交易信号"""
    spread_id: str
    side: SpreadSide
    strength: float            # 信号强度 (0-1)
    z_score: float
    target_spread: float       # 目标价差
    timestamp: Optional[datetime] = None
