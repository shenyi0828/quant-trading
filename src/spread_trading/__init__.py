"""Spread Trading Module — 参考 vnpy_spreadtrading 架构"""
from spread_trading.manager import SpreadManager, SpreadLeg, SpreadDefinition
from spread_trading.engine import SpreadEngine
from spread_trading.base import BaseSpreadStrategy
from spread_trading.strategies.pairs_trading import PairsTradingStrategy

__all__ = [
    "SpreadManager",
    "SpreadLeg",
    "SpreadDefinition",
    "SpreadEngine",
    "BaseSpreadStrategy",
    "PairsTradingStrategy",
]
