"""日亏损限额规则

限制当日累计亏损不超过总资产的设定比例
"""
from risk_manager.base import RiskRule, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order, Direction


class DailyLossLimitRule(RiskRule):
    """当日亏损限额规则
    
    当日累计亏损达到阈值时，禁止继续买入
    
    Example:
        rule = DailyLossLimitRule(max_loss_ratio=0.05)  # 最大亏损5%
    """
    
    def __init__(
        self,
        name: str = "daily_loss_limit",
        max_loss_ratio: float = 0.05,
        enabled: bool = True
    ):
        super().__init__(name=name, enabled=enabled)
        self.max_loss_ratio = max_loss_ratio
    
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
                message="Daily loss limit only applies to buy orders"
            )
        
        daily_loss_ratio = abs(context.daily_pnl) / context.initial_capital if context.daily_pnl < 0 else 0
        
        if daily_loss_ratio >= self.max_loss_ratio:
            return RiskResult(
                action=RiskAction.REJECT,
                rule_name=self.name,
                message=f"Daily loss limit exceeded: {daily_loss_ratio:.2%} (max: {self.max_loss_ratio:.2%})",
                details={
                    "daily_pnl": context.daily_pnl,
                    "daily_loss_ratio": daily_loss_ratio,
                    "max_loss_ratio": self.max_loss_ratio,
                    "initial_capital": context.initial_capital
                }
            )
        
        return RiskResult(
            action=RiskAction.ACCEPT,
            rule_name=self.name,
            message="Daily loss limit check passed",
            details={"daily_pnl": context.daily_pnl}
        )