"""仓位限制规则

限制单只股票的持仓占总资产的比例不超过设定阈值
"""
from risk_manager.base import RiskRule, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order, Direction


class PositionLimitRule(RiskRule):
    """单只股票仓位限制规则
    
    确保单只股票的持仓市值不超过总资产的指定比例
    
    Example:
        rule = PositionLimitRule(max_ratio=0.3)  # 最大30%
    """
    
    def __init__(
        self, 
        name: str = "position_limit",
        max_ratio: float = 0.3,
        enabled: bool = True
    ):
        super().__init__(name=name, enabled=enabled)
        self.max_ratio = max_ratio
    
    def check(self, order: Order, context: RiskContext) -> RiskResult:
        if not self._enabled:
            return RiskResult(
                action=RiskAction.ACCEPT,
                rule_name=self.name,
                message="Rule disabled"
            )
        
        order_value = order.price * order.quantity
        
        if order.direction == Direction.LONG:
            current_position_value = context.get_position_value(order.symbol)
            new_position_value = current_position_value + order_value
            
            if context.total_value == 0:
                return RiskResult(
                    action=RiskAction.REJECT,
                    rule_name=self.name,
                    message=f"Position limit check: total_value is zero",
                    details={
                        "symbol": order.symbol,
                        "order_value": order_value,
                        "max_ratio": self.max_ratio
                    }
                )
            
            new_ratio = new_position_value / context.total_value
            
            if new_ratio > self.max_ratio:
                return RiskResult(
                    action=RiskAction.REJECT,
                    rule_name=self.name,
                    message=f"Position limit exceeded: {order.symbol} would be {new_ratio:.2%} (max: {self.max_ratio:.2%})",
                    details={
                        "symbol": order.symbol,
                        "current_value": current_position_value,
                        "order_value": order_value,
                        "new_value": new_position_value,
                        "new_ratio": new_ratio,
                        "max_ratio": self.max_ratio
                    }
                )
        
        return RiskResult(
            action=RiskAction.ACCEPT,
            rule_name=self.name,
            message="Position limit check passed"
        )