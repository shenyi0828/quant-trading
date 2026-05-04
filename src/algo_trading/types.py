"""算法交易模块类型定义

参考 VeighNa vnpy_algotrading 和 WonderTrader 的算法交易框架设计。
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


class AlgoStatus(Enum):
    """算法状态
    
    状态流转: STOPPED → RUNNING → PAUSED → (COMPLETED/STOPPED)
    """
    STOPPED = "stopped"      # 已停止
    RUNNING = "running"      # 运行中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成（目标达成）
    FAILED = "failed"        # 失败（异常终止)


class AlgoResult(Enum):
    """算法执行结果"""
    SUCCESS = "success"      # 成功完成
    PARTIAL = "partial"      # 部分完成
    TIMEOUT = "timeout"      # 超时终止
    REJECTED = "rejected"    # 被拒绝
    ERROR = "error"          # 执行错误


@dataclass
class AlgoParams:
    """算法参数基类"""
    symbol: str                      # 目标标的
    exchange: str                    # 交易所
    direction: str                   # 交易方向 (buy/sell)
    total_quantity: int              # 总委托数量
    reference: str = ""              # 参考标识


@dataclass
class TWAPParams(AlgoParams):
    """TWAP 算法参数
    
    Time-Weighted Average Price - 时间加权平均价格算法
    将委托数量平均分布在时间区域内，按间隔分批下单。
    """
    total_duration: int = 60         # 总时长（分钟）
    interval: int = 5                # 下单间隔（分钟）
    price_limit: Optional[float] = None  # 价格限制


@dataclass
class VWAPParams(AlgoParams):
    """VWAP 算法参数
    
    Volume-Weighted Average Price - 成交量加权平均价格算法
    跟随市场成交量百分比执行，需要历史成交量数据作为参考。
    """
    target_pov: float = 0.1          # 目标参与率 (Percentage of Volume)
    max_pov: float = 0.3             # 最大参与率限制
    price_limit: Optional[float] = None  # 价格限制


@dataclass
class IcebergParams(AlgoParams):
    """Iceberg 冰山单算法参数
    
    在某个价位只挂部分数量，隐藏真实委托量，成交后自动补单。
    """
    display_quantity: int = 100      # 显示数量（可见部分）
    price: float = 0.0               # 下单价格
    price_offset: float = 0.0        # 价格偏移（tick）
    randomize: bool = False          # 是否随机化显示数量


@dataclass
class AlgoOrder:
    """算法订单跟踪"""
    algo_id: str                     # 算法实例ID
    parent_order_id: str             # 父订单ID（原始大单）
    child_order_id: str              # 子订单ID（拆分后的单）
    slice_index: int                 # 拆单序号
    quantity: int                    # 本次拆单数量
    price: float                     # 本次下单价格
    filled_quantity: int = 0         # 已成交数量
    filled_price: float = 0.0        # 成交均价
    status: str = "pending"          # 子订单状态
    created_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None


@dataclass
class AlgoStatistics:
    """算法执行统计"""
    algo_id: str
    total_quantity: int              # 目标总量
    filled_quantity: int = 0         # 已完成数量
    total_cost: float = 0.0          # 总成交金额
    child_orders: int = 0            # 子订单数
    active_orders: int = 0           # 活跃订单数
    completed_orders: int = 0        # 已完成订单数
    rejected_orders: int = 0         # 拒绝订单数
    created_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0    # 执行时长
    
    @property
    def avg_price(self) -> float:
        if self.filled_quantity <= 0:
            return 0.0
        return self.total_cost / self.filled_quantity
    
    @property
    def fill_rate(self) -> float:
        """完成率"""
        if self.total_quantity == 0:
            return 0.0
        return self.filled_quantity / self.total_quantity
    
    @property
    def is_complete(self) -> bool:
        """是否已完成"""
        return self.filled_quantity >= self.total_quantity


@dataclass
class AlgoInstance:
    """算法实例数据结构"""
    algo_id: str
    algo_name: str                    # 算法名称 (TWAP/VWAP/Iceberg)
    algo_type: str                    # 算法类型
    params: Dict                     # 算法参数
    status: AlgoStatus = AlgoStatus.STOPPED
    statistics: AlgoStatistics = field(default_factory=lambda: AlgoStatistics(algo_id="", total_quantity=0))
    variables: Dict = field(default_factory=dict)  # 算法运行时变量
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None