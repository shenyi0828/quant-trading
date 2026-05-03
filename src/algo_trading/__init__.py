"""算法交易模块

提供 TWAP/VWAP/Iceberg 等算法交易模板，
参考 VeighNa vnpy_algotrading 和 WonderTrader 的设计模式。

模块结构:
- base.py: BaseAlgo 基类，定义算法生命周期
- engine.py: AlgoEngine，管理算法实例
- manager.py: AlgoOrderManager，管理拆单生命周期
- templates/: 具体算法实现 (TWAP, VWAP, Iceberg)
- types.py: 类型定义
"""
from algo_trading.types import (
    AlgoStatus,
    AlgoResult,
    AlgoParams,
    TWAPParams,
    VWAPParams,
    IcebergParams,
    AlgoOrder,
    AlgoStatistics,
    AlgoInstance,
)
from algo_trading.base import BaseAlgo
from algo_trading.engine import AlgoEngine
from algo_trading.manager import AlgoOrderManager

__all__ = [
    # 类型
    "AlgoStatus",
    "AlgoResult",
    "AlgoParams",
    "TWAPParams",
    "VWAPParams",
    "IcebergParams",
    "AlgoOrder",
    "AlgoStatistics",
    "AlgoInstance",
    # 核心
    "BaseAlgo",
    "AlgoEngine",
    "AlgoOrderManager",
]