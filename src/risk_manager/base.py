"""风控模块基础类型定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from strategy_engine.types import Order, Position


class RiskAction(Enum):
    """风控动作"""
    ACCEPT = "accept"
    REJECT = "reject"
    WARN = "warn"


@dataclass
class RiskResult:
    """风控检查结果"""
    action: RiskAction
    rule_name: str
    message: str = ""
    details: Dict = field(default_factory=dict)
    
    @property
    def is_accepted(self) -> bool:
        """是否通过检查"""
        return self.action == RiskAction.ACCEPT
    
    @property
    def is_rejected(self) -> bool:
        """是否被拒绝"""
        return self.action == RiskAction.REJECT


@dataclass
class RiskContext:
    """风控检查上下文
    
    包含进行风控检查所需的所有账户和持仓信息
    """
    # 账户信息
    total_capital: float  # 总资金
    available_cash: float  # 可用现金
    initial_capital: float  # 初始资金
    
    # 持仓信息
    positions: Dict[str, Position] = field(default_factory=dict)  # symbol -> Position
    
    # 当日交易信息
    daily_pnl: float = 0.0  # 当日已实现盈亏
    daily_trades: int = 0  # 当日交易次数
    daily_orders: List[Order] = field(default_factory=list)  # 当日订单列表
    
    # 日期
    current_date: Optional[date] = None
    
    # 风控参数 (可由外部设置)
    risk_params: Dict = field(default_factory=dict)
    
    @property
    def total_position_value(self) -> float:
        """持仓总市值"""
        return sum(p.market_value for p in self.positions.values())
    
    @property
    def total_value(self) -> float:
        """总资产 = 现金 + 持仓市值"""
        return self.available_cash + self.total_position_value
    
    @property
    def total_profit(self) -> float:
        """总盈亏"""
        return self.total_value - self.initial_capital
    
    @property
    def return_rate(self) -> float:
        """收益率"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital
    
    @property
    def daily_return_rate(self) -> float:
        """当日收益率"""
        if self.initial_capital == 0:
            return 0.0
        return self.daily_pnl / self.initial_capital
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定股票的持仓"""
        return self.positions.get(symbol)
    
    def get_position_value(self, symbol: str) -> float:
        """获取指定股票的持仓市值"""
        pos = self.get_position(symbol)
        return pos.market_value if pos else 0.0
    
    def get_position_weight(self, symbol: str) -> float:
        """获取指定股票的持仓权重"""
        if self.total_value == 0:
            return 0.0
        return self.get_position_value(symbol) / self.total_value


class RiskRule(ABC):
    """风控规则抽象基类
    
    所有风控规则必须继承此类并实现 check 方法
    """
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self._enabled = enabled
    
    @property
    def enabled(self) -> bool:
        """规则是否启用"""
        return self._enabled
    
    def enable(self):
        """启用规则"""
        self._enabled = True
    
    def disable(self):
        """禁用规则"""
        self._enabled = False
    
    @abstractmethod
    def check(self, order: Order, context: RiskContext) -> RiskResult:
        """检查订单是否满足风控规则
        
        Args:
            order: 待检查的订单
            context: 风控上下文，包含账户和持仓信息
            
        Returns:
            RiskResult: 风控检查结果
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, enabled={self._enabled})"