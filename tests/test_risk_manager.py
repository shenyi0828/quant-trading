"""风控管理模块测试"""
import pytest
from datetime import date
from unittest.mock import Mock

from risk_manager import (
    RiskContext,
    RiskResult,
    RiskAction,
    RiskChecker,
    PositionMonitor,
    StopLossTakeProfit,
    PositionLimitRule,
    OrderLimitRule,
    DailyLossLimitRule,
    ConcentrationRule,
)
from risk_manager.monitor import Alert, AlertType
from strategy_engine.types import Order, Position, Direction, OrderType, OrderStatus


class TestRiskContext:
    """RiskContext 测试"""
    
    def test_total_value_calculation(self):
        context = RiskContext(
            total_capital=100000,
            available_cash=80000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=100,
                    avg_cost=10.0,
                    current_price=12.0
                )
            }
        )
        
        assert context.total_position_value == 1200
        assert context.total_value == 81200
    
    def test_return_rate_calculation(self):
        context = RiskContext(
            total_capital=100000,
            available_cash=110000,
            initial_capital=100000
        )
        
        assert context.total_profit == 10000
        assert context.return_rate == 0.1
    
    def test_get_position_weight(self):
        context = RiskContext(
            total_capital=100000,
            available_cash=80000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=100,
                    avg_cost=10.0,
                    current_price=20.0
                )
            }
        )
        
        weight = context.get_position_weight("000001")
        assert weight == 2000 / 82000
    
    def test_get_position_not_exists(self):
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        assert context.get_position("999999") is None
        assert context.get_position_value("999999") == 0.0


class TestPositionLimitRule:
    """仓位限制规则测试"""
    
    def setup_method(self):
        self.rule = PositionLimitRule(max_ratio=0.3)
    
    def test_accept_order_within_limit(self):
        order = Order(
            order_id="ORD_001",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
        assert result.action == RiskAction.ACCEPT
    
    def test_reject_order_exceeds_limit(self):
        order = Order(
            order_id="ORD_002",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=4000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=100,
                    avg_cost=10.0,
                    current_price=10.0
                )
            }
        )
        
        result = self.rule.check(order, context)
        assert result.is_rejected
        assert result.action == RiskAction.REJECT
    
    def test_sell_order_always_accepted(self):
        order = Order(
            order_id="ORD_003",
            symbol="000001",
            direction=Direction.SHORT,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
    
    def test_disabled_rule_always_accepts(self):
        rule = PositionLimitRule(max_ratio=0.3, enabled=False)
        order = Order(
            order_id="ORD_004",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=10000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        result = rule.check(order, context)
        assert result.is_accepted
    
    def test_enable_disable_rule(self):
        rule = PositionLimitRule(max_ratio=0.3, enabled=False)
        assert not rule.enabled
        
        rule.enable()
        assert rule.enabled
        
        rule.disable()
        assert not rule.enabled


class TestOrderLimitRule:
    """单笔订单限额规则测试"""
    
    def setup_method(self):
        self.rule = OrderLimitRule(max_amount=50000)
    
    def test_accept_order_within_limit(self):
        order = Order(
            order_id="ORD_001",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=4000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
    
    def test_reject_order_exceeds_limit(self):
        order = Order(
            order_id="ORD_002",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=6000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.is_rejected
        assert "60000.00" in result.message
    
    def test_order_details_in_result(self):
        order = Order(
            order_id="ORD_003",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=15.0,
            quantity=4000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.details["order_value"] == 60000
        assert result.details["quantity"] == 4000
        assert result.details["price"] == 15.0


class TestDailyLossLimitRule:
    """日亏损限额规则测试"""
    
    def setup_method(self):
        self.rule = DailyLossLimitRule(max_loss_ratio=0.05)
    
    def test_accept_when_no_loss(self):
        order = Order(
            order_id="ORD_001",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=0
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
    
    def test_accept_when_small_loss(self):
        order = Order(
            order_id="ORD_002",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=-3000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
    
    def test_reject_when_loss_exceeds_limit(self):
        order = Order(
            order_id="ORD_003",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=-6000
        )
        
        result = self.rule.check(order, context)
        assert result.is_rejected
    
    def test_sell_order_always_accepted(self):
        order = Order(
            order_id="ORD_004",
            symbol="000001",
            direction=Direction.SHORT,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=-6000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted


class TestConcentrationRule:
    """持仓集中度规则测试"""
    
    def setup_method(self):
        self.rule = ConcentrationRule(max_concentration=0.4, min_positions=3)
    
    def test_accept_first_position(self):
        order = Order(
            order_id="ORD_001",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted
    
    def test_reject_excessive_concentration(self):
        order = Order(
            order_id="ORD_003",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=5000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=50000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=5000,
                    avg_cost=10.0,
                    current_price=10.0
                )
            }
        )
        
        result = self.rule.check(order, context)
        assert result.is_rejected
    
    def test_sell_order_always_accepted(self):
        order = Order(
            order_id="ORD_004",
            symbol="000001",
            direction=Direction.SHORT,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=100
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=50000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=5000,
                    avg_cost=10.0,
                    current_price=10.0
                )
            }
        )
        
        result = self.rule.check(order, context)
        assert result.is_accepted


class TestRiskChecker:
    """风控规则引擎测试"""
    
    def setup_method(self):
        self.checker = RiskChecker()
        self.checker.add_rule(OrderLimitRule(max_amount=50000))
        self.checker.add_rule(PositionLimitRule(max_ratio=0.3))
    
    def test_accept_valid_order(self):
        order = Order(
            order_id="ORD_001",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=2000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        report = self.checker.check(order, context)
        assert report.is_accepted
        assert len(report.results) == 2
    
    def test_reject_by_first_rule(self):
        order = Order(
            order_id="ORD_002",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=6000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000
        )
        
        report = self.checker.check(order, context)
        assert report.is_rejected
        assert report.rejected_by == "order_limit"
    
    def test_reject_by_second_rule(self):
        checker = RiskChecker()
        checker.add_rule(PositionLimitRule(max_ratio=0.1))
        checker.add_rule(OrderLimitRule(max_amount=100000))
        
        order = Order(
            order_id="ORD_003",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=2000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        report = checker.check(order, context)
        assert report.is_rejected
        assert report.rejected_by == "position_limit"
    
    def test_enable_disable_rules(self):
        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=1000, enabled=False))
        
        order = Order(
            order_id="ORD_004",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=10.0,
            quantity=10000
        )
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        report = checker.check(order, context)
        assert report.is_accepted
        
        checker.enable_rule("order_limit")
        report = checker.check(order, context)
        assert report.is_rejected
    
    def test_remove_rule(self):
        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=1000))
        
        assert len(checker.get_all_rules()) == 1
        assert checker.remove_rule("order_limit")
        assert len(checker.get_all_rules()) == 0
    
    def test_check_multiple_orders(self):
        orders = [
            Order(
                order_id="ORD_001",
                symbol="000001",
                direction=Direction.LONG,
                order_type=OrderType.MARKET,
                price=10.0,
                quantity=1000
            ),
            Order(
                order_id="ORD_002",
                symbol="000002",
                direction=Direction.LONG,
                order_type=OrderType.MARKET,
                price=10.0,
                quantity=10000
            ),
        ]
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        reports = self.checker.check_all(orders, context)
        assert len(reports) == 2
        assert reports["ORD_001"].is_accepted
        assert reports["ORD_002"].is_rejected
    
    def test_chain_builder_pattern(self):
        checker = RiskChecker()
        checker.add_rule(PositionLimitRule(max_ratio=0.3)).add_rule(OrderLimitRule(max_amount=50000))
        
        assert len(checker.get_all_rules()) == 2


class TestStopLossTakeProfit:
    """止损止盈引擎测试"""
    
    def setup_method(self):
        self.sltp = StopLossTakeProfit()
    
    def test_stop_loss_by_price(self):
        self.sltp.set_stop_loss("000001", stop_loss_price=9.0)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=8.5
            )
        }
        
        alerts = self.sltp.check_positions(
            positions,
            {"000001": 8.5},
            date.today()
        )
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.STOP_LOSS
    
    def test_stop_loss_by_ratio(self):
        self.sltp.set_stop_loss("000001", stop_loss_ratio=0.1)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=8.5
            )
        }
        
        alerts = self.sltp.check_positions(
            positions,
            {"000001": 8.5},
            date.today()
        )
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.STOP_LOSS
    
    def test_take_profit_by_price(self):
        self.sltp.set_take_profit("000001", take_profit_price=12.0)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=13.0
            )
        }
        
        alerts = self.sltp.check_positions(
            positions,
            {"000001": 13.0},
            date.today()
        )
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.TAKE_PROFIT
    
    def test_take_profit_by_ratio(self):
        self.sltp.set_take_profit("000001", take_profit_ratio=0.2)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=13.0
            )
        }
        
        alerts = self.sltp.check_positions(
            positions,
            {"000001": 13.0},
            date.today()
        )
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.TAKE_PROFIT
    
    def test_no_alert_when_not_triggered(self):
        self.sltp.set_stop_loss("000001", stop_loss_ratio=0.1)
        self.sltp.set_take_profit("000001", take_profit_ratio=0.2)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=10.5
            )
        }
        
        alerts = self.sltp.check_positions(
            positions,
            {"000001": 10.5},
            date.today()
        )
        
        assert len(alerts) == 0
    
    def test_remove_config(self):
        self.sltp.set_stop_loss("000001", stop_loss_ratio=0.1)
        assert self.sltp.get_config("000001") is not None
        
        self.sltp.remove_config("000001")
        assert self.sltp.get_config("000001") is None


class TestPositionMonitor:
    """持仓监控器测试"""
    
    def setup_method(self):
        self.monitor = PositionMonitor()
    
    def test_position_weight_warning(self):
        self.monitor.set_position_warning_threshold(weight=0.3)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=4000,
                avg_cost=10.0,
                current_price=10.0
            )
        }
        context = RiskContext(
            total_capital=100000,
            available_cash=60000,
            initial_capital=100000
        )
        
        alerts = self.monitor.monitor(positions, context)
        
        weight_warnings = [a for a in alerts if a.alert_type == AlertType.POSITION_WARNING]
        assert len(weight_warnings) == 1
    
    def test_loss_warning(self):
        self.monitor.set_warning_threshold(loss_ratio=0.05)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=9.0
            )
        }
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        alerts = self.monitor.monitor(positions, context)
        
        loss_warnings = [a for a in alerts if a.alert_type == AlertType.LOSS_WARNING]
        assert len(loss_warnings) == 1
    
    def test_alert_callback(self):
        callback = Mock()
        self.monitor.add_alert_callback(callback)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=5.0
            )
        }
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        self.monitor.monitor(positions, context)
        
        assert callback.called
    
    def test_integrated_stop_loss(self):
        sltp = self.monitor.get_stop_loss_engine()
        sltp.set_stop_loss("000001", stop_loss_ratio=0.1)
        
        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=8.5
            )
        }
        context = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000
        )
        
        alerts = self.monitor.monitor(positions, context)
        
        stop_loss_alerts = [a for a in alerts if a.alert_type == AlertType.STOP_LOSS]
        assert len(stop_loss_alerts) == 1


class TestRiskResult:
    """RiskResult 测试"""
    
    def test_is_accepted_property(self):
        result = RiskResult(action=RiskAction.ACCEPT, rule_name="test")
        assert result.is_accepted
        assert not result.is_rejected
    
    def test_is_rejected_property(self):
        result = RiskResult(action=RiskAction.REJECT, rule_name="test")
        assert result.is_rejected
        assert not result.is_accepted


class TestAlert:
    """Alert 测试"""
    
    def test_alert_creation(self):
        alert = Alert(
            alert_type=AlertType.STOP_LOSS,
            symbol="000001",
            message="Stop loss triggered",
            trigger_price=9.0,
            current_price=8.5,
            timestamp=date.today()
        )
        
        assert alert.alert_type == AlertType.STOP_LOSS
        assert alert.symbol == "000001"
        assert alert.trigger_price == 9.0
        assert alert.current_price == 8.5