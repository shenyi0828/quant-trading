"""风控规则引擎

使用责任链模式依次检查订单
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from risk_manager.base import RiskRule, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order


@dataclass
class RiskCheckReport:
    """风控检查报告"""
    order_id: str
    symbol: str
    results: List[RiskResult] = field(default_factory=list)
    final_action: RiskAction = RiskAction.ACCEPT
    rejected_by: Optional[str] = None
    rejected_message: Optional[str] = None
    
    @property
    def is_accepted(self) -> bool:
        return self.final_action == RiskAction.ACCEPT
    
    @property
    def is_rejected(self) -> bool:
        return self.final_action == RiskAction.REJECT
    
    @property
    def has_warnings(self) -> bool:
        return any(r.action == RiskAction.WARN for r in self.results)
    
    def get_warnings(self) -> List[RiskResult]:
        return [r for r in self.results if r.action == RiskAction.WARN]


class RiskChecker:
    """风控规则引擎
    
    使用责任链模式，订单依次通过所有规则检查
    
    Example:
        checker = RiskChecker()
        checker.add_rule(PositionLimitRule(max_ratio=0.3))
        checker.add_rule(OrderLimitRule(max_amount=50000))
        
        report = checker.check(order, context)
        if report.is_rejected:
            print(f"Rejected by {report.rejected_by}: {report.rejected_message}")
    """
    
    def __init__(self):
        self._rules: List[RiskRule] = []
    
    def add_rule(self, rule: RiskRule) -> "RiskChecker":
        """添加风控规则"""
        self._rules.append(rule)
        return self
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除风控规则"""
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                self._rules.pop(i)
                return True
        return False
    
    def get_rule(self, rule_name: str) -> Optional[RiskRule]:
        """获取指定规则"""
        for rule in self._rules:
            if rule.name == rule_name:
                return rule
        return None
    
    def enable_rule(self, rule_name: str) -> bool:
        """启用指定规则"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.enable()
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """禁用指定规则"""
        rule = self.get_rule(rule_name)
        if rule:
            rule.disable()
            return True
        return False
    
    def get_all_rules(self) -> List[RiskRule]:
        """获取所有规则"""
        return self._rules.copy()
    
    def clear_rules(self):
        """清除所有规则"""
        self._rules.clear()
    
    def check(self, order: Order, context: RiskContext) -> RiskCheckReport:
        """检查订单
        
        订单依次通过所有启用的规则检查，
        任一规则返回 REJECT 则订单被拦截
        
        Args:
            order: 待检查的订单
            context: 风控上下文
            
        Returns:
            RiskCheckReport: 包含所有规则检查结果的报告
        """
        report = RiskCheckReport(
            order_id=order.order_id,
            symbol=order.symbol
        )
        
        for rule in self._rules:
            if not rule.enabled:
                continue
            
            result = rule.check(order, context)
            report.results.append(result)
            
            if result.action == RiskAction.REJECT:
                report.final_action = RiskAction.REJECT
                report.rejected_by = rule.name
                report.rejected_message = result.message
                break
        
        return report
    
    def check_all(self, orders: List[Order], context: RiskContext) -> Dict[str, RiskCheckReport]:
        """批量检查多个订单"""
        return {
            order.order_id: self.check(order, context)
            for order in orders
        }
    
    def __repr__(self) -> str:
        enabled_count = sum(1 for r in self._rules if r.enabled)
        return f"RiskChecker(rules={len(self._rules)}, enabled={enabled_count})"