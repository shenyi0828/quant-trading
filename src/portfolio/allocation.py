"""资金分配引擎"""
from datetime import datetime
from typing import Dict, List, Optional

from portfolio.models import Allocation, AllocationMethod


class AllocationEngine:
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        self.allocations: Dict[str, Allocation] = {}

    def equal_weight(self, account_ids: List[str]) -> Dict[str, Allocation]:
        if not account_ids:
            return {}

        weight = 1.0 / len(account_ids)
        allocated_capital = self.total_capital * weight

        for account_id in account_ids:
            self.allocations[account_id] = Allocation(
                account_id=account_id,
                allocated_capital=allocated_capital,
                weight=weight,
                method=AllocationMethod.EQUAL_WEIGHT,
                allocated_at=datetime.now()
            )

        return self.allocations

    def manual_weights(self, weights: Dict[str, float]) -> Dict[str, Allocation]:
        total_weight = sum(weights.values())
        if total_weight <= 0:
            raise ValueError("Total weight must be positive")

        normalized_weights = {
            account_id: w / total_weight for account_id, w in weights.items()
        }

        for account_id, weight in normalized_weights.items():
            self.allocations[account_id] = Allocation(
                account_id=account_id,
                allocated_capital=self.total_capital * weight,
                weight=weight,
                method=AllocationMethod.MANUAL,
                allocated_at=datetime.now()
            )

        return self.allocations

    def risk_parity(self, account_ids: List[str]) -> Dict[str, Allocation]:
        raise NotImplementedError(
            "Risk parity allocation is not implemented yet. "
            "Use equal_weight or manual_weights instead."
        )

    def get_allocation(self, account_id: str) -> Optional[Allocation]:
        return self.allocations.get(account_id)

    def get_allocated_capital(self, account_id: str) -> float:
        allocation = self.allocations.get(account_id)
        return allocation.allocated_capital if allocation else 0.0

    def rebalance(
        self,
        account_ids: List[str],
        method: AllocationMethod = AllocationMethod.EQUAL_WEIGHT
    ):
        if method == AllocationMethod.EQUAL_WEIGHT:
            return self.equal_weight(account_ids)
        elif method == AllocationMethod.RISK_PARITY:
            return self.risk_parity(account_ids)
        else:
            raise ValueError(f"Rebalance requires weights for method: {method}")

    def clear_allocations(self):
        self.allocations.clear()

    def summary(self) -> Dict[str, float]:
        allocated = sum(a.allocated_capital for a in self.allocations.values())
        return {
            "total_capital": self.total_capital,
            "allocated_capital": allocated,
            "unallocated_capital": self.total_capital - allocated,
            "account_count": len(self.allocations),
        }
