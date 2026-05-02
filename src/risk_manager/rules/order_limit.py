"""单笔订单限额规则

限制单笔订单的金额不超过设定阈值
"""
from risk_manager.base import RiskRule, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order


class OrderLimitRule(RiskRule):
    """单笔订单金额限制规则
    
    确保单笔订单金额不超过设定的最大值
    
    Example:
        rule = OrderLimitRule(max_amount=50000)  # 单笔最大5万元
    """
    
    def __init__(
        self,
        name: str = "order_limit",
        max_amount: float = 50000.0,
        enabled: bool = True
    ):
        super().__init__(name=name, enabled=enabled)
        self.max_amount = max_amount
    
    def check(self, order: Order, context: RiskContext) -> RiskResult:
        if not self._enabled:
            return RiskResult(
                action=RiskAction.ACCEPT,
                rule_name=self.name,
                message="Rule disabled"
            )
        
        order_value = order.price * order.quantity
        
        if order_value > self.max_amount:
            return RiskResult(
                action=RiskAction.REJECT,
                rule_name=self.name,
                message=f"Order amount exceeded: {order_value:.2f} (max: {self.max_amount:.2f})",
                details={
                    "symbol": order.symbol,
                    "order_value": order_value,
                    "max_amount": self.max_amount,
                    "quantity": order.quantity,
                    "price": order.price
                }
            )
        
        return RiskResult(
            action=RiskAction.ACCEPT,
            rule_name=self.name,
            message="Order limit check passed",
            details={"order_value": order_value}
        )