"""组合管理模型定义"""
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AllocationMethod(Enum):
    """资金分配方法"""
    EQUAL_WEIGHT = "equal_weight"      # 等权重分配
    RISK_PARITY = "risk_parity"        # 风险平价分配 (预留)
    MANUAL = "manual"                  # 手动权重指定


class AccountStatus(Enum):
    """子账户状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class PositionInfo:
    """持仓信息"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price

    @property
    def profit(self) -> float:
        """持仓盈亏"""
        return (self.current_price - self.avg_cost) * self.quantity

    @property
    def profit_pct(self) -> float:
        """持仓盈亏百分比"""
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost


@dataclass
class Allocation:
    """资金分配记录"""
    account_id: str
    allocated_capital: float
    weight: float
    method: AllocationMethod
    allocated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SubAccount:
    """策略子账户"""
    account_id: str
    strategy_name: str
    initial_capital: float
    cash: float = field(init=False)
    positions: Dict[str, PositionInfo] = field(default_factory=dict)
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.cash = self.initial_capital

    @property
    def total_value(self) -> float:
        """账户总市值"""
        return self.cash + sum(p.market_value for p in self.positions.values())

    @property
    def total_profit(self) -> float:
        """账户总盈亏"""
        return self.total_value - self.initial_capital

    @property
    def return_rate(self) -> float:
        """收益率"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital

    @property
    def position_profit(self) -> float:
        """持仓盈亏"""
        return sum(p.profit for p in self.positions.values())

    def update_position_price(self, symbol: str, current_price: float):
        """更新持仓价格"""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price

    def get_position(self, symbol: str) -> Optional[PositionInfo]:
        """获取指定持仓"""
        return self.positions.get(symbol)


@dataclass
class DailyPnL:
    """日盈亏记录"""
    date: date
    account_id: str
    start_value: float
    end_value: float
    profit: float
    profit_pct: float


@dataclass
class PortfolioSummary:
    """组合摘要"""
    total_capital: float
    total_value: float
    total_profit: float
    return_rate: float
    account_count: int
    active_accounts: int
    position_count: int
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    positions: List[Dict[str, Any]] = field(default_factory=list)
