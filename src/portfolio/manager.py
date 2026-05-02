"""组合管理器"""
from datetime import date
from typing import Any, Dict, List, Optional

from portfolio.allocation import AllocationEngine
from portfolio.models import (
    AccountStatus,
    Allocation,
    AllocationMethod,
    PortfolioSummary,
    PositionInfo,
    SubAccount,
)
from portfolio.pnl import PnLCalculator, PnLSnapshot


class PortfolioManager:
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        self.accounts: Dict[str, SubAccount] = {}
        self.allocation_engine = AllocationEngine(total_capital)
        self.pnl_calculator = PnLCalculator()
        self._account_counter = 0

    def create_account(
        self,
        strategy_name: str,
        initial_capital: Optional[float] = None,
        account_id: Optional[str] = None
    ) -> SubAccount:
        if account_id is None:
            self._account_counter += 1
            account_id = f"ACC_{self._account_counter}_{strategy_name}"

        if initial_capital is None:
            allocation = self.allocation_engine.get_allocation(account_id)
            initial_capital = allocation.allocated_capital if allocation else 0.0

        account = SubAccount(
            account_id=account_id,
            strategy_name=strategy_name,
            initial_capital=initial_capital
        )

        self.accounts[account_id] = account
        return account

    def remove_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            account = self.accounts[account_id]
            account.status = AccountStatus.CLOSED
            self.pnl_calculator.clear_records(account_id)
            return True
        return False

    def pause_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            self.accounts[account_id].status = AccountStatus.PAUSED
            return True
        return False

    def resume_account(self, account_id: str) -> bool:
        if account_id in self.accounts:
            self.accounts[account_id].status = AccountStatus.ACTIVE
            return True
        return False

    def get_account(self, account_id: str) -> Optional[SubAccount]:
        return self.accounts.get(account_id)

    def get_active_accounts(self) -> List[SubAccount]:
        return [a for a in self.accounts.values() if a.status == AccountStatus.ACTIVE]

    def allocate_capital(
        self,
        method: AllocationMethod = AllocationMethod.EQUAL_WEIGHT,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Allocation]:
        account_ids = list(self.accounts.keys())

        if method == AllocationMethod.EQUAL_WEIGHT:
            return self.allocation_engine.equal_weight(account_ids)
        elif method == AllocationMethod.MANUAL:
            if weights is None:
                raise ValueError("Manual allocation requires weights dict")
            return self.allocation_engine.manual_weights(weights)
        elif method == AllocationMethod.RISK_PARITY:
            return self.allocation_engine.risk_parity(account_ids)
        else:
            raise ValueError(f"Unknown allocation method: {method}")

    def update_position(
        self,
        account_id: str,
        symbol: str,
        quantity: int,
        avg_cost: float,
        current_price: float = 0.0
    ) -> Optional[PositionInfo]:
        account = self.get_account(account_id)
        if account is None:
            return None

        position = PositionInfo(
            symbol=symbol,
            quantity=quantity,
            avg_cost=avg_cost,
            current_price=current_price
        )
        account.positions[symbol] = position
        return position

    def update_position_prices(self, prices: Dict[str, float]):
        for account in self.accounts.values():
            for symbol, price in prices.items():
                account.update_position_price(symbol, price)

    def update_all_prices(self, account_id: str, prices: Dict[str, float]):
        account = self.get_account(account_id)
        if account:
            for symbol, price in prices.items():
                account.update_position_price(symbol, price)

    def calculate_pnl(self, current_date: Optional[date] = None) -> Dict[str, PnLSnapshot]:
        if current_date is None:
            current_date = date.today()

        active_accounts = self.get_active_accounts()
        return self.pnl_calculator.calculate_portfolio_pnl(active_accounts, current_date)

    def get_aggregated_positions(self) -> Dict[str, PositionInfo]:
        aggregated: Dict[str, PositionInfo] = {}

        for account in self.get_active_accounts():
            for symbol, pos in account.positions.items():
                if symbol in aggregated:
                    existing = aggregated[symbol]
                    total_cost = existing.avg_cost * existing.quantity + pos.avg_cost * pos.quantity
                    total_qty = existing.quantity + pos.quantity
                    existing.quantity = total_qty
                    existing.avg_cost = total_cost / total_qty if total_qty > 0 else 0.0
                else:
                    aggregated[symbol] = PositionInfo(
                        symbol=symbol,
                        quantity=pos.quantity,
                        avg_cost=pos.avg_cost,
                        current_price=pos.current_price
                    )

        return aggregated

    def get_summary(self) -> PortfolioSummary:
        active_accounts = self.get_active_accounts()
        total_value = sum(a.total_value for a in active_accounts)
        total_profit = sum(a.total_profit for a in active_accounts)

        aggregated_positions = self.get_aggregated_positions()

        account_summaries = [
            {
                "account_id": a.account_id,
                "strategy_name": a.strategy_name,
                "total_value": a.total_value,
                "profit": a.total_profit,
                "return_rate": a.return_rate,
                "status": a.status.value,
            }
            for a in active_accounts
        ]

        position_summaries = [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "avg_cost": p.avg_cost,
                "current_price": p.current_price,
                "market_value": p.market_value,
                "profit": p.profit,
            }
            for p in aggregated_positions.values()
        ]

        return PortfolioSummary(
            total_capital=self.total_capital,
            total_value=total_value,
            total_profit=total_profit,
            return_rate=total_profit / self.total_capital if self.total_capital > 0 else 0.0,
            account_count=len(self.accounts),
            active_accounts=len(active_accounts),
            position_count=len(aggregated_positions),
            accounts=account_summaries,
            positions=position_summaries,
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        return self.pnl_calculator.get_dashboard_data(list(self.accounts.values()))

    def rebalance(self, method: AllocationMethod = AllocationMethod.EQUAL_WEIGHT):
        account_ids = list(self.accounts.keys())
        allocations = self.allocation_engine.rebalance(account_ids, method)

        for account_id, allocation in allocations.items():
            account = self.accounts.get(account_id)
            if account:
                pass

        return allocations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_capital": self.total_capital,
            "account_count": len(self.accounts),
            "accounts": [
                {
                    "account_id": a.account_id,
                    "strategy_name": a.strategy_name,
                    "initial_capital": a.initial_capital,
                    "total_value": a.total_value,
                    "profit": a.total_profit,
                    "return_rate": a.return_rate,
                    "status": a.status.value,
                    "positions": {
                        s: {
                            "quantity": p.quantity,
                            "avg_cost": p.avg_cost,
                            "current_price": p.current_price,
                            "profit": p.profit,
                        }
                        for s, p in a.positions.items()
                    }
                }
                for a in self.accounts.values()
            ],
        }
