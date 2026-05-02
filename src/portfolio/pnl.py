"""盈亏计算器"""
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from portfolio.models import DailyPnL, SubAccount


@dataclass
class PnLSnapshot:
    account_id: str
    date: date
    total_value: float
    cash: float
    position_value: float
    position_profit: float
    daily_profit: float = 0.0
    cumulative_profit: float = 0.0
    return_rate: float = 0.0


class PnLCalculator:
    def __init__(self):
        self.daily_records: Dict[str, List[DailyPnL]] = {}
        self.snapshots: Dict[str, List[PnLSnapshot]] = {}
        self._prev_values: Dict[str, float] = {}

    def calculate_account_pnl(
        self,
        account: SubAccount,
        current_date: date
    ) -> PnLSnapshot:
        account_id = account.account_id
        position_value = sum(p.market_value for p in account.positions.values())
        position_profit = sum(p.profit for p in account.positions.values())

        prev_value = self._prev_values.get(account_id, account.initial_capital)
        daily_profit = account.total_value - prev_value

        snapshot = PnLSnapshot(
            account_id=account_id,
            date=current_date,
            total_value=account.total_value,
            cash=account.cash,
            position_value=position_value,
            position_profit=position_profit,
            daily_profit=daily_profit,
            cumulative_profit=account.total_profit,
            return_rate=account.return_rate
        )

        self._prev_values[account_id] = account.total_value

        if account_id not in self.snapshots:
            self.snapshots[account_id] = []
        self.snapshots[account_id].append(snapshot)

        daily_pnl = DailyPnL(
            date=current_date,
            account_id=account_id,
            start_value=prev_value,
            end_value=account.total_value,
            profit=daily_profit,
            profit_pct=daily_profit / prev_value if prev_value > 0 else 0.0
        )

        if account_id not in self.daily_records:
            self.daily_records[account_id] = []
        self.daily_records[account_id].append(daily_pnl)

        return snapshot

    def calculate_portfolio_pnl(
        self,
        accounts: List[SubAccount],
        current_date: date
    ) -> Dict[str, PnLSnapshot]:
        results = {}
        for account in accounts:
            if account.status.value == "active":
                results[account.account_id] = self.calculate_account_pnl(account, current_date)
        return results

    def get_account_daily_pnl(self, account_id: str) -> List[DailyPnL]:
        return self.daily_records.get(account_id, [])

    def get_account_snapshots(self, account_id: str) -> List[PnLSnapshot]:
        return self.snapshots.get(account_id, [])

    def get_total_cumulative_pnl(self, accounts: List[SubAccount]) -> float:
        return sum(a.total_profit for a in accounts if a.status.value == "active")

    def get_total_daily_pnl(self, date: Optional[date] = None) -> float:
        total = 0.0
        for records in self.daily_records.values():
            if date:
                matching = [r for r in records if r.date == date]
                total += sum(r.profit for r in matching)
            else:
                if records:
                    total += records[-1].profit
        return total

    def get_aggregated_positions_pnl(self, accounts: List[SubAccount]) -> Dict[str, float]:
        aggregated: Dict[str, float] = {}
        for account in accounts:
            if account.status.value == "active":
                for symbol, pos in account.positions.items():
                    if symbol not in aggregated:
                        aggregated[symbol] = 0.0
                    aggregated[symbol] += pos.profit
        return aggregated

    def get_dashboard_data(self, accounts: List[SubAccount]) -> Dict:
        active_accounts = [a for a in accounts if a.status.value == "active"]

        return {
            "total_value": sum(a.total_value for a in active_accounts),
            "total_profit": sum(a.total_profit for a in active_accounts),
            "total_return_rate": self._calculate_portfolio_return_rate(active_accounts),
            "account_pnl": {
                a.account_id: {
                    "value": a.total_value,
                    "profit": a.total_profit,
                    "return_rate": a.return_rate,
                }
                for a in active_accounts
            },
            "position_pnl": self.get_aggregated_positions_pnl(accounts),
        }

    def _calculate_portfolio_return_rate(self, accounts: List[SubAccount]) -> float:
        if not accounts:
            return 0.0
        total_initial = sum(a.initial_capital for a in accounts)
        total_current = sum(a.total_value for a in accounts)
        if total_initial == 0:
            return 0.0
        return (total_current - total_initial) / total_initial

    def clear_records(self, account_id: Optional[str] = None):
        if account_id:
            self.daily_records.pop(account_id, None)
            self.snapshots.pop(account_id, None)
            self._prev_values.pop(account_id, None)
        else:
            self.daily_records.clear()
            self.snapshots.clear()
            self._prev_values.clear()
