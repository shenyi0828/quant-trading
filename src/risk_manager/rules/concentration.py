"""持仓集中度限制规则

限制持仓集中度，确保持仓分散化
"""
from risk_manager.base import RiskRule, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order, Direction
from typing import List


class ConcentrationRule(RiskRule):
    """持仓集中度限制规则
    
    确保持仓不会过度集中在少数几只股票
    
    计算方式：
    - 使用赫芬达尔指数（Herfindahl Index）衡量集中度
    - H = Σ(wi²)，其中 wi 为各持仓权重
    - H 越大表示集中度越高
    
    Example:
        rule = ConcentrationRule(max_concentration=0.4)  # 最大集中度40%
    """
    
    def __init__(
        self,
        name: str = "concentration_limit",
        max_concentration: float = 0.4,
        min_positions: int = 3,
        enabled: bool = True
    ):
        super().__init__(name=name, enabled=enabled)
        self.max_concentration = max_concentration
        self.min_positions = min_positions
    
    def _calculate_herfindahl_index(self, weights: List[float]) -> float:
        """计算赫芬达尔指数"""
        return sum(w ** 2 for w in weights)
    
    def check(self, order: Order, context: RiskContext) -> RiskResult:
        if not self._enabled:
            return RiskResult(
                action=RiskAction.ACCEPT,
                rule_name=self.name,
                message="Rule disabled"
            )
        
        if order.direction != Direction.LONG:
            return RiskResult(
                action=RiskAction.ACCEPT,
                rule_name=self.name,
                message="Concentration limit only applies to buy orders"
            )
        
        if context.total_value == 0:
            return RiskResult(
                action=RiskAction.ACCEPT,
                rule_name=self.name,
                message="No existing positions"
            )
        
        order_value = order.price * order.quantity
        new_total_value = context.total_value + order_value
        
        current_weights = []
        for symbol, pos in context.positions.items():
            weight = pos.market_value / new_total_value
            current_weights.append(weight)
        
        new_symbol_weight = order_value / new_total_value
        
        existing_pos = context.get_position(order.symbol)
        if existing_pos:
            existing_weight = existing_pos.market_value / new_total_value
            combined_weight = existing_weight + new_symbol_weight
            current_weights = [w for w in current_weights if w != existing_weight]
            current_weights.append(combined_weight)
        else:
            current_weights.append(new_symbol_weight)
        
        herfindahl_index = self._calculate_herfindahl_index(current_weights)
        
        position_count = len(context.positions) + (1 if not existing_pos else 0)
        
        if position_count < self.min_positions and herfindahl_index > self.max_concentration:
            return RiskResult(
                action=RiskAction.REJECT,
                rule_name=self.name,
                message=f"Concentration too high: H={herfindahl_index:.4f}, positions={position_count} (min: {self.min_positions})",
                details={
                    "herfindahl_index": herfindahl_index,
                    "max_concentration": self.max_concentration,
                    "position_count": position_count,
                    "min_positions": self.min_positions,
                    "weights": current_weights
                }
            )
        
        if herfindahl_index > self.max_concentration and position_count >= self.min_positions:
            return RiskResult(
                action=RiskAction.WARN,
                rule_name=self.name,
                message=f"High concentration warning: H={herfindahl_index:.4f}",
                details={
                    "herfindahl_index": herfindahl_index,
                    "max_concentration": self.max_concentration,
                    "position_count": position_count
                }
            )
        
        return RiskResult(
            action=RiskAction.ACCEPT,
            rule_name=self.name,
            message="Concentration check passed",
            details={
                "herfindahl_index": herfindahl_index,
                "position_count": position_count
            }
        )